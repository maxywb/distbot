import requests
import datetime
import time


types = set(["locality", "administrative_area_level_1", "country"])

def get_location_description(location):
    info = dict()
    for attr in location["address_components"]:
        intersect = set.intersection(types, set(attr["types"]))
        if len(intersect):
            name = list(intersect)[0]
            info[name] = attr["short_name"]

    description = list()
    for index in ["locality", "administrative_area_level_1", "country"]:
        value = info.get(index, None)
        if value is not None:
            description.append(value)

    return ", ".join(description)

def get_location_details(keys, query_location):
    # get utc_offset for location 

    base_tz_url = "https://maps.googleapis.com/maps/api/geocode/json?key=%s" % keys["google"]

    query_location = "+".join(query_location)

    url = base_tz_url + "&" + "address=%s" % query_location

    latlon = requests.get(url).json()["results"][0]

    location = get_location_description(latlon)

    results = latlon["geometry"]["location"]

    lat = results["lat"]
    lng = results["lng"]

    timestamp=int(time.time())
    tz_url = "https://maps.googleapis.com/maps/api/timezone/json?key=%s&location=%s,%s&timestamp=%d" % (keys["google"], lat, lng, timestamp)

    raw_timezone = requests.get(tz_url).json()

    utc_offset = raw_timezone["dstOffset"] + raw_timezone["rawOffset"]

    utc_delta = datetime.timedelta(seconds=utc_offset)

    return location, lat, lng, utc_delta


keys = {
    "google":"AIzaSyDDuBpbBWXAfQELUto83BchIPONBgvf1ao",
    "weather": "e81fbe4eb94b7a5511e9e76b5dab64ec",
}


