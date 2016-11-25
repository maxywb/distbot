import util.admin
import util.message 

MODULE_CLASS_NAME="Unignore"

MODULE_SUBCOMMAND="unignore"

class Unignore():
    def __init__(self, configuration, zk_client, **kwargs):
        self.configuration = configuration
        self.zk_client = zk_client

    def consume(self, message):
        if not util.admin.is_admin(self.zk_client, self.configuration, message):
            return util.admin.admonish(self.zk_client, self.configuration, message)

        for user in message["message"].command[1:]:
            self.configuration.bad_users.discard(user)
        
        
