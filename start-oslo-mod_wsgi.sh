#!/bin/bash -eux
source runtime.sh
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
rabbit_host=$(sudo ${CONTAINER_RUNTIME} inspect oslomsg-rabbitmq  | niet ".[0].Config.Hostname")
transport_url="rabbit://testuser:testpwd@${rabbit_host}:5672"
sudo ${CONTAINER_RUNTIME} build -t oslo_mod_wsgi . --build-arg LOCAL_PKG=${pkg_name} --build-arg TRANSPORT_URL=${transport_url}
sudo ${CONTAINER_RUNTIME} run -it --rm -p 8000:80 --name oslo_mod_wsgi oslo_mod_wsgi
