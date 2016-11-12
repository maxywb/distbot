import datetime
import enum
import requests

import util

HELP_TEXT = "\"hockey <command> <search terms>\""
DETAIL_HELP_TEXT = "stats|search !season=int space separated search terms"

SEARCH_BASE_URL = "http://www.hockey-reference.com/search/search.fcgi?search="
BASE_RESULT_URL = "http://www.hockey-reference.com"


class HockeyErrorCode(enum.Enum):
    No_Search_Terms = 0
    Bad_Season_Format = 1
    Unknown_Command = 2

class HockeyError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code

class SearchType(enum.Enum):
    Any = ""
    Franchise = "franchise"
    Player = "player"

ALL_TYPES = [st.value for st in SearchType]

def get_search_type(name):
    name = name.lower()
    if name in ["team", "franchise"]:
        return SearchType.Franchise
    elif name == "player":
        return SearchType.Player
    else:
        raise ValueError("unknown type %s" % name)

def search(search_type, terms, result_limit=None):
    if isinstance(search_type, str):
        search_type = get_search_type(search_type)

    if not isinstance(terms, list):
        raise ValueError("terms must be a list")

    url = SEARCH_BASE_URL + "+".join(terms)

    dom = util.get_dom_from_url(url)

    search_results = dom.find_class("search-item")

    results = {
        SearchType.Franchise : list(),
        SearchType.Player : list(),
    }

    result_counter = 0

    for result in search_results:
        result_counter += 1
        next_result = dict()

        try:
            result_type = get_search_type(result.getparent().attrib['id'][:-1]) # lose trailing s
        except ValueError:
            # unknown result type
            continue

        next_result["type"] = result_type
        
        if search_type != SearchType.Any:
            if result_type != search_type:
                continue

        for child in result:

            attribute = child.attrib["class"].split("-")[-1]

            if attribute == "name":
                try:
                    link = child[0][0].attrib["href"]
                    value = child[0][0].text
                except IndexError: 
                    link = child[0].attrib["href"]
                    value = child[0].text

            elif attribute == "url":
                value = (BASE_RESULT_URL + child.text)
            else:
                value = child.text

            next_result[attribute] = value

        if result_type == "player":
            try:
                next_result["team"] = next_result["team"].replace("Last Played for the ","")
            except KeyError:
                next_result["team"] = "N/A"

        # extract active years from name
        parts = next_result["name"].split()
        years_active = parts[-1][1:-1]
        name = " ".join(parts[:-1])
        next_result["name"] = name
        next_result["years-active"] = years_active

        results[result_type].append(next_result)

        if (result_limit is not None) and (result_counter >= result_limit):
            break

    return results

ATTRIBUTE_MAP = {
    "losses_ot" : "otl",
    "rank_team" : "seed",
    "rank_team_playoffs" : "playoffs",
    "points_pct" : "points",
    "faceoff_percentage" : "FO%",
    "games_played" : "GP",
    "giveaways" : "GV",
    "goals" : "G",
    "hits" : "HIT",
    "pen_min" : "PIM",
    "plus_minus" : "+/-",
    "points" : "PTS",
    "shot_pct" : "S%",
    "shots" : "S",
    "takeaways" : "TK",
    "time_on_ice_avg" : "ATOI",
    "assists" : "A",
    "team_id" : "Tm",
}

TABLE_OFFSET = {
    SearchType.Franchise : 0,
    SearchType.Player : 1,
    
}

IGNORE_ATTRIBUTES = {
    SearchType.Franchise : [
        "lg_id",
        "coaches",
        "sos",
        "srs",
        "team_name",
    ],
    SearchType.Player : [
        "assists_ev",
        "assists_pp",
        "assists_sh",
        "award_summary",
        "faceoff_losses",
        "faceoff_wins",
        "goals_ev",
        "goals_gw",
        "goals_pp",
        "goals_sh",
        "shots_attempted",
        "time_on_ice",
    ]
}

def __extract_season_stats(row, ignored_attributes):
    stats = dict()

    for col in row:

        attribute = col.attrib["data-stat"]

        if attribute in ignored_attributes:
            # don't care about these attributes
            continue
        elif attribute == "season":
            try:
                value = col[0].text
            except IndexError:
                value = col.text

            start, end = value.split("-")

            end = start[:2] + end

            value = int(end)
        else:

            try:
                raw_text = col[0].text
            except IndexError:
                raw_text = col.text

            try:
                value = int(raw_text)
            except ValueError:
                value = raw_text
            except TypeError:
                value = ""
                
        attribute = ATTRIBUTE_MAP.get(attribute, attribute)

        stats[attribute] = value

    return stats

def __get_current_season():
    now = datetime.datetime.now()

    if now.month < 9:
        return now.year
    else:
        return now.year + 1

def __get_stats(search_type, results, season):
    try:
        result = results[search_type][0]
    except IndexError:
        return None

    if season is None:
        season = __get_current_season()

    dom = util.get_dom_from_url(result["url"])

    stats_table = dom.find_class("table_outer_container")[TABLE_OFFSET[search_type]][0][0][3]
    
    for row in stats_table:

        season_stats = __extract_season_stats(row, IGNORE_ATTRIBUTES[search_type])
        season_stats["type"] = search_type
        season_stats["name"] = result["name"]
        if season_stats["season"] == season:
            return season_stats
        
def __get_any_stats(results, season):
    if len(results[SearchType.Franchise]) > 0:
        return __get_stats(SearchType.Franchise, results, season)
    else:
        return __get_stats(SearchType.Player, results, season)


def get_stats(search_type, terms, season=None):
    if isinstance(search_type, str):
        search_type = get_search_type(search_type)

    if not isinstance(terms, list):
        raise ValueError("terms must be a list")

    results = search(search_type, terms, result_limit=1)

    if search_type == SearchType.Any:
        return __get_any_stats(results, season)
    else:
        return __get_stats(search_type, results, season)


FORMATS = {
    SearchType.Franchise : "%(season)s %(name)s: GP:%(games)s, W:%(wins)s, L:%(losses)s, OL:%(otl)s, PTS:%(PTS)s, seed:%(seed)s %(playoffs)s",
    SearchType.Player : "%(season)s %(name)s (%(age)s)- %(Tm)s: GP:%(GP)s, G:%(G)s, A:%(A)s, PTS:%(PTS)s, +/-:%(+/-)s, S:%(S)s, FO%%:%(S%)s, PIM:%(PIM)s, ATOI:%(ATOI)smin, HIT:%(HIT)s",
}


def __format_stats(stats):
    stats_type = stats["type"]

    return FORMATS[stats_type] % stats

def __format_search(results):
    pass

def execute_command(query):
    season = __get_current_season()
    search_type = SearchType.Any
    if "=" in query:
        equals = query.index("=")
        start = equals - 1
        end = equals + 1
        
        query[start] = "%s=%s" % (query[start], query[end])
        del query[equals]
        del query[equals] # due to shift, just delete the same place twice
        
    i = 0
    while i < len(query):
        if query[i].startswith("!season"):
            raw_text = query[i].split("=")[-1]
            try:
                season = int(raw_text)
            except ValueError:
                raise HockeyError(HockeyErrorCode.Bad_Season_Format, "invalid season: %s" % raw_text)

            del query[i]
            continue

        i += 1

    if len(query) < 2:
        raise HockeyError(HockeyErrorCode.No_Search_Terms, "must provide search terms")

    command = query[0].lower()
    terms = query[1:]

    if command == "stats":
        stats = get_stats(search_type, terms, season=season)
        return __format_stats(stats)
    elif command == "search":
        results = search(search_type, ["boston","bruins"], result_limit=1)
        return __format_search(results)
    elif command == "help":
        return DETAIL_HELP_TEXT
    else:
        raise HockeyError(HockeyErrorCode.Unknown_Command, "unknown command: %s" % command)

def __test():
    results = search("player", ["boston","bruins"])
    assert len(results[SearchType.Franchise]) == 0, len(results[SearchType.Franchise])

    results = search("playER", ["boston","bruins"])
    assert len(results[SearchType.Franchise]) == 0, len(results[SearchType.Franchise])

    results = search(SearchType.Player, ["boston","bruins"])
    assert len(results[SearchType.Franchise]) == 0, len(results[SearchType.Franchise])

    results = search(SearchType.Franchise, ["boston","bruins"], result_limit=1)
    assert len(results[SearchType.Franchise]) == 1, len(results[SearchType.Franchise])

    results = search("team", ["boston","bruins"], result_limit=1)
    assert len(results[SearchType.Franchise]) == 1, len(results[SearchType.Franchise])

    results = search(SearchType.Player, ["seguin"])
    assert len(results[SearchType.Player]) == 3, len(results[SearchType.Player])

    results = search(SearchType.Any, ["cal"], result_limit=1)
    assert len(results[SearchType.Franchise]) == 0, len(results[SearchType.Franchise])
    assert len(results[SearchType.Player]) == 1, len(results[SearchType.Player])

    stats = get_stats(SearchType.Player, ["seguin"], season=2017)
    assert stats["age"] == 25, stats["age"]

    stats = get_stats(SearchType.Franchise, ["boston"], season=2012)
    assert stats["losses"] == 29, stats["losses"]

    try:
        execute_command("stats !season=asdf".split())
        assert False, "should have thrown"
    except HockeyError as e:
        assert e.code == HockeyErrorCode.Bad_Season_Format, e.code

    try:
        execute_command("stats !season=2017".split())
        assert False, "should have thrown"
    except HockeyError as e:
        assert e.code == HockeyErrorCode.No_Search_Terms, e.code
        
    try:
        execute_command("foo !season=2017 boston".split())
        assert False, "should have thrown"
    except HockeyError as e:
        assert e.code == HockeyErrorCode.Unknown_Command, e.code

    text = execute_command("help".split())
    assert text == DETAIL_HELP_TEXT

    print("probably good")

if __name__ == "__main__":

    text = execute_command("stats seguin".split())
    print(text)

    text = execute_command("stats !season=2012 boston".split())
    print(text)

    #__test()
