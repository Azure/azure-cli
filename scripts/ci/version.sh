#!/usr/bin/env bash

# Update the version strings in the source code

# Input:
#   $1 - the version string, if omitted, use current time

version=$1

if [ -z $version ]; then
    echo 'Use utc timestamp as version'
    version=dev`date -u '+%Y%m%d%H%M%S'`
fi

echo "Replace with version: $version"

platform=`uname`

for each in $(find src -name __main__.py); do
    if [ "$platform" == "Darwin" ]; then
        sed -i "" "s/^__version__ = [\"']\(.*\)[\"']/__version__ = \"\1.$version\"/" $each
    else
        sed -i "s/^__version__ = [\"']\(.*\)[\"']/__version__ = \"\1.$version\"/" $each
    fi
done

for each in $(find src -name __init__.py); do
    if [ "$platform" == "Darwin" ]; then
        sed -i "" "s/^__version__ = [\"']\(.*\)[\"']/__version__ = \"\1.$version\"/" $each
    else
        sed -i "s/^__version__ = [\"']\(.*\)[\"']/__version__ = \"\1.$version\"/" $each
    fi
done

for each in $(find src -name setup.py); do
    if [ "$platform" == "Darwin" ]; then
        sed -i "" "s/^VERSION = [\"']\(.*\)[\"']/VERSION = \"\1.$version\"/" $each
    else
        sed -i "s/^VERSION = [\"']\(.*\)[\"']/VERSION = \"\1.$version\"/" $each
    fi
done

for each in src/azure-cli-core/azure/cli/core/commandIndex.latest.json src/azure-cli-core/azure/cli/core/helpIndex.latest.json; do
    if [ -f "$each" ]; then
        if [ "$platform" == "Darwin" ]; then
            sed -i "" "s/^  \"version\": \"\(.*\)\",/  \"version\": \"\1.$version\",/" $each
        else
            sed -i "s/^  \"version\": \"\(.*\)\",/  \"version\": \"\1.$version\",/" $each
        fi
    fi
done
