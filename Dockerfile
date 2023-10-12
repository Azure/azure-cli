# syntax=docker/dockerfile:1.4
#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

ARG PYTHON_VERSION="3.11"

FROM python:${PYTHON_VERSION}-alpine AS base

# We don't use openssl (3.0) for now. We only install it so that users can use it.
# libintl and icu-libs - required by azure devops artifact (az extension add --name azure-devops)
RUN apk add --no-cache \
    bash bash-completion openssh-keygen ca-certificates openssl \
    curl jq git perl zip \
    libintl icu-libs libc6-compat \
 && update-ca-certificates


FROM base AS builder

ARG JP_VERSION="0.2.1"
# bash gcc make openssl-dev libffi-dev musl-dev - dependencies required for CLI
RUN apk add --no-cache --virtual .build-deps gcc make openssl-dev libffi-dev musl-dev linux-headers

WORKDIR azure-cli
COPY . /azure-cli

# 1. Install azure-cli in /usr/local
# 2. Run trim_sdk.py to clean up un-used py files: https://github.com/Azure/azure-cli/pull/25801
# 3. Check that az and az.completion.sh can run
# 4. Remove __pycache__. It is important that we run this at the end
RUN ./scripts/install_full.sh
RUN python3 ./scripts/trim_sdk.py
RUN /usr/local/bin/az && bash -c "source /usr/local/bin/az.completion.sh"
RUN find /usr/local/lib/python*/site-packages/azure -name __pycache__ | xargs rm -rf

# Install jp tool
RUN <<HERE
  arch=$(arch | sed s/aarch64/arm64/ | sed s/x86_64/amd64/)
  curl -L https://github.com/jmespath/jp/releases/download/${JP_VERSION}/jp-linux-${arch} -o /usr/local/bin/jp
  chmod +x /usr/local/bin/jp
HERE


FROM base

ARG CLI_VERSION

# Metadata as defined at http://label-schema.org
ARG BUILD_DATE

LABEL maintainer="Microsoft" \
      org.label-schema.schema-version="1.0" \
      org.label-schema.vendor="Microsoft" \
      org.label-schema.name="Azure CLI" \
      org.label-schema.version=$CLI_VERSION \
      org.label-schema.license="MIT" \
      org.label-schema.description="The Azure CLI is used for all Resource Manager deployments in Azure." \
      org.label-schema.url="https://docs.microsoft.com/cli/azure/overview" \
      org.label-schema.usage="https://docs.microsoft.com/cli/azure/install-az-cli2#docker" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.vcs-url="https://github.com/Azure/azure-cli.git" \
      org.label-schema.docker.cmd="docker run -v \${HOME}/.azure:/root/.azure -it mcr.microsoft.com/azure-cli:$CLI_VERSION"

RUN --mount=from=builder,target=/mnt <<HERE
  cd /mnt/usr/local
  cp -ru . /usr/local/
  ln -s /usr/local/bin/az.completion.sh /etc/profile.d/
HERE

ENV AZ_INSTALLER=DOCKER
CMD bash
