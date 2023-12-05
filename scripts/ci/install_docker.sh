#!/usr/bin/env bash
# ARM64 image does not have docker, install manually
set -evx
if [[ $(dpkg --print-architecture) == "amd64" ]]; then
    echo "Docker is already installed on AMD64"
    exit 0
fi
# https://docs.docker.com/engine/security/rootless/
/bin/bash -c "$(curl -fsSL https://get.docker.com)"
sudo apt-get install -y uidmap
dockerd-rootless-setuptool.sh install
export XDG_RUNTIME_DIR=/home/cloudtest/.docker/run
PATH=/usr/bin:/sbin:/usr/sbin:$PATH dockerd-rootless.sh &
sleep 5
docker context use rootless
