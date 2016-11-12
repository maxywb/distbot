import requests
import lxml.etree
import lxml.html
## lxml

def get_xml_text(blob):
    return lxml.etree.tostring(blob, pretty_print=True).decode("utf-8")

## requests

session = None
def get_requests_session():
    global session

    if session is None:
        session = requests.Session()
        session.headers["User-Agent"] = "Mozilla/4.0"

    return session

def get_dom_from_url(url):
    session = get_requests_session()
    request = session.get(url, allow_redirects=False)
    return lxml.html.fromstring(request.text)
    
