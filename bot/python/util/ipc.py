import logging
import kafka

class Consumer():
    def __init__(self, server, name, topic):
        self.consumer = kafka.KafkaConsumer(bootstrap_servers=server,
                                            group_id=name,
                                            enable_auto_commit=True,
                                            auto_commit_interval_ms=1000,
                                            session_timeout_ms=30000
        )

        # take control of the partitions and don't handle queued messages
        # sort of stupuid to do, but since there's only one commander...
        for partition in self.consumer.partitions_for_topic(topic):
            tp = kafka.structs.TopicPartition(topic, partition)

            self.consumer.assign([tp])
            self.consumer.seek_to_end(tp)
        
    def __iter__(self):
        for message in self.consumer:
            yield message

class Producer():
    def __init__(self, server, topic):
        self.producer = kafka.KafkaProducer(bootstrap_servers=server)
        self.topic = topic

        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(logging.INFO)

    def send(self, message):
        text = message.wire_repr()
        self.log.info("sending: %s" % text)
        self.producer.send(self.topic, bytes(text, "utf-8"))        

if __name__ == "__main__":
    import sys, time, json

    if sys.argv[1] == "consumer":
        c = Consumer(server="192.168.1.201:9092",
                     topic="irc-publish",
                     name="irc-bot-commander")
        for message in c:
            print(message)
    else:
        p = Producer(server="192.168.1.201:9092",
                     topic="irc-action")

        message = json.dumps({
            "timestamp" : int(round(time.time() * 1000)),
            "action" : "SAY",
            "destination" : "#boatz",
            "message" : "testing",
        })

        p.send(message)
