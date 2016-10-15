package com.beckett.IrcCommand;


import com.google.gson.annotations.SerializedName;

public class IrcAction {
    public Action action;

    public String message;
    public String channel;

    public IrcAction(Action action, String message, String channel) {
        this.action = action;
        this.message = message;
        this.channel = channel;
    }

    public enum Action {
        @SerializedName("JOIN")
        Join,
        @SerializedName("PART")
        Part,
        @SerializedName("SAY")
        Say,
    }
}
