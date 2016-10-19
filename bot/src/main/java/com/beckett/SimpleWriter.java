package com.beckett;
import java.util.HashMap;
import java.util.Map;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.FSDataOutputStream;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.Path;
import org.apache.kafka.clients.consumer.Consumer;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.clients.consumer.ConsumerRecords;

import java.io.IOException;

public class SimpleWriter {

  public static void main(String[] args) throws Exception, IOException {

    Consumer<String, String> consumer = IrcUtils.getConsumer("192.168.1.201:9092",
                                                             "irc-bot-listener",
                                                             IrcUtils.Type.AllListener);

    Configuration conf = new Configuration();
    conf.set("fs.defaultFS", "hdfs://192.168.1.201:9000/bot/logs");
    conf.set("hadoop.job.ugi", "hadoop");
    conf.set("dfs.client.use.datanode.hostname", "true");
    conf.set("dfs.client.block.write.replace-datanode-on-failure.policy","NEVER");

    FileSystem fs = FileSystem.get(conf);
        
    Map<Path, FSDataOutputStream> outputs = new HashMap();
    try {
      while (true) {
        ConsumerRecords<String, String> records = consumer.poll(100);
        for (ConsumerRecord<String, String> record : records) {
          Path path = null;
          if (record.topic().equals("irc-publish")) {
            path = new Path("/bot/logs/irc-publish");
          } else if (record.topic().equals("irc-action")) {
            path = new Path("/bot/logs/irc-action");
          } else {
            path = new Path("/bot/logs/misc");
          }

          if (record.key() != null) {
            path = new Path(path, record.key());
          } else {
            path = new Path(path, "default");
          }

          FSDataOutputStream stream;

          if (outputs.containsKey(path)) {
            stream = outputs.get(path);
          } else {
            try {
              stream = fs.create(path, false);
              stream.writeBytes("{\"start\":1}\n");
              stream.close();
            } catch (IOException e) {
              // nothing
            } finally {
              stream = fs.append(path);
            } 
            outputs.put(path, stream);
          }
                

          stream.writeBytes(record.value());
          stream.writeBytes("\n");
          stream.hsync();
          
          System.out.println(String.format("%s - %s: %s",
                                           record.topic(), record.key(), record.value()));


        }
      }
    } catch (Exception e) {
      for (Map.Entry<Path, FSDataOutputStream> entry : outputs.entrySet()) {
        entry.getValue().close();
      }
      fs.close();
      throw e;
    }
  }
}
