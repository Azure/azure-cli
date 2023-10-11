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
# libintl icu-libs - required by azure-devops https://github.com/Azure/azure-cli/pull/9683
# libc6-compat - required by az storage blob sync https://github.com/Azure/azure-cli/issues/10381
# gcc python3-dev musl-dev linux-headers libffi-dev - temporarily required by psutil

WORKDIR azure-cli
COPY . /azure-cli
RUN apk add --no-cache ca-certificates bash bash-completion libintl icu-libs libc6-compat \
    && apk add --no-cache --virtual .build-deps gcc python3-dev musl-dev linux-headers libffi-dev \
    && update-ca-certificates && ./scripts/install_full.sh && python ./scripts/trim_sdk.py \
    && cat /azure-cli/az.completion > ~/.bashrc \
    && dos2unix /root/.bashrc /usr/local/bin/az \
    && apk del .build-deps

RUN rm -rf /azure-cli

WORKDIR /

ENV AZ_INSTALLER=DOCKER
CMD bash
