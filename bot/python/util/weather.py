import datetime
import requests

import util.location

def get_weather(weather_key, location_key, query_location):
    location_name, lat, lng, _ = util.location.get_location_details(location_key, query_location)

    # 
    r = requests.get("http://api.openweathermap.org/data/2.5/weather?lat=%s&lon=%s&appid=%s&units=imperial" % (lat, lng, weather_key))

    temp = r.json()["main"]["temp"]

    description = r.json()["weather"][0]["description"]

    message = "%s -  %s, %sf" % (location_name, description, temp)
    return message

def get_forecast(weather_key, location_key, query_location):
    location_name, lat, lng, utc_delta = util.location.get_location_details(location_key, query_location)

    # get forecast, normalize times to local timezone

    now = datetime.datetime.utcnow()

    days = list()

    # get forecast
    count = 3
    r = requests.get("http://api.openweathermap.org/data/2.5/forecast/daily?cnt=%d&lat=%s&lon=%s&appid=%s&units=imperial" % (count, lat, lng, weather_key))

    raw = r.json()["list"]

    for record in raw:
        dt = datetime.datetime.fromtimestamp(record["dt"]) + utc_delta
        days.append(record)

        blobs = list()

    for record in days:
        dt = datetime.datetime.fromtimestamp(record["dt"]) + utc_delta
        description = record["weather"][0]["description"]
        min_temp = int(record["temp"]["min"])
        max_temp = int(record["temp"]["max"])

        blob = "%s: %s, %s-%sf" % (dt.strftime("%a"), description, min_temp, max_temp)
        blobs.append(blob)

    message = "%s -  %s" % (location_name, ", ".join(blobs))
    return message

