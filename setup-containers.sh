#!/bin/bash -eux
source runtime.sh
echo "Checking sudo permissions to run ${CONTAINER_RUNTIME} commands"
sudo true
sudo ${CONTAINER_RUNTIME} ps -aq --filter name=oslomsg | xargs --no-run-if-empty sudo ${CONTAINER_RUNTIME} rm --force
# use net=host to not deal with intermediate connections
sudo ${CONTAINER_RUNTIME} run -d \
    -e RABBITMQ_NODENAME=rabbitmq \
    -p 5672:5672 \
    -p 15672:15672 \
    --net=host \
    --hostname my-rabbit \
    --name oslomsg-rabbitmq \
    rabbitmq:management
sudo ${CONTAINER_RUNTIME} exec oslomsg-rabbitmq \
    timeout 40 /bin/bash -c 'while ! rabbitmqctl status &>/dev/null; do sleep 10; done; sleep 2'
sudo ${CONTAINER_RUNTIME} exec oslomsg-rabbitmq \
    rabbitmqctl --node rabbitmq add_user testuser testpwd
sudo ${CONTAINER_RUNTIME} exec oslomsg-rabbitmq \
    rabbitmqctl set_permissions -p / testuser '.*' '.*' '.*'
echo "RabbitMQ setup done!"
echo "Browse the rabbitmq management dashboard at http://127.0.0.1:15672 (user=guest, pwd=guest)"
