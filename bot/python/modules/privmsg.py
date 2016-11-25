import util.admin
import util.message 

MODULE_CLASS_NAME="Privmsg"

MODULE_SUBCOMMAND="privmsg"

class Privmsg():
    def __init__(self, configuration, zk_client, **kwargs):
        self.configuration = configuration
        self.zk_client = zk_client

    def consume(self, message):
        if not util.admin.is_admin(self.zk_client, self.configuration, message):
            return util.admin.admonish(self.zk_client, self.configuration, message)

        pieces = message["message"].command
        who = pieces[1]
        where = "PRIVMSG"
        text = " ".join(pieces[2:])

        return util.message.Message(who, where, text)

