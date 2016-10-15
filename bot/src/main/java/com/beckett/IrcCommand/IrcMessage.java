package com.beckett.IrcCommand;


import org.pircbotx.hooks.events.IncomingChatRequestEvent;
import org.pircbotx.hooks.events.MessageEvent;
import org.pircbotx.hooks.events.PrivateMessageEvent;

public class IrcMessage {

    public String message;
    public String nick;
    public String hostmask;
    public String destination;

    public IrcMessage(String message, String nick, String hostmask, String destination) {
        this.message = message;
        this.nick = nick;
        this.hostmask = hostmask;
        this.destination = destination;
    }

    public IrcMessage(MessageEvent event) {
        this(event.getMessage(),
                event.getUserHostmask().getNick(),
                event.getUserHostmask().getHostmask(),
                event.getChannelSource());
    }

    public IrcMessage(PrivateMessageEvent event) {
        this(event.getMessage(),
                event.getUserHostmask().getNick(),
                event.getUserHostmask().getHostmask(),
                "PRIVMSG"); // kinda hacky...
    }

    public IrcMessage(IncomingChatRequestEvent event, String line) {
        this(line, event.getUserHostmask().getNick(),
                event.getUserHostmask().getHostmask(),
                "DCC"); // kinda hacky...

    }
}
