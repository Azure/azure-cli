#!/usr/bin/env bash

set -e

for TOX_FILE in $(find src -name tox.ini); do
    pwd
    (cd $(dirname $TOX_FILE) && tox)
done