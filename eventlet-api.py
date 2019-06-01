#!/usr/bin/env python

from eventlet import wsgi
import eventlet
from urllib.parse import parse_qs
import client
import log  # noqa


def application(env, start_response):
    num = parse_qs(env["QUERY_STRING"]).get("num", ["1"])[0]
    r = client.adder(int(num))
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [str(r).encode()]


wsgi.server(eventlet.listen(('', 8090)), application)
