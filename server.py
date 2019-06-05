#!/usr/bin/env python
import argparse

import eventlet

from oslo_config import cfg
import oslo_messaging
import time
import log  # noqa


class TestEndpoint(object):

    def adder(self, ctx, arg):
        return arg+1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--eventlet-turned-on', action='store_true',
                        help='turn on eventlet and monkey patch the env')
    parser.add_argument("--heartbeat-timeout", help="the heartbeat timeout",
                        default=60)
    args = parser.parse_args()
    if args.eventlet_turned_on:
        print("----------------------------------------------")
        print("/!\  Running a monkey patched environment  /!\\")
        print("----------------------------------------------")
        eventlet.monkey_patch()

    transport_url = 'rabbit://testuser:testpwd@localhost:5672/'
    transport = oslo_messaging.get_rpc_transport(cfg.CONF)
    target = oslo_messaging.Target(topic='test', server='myname')
    endpoints = [TestEndpoint()]
    
    server = oslo_messaging.get_rpc_server(transport, target, endpoints,
                                           executor='threading')
    server.start()
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
