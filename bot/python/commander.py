#!/usr/bin/env python2.7
import json
import logging
import time

import kafka
import kazoo.client as kzc
import kazoo.recipe.watchers as kzw

logging.basicConfig()

consumer = kafka.KafkaConsumer(bootstrap_servers="192.168.1.201:9092",                               
                               group_id="irc-bot-commander",
                               enable_auto_commit=True,
                               auto_commit_interval_ms=1000,
                               session_timeout_ms=30000
)

producer = kafka.KafkaProducer(bootstrap_servers="192.168.1.201:9092")

def zk_listener(state):
    if state == kzc.KazooState.LOST:
        print("zk connection lost")
    elif state == kzc.KazooState.SUSPENDED:
        print("zk connection suspended")
    else:
        print("zk connection connected")



zk = kzc.KazooClient(hosts="192.168.1.201:2181")
zk.add_listener(zk_listener)
zk.start()

bad_users = set() # this should probably have a mutex but there's only one writer so...
@kzw.ChildrenWatch(zk, "/bot/config/ignore")
def watcher(nodes):
    global bad_users
    bad_users = bad_users.union(set(nodes))

def ignore_name(name):
    path = "/bot/config/ignore/%s" % name

    value = bytes(name, "utf-8")
    if zk.exists(path) is None:
        zk.create(path, value=value)
        bad_users.add(name)

def unignore_name(name):
    path = "/bot/config/ignore/%s" % name

    if zk.exists(path) is not None:
        zk.delete(path)
        bad_users.remove(name)

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

def handle_ignore(message, pieces):
    names = pieces[2:]

    for name in names:
        ignore_name(name)

    return {
        "timestamp" : get_millis(),
        "action" : "SAY",
        "channel" : message["destination"],
        "message" : "done",
    }

def handle_unignore(message, pieces):
    names = pieces[2:]

    for name in names:
        unignore_name(name)

    return {
        "timestamp" : get_millis(),
        "action" : "SAY",
        "channel" : message["destination"],
        "message" : "done",
    }

COMMANDS={
    "ping": handle_ping,
}

PRIV_COMMANDS={
    "ignore": handle_ignore,
    "unignore": handle_unignore,
    "say": handle_say,
    "join": handle_join,
    "part": handle_part,
}

rates = dict()
ten_seconds = 10000
def rate_limit(message):
    nick = message["nick"]
    ts = int(message["timestamp"])

    if nick not in rates:
        rates[nick] = list()

    rate_list = list()
    ten_seconds_ago = ts - ten_seconds
    for r in rates[nick]:
        if r < ten_seconds_ago:
            continue
        rate_list.append(r)

    rate_list.append(ts)

    rates[nick] = rate_list

    if len(rate_list) >= 4:
        bad_users.add(nick)
        return True, {
            "timestamp" : get_millis(),
            "action" : "SAY",
            "channel" : message["destination"],
            "message" : "chill out kid",
        }        
    else:
        bad_users.discard(nick)

    return False, None

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
        rate_limit(message)
        return 

    elif talking_to_me:
        pieces = text.split(" ")

        if text.startswith(ME):
            pieces = pieces[1:]

        if len(pieces) <= 0:
            return

        command = pieces[0]

        handler = COMMANDS.get(command, None)
        bail = False
        if handler is None:
            handler = PRIV_COMMANDS.get(command, None)
            
            if handler is None:
                handler = handle_bad_command
            elif message["hostmask"] != OWNER:
                parts = {
                    "timestamp" : get_millis(),
                    "action" : "SAY",
                    "channel" : message["destination"],
                    "message" : "%s: you can't do that" % message["nick"]
                }
                bail = True
        else:
            # rate limit
            bail, parts = rate_limit(message)

        if not bail:
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
