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

def get_dom_from_url(url, allow_redirects=False):
    session = get_requests_session()
    request = session.get(url, allow_redirects=allow_redirects)

    if request.status_code == 302:
        raise RedirectError()

    return lxml.html.fromstring(request.text), request.url
    
