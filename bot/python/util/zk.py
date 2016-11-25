import os
import threading

import kazoo.recipe.watchers

def get_data(zk, path):
    return zk.get(path)[0].decode("utf-8")

def get_user(zk, nick):
    path = "/bot/users/%s" % nick
    if zk.exists(path) is None:
        return None

    locations = dict()
    # build up locations
    locations_path = "%s/%s" % (path, "locations")
    for location in zk.get_children(locations_path):
        specific_path = "%s/%s" % (locations_path, location)
        value = zk.get(specific_path)[0].decode("utf-8")
        locations[location] = value

    return {
        "locations" : locations,
        }

class ChildrenSet():
    def __init__(self, zk_client, path, *args, **kwargs):
        self.zk_client = zk_client
        self.path = path
        self.contents = set(*args, **kwargs)
        self.lock = threading.Lock()

        @kazoo.recipe.watchers.ChildrenWatch(zk_client, path)
        def __watcher(nodes):
            with self.lock:
                self.contents = set(nodes)

    def add(self, item, value=None):
        string = str(item)
        fullpath = os.path.join(self.path, string)

        value = string if value is None else value
        value = bytes(value, "utf-8")

        if self.zk_client.exists(fullpath) is None:
            self.zk_client.create(fullpath, value=value)
        
    def discard(self, item):
        string = str(item)
        fullpath = os.path.join(self.path, string)

        if self.zk_client.exists(fullpath) is not None:
            self.zk_client.delete(fullpath)

    def contains(self, item):
        with self.lock:
            return item in self.contents

    def __repr__(self):
        with self.lock:
            return self.contents.__repr__()

    def __str__(self):
        with self.lock:
            return self.contents.__str__()

if __name__ == "__main__":
    import time
    import kazoo.client as kzc
    zk_client = kzc.KazooClient(hosts="192.168.1.201:2181")
    zk_client.start()
    
    cs = ChildrenSet(zk_client, "/test/util")

    cs.add("test-1")
    cs.add("test-2")
    cs.add("test-3", "foobar")

    time.sleep(3)

    print(cs.contains("test-1"))

    while True:

        print(cs)
        cs.discard("test-1")
        time.sleep(1)

