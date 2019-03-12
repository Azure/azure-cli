#!/usr/bin/env bash

set -ev


if [[ $TRAVIS_PULL_REQUEST != 'false' && $TRAVIS_BRANCH == 'master' ]]; then
    echo "PRs should target a branch other than master"
    exit 1
else
    exit 0
fi

