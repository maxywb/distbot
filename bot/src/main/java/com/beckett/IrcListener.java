package com.beckett;

import org.apache.kafka.clients.consumer.Consumer;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.clients.consumer.ConsumerRecords;

public class IrcListener {
    public static void main(String[] args) {

        Consumer<String, String> consumer = IrcUtils.getConsumer("192.168.1.201:9092",
                "irc-bot-listener",
                IrcUtils.Type.AllListener);


        while (true) {
            ConsumerRecords<String, String> records = consumer.poll(100);
            for (ConsumerRecord<String, String> record : records)
                System.out.println(String.format("%s - %s: %s",
                        record.topic(), record.key(), record.value()));
        }
    }


}
