#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

ARG IMAGE
FROM $IMAGE

# ca-certificates: Azure Linux base image does not contain Mozilla CA certificates, install it to prevent CERTIFICATE_VERIFY_FAILED errors, see https://github.com/Azure/azure-cli/issues/26026
# jq: It's widely used for parsing JSON output in Azure CLI and has a small size. See https://github.com/Azure/azure-cli/issues/29830
RUN --mount=type=bind,target=/azure-cli.rpm,source=./docker-temp/azure-cli.rpm tdnf install ca-certificates jq /azure-cli.rpm -y && tdnf clean all && rm -rf /var/cache/tdnf

ENV AZ_INSTALLER=DOCKER
CMD bash
