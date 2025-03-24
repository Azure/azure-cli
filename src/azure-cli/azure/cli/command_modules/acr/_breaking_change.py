# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_output_breaking_change, register_conditional_breaking_change, AzCLIOtherChange

register_output_breaking_change(command_name='acr login',
                                description='Exit code will be 1 if command fails for docker login')

register_conditional_breaking_change('HELM2RETIRE', AzCLIOtherChange(
    'acr helm',
    'In November 2020, Helm 2 reached end of life. Starting on March 30th, 2025 Azure Container Registry will no longer support Helm 2. Therefore, the legacy "Helm repositories" functionality will also be retired. **We recommend that you transition to Helm 3 immediately.**\n'
    'Starting January 21st, 2025 the CLI command [az acr helm push](/cli/azure/acr/helm/#az_acr_helm_push) will be retired to prevent pushing new Helm charts to legacy Helm repositories.\n'
    'Starting March 30th, 2025 the CLI command group [az acr helm](/cli/azure/acr/helm) will be retired, ending all legacy Helm repository capabilities in Azure Container Registry.\n'
    'All Helm charts not stored as an OCI artifact will be deleted from Azure Container Registry on March 30th, 2025.\n'
    'Learn how to find all Helm charts stored in a Helm repository here: [az acr helm list](/cli/azure/acr/helm/#az_acr_helm_list). If the Helm chart you are using is listed then it is stored in a legacy Helm repository and is at risk of deletion.\n'
    '\n'
    'For more information on managing and deploying applications for Kubernetes, see [Push and pull Helm charts to an Azure container registry](/azure/container-registry/container-registry-helm-repos).'
))
