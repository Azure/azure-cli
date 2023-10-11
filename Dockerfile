#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

ARG PYTHON_VERSION="3.11"

FROM python:${PYTHON_VERSION}-alpine

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


# ca-certificates bash bash-completion - for convenience
# libintl and icu-libs - required by azure-devops https://github.com/Azure/azure-cli/pull/9683
# libc6-compat - required by az storage blob sync https://github.com/Azure/azure-cli/issues/10381

# We don't use openssl (3.0) for now. We only install it so that users can use it.
RUN apk add --no-cache ca-certificates bash bash-completion libintl icu-libs libc6-compat && update-ca-certificates

WORKDIR azure-cli
COPY . /azure-cli

# 1. Build packages and store in tmp dir
# 2. Install the cli and the other command modules that weren't included
RUN ./scripts/install_full.sh && python ./scripts/trim_sdk.py \
 && cat /azure-cli/az.completion > ~/.bashrc \
 && runDeps="$( \
    scanelf --needed --nobanner --recursive /usr/local \
        | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
        | sort -u \
        | xargs -r apk info --installed \
        | sort -u \
    )" \
 && apk add --virtual .rundeps $runDeps

WORKDIR /

# Remove CLI source code from the final image and normalize line endings.
RUN rm -rf ./azure-cli && \
    dos2unix /root/.bashrc /usr/local/bin/az

ENV AZ_INSTALLER=DOCKER
CMD bash
