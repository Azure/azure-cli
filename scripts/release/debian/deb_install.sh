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
    apt-get install --assume-yes --no-install-recommends apt-transport-https ca-certificates curl gnupg lsb-release
    set +v

    assert_consent "Add Microsoft as a trusted package signer?" ${global_consent}
    set -v
    mkdir -p /etc/apt/keyrings
    curl -sLS https://packages.microsoft.com/keys/microsoft.asc |
      gpg --dearmor > /etc/apt/keyrings/microsoft.gpg
    chmod go+r /etc/apt/keyrings/microsoft.gpg
    set +v

    assert_consent "Add the Azure CLI Repository to your apt sources?" ${global_consent}
    set -v
    # Use env var DIST_CODE for the package dist name if provided
    if [[ -z $DIST_CODE ]]; then
        CLI_REPO=$(lsb_release -cs)
        shopt -s nocasematch
        ERROR_MSG="Unable to find a package for your system. Please check if an existing package in https://packages.microsoft.com/repos/azure-cli/dists/ can be used in your system and install with the dist name: 'curl -sL https://aka.ms/InstallAzureCLIDeb | sudo DIST_CODE=<dist_code_name> bash'"
        if [[ ! $(curl -sL https://packages.microsoft.com/repos/azure-cli/dists/) =~ $CLI_REPO ]]; then
            DIST=$(lsb_release -is)
            if [[ $DIST =~ "Ubuntu" ]]; then
                CLI_REPO="jammy"
            elif [[ $DIST =~ "Debian" ]]; then
                CLI_REPO="bookworm"
            elif [[ $DIST =~ "LinuxMint" ]]; then
                CLI_REPO=$(grep -Po 'UBUNTU_CODENAME=\K.*' /etc/os-release) || true
                if [[ -z $CLI_REPO ]]; then
                    echo "$ERROR_MSG"
                    exit 1
                fi
            else
                echo "$ERROR_MSG"
                exit 1
            fi
        fi
    else
        CLI_REPO=$DIST_CODE
        if [[ ! $(curl -sL https://packages.microsoft.com/repos/azure-cli/dists/) =~ $CLI_REPO ]]; then
            echo "Unable to find an azure-cli package with DIST_CODE=$CLI_REPO in https://packages.microsoft.com/repos/azure-cli/dists/."
            exit 1
        fi
    fi

    if [ -f /etc/apt/sources.list.d/azure-cli.list ]; then
      rm /etc/apt/sources.list.d/azure-cli.list
    fi

    echo "Types: deb
URIs: https://packages.microsoft.com/repos/azure-cli/
Suites: ${CLI_REPO}
Components: main
Architectures: $(dpkg --print-architecture)
Signed-by: /etc/apt/keyrings/microsoft.gpg" | tee /etc/apt/sources.list.d/azure-cli.sources
    apt-get update
    set +v

    assert_consent "Install the Azure CLI?" ${global_consent}
    apt-get install --assume-yes azure-cli

}

setup  # ensure the whole file is downloaded before executing
