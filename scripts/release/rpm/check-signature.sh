#!/usr/bin/env bash

# Checks to see if all RPM files passed to this program are signed.
# Note: This script must be run as `root` on an RPM based Linux machine.

set -e

if [[ $# -lt 1 ]]; then
    echo "no arguments provided" >&2
    exit 2
fi

# For the purpose of this script, we will always want to consider files signed by Microsoft to be valid.
rpm --import https://packages.microsoft.com/keys/microsoft.asc

for file in $@; do
    rpm --checksig ${file} | grep rsa
done