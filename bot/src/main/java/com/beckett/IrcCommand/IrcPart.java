package com.beckett.IrcCommand;


import org.pircbotx.hooks.events.PartEvent;

public class IrcPart {

    public String nick;
    public String hostmask;
    public String channel;
    public String reason;

    public IrcPart(String channel, String nick, String hostmask, String reason) {
        this.channel = channel;
        this.nick = nick;
        this.hostmask = hostmask;
        this.reason = reason;
    }

    public IrcPart(PartEvent event) {
        this(event.getChannel().getName(),
                event.getUserHostmask().getNick(),
                event.getUserHostmask().getHostmask(),
                event.getReason());
    }
}
