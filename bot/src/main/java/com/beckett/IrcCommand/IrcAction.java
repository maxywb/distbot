package com.beckett.IrcCommand;


import com.google.gson.annotations.SerializedName;

public class IrcAction {
    public long timestamp;
    public Action action;
    public String message;
    public String destination;

    public IrcAction(long timestamp, Action action, String message, String destination) {
        this.timestamp = timestamp;
        this.action = action;
        this.message = message;
        this.destination = destination;
    }

    public enum Action {
        @SerializedName("JOIN")
        Join,
        @SerializedName("PART")
        Part,
        @SerializedName("SAY")
        Say,
        @SerializedName("PRIVMSG")
        PrivateMessage,
    }
}
