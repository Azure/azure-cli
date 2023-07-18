#!/usr/bin/env bash

set -ev

for TOX_FILE in $(find src -name tox.ini); do
    pwd
    (cd $(dirname $TOX_FILE) && tox)
done