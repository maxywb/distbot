import datetime
import requests

import location

def get_weather(keys, query_location):
    location_name, lat, lng, _ = location.get_location_details(keys, query_location)

    # 
    r = requests.get("http://api.openweathermap.org/data/2.5/weather?lat=%s&lon=%s&appid=%s&units=imperial" % (lat, lng, keys["weather"]))

    temp = r.json()["main"]["temp"]

    description = r.json()["weather"][0]["description"]

    message = "%s -  %s, %sf" % (location_name, description, temp)
    return message

def get_forecast(keys, query_location):
    location_name, lat, lng, utc_delta = location.get_location_details(keys, query_location)

    # get forecast, normalize times to local timezone

    now = datetime.datetime.utcnow()

    days = list()

    # get forecast
    count = 3
    r = requests.get("http://api.openweathermap.org/data/2.5/forecast/daily?cnt=%d&lat=%s&lon=%s&appid=%s&units=imperial" % (count, lat, lng, keys["weather"]))

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

