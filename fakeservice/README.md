# Fake Service

Fake service to emulate how to nova and services consume oslo.messaging.

The main goal of this fake sub project is to reproduce similare behaviour
that openstack service who will use oslo.messaging rabbitmq driver.

# Nova use case inspect

This section would describe the nova use case and how nova
consume oslo.messaging and the mechanismes under the hood to
lunch the rabbitmq driver.

Well, let's go!

#### The puppet part

The [puppet team](https://wiki.openstack.org/wiki/Puppet) provide a [puppet project dedicated to nova](https://github.com/openstack/puppet-nova/)
who define how to run nova under an apache environment. Also it's important to note
that other deployments systems exists and are in use on openstack, like ansible through
the [openstack ansible project](https://docs.openstack.org/project-deploy-guide/openstack-ansible/latest/)
who provide [a different approach to deploy nova](https://github.com/openstack/openstack-ansible-os_nova).
There are many others deployment systems in use too (Chef, Salt, etc.).

This puppet project will configure [apache to run nova](https://github.com/openstack/puppet-nova/blob/master/manifests/wsgi/apache_api.pp#L158)

It is the `script_path` is used for the `wsgi_script_dir` in configuring the
[`httpd conf`](https://github.com/openstack/puppet-nova/blob/master/manifests/wsgi/apache_api.pp#L158).
In the end its all used by https://github.com/openstack/puppet-openstacklib/blob/master/manifests/wsgi/apache.pp to configure the wsgi settings of the vhost

The wsgi [nova entry_point to use to start the nova wsgi application is defined here and the apache vhost file to use too](https://github.com/openstack/puppet-nova/blob/29d307bce168a39477953a856382c2402ac1ff77/spec/classes/nova_wsgi_apache_api_spec.rb#L132,L135)

We can observe that this puppet script define the following configuration `api_wsgi_script_source => '/usr/bin/nova-api-wsgi`.

Nova will be launched by calling the wsgi script available at `/usr/bin/nova-api-wsgi`.

This wsgi scripts is generated by [pbr](https://docs.openstack.org/pbr/latest/user/using.html#entry-points)
and [setuptools](https://setuptools.readthedocs.io/en/latest/setuptools.html?highlight=entry_points) during the nova install.

Nova [define it in its own setup.cfg file](https://github.com/openstack/nova/blob/master/setup.cfg#L76).

This entry point will when it's called while trigger `nova.api.openstack.compute.wsgi:init_application`
[who correspond to the initialization of the nova wsgi application](https://github.com/openstack/nova/blob/master/nova/api/openstack/wsgi_app.py#L74).

To implement the [Python Web Server Gateway Interface (WSGI)(PEP 3333)](https://www.python.org/dev/peps/pep-3333/) nova
use the [`paste.deploy` python module](https://github.com/Pylons/pastedeploy).

#### Generate the wsgi apps by using Paste Deploy

Paste deploy was at the origin a submodule of the [paste module](https://github.com/cdent/paste/).

Basically at some point in the past people realized that `paste.deploy` was
one of the main useful parts of paste and they didn't want all the rest of
paste, so it was extracted.

As paste and paste.deploy both got "old" maintenance sort of diverged.
They are still maintained, but as separate packages.

Even if the [Paste module](https://github.com/cdent/paste) seems not used here
I will describe some `paste` specific behaviours and especially
[concerning requests handling, threads, and the python interpreter life cycle](https://github.com/cdent/paste/blob/5a542da992618e30a508f7f03259f63cf2ee1ceb/docs/paste-httpserver-threadpool.txt#L40),
which I guess we need to take care to really undestand the eventlet issue and green threads for the heartbeat.

Indeed, to avoid issue with requests management (freeze, memory usage, etc...),
`paste` manage threads with 3 states:
- idle (waiting for a request)
- working (on a request)
- should die (a thread that should die for some reasons)

If a `paste` thread initiate the oslo.messaging AMQP heartbeat who will run in
an async way by using green thread maybe in this case the parent thread consider that
it can become idle for some reasons and the main reason is that this thread
(heartbeat) is not a blocking thread.

In parallel, uwsgi (not used here but the heartbeat seems occur within too)
support for `paste` facing some [issues in multiple process/workers mode](https://uwsgi-docs.readthedocs.io/en/latest/Python.html#paste-support)

On the `paste.deploy` side [`nova` call](https://github.com/openstack/nova/blob/master/nova/api/openstack/wsgi_app.py#L99)
the [`loadapp`](https://github.com/Pylons/pastedeploy/blob/master/paste/deploy/loadwsgi.py#L252) method to serve the nova-api.

Paste Deployment is a system for finding and configuring WSGI applications
and servers. 
For WSGI application consumers it provides a single, simple function (loadapp)
for loading a WSGI application from a configuration file or a Python Egg.
For WSGI application providers it only asks for a single, simple entry point
to your application, so that application users don't need to be exposed to the
implementation details of your application.

The nova service call the `loadapp` method by passing available configurations.
The configuration seems to be designed by following the
[nova configuration guide](https://docs.openstack.org/nova/latest/configuration/index.html).

A sample configuration example for nova [is available online](https://docs.openstack.org/nova/latest/configuration/sample-config.html) (cf. the wsgi part).

Paste deploy don't seem to define specific behaviours related to threads management.
It only seem to help to define application parts and related url/uri, database url, etc...

#### Running the WSGI app and services at start

Well, now we will continue to follow the nova code.

During the init of the nova-api application, nova will try to setup some services.
These services are setup by using the [`_setup_service` method](https://github.com/openstack/nova/blob/master/nova/api/openstack/wsgi_app.py#L42).

Services to setup are defined in a [service manager](https://github.com/openstack/nova/blob/013aa1915c79cfcb90c4333ce1e16b3c40f16be8/nova/service.py#L55,L62).

Nova manage services by using a [dedicated service module](https://github.com/openstack/nova/blob/f2b96588efa931fa10b188f0602738c484b965ed/nova/objects/service.py).

They services seems to be also retrieving by [querying the database](https://github.com/openstack/nova/blob/f2b96588efa931fa10b188f0602738c484b965ed/nova/objects/service.py#L321)
by [using the previous](https://github.com/openstack/nova/blob/master/nova/api/openstack/wsgi_app.py#L46) definied service module.

To continue this inspection of nova we will now become focused on the [`ConsoleAuthManager`](https://github.com/openstack/nova/blob/6ac15734b9678bfb876e7dfa6502a13d1fe2ee40/nova/consoleauth/manager.py#L38) module.
This class will instanciate a [`compute_rpcapi.ComputeAPI` object](https://github.com/openstack/nova/blob/6ac15734b9678bfb876e7dfa6502a13d1fe2ee40/nova/consoleauth/manager.py#L48)
This object ([`ComputeAPI`](https://github.com/openstack/nova/blob/51ed40a6a5fc046cef35337980a1fc5ad704a421/nova/compute/rpcapi.py#L73)) define
a [`router` method](https://github.com/openstack/nova/blob/51ed40a6a5fc046cef35337980a1fc5ad704a421/nova/compute/rpcapi.py#L383) who will return
a [rpc client](https://github.com/openstack/nova/blob/51ed40a6a5fc046cef35337980a1fc5ad704a421/nova/compute/rpcapi.py#L405).

The returned [RPC client](https://github.com/openstack/nova/blob/244c9240671d98b0df25b0ad0795b5de0c0c422c/nova/rpc.py#L208) returned by the [nova rpc module](https://github.com/openstack/nova/blob/master/nova/rpc.py) is an [oslo.messaging rpc client](https://github.com/openstack/nova/blob/master/nova/rpc.py#L18)

The instantiated oslo.messaging [`RPCClient`](https://github.com/openstack/oslo.messaging/blob/master/oslo_messaging/rpc/client.py#L239) 

The transport layer is defined by [nova](https://github.com/openstack/nova/blob/244c9240671d98b0df25b0ad0795b5de0c0c422c/nova/rpc.py#L69) and [it will be retrieved](https://github.com/openstack/nova/blob/244c9240671d98b0df25b0ad0795b5de0c0c422c/nova/rpc.py#L259) by using [the oslo.messaging mechanismes based on the config and the url](https://github.com/openstack/oslo.messaging/blob/master/oslo_messaging/transport.py#L218) and the oslo.messaging [defined drivers](https://github.com/openstack/oslo.messaging/blob/master/setup.cfg#L38,L50) by using [stevedore](https://github.com/openstack/oslo.messaging/blob/master/oslo_messaging/transport.py#L204).

In our case we will instantiate a [`RabbitDriver`](https://github.com/openstack/oslo.messaging/blob/master/oslo_messaging/_drivers/impl_rabbit.py#L1266).

The used driver will initiate a [connection pool](https://github.com/openstack/oslo.messaging/blob/master/oslo_messaging/_drivers/impl_rabbit.py#L1299,L1301)
by using the [Connection class](https://github.com/openstack/oslo.messaging/blob/master/oslo_messaging/_drivers/impl_rabbit.py#L417) defined in the driver.

The oslo.messaging connection pool module [will create the connection](https://github.com/openstack/oslo.messaging/blob/master/oslo_messaging/_drivers/pool.py#L144)
and also start the healt check mechanism by [triggering the heartbeat in a dedicated thread](Also://github.com/openstack/oslo.messaging/blob/master/oslo_messaging/_drivers/impl_rabbit.py#L897)

Also on the oslo.messaging we need to [take care about the connection class
execution model](https://github.com/openstack/oslo.messaging/blob/40c25c2bde6d2f5a756e7169060b7ce389caf174/oslo_messaging/_drivers/common.py#L369,L387).
Even if rabbit has only one Connection class,
this connection can be used for two purposes:
* wait and receive amqp messages (only do read stuffs on the socket)
* send messages to the broker (only do write stuffs on the socket)
The code inside a connection class is not concurrency safe.
Using one Connection class instance for doing both, will result
of eventlet complaining of multiple greenthreads that read/write the
same fd concurrently... because 'send' and 'listen' run in different
greenthread.
So, a connection cannot be shared between thread/greenthread and
this two variables permit to define the purpose of the connection
to allow drivers to add special handling if needed (like heatbeat).
amqp drivers create 3 kind of connections:
* driver.listen*(): each call create a new 'PURPOSE_LISTEN' connection
* driver.send*(): a pool of 'PURPOSE_SEND' connections is used
* driver internally have another 'PURPOSE_LISTEN' connection dedicated
  to wait replies of rpc call

On an over hand the connection pool seems to define the [`_on_expire` event
listener](https://github.com/openstack/oslo.messaging/blob/044e6f20e65084f3c4ecc554672d3271b2a2acd3/oslo_messaging/_drivers/pool.py#L137).
This listener seems to be called when an:
> Idle connection has expired and been closed

The _Idle connection_ here seem to be the connection with the rabbitmq server (by example) who have expired.
Then the "thread safe" [`Pool`](https://github.com/openstack/oslo.messaging/blob/044e6f20e65084f3c4ecc554672d3271b2a2acd3/oslo_messaging/_drivers/pool.py#L40) mechanism,
Modelled after the eventlet.pools.Pool interface, but designed to be safe
when using native threads without the GIL, defined the `expire` method who
will clean the pool from the expired connections based on a ttl.

I think we need to take care about the previous mechanism due to the fact that
the connection and the heartbeat have been invoqued from the connection pool mechanism
(cf. previous lines about how the connection pool module start the health check)

The nova rpc module also define a [RPC server](https://github.com/openstack/nova/blob/244c9240671d98b0df25b0ad0795b5de0c0c422c/nova/rpc.py#L215) inherited from [oslo.messaging](https://github.com/openstack/nova/blob/244c9240671d98b0df25b0ad0795b5de0c0c422c/nova/rpc.py#L18)

There the used executor is an [`eventlet` executor](https://github.com/openstack/nova/blob/244c9240671d98b0df25b0ad0795b5de0c0c422c/nova/rpc.py#L226), so the initiated object will use eventlet and so the heartbeat thread will use a green thread.

The oslo.messaging instantiate [RPC server](https://github.com/openstack/nova/blob/master/nova/rpc.py#L223) (https://github.com/openstack/oslo.messaging/blob/40c25c2bde6d2f5a756e7169060b7ce389caf174/oslo_messaging/rpc/server.py#L190)

## References

#### Eventlet story
- [openstack - eventlet to futurist blueprint](https://specs.openstack.org/openstack/oslo-specs/specs/liberty/adopt-futurist.html)
- [BZ1711794](https://bugzilla.redhat.com/show_bug.cgi?id=1711794)
- [LP1825584](https://bugs.launchpad.net/nova/+bug/1825584)
- [LP1826281](https://bugs.launchpad.net/tripleo/+bug/1826281)
- [review where I was](https://review.opendev.org/#/c/656901/)
- [futurist threadpoolexecutor](https://review.opendev.org/#/c/650172/)
- [Damien nova patch](https://review.opendev.org/#/c/657168/)
- [nova eventlet ML discuss - Damien](http://lists.openstack.org/pipermail/openstack-discuss/2019-April/005310.html)
- [[oslo][oslo-messaging][nova] Stein nova-api AMQP issue running under uWSGI](http://lists.openstack.org/pipermail/openstack-discuss/2019-May/005822.html)
- [eventlet best practices on openstack](ttps://review.opendev.org/#/c/154642/)
- [nova heartbeat and eventlet number of threads](https://bugs.launchpad.net/nova/+bug/1829062)
- [RabbitMQ connections lack heartbeat or TCP keepalives](https://bugs.launchpad.net/nova/+bug/856764)
- [A 'greenio' executor for oslo.messaging](https://blueprints.launchpad.net/oslo.messaging/+spec/greenio-executor)

### How nova use oslo.messaging

- [usage of the messaging rpc_transport](https://github.com/openstack/nova/search?q=get_rpc_transport&type=Code)
- [the nova rpc layer init the RPCClient](https://github.com/openstack/nova/blob/244c9240671d98b0df25b0ad0795b5de0c0c422c/nova/rpc.py)
- [the RPC client (ClientRouter) is in use in the nova rpcapi](https://github.com/openstack/nova/search?q=ClientRouter&unscoped_q=ClientRouter)
- [source code where the ClientRouter is used by the nova rpcapi (class ComputeAPI)](https://github.com/openstack/nova/blob/4af8da5b0b832cac6669c4241867f97899643ccd/nova/compute/rpcapi.py#L409)
- [the nova compute API ^^^ is in use in the nova consoles managers](https://github.com/openstack/nova/search?q=ComputeAPI&unscoped_q=ComputeAPI)
- [source code of usage of the compute api in the managers (consoleauth [deprecated])](https://github.com/openstack/nova/blob/6ac15734b9678bfb876e7dfa6502a13d1fe2ee40/nova/consoleauth/manager.py#L48)
- [source code of usage of the compute api in the managers (console)](https://github.com/openstack/nova/blob/c6218428e9b29a2c52808ec7d27b4b21aadc0299/nova/console/manager.py#L48)
- [the nova service will use the managers](https://github.com/openstack/nova/blob/013aa1915c79cfcb90c4333ce1e16b3c40f16be8/nova/service.py#L55)
- [[schema] example of life cycle during of call of the nova-api who will use the consoleauth](https://docs.openstack.org/nova/pike/_images/SCH_5009_V00_NUAC-VNC_OpenStack.png)
- [nova api is a rest api](https://docs.openstack.org/nova/latest/contributor/api-ref-guideline.html)
- [nova api infos](https://docs.openstack.org/nova/latest/contributor/index.html#the-nova-api)
- [nova wsgi init application](https://github.com/openstack/nova/blob/master/nova/api/openstack/compute/wsgi.py)
- [nova wsgi setup service](https://github.com/openstack/nova/blob/master/nova/api/openstack/wsgi_app.py#L42)
- [nova wsgi start](https://github.com/openstack/nova/blob/master/nova/api/openstack/compute/wsgi.py)
- [nova use paste to return the wsgi application](https://pypi.org/project/Paste/)

- [nova apache conf via puppet](https://github.com/openstack/puppet-openstacklib/blob/master/manifests/wsgi/apache.pp)
- [nova apache conf via puppet](https://github.com/openstack/puppet-nova/blob/master/manifests/wsgi/apache_api.pp#L158)

- [monkey patch ASAP on nova - commit](https://github.com/openstack/nova/commit/3c5e2b0e9fac985294a949852bb8c83d4ed77e04)                                                                                       
- [pep3333 - Python Web Server Gateway Interface v1.0.1](https://www.python.org/dev/peps/pep-3333/)
- [pep3333 - thread support](https://www.python.org/dev/peps/pep-3333/#thread-support)
- [uwsgi + paste](https://discuss.newrelic.com/t/uwsgi-paste-not-logging-data/34070)
- [uwsgi support paste](https://uwsgi-docs.readthedocs.io/en/latest/Python.html#paste-support)

- [RPC and nova](https://docs.openstack.org/nova/stein/reference/rpc.html)

- [oslo.messaging connection threads management (read, send)](https://github.com/openstack/oslo.messaging/blob/40c25c2bde6d2f5a756e7169060b7ce389caf174/oslo_messaging/_drivers/common.py#L369,L387)

- [openstack services and green threads (newton/OSP10)](https://docs.openstack.org/nova/newton/threading.html)

### paste and paste.deploy

- [paste deploy project](https://github.com/cdent/paste/issues/25)
- [explainations from Chris Dent](https://github.com/cdent/paste/issues/25#issuecomment-502158572)