import lxml.html
import requests

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
