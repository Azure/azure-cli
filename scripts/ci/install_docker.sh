#!/usr/bin/env bash
# ARM64 image does not have docker, install manually
set -evx
if [[ $(dpkg --print-architecture) == "amd64" ]]; then
    echo "Docker is already installed on AMD64"
    exit 0
fi

# https://docs.docker.com/engine/install/ubuntu/#install-using-the-convenience-script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo chmod 666 /var/run/docker.sock
