#!/usr/bin/env python3

import json
import logging
import requests
import sys
import time
import traceback

import kafka
import kazoo.client as kzc
import kazoo.recipe.watchers as kzw

import hockey
import util.web
import weather

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

my_name = "boatz"
@kzw.DataWatch(zk, "/bot/config/name")
def watcher(data, stat, event):
    global my_name
    if event is None or event.type == "CHANGED":
        my_name = data.decode("utf-8")


keys = {
    "google" : zk.get("/bot/config/key/google")[0].decode("utf-8"),
    "weather" : zk.get("/bot/config/key/weather")[0].decode("utf-8"),
    }

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

BASE_ACTION = '''
{
  "timestamp":"%(timestamp)s",
  "action":"%(action)s",
  "message":"%(message)s",
  "destination":"%(destination)s"
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
        "destination" : where,
        "message" : "%s: no such command %s" % (who, pieces[0])
    }

def handle_help(message, *args):
    where = message["destination"]

    base_message = "usage: %s: <command> <space separated arguments>" % my_name
    blobs = list()
    blobs.append(base_message)
    for command in COMMANDS.keys():
        try:
            text = COMMAND_HELP_TEXT[command]
        except KeyError:
            text = "\"%s\" - undocumented, sorry" % command
        blobs.append(text)

    text = "; ".join(blobs)
    text = text.replace('"', '\\"')

    return {
        "timestamp" : get_millis(),
        "action" : "SAY",
        "destination" : where,
        "message" : text,
    }
    

def handle_ping(message, pieces):
    who = message["nick"]
    where = message["destination"]

    return {
        "timestamp" : get_millis(),
        "action" : "SAY",
        "destination" : where,
        "message" : "%s: pong" % who
    }

def handle_weather(message, pieces):
    where = message["destination"]

    user = get_user(zk, message["nick"])

    if user is not None:
        try:
            if len(pieces) == 1:
                query = user["locations"]["default"].split()
                
            elif len(pieces) == 2:
                query = user["locations"][pieces[1]].split()
            else:
                query = pieces[1:]
        except KeyError:
            query = pieces[1:]            
    else:
        query = pieces[1:]
        

    text = weather.get_weather(keys, query)

    return {
        "timestamp" : get_millis(),
        "action" : "SAY",
        "destination" : where,
        "message" : text,
    }

def handle_forecast(message, pieces):
    where = message["destination"]

    user = get_user(zk, message["nick"])

    if user is not None:
        try:
            if len(pieces) == 1:
                query = user["locations"]["default"].split()
                
            elif len(pieces) == 2:
                query = user["locations"][pieces[1]].split()
            else:
                query = pieces[1:]
        except KeyError:
            query = pieces[1:]            
    else:
        query = pieces[1:]

    text = weather.get_forecast(keys, query)

    return {
        "timestamp" : get_millis(),
        "action" : "SAY",
        "destination" : where,
        "message" : text,
    }

def handle_hockey(message, pieces):
    where = message["destination"]

    query = pieces[1:]

    try:
        text = hockey.execute_command(query)
    except hockey.HockeyError as e:
        text = str(e).replace("'","")

    return {
        "timestamp" : get_millis(),
        "action" : "SAY",
        "destination" : where,
        "message" : text,
    }

def handle_say(message, pieces):
    who = message["nick"]
    where = pieces[1]
    text = " ".join(pieces[2:])
    return {
        "timestamp" : get_millis(),
        "action" : "SAY",
        "destination" : where,
        "message" : text,
    }

def handle_privmsg(message, pieces):
    ret = handle_say(message, pieces)
    ret["action"] = "PRIVMSG"
    return ret

def handle_ip(message, pieces):
    dom = util.web.get_dom_from_url("http://www.networksecuritytoolkit.org/nst/tools/ip.shtml")
    ip = dom.text.strip()
    return {
        "timestamp" : get_millis(),
        "action" : "PRIVMSG",
        "destination" : message["nick"],
        "message" : "your ip is: %s" % ip,
    }

def handle_join(message, pieces):
    where = pieces[1]
    text = pieces[2:] if len(pieces) >=2 else ""
    return {
        "timestamp" : get_millis(),
        "action" : "JOIN",
        "destination" : where,
        "message" : text,
    }

def handle_part(message, pieces):
    where = pieces[1]
    text = " ".join(pieces[2:]) if len(pieces) >=2 else "bye"
    return {
        "timestamp" : get_millis(),
        "action" : "PART",
        "destination" : where,
        "message" : text,
    }

def handle_ignore(message, pieces):
    names = pieces[2:]

    for name in names:
        ignore_name(name)

    return {
        "timestamp" : get_millis(),
        "action" : "SAY",
        "destination" : message["destination"],
        "message" : "done",
    }

def handle_unignore(message, pieces):
    names = pieces[2:]

    for name in names:
        unignore_name(name)

    return {
        "timestamp" : get_millis(),
        "action" : "SAY",
        "destination" : message["destination"],
        "message" : "done",
    }

def handle_config(message, pieces):
    action = pieces[1]
    path = "/".join(pieces[2:-1])
    base_path = "/bot/%s"
    data = pieces[-1].encode("utf-8")
    
    text = "done"

    def exists(path):
        return zk.exists(path) is not None

    if action == "create":
        real_path = base_path % path
        if not exists(real_path):
            zk.create(real_path, data)
        else:
            text = "path exists (%s)" % path
    elif action == "update":
        real_path = base_path % path
        if not exists(real_path):
            text = "path exists (%s)" % path
        else:
            zk.set(real_path, data)
    elif action == "delete":
        # no data, so all args are pathy
        path = "%s%s" % (path, data.decode("utf-8"))
        real_path = base_path % path
        if not exists(real_path):
            text = "path doesn't exist (%s)" % path
        else:
            zk.delete(real_path)
    elif action == "get":
        # no data, so all args are pathy
        path = "%s/%s" % (path, data.decode("utf-8"))
        real_path = base_path % path
        if not exists(real_path):
            text = "path doesn't exist (%s)" % path
        else:
            text = zk.get(real_path)[0].decode("utf-8")
    elif action == "get-children":
        # no data, so all args are pathy
        path = "%s/%s" % (path, data.decode("utf-8"))
        real_path = base_path % path
        if not exists(real_path):
            text = "path doesn't exist (%s)" % path
        else:
            text = ", ".join(zk.get_children(real_path))
            if text == "":
                text = "<none>"
    elif action == "help":
        text = "sub-commands: update, delete, get, get-children"
    else:
        text = "unknown action (%s)" % action


    return {
        "timestamp" : get_millis(),
        "action" : "SAY",
        "destination" : message["destination"],
        "message" : text,
    }

COMMAND_HELP_TEXT={
    "help": "\"help\" - print this text",
    "ping": "\"ping\" - repond with \"<nick>: pong\"",
    "weather": "\"weather <search terms>\" - respond with the current weather for the given location",
    "forecast": "\"forecast <search terms>\" - respond with 3 days forcast (including today), normalized to the appropriate timezone",
    "hockey": hockey.HELP_TEXT,
}

COMMANDS={
    "help":handle_help,
    "ping": handle_ping,
    "weather": handle_weather,
    "forecast": handle_forecast,
    "hockey": handle_hockey,
}

PRIV_COMMANDS={
    "ignore": handle_ignore,
    "unignore": handle_unignore,
    "say": handle_say,
    "privmsg": handle_privmsg,
    "join": handle_join,
    "part": handle_part,
    "config": handle_config,
    "ip": handle_ip,
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
            "destination" : message["destination"],
            "message" : "chill out kid",
        }        
    else:
        bad_users.discard(nick)

    return False, None

def handle_message(destination, message):
    text = message["message"]
    talking_to_me = text.startswith(my_name) or (destination in ["on-privmsg", "on-dcc"])
    if message["message"] in [".bots", "!bots"]:
        parts = {
            "timestamp" : get_millis(),
            "action" : "SAY",
            "destination" : message["destination"],
            "message" : "Reporting in! [java/python] https://github.com/maxywb/distbot",
            }
        
    elif message["nick"] in bad_users:
        rate_limit(message)
        return 

    elif talking_to_me:
        pieces = text.split()

        if text.startswith(my_name):
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
                    "destination" : message["destination"],
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
        if parts["destination"] == "PRIVMSG":
            parts["destination"] = message["nick"]
            parts["action"] = "PRIVMSG"
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

try:
    debug = sys.argv[1].lower() == "debug"
except IndexError:
    debug = False

while True:
    msg = next(consumer)
    if msg.key in [b"on-msg", b"on-privmsg", b"on-dcc"]:
        try:
            message = json.loads(msg.value.decode("utf-8"))
            handle_message(msg.key.decode("utf-8"), message)
        except Exception as e:
            traceback.print_exc()
    elif debug:
        print("no idea what this is", msg)
