package com.beckett.IrcCommand;


import org.pircbotx.hooks.events.JoinEvent;

public class IrcJoin {

    public String nick;
    public String hostmask;
    public String channel;

    public IrcJoin(String channel, String nick, String hostmask) {
        this.channel = channel;
        this.nick = nick;
        this.hostmask = hostmask;
    }

    public IrcJoin(JoinEvent event) {
        this(event.getChannel().getName(),
                event.getUserHostmask().getNick(),
                event.getUserHostmask().getHostmask());
    }

}
