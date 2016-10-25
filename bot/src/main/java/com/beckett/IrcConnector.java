package com.beckett;

import com.beckett.IrcCommand.IrcAction;
import org.apache.curator.framework.CuratorFramework;
import org.apache.curator.framework.recipes.cache.ChildData;
import org.apache.curator.framework.recipes.cache.TreeCacheEvent;
import org.apache.curator.framework.recipes.cache.TreeCacheListener;
import org.apache.kafka.clients.consumer.Consumer;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.pircbotx.Channel;
import org.pircbotx.Configuration;
import org.pircbotx.PircBotX;
import org.pircbotx.dcc.ReceiveChat;
import org.pircbotx.exception.DaoException;
import org.pircbotx.hooks.ListenerAdapter;
import org.pircbotx.hooks.events.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.net.ssl.SSLSocketFactory;
import java.util.Arrays;
import java.util.LinkedList;
import java.util.List;
import java.util.Random;
import java.util.concurrent.atomic.AtomicBoolean;

public class IrcConnector extends ListenerAdapter implements Runnable, TreeCacheListener {
    private static final Logger log = LoggerFactory.getLogger(IrcConnector.class);

    private Producer<String, String> producer;
    private Consumer<String, String> consumer;
    private PircBotX bot;
    private AtomicBoolean running = new AtomicBoolean();
    private static final String PUBLISH_TOPIC = "irc-publish";
    private ZkConnector zk;

    IrcConnector(ZkConnector zk) throws Exception {
        Random r = new Random();
        this.zk = zk;
        this.producer = IrcUtils.getProducer("192.168.1.201:9092");
        this.consumer = IrcUtils.getConsumer("192.168.1.201:9092",
                "irc-bot" + r.nextInt(255),
                IrcUtils.Type.IrcListener);

        this.running.set(true);

        this.registerForConfig();
    }

    private void registerForConfig() throws Exception {
        zk.registerTreeListener("/bot/config", this);
    }

    public void setBot(PircBotX bot) {
        this.bot = bot;
    }

    /**
     * listen for kafka commands
     */
    public void run() {
        while (this.running.get()) {
            ConsumerRecords<String, String> records = consumer.poll(100);
            for (ConsumerRecord<String, String> record : records) {
                IrcAction next = null;
                try {
                    next = IrcMessageConverter.parseAction(record);
                } catch (Exception e) {
                    log.error(e.toString());
                    continue;
                }
                if (!next.channel.startsWith("#")) {
                    next.channel = "#" + next.channel;
                }
                switch (next.action) {
                    case Join:
                        join(next.channel, next.message);
                        break;
                    case Part:
                        part(next.channel, next.message);

                        break;
                    case Say:
                        say(next.channel, next.message);
                        break;
                }
            }

        }

    }

    private void part(String channel, String message) {
        try {
            Channel c = bot.getUserChannelDao().getChannel(channel);
            c.send().part(message);
        } catch (DaoException e) {
            log.error(e.toString());
        }
    }

    private void join(String channel, String key) {
        try {
            if (key.equals("")) {
                bot.send().joinChannel(channel);
            } else {
                bot.send().joinChannel(channel, key);
            }
        } catch (DaoException e) {
            log.error(e.toString());
        }
    }

    private void say(String channel, String message) {
        try {
            Channel dest = bot.getUserChannelDao().getChannel(channel);
            dest.send().message(message);
        } catch (DaoException e) {
            log.error(e.toString());
        }
    }

    private void publish(String key, String value) {
        producer.send(new ProducerRecord<String, String>(PUBLISH_TOPIC, key, value));
    }

    @Override
    public void onJoin(JoinEvent event) {
        publish("on-join", IrcMessageConverter.toJson(event));
    }

    @Override
    public void onPart(PartEvent event) {
        publish("on-part", IrcMessageConverter.toJson(event));
    }

    @Override
    public void onKick(KickEvent event) {
        publish("on-kick", IrcMessageConverter.toJson(event));
    }

    @Override
    public void onMessage(MessageEvent event) {
        publish("on-msg", IrcMessageConverter.toJson(event));
    }

    @Override
    public void onPrivateMessage(PrivateMessageEvent event) {
        publish("on-privmsg", IrcMessageConverter.toJson(event));
    }

    @Override
    public void onIncomingChatRequest(IncomingChatRequestEvent event) throws Exception {
        producer.send(new ProducerRecord<String, String>(PUBLISH_TOPIC, "DCC-init", event.toString()));

        ReceiveChat chat;
        if (event.getUserHostmask().getHostname().equals("never.knows.best")) {
            chat = event.accept();
        } else {
            event.respond("go away");
            return;
        }

        // keep reading lines until the line is null, signaling the end of the connection
        String line;
        while ((line = chat.readLine()) != null) {
            publish("on-dcc", IrcMessageConverter.toJson(event, line));
        }
    }

    public void childEvent(CuratorFramework curator, TreeCacheEvent event) throws Exception {
        ChildData childData = event.getData();
        TreeCacheEvent.Type eventType = event.getType();

        switch (eventType) {
            case CONNECTION_SUSPENDED:
            case CONNECTION_RECONNECTED:
            case CONNECTION_LOST:
            case INITIALIZED:
                return;
            default:
        }

        String fullPath = childData.getPath();
        String path = fullPath.replace("/bot/config/", "");

        if (bot == null || !bot.isConnected()) {
            log.warn("zk config changed while bot was not connected, this change is being ignored");
            return;
        }
        String payload = new String(childData.getData());

        if (path.equals("name")) {
            if (eventType == TreeCacheEvent.Type.NODE_UPDATED) {
                // change nick
                bot.send().changeNick(payload);
            }
        } else if (path.startsWith("channels")) {
            switch (eventType) {
                case NODE_ADDED:
                    // join channel
                    join(payload, "");
                    break;
                case NODE_REMOVED:
                    // leave channel
                    part(payload, "bye");
                    break;
                default:
                    // nothing to do
                    break;
            }
        }

    }

    public static void main(String[] args) throws Exception {
        ZkConnector zk = new ZkConnector("192.168.1.201:2181");
        zk.blockUntilConnected();
        String nick = zk.getData("/bot/config/name", String.class);
        List<String> channels = zk.getChildren("/bot/config/channels");
        List<String> channelsWithHash = new LinkedList();
        for (String channel : channels) {
            String path = "/bot/config/channels/" + channel;
            String channelWithHash = "#" + zk.getData(path,String.class);
            channelsWithHash.add(channelWithHash);
        }

        if (args.length > 0) {
            nick = args[0];
            channelsWithHash = Arrays.asList("#" + args[1]);
        }

        IrcConnector connector = new IrcConnector(zk);

        Configuration configuration = new Configuration.Builder()
                .setName(nick)
                .addServer("irc.rizon.net", 9999)
                .setSocketFactory(SSLSocketFactory.getDefault())
                .addAutoJoinChannels(channelsWithHash)
                .addListener(connector)
                .setAutoNickChange(true)
                .buildConfiguration();

        PircBotX bot = new PircBotX(configuration);
        connector.setBot(bot);
        (new Thread(connector)).start();

        // has to happen last because i guess it's a blocking call
        bot.startBot();
    }


}
