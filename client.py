#!/usr/bin/env python

from oslo_config import cfg
import oslo_messaging

adder_rpc = None


def adder(num):
    global adder_rpc
    if not adder_rpc:
        transport_url = 'rabbit://testuser:testpwd@127.0.0.1:5672/'
        transport = oslo_messaging.get_rpc_transport(cfg.CONF, transport_url)
        target = oslo_messaging.Target(topic='test')
        adder_rpc = oslo_messaging.RPCClient(transport, target)
    return adder_rpc.call({}, 'adder', arg=num)


if __name__ == "__main__":
    import sys
    num = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    print(adder(num))
