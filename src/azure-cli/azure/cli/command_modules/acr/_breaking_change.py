# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_command_group_deprecate

helm_bc_msg = 'In November 2020, Helm 2 reached end of life. ' \
              'Starting on March 30th, 2025 Azure Container Registry will no longer support Helm 2. ' \
              'Therefore, the legacy "Helm repositories" functionality will also be retired. ' \
              'We recommend that you transition to Helm 3 immediately.\n' \
              'Starting January 21st, 2025 the CLI command `az acr helm push` was retired to ' \
              'prevent pushing new Helm charts to legacy Helm repositories.\n' \
              'Starting March 30th, 2025 the CLI command group `az acr helm` was retired, ' \
              'ending all legacy Helm repository capabilities in Azure Container Registry.\n' \
              'All Helm charts not stored as an OCI artifact ' \
              'was deleted from Azure Container Registry on March 30th, 2025.\n' \
              'Learn how to find all Helm charts stored in a Helm repository here: `az acr helm list`. ' \
              'If the Helm chart you are using is listed ' \
              'then it is stored in a legacy Helm repository and is at risk of deletion.\n' \
              'For more information on managing and deploying applications for Kubernetes, ' \
              'see https://aka.ms/acr/helm.'
register_command_group_deprecate(command_group='acr helm', redirect='Helm v3 commands', message=helm_bc_msg,
                                 target_version='Sept 30th, 2025')
