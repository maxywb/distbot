import util.admin
import util.message 

MODULE_CLASS_NAME="Say"

MODULE_SUBCOMMAND="say"

class Say():
    def __init__(self, configuration, zk_client, **kwargs):
        self.configuration = configuration
        self.zk_client = zk_client

    def consume(self, message):
        if not util.admin.is_admin(self.zk_client, self.configuration, message):
            return util.admin.admonish(self.zk_client, self.configuration, message)

        who = message["nick"]
        pieces = message["message"].command
        where = pieces[1]
        text = " ".join(pieces[2:])

        return util.message.Message(who, where, text)

