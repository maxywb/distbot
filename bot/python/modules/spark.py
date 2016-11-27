#!/usr/bin/env python3

import datetime
import json
import time
import urllib
import contextlib

import pyspark

import util.message
import util.web

FORMAT_STRING = "%(datetime)s - %(nick)s -> %(destination)s : %(message)s"


def get_timestamp(time):
    dt = datetime.datetime.fromtimestamp(time)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def get_messages(sc):
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

    session = util.web.get_requests_session()

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

def do_search(sc, args, message_limit):
    messages = get_messages(sc)

    for index, terms in args.items():
        messages = messages.filter(search(index, terms))
    
    host_messages = messages.take(message_limit)

    print(make_paste(host_messages))

    if len(host_messages) == 0:
        text = "no results"
    else:
        text = " || ".join([FORMAT_STRING % msg for msg in host_messages])

    return text


@contextlib.contextmanager
def spark_context(spark_master, app_name, executor_memory="500m"):
    conf = pyspark.SparkConf().setMaster(spark_master) \
                      .setAppName(app_name) \
                      .set("spark.executor.memory", executor_memory)
    spark_context = pyspark.SparkContext(conf=conf)

    spark_context.addPyFile("/home/meatwad/prog/src/distbot/bot/python/modules/spark.py")
    spark_context.addPyFile("/home/meatwad/prog/src/distbot/bot/python/util/web.py")

    try:
        yield spark_context
    finally:
        spark_context.stop()

    

MODULE_CLASS_NAME="Spark"

MODULE_SUBCOMMAND="spark"

class Spark():
    def __init__(self, configuration, zk_client, **kwargs):

        self.configuration = configuration
        self.zk_client = zk_client

    def consume(self, message):
        return
        args = message["message"].args
        query = message["message"].command

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

        sub_command = query[1]
        if sub_command == "search":
            with spark_context("spark://192.168.1.201:7077", "bot") as sc:
                response = do_search(sc, args, 3)
        else:
            response = "no such command %s" % sub_command

        who = message["nick"]
        where = message["destination"]

        return util.message.Message(who, where, response)

