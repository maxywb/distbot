package com.beckett.IrcCommand;


import org.pircbotx.hooks.events.JoinEvent;

public class IrcJoin {
    public long timestamp;
    public String nick;
    public String hostmask;
    public String channel;

    public IrcJoin(long timestamp, String channel, String nick, String hostmask) {
        this.timestamp = timestamp;
        this.channel = channel;
        this.nick = nick;
        this.hostmask = hostmask;
    }

    public IrcJoin(JoinEvent event) {
        this(event.getTimestamp(),
             event.getChannel().getName(),
                event.getUserHostmask().getNick(),
                event.getUserHostmask().getHostmask());
    }

}
