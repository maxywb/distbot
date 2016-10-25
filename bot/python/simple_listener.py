import sys
import time

import kafka

consumer = kafka.KafkaConsumer(bootstrap_servers="192.168.1.201:9092",                               
                               group_id="test-listener",
                               enable_auto_commit=True,
                               auto_commit_interval_ms=1000,
                               session_timeout_ms=30000
)

topic = sys.argv[1]

# take control of the partitions and don't handle queued messages
# sort of stupuid to do, but since there's only one commander...
for partition in consumer.partitions_for_topic(topic):
    tp = kafka.structs.TopicPartition(topic, partition)

    consumer.assign([tp])

    consumer.seek_to_end(tp)

while True:

    msg = next(consumer)
    print(msg)






