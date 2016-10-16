package com.beckett;

import com.beckett.IrcCommand.IrcAction;
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
import org.pircbotx.exception.IrcException;
import org.pircbotx.hooks.ListenerAdapter;
import org.pircbotx.hooks.events.*;

import javax.net.ssl.SSLSocketFactory;
import java.io.IOException;
import java.util.concurrent.atomic.AtomicBoolean;

public class IrcConnector extends ListenerAdapter implements Runnable {
    private Producer<String, String> producer;
    private Consumer<String, String> consumer;
    private PircBotX bot;
    private AtomicBoolean running = new AtomicBoolean();
    private static final String PUBLISH_TOPIC = "irc-publish";

    IrcConnector() {
        this.producer = IrcUtils.getProducer("192.168.1.201:9092");
        this.consumer = IrcUtils.getConsumer("192.168.1.201:9092",
                "irc-bot",
                IrcUtils.Type.IrcListener);

        this.running.set(true);
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
                    System.out.println(e);
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
            System.out.println(e);
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
            System.out.println(e);
        }
    }

    private void say(String channel, String message) {
        try {
            Channel dest = bot.getUserChannelDao().getChannel(channel);
            dest.send().message(message);
        } catch (DaoException e) {
            System.out.println(e);
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

    public static void main(String[] args) throws IOException, IrcException {

        IrcConnector connector = new IrcConnector();

        Configuration configuration = new Configuration.Builder()
                .setName("boatz")
                .addServer("irc.rizon.net", 9999)
                .setSocketFactory(SSLSocketFactory.getDefault())
                .addAutoJoinChannel("#boatz")
                .addListener(connector)
                .setAutoNickChange(true)
                .buildConfiguration();

        PircBotX bot = new PircBotX(configuration);
        connector.setBot(bot);
        (new Thread(connector)).start();
        // has to happen last!
        bot.startBot();
    }


}
