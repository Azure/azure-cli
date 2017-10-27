#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

FROM python:3.6.3-alpine

ARG CLI_VERSION

# Metadata as defined at http://label-schema.org
ARG BUILD_DATE
LABEL maintainer="Microsoft" \
      org.label-schema.schema-version="1.0" \
      org.label-schema.vendor="Microsoft" \
      org.label-schema.name="Azure CLI 2.0" \
      org.label-schema.version=$CLI_VERSION \
      org.label-schema.license="MIT" \
      org.label-schema.description="The Azure CLI 2.0 is the new Azure CLI and is applicable when you use the Resource Manager deployment model." \
      org.label-schema.url="https://docs.microsoft.com/en-us/cli/azure/overview" \
      org.label-schema.usage="https://docs.microsoft.com/en-us/cli/azure/install-az-cli2#docker" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.vcs-url="https://github.com/Azure/azure-cli.git" \
      org.label-schema.docker.cmd="docker run -v \${HOME}/.azure:/root/.azure -it azuresdk/azure-cli-python:$CLI_VERSION"

WORKDIR azure-cli
COPY . /azure-cli
# pip wheel - required for CLI packaging
# jmespath-terminal - we include jpterm as a useful tool
RUN pip install --no-cache-dir --upgrade pip wheel jmespath-terminal
# bash gcc make openssl-dev libffi-dev musl-dev - dependencies required for CLI
# jq - we include jq as a useful tool
# openssh - included for ssh-keygen
# ca-certificates
# wget - required for installing jp
RUN apk add --no-cache bash gcc make openssl-dev libffi-dev musl-dev jq openssh \
    ca-certificates wget openssl git && update-ca-certificates
# We also, install jp
RUN wget https://github.com/jmespath/jp/releases/download/0.1.2/jp-linux-amd64 -qO /usr/local/bin/jp && chmod +x /usr/local/bin/jp

# 1. Build packages and store in tmp dir
# 2. Install the cli and the other command modules that weren't included
# 3. Temporary fix - install azure-nspkg to remove import of pkg_resources in azure/__init__.py (to improve performance)
RUN /bin/bash -c 'TMP_PKG_DIR=$(mktemp -d); \
    for d in src/azure-cli src/azure-cli-core src/azure-cli-nspkg src/azure-cli-command_modules-nspkg src/command_modules/azure-cli-*/; \
    do cd $d; echo $d; python setup.py bdist_wheel -d $TMP_PKG_DIR; cd -; \
    done; \
    [ -d privates ] && cp privates/*.whl $TMP_PKG_DIR; \
    all_modules=`find $TMP_PKG_DIR -name "*.whl"`; \
    pip install --no-cache-dir $all_modules; \
    pip install --no-cache-dir --force-reinstall --upgrade azure-nspkg azure-mgmt-nspkg;'

# Tab completion
RUN cat /azure-cli/az.completion > ~/.bashrc

WORKDIR /

CMD bash
