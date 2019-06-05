# Behaviour of the AMQP heartbeat thread under various execution models

## Quick setup

    pipenv install
    pipenv run ./setup-containers.sh
    pipenv shell

The setup installs the neccessary python dependencies, and runs a
rabbitmq server in a podman or docker container. After the installation, you
are in the virtual env prepared by `pipenv` for you.

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
