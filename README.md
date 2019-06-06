# Behaviour of the AMQP heartbeat thread under various execution models

The main goal of this project is to test and develop [oslo.messaging](https://github.com/openstack/oslo.messaging) behaviors related to rabbitmq and especially the [rabbitmq driver](https://docs.openstack.org/oslo.messaging/latest/configuration/opts.html#oslo-messaging-rabbit)

## Setup

You can use setup your environment in 2 ways:
- The quick setup
- The debug setup

The *quick setup* will install dependencies from the internet by using
the latest available releases of the needed requirements.

The *debug setup* let's you setup your virtual environment free from any
dependencies, and in a second time it allow to you to install local packages
in a development mode to let's you tweak, modify and test your changes.

### Quick setup

```sh
pipenv install
pipenv run ./setup-containers.sh
pipenv shell
```

The setup installs the neccessary python dependencies from the latest
available official releases, and runs a rabbitmq server in a podman or docker
container. After the installation, you are in the virtual env prepared
by `pipenv` for you.

### Debug setup

```sh
pipenv
pipenv run ./setup-containers.sh
pipenv install -e /local/path/to/your/oslo.messaging/clone/oslo.messaging
pipenv shell
pip list | grep "oslo.messaging"
oslo.messaging     9.7.2.dev1 /local/path/to/your/oslo.messaging/clone/oslo.messaging
```

The debug setup runs a rabbitmq server in a podman or docker container.
This method let's you install a local version of your oslo.messaging
to help you to modify, debug, and test.
After the installation, you are in the virtual env prepared
by `pipenv` for you and you can add changes to your oslo.messaging clone to
test them interactively by using the following scenarios.

## Test 1: thread-based server

Spawns a oslo.messaging RPC server, running in a standalone python
process, with native thread polling.

```sh
./server.py > server.log &
```

You can target the server at the command line with:

```sh
./client.py 42
```

Check the AMQP connections to rabbitmq with:

```sh
ss -4tnp | grep 5672
```

## Test 2: uwsgi api server that contacts the thread-based server

Run the original RPC server as in test 1, and run an additional WSGI
api hosted by uwsgi:

```sh
./server.py > server.log &
uwsgi --http :9090 --logto uwsgi.log --wsgi-file uwsgi-api.py &
```

this time, the RPC service is accessible on localhost:9090:

```
curl http://localhost:9090/\?num\=1336
```

When uwsgi processes an incoming HTTP request, the API services
receives the query and makes a collateral RPC call to the RPC server.

In this test both the RPC server ans the API service running in uwsgi
hold AMQP connections the rabbitmq server.

## Test 3: eventlet WSGI API server

Run the original RPC server as in test 1, and the API service runs
under a eventlet-based WSGI server:

```sh
./server.py > server.log &
./eventlet-api.py > eventlet-api.log &
```

the RPC service is now accessible on localhost:8090:

```sh
curl http://localhost:8090/\?num\=1336
```

As in Test 2, the heartbeat can be inspected after the first API call.

## Test 4: Apache mod_wsgi server with monkey patched environment

Run the original RPC server as in test 1
in an apache mod_wsgi environment
with and monkey patched with eventlet, and the API service runs
under a eventlet-based WSGI server (by example):

```sh
pipenv run ./start-oslo-mod_wsgi.sh &
./eventlet-api.py > eventlet-api.log &
```

The previous example use upstream release of oslo.messaging and installed
as a dependencies like in test 1 but you can choose to install and use a
local clone of `oslo.messaging` or a local copy of another dependencies
(`oslo.utils` by example or `pyamqp`) by passing the root path of your local
clone as a parameter of your command, like the following example:

```sh
pipenv run ./start-oslo-mod_wsgi.sh ~/dev/openstack/oslo.messaging &
./eventlet-api.py > eventlet-api.log &
```

Or local clone will be installed and used in your fresh created
apache mod_wsgi container.

the RPC services is now accessible on localhost:8000 (mod_wsgi) and
localhost:8090 (eventlet-api):

You can send requests to the both by using:
```sh
curl 0.0.0.0:8000
```

```sh
curl http://localhost:8090/\?num\=1336
```

As in Test 2, the heartbeat can be inspected after the first API call.


## How to reproduce the heartbeat issue

Run the original RPC server as in test 1
in an apache mod_wsgi environment
with and monkey patched with eventlet, and the API service runs
under a eventlet-based WSGI server (by example):

```sh
pipenv run ./start-oslo-mod_wsgi.sh
```

the RPC services is now accessible on localhost:8000 (mod_wsgi):

You send a request to it by using:

```sh
curl 0.0.0.0:8000
```

Observe your connection appear into the [Rabbit management dashboard](http://127.0.0.1:15672/#/connections)
and see your connection disapear few secondes/minutes after your request

Now kill your running server and respawn a fresh server by using the server
without eventlet activated by using:

```sh
sudo podman run -it \
    --rm \
    -p 8000:80 \
    -e TRANSPORT_URL=rabbit://testuser:testpwd@$(sudo podman inspect oslomsg-rabbitmq  | niet '.[0].NetworkSettings.IPAddress'):5672/ \
    --name oslo_mod_wsgi \
    oslo_mod_wsgi \
    server.wsgi
```

Now observe your new created connection into the dashboard and observe 
that this connection still active all the time.

### Advanced usages for test 4

You can choose to start your test by using mod_wsgi like is described in the
previous section but maybe you want to test behaviours without eventlet turned
on or with the oslo.messaging server embdded in a high level greenthread, then
this section is made for you.

In the previous section by using the `start-oslo-mod_wsgi.sh` you have build
a container image who contains apache and mod_wsgi who will run a wsgi apps that
will start your oslo.messaging server.

You have choice between 3 apps modes:
- eventlet turned on and oslo.messaging who will use greenthreads (the default) - `server-eventlet.wsgi`
- eventlet turned off and oslo.messaging who will use pthreads - `server-eventlet.wsgi`
- eventlet turned on with your server apps (`server.py.start_server`) which will executed in a greenthread and oslo.messaging who will use greenthread too - `server-eventlet-gthread.wsgi`

To execute a specific mode please use the following command and replace the
wsgi filename by one of the 3 previous described modes, example `server-eventlet.gthread.wsgi`:

```sh
sudo podman run -it \
    --rm \
    -p 8000:80 \
    -e TRANSPORT_URL=rabbit://testuser:testpwd@$(sudo podman inspect oslomsg-rabbitmq  | niet '.[0].NetworkSettings.IPAddress'):5672/ \
    --name oslo_mod_wsgi \
    oslo_mod_wsgi \
    server-eventlet-gthread.wsgi # replace the filename here
```

## Server advanced usages

The server part offer to you few config options like define the rabbit config
choose the [oslo.messaging executor](https://docs.openstack.org/oslo.messaging/latest/reference/executors.html) (default `threading` here).

To see all the available options use the following command:
```sh
./server.py --help
usage: server.py [-h] [--eventlet-turned-on]
                 [--heartbeat-timeout HEARTBEAT_TIMEOUT]
                 [--rabbit-host RABBIT_HOST] [--rabbit-port RABBIT_PORT]
                 [--rabbit-user RABBIT_USER]
                 [--rabbit-user-pwd RABBIT_USER_PWD] [--run-oslo-in-thread]
                 [--oslo-executor OSLO_EXECUTOR]

optional arguments:
  -h, --help            show this help message and exit
  --eventlet-turned-on  turn on eventlet and monkey patch the env
  --heartbeat-timeout HEARTBEAT_TIMEOUT
                        the heartbeat timeout
  --rabbit-host RABBIT_HOST
  --rabbit-port RABBIT_PORT
  --rabbit-user RABBIT_USER
  --rabbit-user-pwd RABBIT_USER_PWD
  --run-oslo-in-thread
  --oslo-executor OSLO_EXECUTOR
```
