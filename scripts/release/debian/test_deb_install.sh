#!/usr/bin/env bash

base_images=("ubuntu:xenial" "ubuntu:bionic" "debian:stretch" "debian:jessie" "debian:buster")

set -e

for image in ${base_images[@]}; do
    docker build --build-arg base=${image} s-t deb-installer:current -f Dockerfile.install_test .
    docker run -it --rm deb-installer:current
done
