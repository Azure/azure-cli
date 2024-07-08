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
      org.label-schema.description="A great cloud needs great tools; we're excited to introduce Azure CLI, our next generation multi-platform command line experience for Azure." \
      org.label-schema.url="https://docs.microsoft.com/cli/azure/overview" \
      org.label-schema.usage="https://docs.microsoft.com/cli/azure/install-az-cli2#docker" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.vcs-url="https://github.com/Azure/azure-cli.git" \
      org.label-schema.docker.cmd="docker run -v \${HOME}/.azure:/root/.azure -it mcr.microsoft.com/azure-cli:$CLI_VERSION"


# ca-certificates bash bash-completion jq jp openssh-keygen - for convenience
# libintl icu-libs - required by azure-devops extension https://github.com/Azure/azure-cli/pull/9683
# libc6-compat - required by az storage blob sync https://github.com/Azure/azure-cli/issues/10381
# gcc musl-dev linux-headers libffi-dev - temporarily required by psutil
# curl - temporarily required by jp

ARG JP_VERSION="0.2.1"

RUN --mount=type=bind,target=/azure-cli,source=./,rw apk add --no-cache ca-certificates bash bash-completion libintl icu-libs libc6-compat jq openssh-keygen \
    && apk add --no-cache --virtual .build-deps gcc musl-dev linux-headers libffi-dev curl \
    && update-ca-certificates && cd /azure-cli && ./scripts/install_full.sh && python ./scripts/trim_sdk.py \
    && cat /azure-cli/az.completion > ~/.bashrc \
    && dos2unix /root/.bashrc /usr/local/bin/az \
    && arch=$(arch | sed s/aarch64/arm64/ | sed s/x86_64/amd64/) && curl -L https://github.com/jmespath/jp/releases/download/${JP_VERSION}/jp-linux-$arch -o /usr/local/bin/jp \
    && chmod +x /usr/local/bin/jp \
    && apk del .build-deps

RUN rm -rf /azure-cli

WORKDIR /

ENV AZ_INSTALLER=DOCKER
CMD bash
