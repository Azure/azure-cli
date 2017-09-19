#!/usr/bin/env bash

# Update the version strings in the source code

# Input:
#   $1 - the version string, if omitted, use $TRAVIS_BUILD_NUMBER

version=$1

if [ -z $version ]; then
    version=$TRAVIS_BUILD_NUMBER
fi

if [ -z $version ]; then
    echo 'Missing version string'
    exit 1
fi

echo "Replace with version: $version"

platform=`uname`

for each in $(find src -name __init__.py); do
    if [ "$platform" == "Darwin" ]; then
        sed -i "" "s/^__version__ = [\"']\(.*\)+dev[\"']/__version__ = \"\1+dev.$version\"/" $each
    else
        sed -i "s/^__version__ = [\"']\(.*\)+dev[\"']/__version__ = \"\1+dev.$version\"/" $each
    fi
done

for each in $(find src -name setup.py); do
    if [ "$platform" == "Darwin" ]; then
        sed -i "" "s/^VERSION = [\"']\(.*\)+dev[\"']/VERSION = \"\1+dev.$version\"/" $each
    else
        sed -i "s/^VERSION = [\"']\(.*\)+dev[\"']/VERSION = \"\1+dev.$version\"/" $each
    fi
done

