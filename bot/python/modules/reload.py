import os

import util.admin
import util.message 

MODULE_CLASS_NAME="Reload"

MODULE_SUBCOMMAND="reload"

class Reload():
    def __init__(self, configuration, zk_client, **kwargs):
        self.configuration = configuration
        self.zk_client = zk_client

    def consume(self, message):
        if not util.admin.is_admin(self.zk_client, self.configuration, message):
            return util.admin.admonish(self.zk_client, self.configuration, message)

        def get_path(path):
            return os.path.join(self.configuration.config_root, path)

        modules_path = get_path("modules/enabled")
        modules = self.zk_client.get_children(modules_path)

        delete_xact = self.zk_client.transaction()
        for module in modules:
            path = os.path.join(modules_path, module)
            delete_xact.delete(path)
        delete_xact.commit()

        create_xact = self.zk_client.transaction()
        for module in modules:
            path = os.path.join(modules_path, module)
            data = module.encode("utf-8")
            create_xact.create(path, data)
        create_xact.commit()
        
