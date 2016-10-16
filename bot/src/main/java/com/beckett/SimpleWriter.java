package com.beckett;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.Path;
import org.apache.kafka.clients.consumer.Consumer;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.hadoop.fs.FSDataOutputStream;

import java.io.IOException;

public class SimpleWriter {
    public static void main(String[] args) throws IOException {

        Consumer<String, String> consumer = IrcUtils.getConsumer("192.168.1.201:9092",
                "irc-bot-listener",
                IrcUtils.Type.AllListener);

        Configuration conf = new Configuration();
                    conf.set("fs.defaultFS", "hdfs://192.168.1.201:9000/bot/logs");
                    //conf.set("hadoop.job.ugi", "hadoop");
        FileSystem fs = FileSystem.get(conf);

        fs.create(new Path("/tmp/online"));

        while (true) {
            ConsumerRecords<String, String> records = consumer.poll(100);
            for (ConsumerRecord<String, String> record : records){
                Path path = null;
                if (record.topic() == "irc-publish") {
                    path = new Path("/bot/logs/irc-publish");
                } else if (record.topic() == "irc-publish") {
                    path = new Path("/bot/logs/irc-action");
                } else {
                    path = new Path("/bot/logs/misc");
                }

                if (record.key() != null) {
                    path = new Path(path, record.key());
                } else {
                    path = new Path(path, "default");
                }

                FSDataOutputStream stream = fs.append(path);

                stream.writeBytes(record.value());
                stream.writeBytes("\n");

                System.out.println(String.format("%s - %s: %s",
                        record.topic(), record.key(), record.value()));

                


            }
        }
    }


}
