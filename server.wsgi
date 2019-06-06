import sys
sys.path.append('/setup')
import server


def application(environ, start_response):
    server.run_oslo(eventlet_turned_on=True)
    num = parse_qs(env["QUERY_STRING"]).get("num", ["1"])[0]
    r = client.adder(int(num))
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [str(r).encode()]
