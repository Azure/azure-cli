# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import (
    register_command_group_deprecate,
    register_logic_breaking_change
)

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

content_trust_bc_msg = 'Content Trust is being deprecated and will be completely removed on March 31, 2028. ' \
                       'Refer to https://aka.ms/acr/dctdeprecation for details and transition guidance'

register_command_group_deprecate(command_group='acr helm', redirect='Helm v3 commands', message=helm_bc_msg,
                                 target_version='Sept 30th, 2025')

register_command_group_deprecate(command_group='acr config content-trust', message=content_trust_bc_msg)

register_logic_breaking_change('acr check-health', 'Remove Notary client version validation',
                               detail='The Notary client version check will no longer be performed as part of the '
                                      'check-health command due to Docker Content Trust deprecation.',
                               doc_link='https://aka.ms/acr/dctdeprecation')

register_logic_breaking_change('acr config content-trust update', 'Remove content-trust enabled configuration',
                               detail='The `--status enabled` parameter will no longer be accepted and will result in '
                                      'an error due to Docker Content Trust deprecation.',
                               doc_link='https://aka.ms/acr/dctdeprecation')
