import os

import kazoo.recipe.watchers as kzw

import util.zk

MODULE_CLASS_NAME="Ping"

class Ping():
    HELP_TEXT = "ping - repond with <nick>: <response>"

    def __init__(self, zk_client, zk_tree):
        self.zk_client = zk_client

        response_path = os.path.join(zk_tree, "modules/config/ping/response")
        self.response = util.zk.get_data(self.zk_client, response_path)

        @kzw.DataWatch(zk_client, response_path)
        def my_name_watcher(data, stat, event):
            if event is None or event.type == "CHANGED":
                self.response = data.decode("utf-8")
        
    def consume(self, message):
        return "%s: %s" % (message["nick"], self.response)
