#!/usr/bin/env python
import argparse
import threading

import eventlet

from oslo_config import cfg
from oslo_utils import eventletutils
import oslo_messaging
import time
import log  # noqa


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

    event = eventletutils.Event()
    transport_url = 'rabbit://testuser:testpwd@localhost:5672/'
    transport = oslo_messaging.get_transport(cfg.CONF, transport_url)
    conn = transport._driver._get_connection()
    conn.ensure(method=lambda: True)
    event.wait()
    conn._heartbeat_stop()


if __name__ == "__main__":
    main()
