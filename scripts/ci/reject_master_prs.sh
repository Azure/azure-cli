#!/usr/bin/env bash

set -ev

! [[ $TRAVIS_PULL_REQUEST != 'false' && $TRAVIS_BRANCH == 'master' ]]
