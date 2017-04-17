#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

FROM python:3.5.2-alpine

ENV CLI_VERSION 0.2.5
ENV CLI_DOWNLOAD_SHA256 10d443edce3e61ef2123786e4c242ddf1c0a4ff46574742a37f8c1edd80e0914

# Metadata as defined at http://label-schema.org
ARG BUILD_DATE
LABEL org.label-schema.schema-version="1.0" \
      org.label-schema.vendor="Microsoft" \
      org.label-schema.name="Azure CLI 2.0" \
      org.label-schema.version=$CLI_VERSION \
      org.label-schema.license="MIT" \
      org.label-schema.description="The Azure CLI 2.0 is the new Azure CLI and is applicable when you use the Resource Manager deployment model." \
      org.label-schema.url="https://docs.microsoft.com/en-us/cli/azure/overview" \
      org.label-schema.usage="https://docs.microsoft.com/en-us/cli/azure/install-az-cli2#docker" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.vcs-url="https://github.com/Azure/azure-cli.git" \
      org.label-schema.docker.cmd="docker run -v ${HOME}:/root -it azuresdk/azure-cli-python:<version>"

# INSTALL DEPENDENCIES
# pip wheel - required for CLI packaging
# jmespath-terminal - we include jpterm as a useful tool
RUN pip install --upgrade pip wheel jmespath-terminal
# bash gcc openssl-dev libffi-dev musl-dev - dependencies required for CLI
# jq - we include jq as a useful tool
# openssh - included for ssh-keygen
# ca-certificates 
# wget - required for installing jp
RUN apk update \
        && apk add bash gcc openssl-dev libffi-dev musl-dev jq openssh ca-certificates wget openssl git \
        && update-ca-certificates
# We also, install jp
RUN wget https://github.com/jmespath/jp/releases/download/0.1.2/jp-linux-amd64 -qO /usr/local/bin/jp \
        && chmod +x /usr/local/bin/jp

# DOWNLOAD, EXTRACT, PATCH, BUILD, INSTALL CLI
# Download and extract
RUN mkdir /cli-src
RUN src_zip=$(mktemp) \
        && wget https://azurecliprod.blob.core.windows.net/releases/azure-cli_packaged_${CLI_VERSION}.tar.gz -qO $src_zip \
        && echo "$CLI_DOWNLOAD_SHA256  $src_zip" | sha256sum -c - \
        && tar -xvzf $src_zip -C /cli-src \
        && rm $src_zip
# Build and install
RUN /bin/bash -c 'cd /cli-src/*; tmp_pkg_dir=$(mktemp -d); \
    for d in src/azure-cli src/azure-cli-core src/azure-cli-nspkg src/command_modules/azure-cli-*/; \
    do cd $d; python setup.py bdist_wheel -d $tmp_pkg_dir; cd -; \
    done; \
    pip install azure-cli -f $tmp_pkg_dir;'
# Tab completion
RUN cat /cli-src/*/az.completion >> ~/.bashrc

RUN rm -rf /cli-src

WORKDIR /

CMD bash
