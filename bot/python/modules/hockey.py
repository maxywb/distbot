import util.hockey
import util.message 

MODULE_CLASS_NAME="Hockey"

MODULE_SUBCOMMAND="hockey"


class Hockey():
    HELP_TEXT = "hockey <command> <search terms>"

    def __init__(self, configuration, zk_client, **kwargs):

        self.configuration = configuration

        self.zk_client = zk_client

    def consume(self, message):

        try:
            text = util.hockey.execute_command(message["message"].args, message["message"].command[1:])
        except util.hockey.HockeyError as e:
            text = str(e).replace("'","")

        return util.message.Message(message["nick"], message["destination"], text)

