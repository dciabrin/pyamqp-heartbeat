from urllib.parse import parse_qs
import os
from eventlet import greenthread
import log  # noqa
import sys
sys.path.append('/setup')
import server


def application(environ, start_response):
    server.monkey_patch_if_needed(eventlet_turned_on=True)
    transport_url = os.getenv('TRANSPORT_URL',
        default='rabbit://testuser:testpwd@127.0.0.1:5672/')
    oslo_server = greenthread.spawn(server.start_server,
        args=(transport_url,))
    num = parse_qs(environ["QUERY_STRING"]).get("num", ["1"])[0]
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [str("it's work").encode()]
