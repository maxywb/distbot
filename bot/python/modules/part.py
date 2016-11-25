import util.admin
import util.message 

MODULE_CLASS_NAME="Part"

MODULE_SUBCOMMAND="part"

class Part():
    HELP_TEXT = ""

    def __init__(self, configuration, zk_client, **kwargs):
        self.configuration = configuration
        self.zk_client = zk_client

    def consume(self, message):
        if not util.admin.is_admin(self.zk_client, self.configuration, message):
            return util.admin.admonish(self.zk_client, self.configuration, message)

        pieces = message["message"].command
        
        where = pieces[1]
        text = " ".join(pieces[2:]) if len(pieces) >=2 else "bye"        

        return util.message.Command("PART", where)
