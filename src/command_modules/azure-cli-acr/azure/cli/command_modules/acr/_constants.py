# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

STORAGE_RESOURCE_TYPE = 'Microsoft.Storage/storageAccounts'

ACR_RESOURCE_PROVIDER = 'Microsoft.ContainerRegistry'
REGISTRY_RESOURCE_TYPE = ACR_RESOURCE_PROVIDER + '/registries'
WEBHOOK_RESOURCE_TYPE = REGISTRY_RESOURCE_TYPE + '/webhooks'
REPLICATION_RESOURCE_TYPE = REGISTRY_RESOURCE_TYPE + '/replications'
BUILD_TASK_RESOURCE_TYPE = REGISTRY_RESOURCE_TYPE + '/buildTasks'
BUILD_STEP_RESOURCE_TYPE = BUILD_TASK_RESOURCE_TYPE + '/steps'

CLASSIC_REGISTRY_SKU = ['Classic']
MANAGED_REGISTRY_SKU = ['Basic', 'Standard', 'Premium']
