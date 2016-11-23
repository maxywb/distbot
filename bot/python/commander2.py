#!/usr/bin/env python3

import importlib
import json
import logging
import os
import threading

import kazoo.recipe.watchers as kzw

import util.ipc
import util.zk
import util.tokenizer

class Commander():
    def __init__(self, zk_client, zk_tree="/bot", worker_count=2):
        self.zk_client = zk_client
        self.zk_tree = zk_tree

        def get_path(path):
            return os.path.join(self.zk_tree, path)

        # setup logger
        logging.basicConfig()
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(logging.DEBUG)
        
        # setup kafka
        kafka_name_path = get_path("config/commander/name")
        kafka_name = util.zk.get_data(self.zk_client, kafka_name_path)
        kafka_server_path = get_path("config/kafka")
        kafka_server_string = util.zk.get_data(zk_client, kafka_server_path)
        
        commander_consumer_topic_path = get_path("config/commander/consumer")
        commander_consumer_topic = util.zk.get_data(self.zk_client, commander_consumer_topic_path)
        self.consumer = util.ipc.Consumer(server=kafka_server_string,
                                          name=kafka_name,
                                          topic=commander_consumer_topic)

        commander_producer_topic_path = get_path("config/commander/producer")
        commander_producer_topic = util.zk.get_data(self.zk_client, commander_producer_topic_path)
        self.producer = util.ipc.Producer(server=kafka_server_string,
                                          topic=commander_producer_topic)

        # zk related setup
        bad_user_path = get_path("config/ignore")
        self.bad_users = util.zk.ChildrenSet(self.zk_client, bad_user_path)
        
        my_name_path = get_path("config/name")
        self.my_name = util.zk.get_data(self.zk_client, my_name_path)
        @kzw.DataWatch(zk_client, my_name_path)
        def my_name_watcher(data, stat, event):
            if event is None or event.type == "CHANGED":
                self.my_name = data.decode("utf-8")
        
        # modules
        self.handler_lock = threading.Lock()
        self.loaded_modules = set()
        self.handlers = {}

    def _unload_module(self, module_name):
        with self.handler_lock:
            del self.handlers[module_name]
            self.loaded_modules.discard(module_name)

    def _load_module(self, module_name):
        module_name = "modules." + module_name

        try:
            module = importlib.import_module(module_name)
            module_class = getattr(module, module.MODULE_CLASS_NAME)
            handler = module_class(self.zk_client, self.zk_tree)
        except (ImportError, AttributeError) as e:
            self.log.error(e)
            return
        except:
            self.log.exception("something went wrong while loading %s" % module_name)
            return

        with self.handler_lock:
            self.handlers[module_name] = handler
            self.loaded_modules.add(module_name)

    def _handle_message(self, message):
        results = list()

        with self.handler_lock:
            for _, handler in self.handlers.items():
                if handler.accepts(message)
                result = handler.consume(message)
                if result is not None:
                    results.append(result)
        
        if len(results) >= 1:
            if len(results) >= 2:
                log.error("more than one respondent to %s" % raw_message)
            self._respond(results[0])
            

    def _respond(self, response):
        print(response)

    def run(self):
        for raw_message in self.consumer:

            message = json.loads(raw_message.value.decode("utf-8"))
            topic = msg.key.decode("utf-8")
            talking_to_me = message["message"].startswith(self.my_name) or (destination in ["on-privmsg", "on-dcc"])

            message["raw_message"] = message["message"].split()
            message["message"] = util.tokenizer.tokenize(message["message"])

            self._handle_message(message)


if __name__ == "__main__":
    import kazoo.client as kzc

    zk_client = kzc.KazooClient(hosts="192.168.1.201:2181")
    zk_client.start()

    c = Commander(zk_client)

    c._load_module("ping")

    c.run()
