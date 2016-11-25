import util.message 
import util.weather

MODULE_CLASS_NAME="Forecast"

MODULE_SUBCOMMAND="forecast"


class Forecast():
    HELP_TEXT =  "forecast <search terms> - respond with 3 days forcast (including today), normalized to the appropriate timezone",

    def __init__(self, configuration, zk_client, **kwargs):

        self.configuration = configuration

        self.zk_client = zk_client

        self.configuration.watch_for_data("weather_key", "config/key/weather")
        self.configuration.watch_for_data("location_key", "config/key/google")

    def consume(self, message):
        who = message["nick"]
        where = message["destination"]

        user = util.zk.get_user(self.zk_client, self.configuration.config_root, message["nick"])

        pieces = message["message"].command

        if user is not None:
            try:
                if len(pieces) == 1:
                    query = user["locations"]["default"].split()
                
                elif len(pieces) == 2:
                    query = user["locations"][pieces[1]].split()
                else:
                    query = pieces[1:]
            except KeyError:
                query = pieces[1:]            
        else:
            query = pieces[1:]

        text = util.weather.get_forecast(self.configuration.weather_key, self.configuration.location_key, query)
    
        return util.message.Message(who, where, text)
