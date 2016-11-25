import util.admin
import util.message 

MODULE_CLASS_NAME="Join"

MODULE_SUBCOMMAND="join"

class Join():
    HELP_TEXT = ""

    def __init__(self, configuration, zk_client, **kwargs):
        self.configuration = configuration
        self.zk_client = zk_client

    def consume(self, message):
        if not util.admin.is_admin(self.zk_client, self.configuration, message):
            return util.admin.admonish(self.zk_client, self.configuration, message)
        
        pieces = message["message"].command
        
        where = pieces[1]
        
        return util.message.Command("JOIN", where)
