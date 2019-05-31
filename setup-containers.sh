#!/bin/bash -eux
echo "Checking sudo permissions to run docker commands"
sudo true
sudo docker ps -aq --filter name=oslomsg | xargs --no-run-if-empty sudo docker rm --force
# use net=host to not deal with intermediate connections
sudo docker run -d --net=host --hostname my-rabbit --name oslomsg-rabbitmq rabbitmq
sudo docker exec oslomsg-rabbitmq timeout 20 /bin/bash -c 'while ! rabbitmqctl status &>/dev/null; do sleep 2; done; sleep 2'
sudo docker exec oslomsg-rabbitmq rabbitmqctl add_user testuser testpwd
sudo docker exec oslomsg-rabbitmq rabbitmqctl set_permissions -p / testuser '.*' '.*' '.*'
