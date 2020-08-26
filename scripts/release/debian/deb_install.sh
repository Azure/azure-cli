#!/usr/bin/env bash

#######################################################################################################################
# This script does three fundamental things:                                                                          #
#   1. Add Microsoft's GPG Key has a trusted source of apt packages.                                                  #
#   2. Add Microsoft's repositories as a source for apt packages.                                                     #
#   3. Installs the Azure CLI from those repositories.                                                                #
# Given the nature of this script, it must be executed with elevated privileges, i.e. with `sudo`.                    #
#                                                                                                                     #
# Remember, with great power comes great responsibility.                                                              #
#                                                                                                                     #
# Do not be in the habit of executing scripts from the internet with root-level access to your machine. Only trust    #
# well-known publishers.                                                                                              #
#######################################################################################################################

set -e

if [[ $# -ge 1 && $1 == "-y" ]]; then
    global_consent=0
else
    global_consent=1
fi

function assert_consent {
    if [[ $2 -eq 0 ]]; then
        return 0
    fi

    echo -n "$1 [Y/n] "
    read consent
    if [[ ! "${consent}" == "y" && ! "${consent}" == "Y" && ! "${consent}" == "" ]]; then
        echo "'${consent}'"
        exit 1
    fi
}

global_consent=0 # Artificially giving global consent after review-feedback. Remove this line to enable interactive mode

setup() {

    assert_consent "Add packages necessary to modify your apt-package sources?" ${global_consent}
    set -v
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y apt-transport-https lsb-release gnupg curl
    set +v

    assert_consent "Add Microsoft as a trusted package signer?" ${global_consent}
    set -v
    curl -sL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /etc/apt/trusted.gpg.d/microsoft.asc.gpg
    set +v

    assert_consent "Add the Azure CLI Repository to your apt sources?" ${global_consent}
    set -v
    CLI_REPO=$(lsb_release -cs)
    echo "deb [arch=amd64] https://packages.microsoft.com/repos/azure-cli/ ${CLI_REPO} main" \
        > /etc/apt/sources.list.d/azure-cli.list
    apt-get update
    set +v

    assert_consent "Install the Azure CLI?" ${global_consent}
    apt-get install -y azure-cli

}

setup  # ensure the whole file is downloaded before executing
