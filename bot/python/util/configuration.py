#!/usr/bin/env python3

import logging
import os

import kazoo.recipe.watchers as kzw

import util.zk

class Configuration():

    def __init__(self, zk_client, config_root):
        self.zk_client = zk_client
        self.config_root = config_root

        self.contents = dict()

    def __get_path(self, path):
        return os.path.join(self.config_root, path)

    def watch_for_data(self, tag, path):
        setattr(self, tag, None)

        real_path = os.path.join(self.config_root, path)

        @kzw.DataWatch(self.zk_client, real_path)
        def my_name_watcher(data, stat, event):
            if event is None or event.type == "CHANGED":
                value = data.decode("utf-8")
                setattr(self, tag, value)

    def watch_for_children(self, tag, path):
        real_path = os.path.join(self.config_root, path)
        setattr(self, tag, util.zk.ChildrenSet(self.zk_client, real_path))

if __name__ == "__main__":
    import kazoo.client as kzc
    zk_client = kzc.KazooClient(hosts="192.168.1.201:2181")
    zk_client.start()
    
    c = Configuration(zk_client, "/test")

    c.watch_for_data("asdf", "asdf")
    print(c.asdf)

    c.watch_for_children("util", "util")
    print(c.util)
