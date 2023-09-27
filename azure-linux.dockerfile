#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

FROM mcr.microsoft.com/cbl-mariner/base/core:2.0

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
      org.label-schema.usage="https://learn.microsoft.com/en-us/cli/azure/run-azure-cli-docker" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.vcs-url="https://github.com/Azure/azure-cli.git" \
      org.label-schema.docker.cmd="docker run -v \${HOME}/.azure:/root/.azure -it mcr.microsoft.com/azure-cli:$CLI_VERSION-azure"


# Azure Linux base image does not contain Mozilla CA certificates, install ca-certificates package to prevent CERTIFICATE_VERIFY_FAILED errors, see https://github.com/Azure/azure-cli/issues/26026
RUN --mount=type=bind,target=/azure-cli.rpm,source=./docker-temp/azure-cli.rpm tdnf install ca-certificates /azure-cli.rpm -y && tdnf clean all && rm -rf /var/cache/tdnf

ENV AZ_INSTALLER=DOCKER
CMD bash
