import util.message 

MODULE_CLASS_NAME="Ping"

MODULE_SUBCOMMAND="ping"

class Ping():
    HELP_TEXT = "ping - repond with <nick>: <response>"

    def __init__(self, configuration, **kwargs):

        self.configuration = configuration

        self.configuration.watch_for_data("ping_response", "modules/config/ping/response")
        
    def consume(self, message):

        who = message["nick"]
        where = message["destination"]
        response = "%s: %s" % (message["nick"], self.configuration.ping_response)

        return util.message.Message(who, where, response)

    
