package com.beckett;

import com.beckett.IrcCommand.*;
import com.google.gson.Gson;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.pircbotx.hooks.events.*;

public class IrcMessageConverter {
    private static Gson gson = new Gson();

    public static String toJson(JoinEvent event) {
        return gson.toJson(new IrcJoin(event));
    }

    public static String toJson(KickEvent event) {
        return gson.toJson(new IrcKick(event));
    }

    public static String toJson(MessageEvent event) {
        return gson.toJson(new IrcMessage(event));
    }

    public static String toJson(PrivateMessageEvent event) {
        return gson.toJson(new IrcMessage(event));
    }

    public static String toJson(PartEvent event) {
        return gson.toJson(new IrcPart(event));
    }

    public static IrcAction parseAction(ConsumerRecord<String, String> record) {
        return gson.fromJson(record.value(), IrcAction.class);
    }

    public static String toJson(IncomingChatRequestEvent event, String line) {
        return gson.toJson(new IrcMessage(event, line));

    }
}
