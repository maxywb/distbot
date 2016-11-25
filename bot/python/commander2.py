#!/usr/bin/env python3

import importlib
import importlib.util
import json
import logging
import os
import threading
import traceback
import sys

import kazoo.recipe.watchers as kzw

import util.configuration
import util.ipc
import util.message
import util.tokenizer
import util.zk

class Commander():
    def __init__(self, zk_client, configuration, zk_tree="/bot", worker_count=2):
        self.zk_client = zk_client
        self.zk_tree = zk_tree

        self.configuration = configuration

        def get_path(path):
            return os.path.join(self.zk_tree, path)

        # setup logger
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(self.configuration.log_level)
        
        # setup kafka
        kafka_name_path = get_path("config/commander/name")
        kafka_name = util.zk.get_data(self.zk_client, kafka_name_path)
        kafka_server_path = get_path("config/kafka")
        kafka_server_string = util.zk.get_data(zk_client, kafka_server_path)
        
        # consumer (read from wire)
        commander_consumer_topic_path = get_path("config/commander/consumer")
        commander_consumer_topic = util.zk.get_data(self.zk_client, commander_consumer_topic_path)
        self.consumer = util.ipc.Consumer(server=kafka_server_string,
                                          name=kafka_name,
                                          topic=commander_consumer_topic,
                                          configuration=self.configuration)

        # consumer (write to wire)
        commander_producer_topic_path = get_path("config/commander/producer")
        commander_producer_topic = util.zk.get_data(self.zk_client, commander_producer_topic_path)
        self.producer = util.ipc.Producer(server=kafka_server_string,
                                          topic=commander_producer_topic,
                                          configuration=self.configuration)

        # bad users
        bad_user_path = get_path("config/ignore")
        self.bad_users = util.zk.ChildrenSet(self.zk_client, bad_user_path)
        
        # my name
        my_name_path = get_path("config/name")
        self.my_name = util.zk.get_data(self.zk_client, my_name_path)

        @kzw.DataWatch(zk_client, my_name_path)
        def my_name_watcher(data, stat, event):
            if event is None or event.type == "CHANGED":
                self.my_name = data.decode("utf-8")
        
        # modules
        self.handler_lock = threading.Lock()
        self.handlers = {}
        self.subcommands = {}
        self.loaded_modules = set()

        modules_path = get_path("modules/enabled")

        @kzw.ChildrenWatch(self.zk_client, modules_path)
        def modules_watcher(nodes):
            cannon_modules = set(nodes)
            new_modules = cannon_modules - self.loaded_modules
            del_modules = self.loaded_modules - cannon_modules

            self.log.debug("adding modules: %s", new_modules)
            self.log.debug("removing modules: %s", del_modules)

            for mod in del_modules:
                self._unload_module(mod)

            for mod in new_modules:
                self._load_module(mod)

            assert self.loaded_modules == cannon_modules

    def _unload_module(self, base_module_name):
        module_name = "modules." + base_module_name
        with self.handler_lock:
            self.loaded_modules.remove(base_module_name)
            subcommand = self.handlers[module_name]
            del self.handlers[module_name]
            del self.subcommands[subcommand]


    def _load_module(self, base_module_name):
        importlib.invalidate_caches()
        module_name = "modules." + base_module_name
        
        try:
            # check if it's been reloaded
            if module_name in sys.modules:
                module = sys.modules[module_name]
                importlib.reload(module)            
            else:
                module = importlib.import_module(module_name)

            module_class = getattr(module, module.MODULE_CLASS_NAME)
            subcommand = module.MODULE_SUBCOMMAND
            handler = module_class(configuration=self.configuration,
                                   zk_client=self.zk_client)
            
        except (ImportError, AttributeError) as e:
            self.log.exception("something wrong with the module")
            return
        except:
            self.log.exception("something went wrong while loading %s" % module_name)
            return

        with self.handler_lock:
            self.handlers[module_name] = subcommand
            self.subcommands[subcommand] = handler
            self.loaded_modules.add(base_module_name)

        # reload util modules
        dir_path = os.path.dirname(os.path.realpath(__file__))

        util_path = os.path.join(dir_path, "util")
        for _, module in sys.modules.items():
            filename = getattr(module, "__file__", "")
            if filename.startswith(util_path):
                importlib.reload(module)

    def _handle_message(self, message):
        
        args = message["message"].args
        pieces = message["message"].command

        if len(pieces) <= 0:
            return

        talking_to_me = (pieces[0] == self.my_name) \
                        or (pieces[0] == (self.my_name + ":")) 
        if talking_to_me:
            del pieces[0]
        else:
            if message["destination"] != "PRIVMSG":
                return

        subcommand = pieces[0]
        who = message["nick"]
        where = message["destination"]

        with self.handler_lock:
            handler = self.subcommands.get(subcommand, None)
            if handler is None:
                if subcommand == "help":
                    text = list()
                    for _, handler in self.subcommands.items():
                        text.append(handler.HELP_TEXT)
                    response_text = "; ".join(text)
                else:
                    response_text = "%s: no such command: %s" % (who, subcommand)

                response = util.message.Message(who,
                                                where,
                                                response_text)
            else:
                response = handler.consume(message)

        self._respond(response)

    def _respond(self, response):
        if isinstance(response, list):
            for message in response:
                self.producer.send(message)
        else:
            self.producer.send(response)
                
    def run(self):
        for raw_message in self.consumer:
            try:
                message = json.loads(raw_message.value.decode("utf-8"))
                key = raw_message.key.decode("utf-8")

                if key not in  ["on-msg", "on-privmsg"]:
                    self.log.debug("unhandled: %s", raw_message)
                    continue

                self.log.debug(raw_message)

                message["raw_message"] = message["message"].split()
                message["message"] = util.tokenizer.tokenize(message["message"])

                self._handle_message(message)
            except:
                self.log.exception("something happend with the message")

if __name__ == "__main__":
    import kazoo.client as kzc

    zk_client = kzc.KazooClient(hosts="192.168.1.201:2181")
    zk_client.start()

    configuration = util.configuration.Configuration(zk_client, "/bot")
    c = Commander(zk_client, configuration)

    c.run()
