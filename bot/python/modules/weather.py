import util.message 
import util.weather

MODULE_CLASS_NAME="Weather"

MODULE_SUBCOMMAND="weather"

def get_user(zk, nick):
    path = "/bot/users/%s" % nick
    if zk.exists(path) is None:
        return None

    locations = dict()
    # build up locations
    locations_path = "%s/%s" % (path, "locations")
    for location in zk.get_children(locations_path):
        specific_path = "%s/%s" % (locations_path, location)
        value = zk.get(specific_path)[0].decode("utf-8")
        locations[location] = value

    return {
        "locations" : locations,
        }


class Weather():
    HELP_TEXT = "ping - repond with <nick>: <response>"

    def __init__(self, configuration, zk_client, **kwargs):

        self.configuration = configuration

        self.zk_client = zk_client

        self.configuration.watch_for_data("weather_key", "config/key/weather")
        self.configuration.watch_for_data("location_key", "config/key/google")

    def consume(self, message):
        who = message["nick"]
        where = message["destination"]

        user = get_user(self.zk_client, message["nick"])

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

        text = util.weather.get_weather(self.configuration.weather_key, self.configuration.location_key, query)
    
        return util.message.Message(who, where, text)
