#!/usr/bin/env python3

import datetime
import json
import time
import urllib

import pyspark

import util

FORMAT_STRING = "%(datetime)s - %(nick)s -> %(destination)s : %(message)s"


def get_timestamp(time):
    dt = datetime.datetime.fromtimestamp(time)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def get_messages():
    sc = pyspark.SparkContext("spark://192.168.1.201:7077", "bot")
    sc.addPyFile("/home/meatwad/prog/src/distbot/bot/python/spark.py")
    sc.addPyFile("/home/meatwad/prog/src/distbot/bot/python/util.py")

    text = sc.textFile("hdfs://192.168.1.201:9000/bot/logs/irc-publish/on-msg")
    def loader(line):
        try:
            blob = json.loads(line)
        except json.decoder.JSONDecodeError as e:
            return None

        blob["datetime"] = get_timestamp(blob["timestamp"] / 1000)
        return blob

    return text.map(loader).filter(lambda blob: blob is not None)   

def search(index, terms):
    is_string = isinstance(terms, str)
    if is_string:
        term = terms.lower()

    def list_search(blob):
        for term in terms:
            if term.lower() not in blob[index].lower:
                return False
        return True

    def single_search(blob):
        return term.lower() in blob[index].lower()

    return single_search if is_string else list_search

def make_paste(messages):
    content = "\n".join([FORMAT_STRING % msg for msg in messages])

    headers = {'User-Agent': 'Mozilla/5.0'}

    payload = {
        "Content" : urllib.parse.quote(content),
        "Title" : "test",
        "Syntax" : "text",
        "ExpireLength" : "1",
        "ExpireUnit" : "day",
        "Password" : "",
    }
    
    url = "https://api.teknik.io/v1/Paste"

    session = util.get_requests_session()

    result = session.post(url, headers=headers, data=payload).json()

    return result

CONVINIENCE_MAPPING = {
    "destination" : [
        "chan",
        "channel",
    ],
    "nick" : [
        "user",
        "name",
    ],
    "message" : [
        "msg",
        "text",
    ],
}

def do_search(args, message_limit):
    messages = get_messages()

    for index, terms in args.items():
        messages = messages.filter(search(index, terms))
    
    host_messages = messages.take(message_limit)

    print(make_paste(host_messages))

    if len(host_messages) == 0:
        text = "no results"
    else:
        text = " || ".join([FORMAT_STRING % msg for msg in host_messages])

    return text

def execute_command(query, message_limit=5):
    sub_command = query[1]
    args, query = util.tokenize(query[2:])

    # setup convinience mappings
    for real_name, nice_names in CONVINIENCE_MAPPING.items():
        for nice_name in nice_names:
            if nice_name in args:
                if real_name not in args:
                    args[real_name] = args[nice_name]
                del args[nice_name]

    # ensure channel # prefix
    if "destination" in args and args["destination"][0] != "#":
        args["destination"] = "#" + args["destination"]

    if sub_command == "search":
        return do_search(args, message_limit)
    else:
        return "no such command %s" % sub_command
if __name__ == "__main__":


    text = execute_command("spark search !nick=oatzhakok !msg=asdf !chan=boatz".split())
    print(text)

    quit()

    filtered_messages = blobs.filter(search("nick", "oatzhakok")).filter(search("message", "boatz"))

    for msg in filtered_messages.take(10):
        print(msg)
    print(filtered_messages.count())

    #result = make_paste(hello_messages)
    #print(result)


