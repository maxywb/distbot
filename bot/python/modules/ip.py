import util.admin
import util.message 
import util.web

MODULE_CLASS_NAME="Ip"

MODULE_SUBCOMMAND="ip"

class Ip():
    HELP_TEXT = ""

    def __init__(self, configuration, zk_client, **kwargs):
        self.configuration = configuration
        self.zk_client = zk_client

    def consume(self, message):
        if not util.admin.is_admin(self.zk_client, self.configuration, message):
            return util.admin.admonish(self.zk_client, self.configuration, message)

        who = message["nick"]
        where = "PRIVMSG"
        dom = util.web.get_dom_from_url("http://www.networksecuritytoolkit.org/nst/tools/ip.shtml")
        ip = dom.text.strip()

        return util.message.Message(who, where, "my ip is: %s" % ip)

