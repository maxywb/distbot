package com.beckett;


import org.apache.kafka.clients.consumer.Consumer;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.Producer;

import java.util.Arrays;
import java.util.Properties;

public class IrcUtils {
    public static Producer<String, String> getProducer(String brokerConnection) {
        Properties producerProps = new Properties();
        producerProps.put("bootstrap.servers", brokerConnection);
        producerProps.put("acks", "all");
        producerProps.put("retries", 0);
        producerProps.put("batch.size", 16384);
        producerProps.put("linger.ms", 1);
        producerProps.put("buffer.memory", 33554432);
        producerProps.put("key.serializer",
                "org.apache.kafka.common.serialization.StringSerializer");
        producerProps.put("value.serializer",
                "org.apache.kafka.common.serialization.StringSerializer");

        return new KafkaProducer<String, String>(producerProps);
    }

    public static Consumer<String, String> getConsumer(String brokerConnection, String groupId, Type type) {
        Properties consumerProps = new Properties();
        consumerProps.put("bootstrap.servers", brokerConnection);
        consumerProps.put("group.id", groupId);
        consumerProps.put("enable.auto.commit", "true");
        consumerProps.put("auto.commit.interval.ms", "1000");
        consumerProps.put("session.timeout.ms", "30000");
        consumerProps.put("key.deserializer",
                "org.apache.kafka.common.serialization.StringDeserializer");
        consumerProps.put("value.deserializer",
                "org.apache.kafka.common.serialization.StringDeserializer");

        Consumer<String, String> consumer = new KafkaConsumer(consumerProps);

        switch (type) {
            case IrcListener:
                consumer.subscribe(Arrays.asList("irc-action"));
                break;
            case AllListener:
                consumer.subscribe(Arrays.asList("irc-action", "irc-publish"));
        }

        return consumer;
    }

    public enum Type {
        IrcListener,
        AllListener,
    }
}
