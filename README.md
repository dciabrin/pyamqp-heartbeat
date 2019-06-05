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

```
pipenv install
pipenv run ./setup-containers.sh
pipenv shell
```

The setup installs the neccessary python dependencies from the latest
available official releases, and runs a rabbitmq server in a podman or docker
container. After the installation, you are in the virtual env prepared
by `pipenv` for you.

### Debug setup

```
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

    ./server.py > server.log &

You can target the server at the command line with:

    ./client.py 42

Check the AMQP connections to rabbitmq with:

    ss -4tnp | grep 5672

## Test 2: uwsgi api server that contacts the thread-based server

Run the original RPC server as in test 1, and run an additional WSGI
api hosted by uwsgi:

    ./server.py > server.log &
    uwsgi --http :9090 --logto uwsgi.log --wsgi-file uwsgi-api.py &

this time, the RPC service is accessible on localhost:9090:

    curl http://localhost:9090/\?num\=1336

When uwsgi processes an incoming HTTP request, the API services
receives the query and makes a collateral RPC call to the RPC server.

In this test both the RPC server ans the API service running in uwsgi
hold AMQP connections the rabbitmq server.

## Test 3: eventlet WSGI API server

Run the original RPC server as in test 1, and the API service runs
under a eventlet-based WSGI server:

    ./server.py > server.log &
    ./eventlet-api.py > eventlet-api.log &

the RPC service is now accessible on localhost:8090:

    curl http://localhost:8090/\?num\=1336

As in Test 2, the heartbeat can be inspected after the first API call.
