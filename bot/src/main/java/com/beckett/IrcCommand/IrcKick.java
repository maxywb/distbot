package com.beckett.IrcCommand;


import org.pircbotx.hooks.events.KickEvent;

public class IrcKick {

    public String nick;
    public String hostmask;
    public String channel;
    public String recipientNick;
    public String recipientHostmask;
    public String reason;

    public IrcKick(String channel, String nick, String hostmask, String recipientNick, String recipientHostmask, String reason) {
        this.channel = channel;
        this.nick = nick;
        this.hostmask = hostmask;
        this.recipientNick = recipientNick;
        this.recipientHostmask = recipientHostmask;
        this.reason = reason;
    }

    public IrcKick(KickEvent event) {
        this(event.getChannel().getName(),
                event.getUserHostmask().getNick(),
                event.getUserHostmask().getHostmask(),
                event.getRecipientHostmask().getNick(),
                event.getRecipientHostmask().getNick(),
                event.getReason());
    }

}
