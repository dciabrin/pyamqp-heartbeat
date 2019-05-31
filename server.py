#!/usr/bin/env python

from oslo_config import cfg
import oslo_messaging
import time
import log  # noqa


class TestEndpoint(object):

    def adder(self, ctx, arg):
        return arg+1


transport_url = 'rabbit://testuser:testpwd@localhost:5672/'
transport = oslo_messaging.get_rpc_transport(cfg.CONF)
target = oslo_messaging.Target(topic='test', server='myname')
endpoints = [TestEndpoint()]

server = oslo_messaging.get_rpc_server(transport, target, endpoints,
                                       executor='threading')
server.start()
while True:
    time.sleep(1)
