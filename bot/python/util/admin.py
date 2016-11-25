import util.message
import util.zk

def is_admin(zk_client, configuration, message):

    hostmask = message["hostmask"]

    admin_hostmasks = util.zk.get_child_data(zk_client, configuration.config_root, "admin")

    return hostmask in set(admin_hostmasks)

def admonish(zk_client, configuration, message):
    who = message["nick"]
    where = message["destination"]

    text = "%s, you can't do that" % who
    return util.message.Message(who, where, text)
    
