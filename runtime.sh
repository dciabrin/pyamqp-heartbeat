#!/bin/bash -eux
if ! [[ $_ != $0 ]]; then
    echo "This is supposed to be sourced!"
    exit 1
fi
CONTAINER_RUNTIME=podman
if [ -z "$(which podman)" ]; then
    if [ -z "$(which docker)" ]; then
        echo "No container runtimes are available please install podman or docker first"
        exit 1
    fi
    CONTAINER_RUNTIME=docker
fi

RABBIT_RUNNING_CONTAINER_ID=$(sudo ${CONTAINER_RUNTIME} ps --filter name=oslomsg --quiet)

function rabbit_is_running {
    if [ -n "${RABBIT_RUNNING_CONTAINER_ID}" ]; then
        echo "rabbit server is up"
        true
    else
        echo "rabbit server is down"
        false
    fi
}
