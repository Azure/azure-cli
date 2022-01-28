#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# Dockerfile used by VS Code Spot extension. (https://marketplace.visualstudio.com/items?itemName=derek-bekoe.Spot)
# This allows Spots to be created directly from PRs.
# The major difference between Dockerfile.spot and Dockerfile is the latter depends on alpine and this one does not.

ARG PYTHON_VERSION="3.6.4"

FROM python:$PYTHON_VERSION

RUN apt-get install -y ca-certificates curl openssl git \
 && apt-get install -y gcc make libffi-dev \
 && update-ca-certificates

ARG JP_VERSION="0.1.3"

RUN curl https://github.com/jmespath/jp/releases/download/${JP_VERSION}/jp-linux-amd64 -o /usr/local/bin/jp \
 && chmod +x /usr/local/bin/jp \
 && pip install --no-cache-dir --upgrade jmespath-terminal

WORKDIR azure-cli
COPY . /azure-cli

# bash gcc make openssl-dev libffi-dev musl-dev - dependencies required for CLI
# openssh - included for ssh-keygen
# ca-certificates

# curl - required for installing jp
# pip wheel - required for CLI packaging
# jmespath-terminal - we include jpterm as a useful tool
# 1. Build packages and store in tmp dir
# 2. Install the cli and the other command modules that weren't included
RUN /bin/bash -c 'TMP_PKG_DIR=$(mktemp -d); \
    for d in src/azure-cli src/azure-cli-core src/command_modules/azure-cli-*/; \
    do cd $d; echo $d; python setup.py bdist_wheel -d $TMP_PKG_DIR; cd -; \
    done; \
    [ -d privates ] && cp privates/*.whl $TMP_PKG_DIR; \
    all_modules=`find $TMP_PKG_DIR -name "*.whl"`; \
    pip install --no-cache-dir $all_modules;' \
 && cat /azure-cli/az.completion > ~/.bashrc

WORKDIR /

RUN rm -rf azure-cli

CMD bash
