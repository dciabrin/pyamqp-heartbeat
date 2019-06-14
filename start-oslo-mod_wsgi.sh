#!/bin/bash -eux
source runtime.sh
if ! rabbit_is_running; then
    echo "Rabbit server isn't running... launching an auto setup"
    exit 1
fi
sudo ${CONTAINER_RUNTIME} ps -aq --filter name=oslo_mod_wsgi | xargs --no-run-if-empty sudo ${CONTAINER_RUNTIME} rm --force
pkg_name=false
if [ $# -eq 1 ]; then
    local_pkg=$1
    if [ -d ${local_pkg} ]; then
        pkg_name=$(basename ${local_pkg})
    fi
    if [ -d ./${pkg_name} ]; then
        rm -rf ./${pkg_name}
    fi
    cp -r ${local_pkg} ./${pkg_name}
fi
rabbit_host=$(sudo ${CONTAINER_RUNTIME} inspect oslomsg-rabbitmq  | niet ".[0].NetworkSettings.IPAddress")
transport_url="rabbit://testuser:testpwd@${rabbit_host}:5672/"
sudo ${CONTAINER_RUNTIME} build --no-cache \
    -t oslo_mod_wsgi . \
    --build-arg LOCAL_PKG=${pkg_name} \
    --build-arg TRANSPORT_URL=${transport_url}
sudo ${CONTAINER_RUNTIME} run \
    -it \
    --rm \
    -p 8000:80 \
    -e TRANSPORT_URL=${transport_url} \
    --name oslo_mod_wsgi oslo_mod_wsgi
