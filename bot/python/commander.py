#!/usr/bin/env python2.7
import json
import time

import kafka



consumer = kafka.KafkaConsumer(bootstrap_servers="192.168.1.201:9092",                               
                               group_id="irc-bot-commander",
                               enable_auto_commit=True,
                               auto_commit_interval_ms=1000,
                               session_timeout_ms=30000
)

producer = kafka.KafkaProducer(bootstrap_servers="192.168.1.201:9092")

OWNER = "oatzhakok!~meatwad@never.knows.best"
ME = "boatz"

BASE_ACTION = '''
{
  "timestamp":"%(timestamp)s",
  "action":"%(action)s",
  "message":"%(message)s",
  "channel":"%(channel)s"
}
'''

def get_millis():
    return int(round(time.time() * 1000))

def handle_bad_command(message, pieces):
    who = message["nick"]
    where = message["destination"]

    return {
        "timestamp" : get_millis(),
        "action" : "SAY",
        "channel" : where,
        "message" : "%s: no such command %s" % (who, pieces[0])
    }

def handle_ping(message, pieces):
    who = message["nick"]
    where = message["destination"]

    return {
        "timestamp" : get_millis(),
        "action" : "SAY",
        "channel" : where,
        "message" : "%s: pong" % who
    }

def handle_say(message, pieces):
    who = message["nick"]
    where = pieces[1]
    text = " ".join(pieces[2:])
    return {
        "timestamp" : get_millis(),
        "action" : "SAY",
        "channel" : where,
        "message" : text,
    }

def handle_join(message, pieces):
    where = pieces[1]
    text = pieces[2:] if len(pieces) >=2 else ""
    return {
        "timestamp" : get_millis(),
        "action" : "JOIN",
        "channel" : where,
        "message" : text,
    }

def handle_part(message, pieces):
    where = pieces[1]
    text = " ".join(pieces[2:]) if len(pieces) >=2 else "bye"
    return {
        "timestamp" : get_millis(),
        "action" : "PART",
        "channel" : where,
        "message" : text,
    }

COMMANDS_WITH_OUTPUT={
    "ping": handle_ping,
    "say": handle_say,
    "join": handle_join,
    "part": handle_part,
}

bad_users = set()

def handle_message(channel, message):
    text = message["message"]
    talking_to_me = text.startswith(ME) or (channel in ["on-privmsg", "on-dcc"])
    if message["message"] in [".bots", "!bots"]:
        parts = {
            "timestamp" : get_millis(),
            "action" : "SAY",
            "channel" : message["destination"],
            "message" : "i'm a robot [java/python]"
            }
        
    elif message["nick"] in bad_users:
        return 

    elif message["hostmask"] != OWNER and talking_to_me:
        
        parts = {
            "timestamp" : get_millis(),
            "action" : "SAY",
            "channel" : message["destination"],
            "message" : "%s: i don't know you" % message["nick"]
            }
        bad_users.add(message["nick"])

    elif talking_to_me:
        pieces = text.split(" ")

        if text.startswith(ME):
            pieces = pieces[1:]

        command = pieces[0]

        handler = COMMANDS_WITH_OUTPUT.get(command, None)

        if handler is None:
            handler = handle_bad_command

        parts = handler(message, pieces)

    else:
        return

    if parts is not None:
        action = BASE_ACTION % parts
        action = json.dumps(json.loads(action))
        print("sending:", action)
        producer.send("irc-action", bytes(action, "utf-8"))


# take control of the partitions and don't handle queued messages
# sort of stupuid to do, but since there's only one commander...
for partition in consumer.partitions_for_topic("irc-publish"):
    tp = kafka.structs.TopicPartition("irc-publish", partition)

    consumer.assign([tp])

    consumer.seek_to_end(tp)

while True:

    msg = next(consumer)
    if msg.key in [b"on-msg", b"on-privmsg", b"on-dcc"]:
        try:
            message = json.loads(msg.value.decode("utf-8"))
            handle_message(msg.key.decode("utf-8"), message)
        except ValueError:
            print("json parse error: %s" % msg.value)
    else:
        print("no idea what this is", msg)
