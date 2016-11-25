import os

import util.admin
import util.message 

MODULE_CLASS_NAME="Config"

MODULE_SUBCOMMAND="config"

class Config():
    def __init__(self, configuration, zk_client, **kwargs):
        self.configuration = configuration
        self.zk_client = zk_client

    def consume(self, message):
        if not util.admin.is_admin(self.zk_client, self.configuration, message):
            return util.admin.admonish(self.zk_client, self.configuration, message)

        
        pieces = message["message"].command
        action = pieces[1]
        
        def exists(path):
            return self.zk_client.exists(path) is not None
    
        text = "done"

        if action in ["create", "update"]:
            path_pieces = pieces[2:-1]
            path = os.path.join(self.configuration.config_root, *path_pieces)
            data = pieces[-1].encode("utf-8")

            if exists(path):
                if action == "create":
                    text = "path exists (%s)" % path
                elif action == "update":
                    self.zk_client.set(path, data)    
                else:
                    text = "path exists (%s)" % path
            else:
                if action == "create":
                    self.zk_client.create(path, data)
                else:
                    text = "path doesn't exist (%s)" % path

        elif action in ["get", "get-children", "delete"]:
            path_pieces = pieces[2:]
            path = os.path.join(self.configuration.config_root, *path_pieces)

            if exists(path):
                if action == "get":
                    text = self.zk_client.get(path)[0].decode("utf-8")
                elif action == "delete":
                    self.zk_client.delete(path)
                elif action == "get-children":
                    text = ", ".join(self.zk_client.get_children(path))
                    if text == "":
                        text = "<none>"
                else:
                    assert False, "unhandled %s" % action
            else:
                text = "path doesn't exist (%s)" % path

        elif action == "help":
            text = "sub-commands: update, delete, get, get-children"
        else:
            text = "unknown action (%s)" % action
    
    
        return util.message.Message(message["nick"], message["destination"], text)        
