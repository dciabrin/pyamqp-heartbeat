#!/usr/bin/env python
import argparse
import os
import threading

import eventlet

from oslo_config import cfg
import oslo_messaging
from oslo_messaging._drivers import common as driver_common
import time
import log  # noqa


class TestEndpoint(object):

    def adder(self, ctx, arg):
        return arg+1


def get_transport_url(host, port, user, pwd):
    return 'rabbit://{user}:{pwd}@{host}:{port}/'.format(
        host=host, port=port, user=user, pwd=pwd
    )


def start_server(transport_url, executor='threading', need_to_wait=False):
    print("Used transport url: {}".format(transport_url))
    transport = oslo_messaging.get_rpc_transport(cfg.CONF, transport_url)
    transport._driver._get_connection(driver_common.PURPOSE_SEND)
    target = oslo_messaging.Target(topic='test', server='myname')
    endpoints = [TestEndpoint()]
    
    server = oslo_messaging.get_rpc_server(
        transport, target, endpoints, executor=executor)
    server.start()
    if need_to_wait:
        while True:
            time.sleep(1)


def monkey_patch_if_needed(eventlet_turned_on=False):
    msg = "/!\  Running a *NON* monkey patched environment /!\\"
    if eventlet_turned_on:
        eventlet.monkey_patch()
        msg = "/!\  Running a monkey patched environment  /!\\"
    print("-" * len(msg))
    print(msg)
    print("-" * len(msg))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--eventlet-turned-on', action='store_true',
                        help='turn on eventlet and monkey patch the env')
    parser.add_argument("--heartbeat-timeout", help="the heartbeat timeout",
                        default=60)
    parser.add_argument("--rabbit-host", default="127.0.0.1")
    parser.add_argument("--rabbit-port", default="5672")
    parser.add_argument("--rabbit-user", default="testuser")
    parser.add_argument("--rabbit-user-pwd", default="testpwd")
    parser.add_argument("--run-oslo-in-thread", action='store_true',
        default=False)
    parser.add_argument("--oslo-executor", default='threading')
    args = parser.parse_args()
    transport_url = get_transport_url(
        args.rabbit_host,
        args.rabbit_port,
        args.rabbit_user,
        args.rabbit_user_pwd)
    print("Default transport url: {}".format(transport_url))
    monkey_patch_if_needed(args.eventlet_turned_on)
    if args.run_oslo_in_thread:
        oslo_server = threading.Thread(target=start_server,
            args=(transport_url, args.oslo_executor,))
        oslo_server.start()
        oslo_server.join()
    else:
        start_server(transport_url, args.oslo_executor)


if __name__ == "__main__":
    main()
