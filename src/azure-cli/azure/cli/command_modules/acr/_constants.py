# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.profiles import ResourceType
from azure.mgmt.containerregistry.v2019_06_01_preview.models import (
    Architecture,
    OS,
    ProvisioningState as AgentPoolStatus,
    RunStatus,
    Variant
)

ACR_RESOURCE_PROVIDER = 'Microsoft.ContainerRegistry'
REGISTRY_RESOURCE_TYPE = ACR_RESOURCE_PROVIDER + '/registries'
WEBHOOK_RESOURCE_TYPE = REGISTRY_RESOURCE_TYPE + '/webhooks'
REPLICATION_RESOURCE_TYPE = REGISTRY_RESOURCE_TYPE + '/replications'

TASK_RESOURCE_TYPE = REGISTRY_RESOURCE_TYPE + '/tasks'
TASK_VALID_VSTS_URLS = ['visualstudio.com', 'dev.azure.com']
TASK_RESOURCE_ID_TEMPLATE = '/subscriptions/{sub_id}/resourceGroups/{rg}/providers/Microsoft.ContainerRegistry/registries/{reg}/tasks/{name}'

TASKRUN_RESOURCE_TYPE = REGISTRY_RESOURCE_TYPE + '/taskruns'

ACR_TASK_YAML_DEFAULT_NAME = 'acb.yaml'

ACR_CACHED_BUILDER_IMAGES = ('cloudfoundry/cnb:bionic',)

ACR_NULL_CONTEXT = '/dev/null'

ACR_TASK_QUICKTASK = 'quicktask'


def get_classic_sku(cmd):
    SkuName = cmd.get_models('SkuName')
    return [SkuName.classic.value]


def get_managed_sku(cmd):
    SkuName = cmd.get_models('SkuName')
    return [SkuName.basic.value, SkuName.standard.value, SkuName.premium.value]


def get_premium_sku(cmd):
    SkuName = cmd.get_models('SkuName')
    return [SkuName.premium.value]


def get_valid_os(cmd):
    return [item.value.lower() for item in OS]


def get_valid_architecture(cmd):
    return [item.value.lower() for item in Architecture]


def get_valid_variant(cmd):
    return [item.value.lower() for item in Variant]


def get_finished_run_status(cmd):
    return [RunStatus.succeeded.value,
            RunStatus.failed.value,
            RunStatus.canceled.value,
            RunStatus.error.value,
            RunStatus.timeout.value]


def get_succeeded_run_status(cmd):
    return [RunStatus.succeeded.value]


def get_acr_task_models(cmd):
    from azure.cli.core.profiles import get_sdk
    return get_sdk(cmd.cli_ctx, ResourceType.MGMT_CONTAINERREGISTRY, 'models')


def get_succeeded_agentpool_status(cmd):
    return [AgentPoolStatus.succeeded.value]


def get_finished_agentpool_status(cmd):
    return [AgentPoolStatus.succeeded.value,
            AgentPoolStatus.failed.value,
            AgentPoolStatus.canceled.value]
