import requests
import lxml.etree
import lxml.html


## lxml

def get_xml_text(blob):
    return lxml.etree.tostring(blob, pretty_print=True).decode("utf-8")

## requests

class RedirectError(Exception):
    pass

session = None
def get_requests_session():
    global session

    if session is None:
        session = requests.Session()
        session.headers["User-Agent"] = "Mozilla/4.0"

    return session

def get_dom_from_url(url, allow_redirects=False, auth=None):
    session = get_requests_session()
    if auth is None:
        request = session.get(url, allow_redirects=allow_redirects)
    else:
        request = session.get(url, allow_redirects=allow_redirects, auth=auth)
    if request.status_code == 302:
        raise RedirectError()

    if allow_redirects:
        return lxml.html.fromstring(request.text), request.url
    else:
        return lxml.html.fromstring(request.text)


## tokenizer

def find_string_end(query):
    i = 0
    pieces = list()
    while len(query) > 0:
        part = query[i]
        pieces.append(part)
        del query[i]
        if part[-1] == "\"":
            i += 1
            break

    return " ".join(pieces), query

def tokenize(query):
    while "=" in query:
        equals = query.index("=")
        start = equals - 1
        end = equals + 1
        
        query[start] = "%s=%s" % (query[start], query[end])
        del query[equals:end+1]

    args = dict()
    i = 0
    while i < len(query):
        if query[i].startswith("!"):
            parts = query[i].split("=")
            key = parts[0][1:]
            value = "=".join(parts[1:])
            
            if value[0] == "\"":
                remainder, new_query = find_string_end(query[i+1:])
                value += " " + remainder
                value = value.replace("\"", "")
                del query[i+1:]
                query += new_query

            args[key] = value
            del query[i]
            continue
        elif query[i][0] == "\"":
            base = query[i]
            remainder, new_query = find_string_end(query[i+1:])
            value = query[i] + " " + remainder
            query[i] = value.replace("\"", "")
            del query[i+1:]
            query += new_query
                
        i += 1

    return args, query

if __name__ == "__main__":
    query = "spark search !nick=oatzhakok !msg=asdf !chan=boatz".split()

    import bot.spark

    text = bot.spark.execute_command(query)
    print(text)
