# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from enum import Enum

ACR_RESOURCE_PROVIDER = 'Microsoft.ContainerRegistry'
REGISTRY_RESOURCE_TYPE = ACR_RESOURCE_PROVIDER + '/registries'
WEBHOOK_RESOURCE_TYPE = REGISTRY_RESOURCE_TYPE + '/webhooks'
REPLICATION_RESOURCE_TYPE = REGISTRY_RESOURCE_TYPE + '/replications'

CREDENTIAL_SET_RESOURCE_ID_TEMPLATE = '/subscriptions/{sub_id}/resourceGroups/{rg}/providers/Microsoft.ContainerRegistry/registries/{reg_name}/credentialSets/{cred_set_name}'

USER_ASSIGNED_IDENTITY_RESOURCE_ID_TEMPLATE = '/subscriptions/{sub_id}/resourceGroups/{rg}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/{identity_name}'

TASK_RESOURCE_TYPE = REGISTRY_RESOURCE_TYPE + '/tasks'
TASK_VALID_VSTS_URLS = ['visualstudio.com', 'dev.azure.com']
TASK_RESOURCE_ID_TEMPLATE = '/subscriptions/{sub_id}/resourceGroups/{rg}/providers/Microsoft.ContainerRegistry/registries/{reg}/tasks/{name}'

TASKRUN_RESOURCE_TYPE = REGISTRY_RESOURCE_TYPE + '/taskruns'

ACR_TASK_YAML_DEFAULT_NAME = 'acb.yaml'

ACR_CACHED_BUILDER_IMAGES = ('cloudfoundry/cnb:bionic',)

ACR_NULL_CONTEXT = '/dev/null'

ACR_TASK_QUICKTASK = 'quicktask'

ACR_RUN_DEFAULT_TIMEOUT_IN_SEC = 60 * 60  # 60 minutes

ACR_AUDIENCE_RESOURCE_NAME = "containerregistry"

# Regex pattern to validate that registry name is alphanumeric and between 5 and 50 characters
# Dashes "-" are allowed to accomodate for domain name label scope, but is blocked on registry creation "acr create"
ACR_NAME_VALIDATION_REGEX = r'^[a-zA-Z0-9-]{5,50}$'

ALLOWED_TASK_FILE_TYPES = ('.yaml', '.yml', '.toml', '.json', '.sh', '.bash', '.zsh', '.ps1',
                           '.ps', '.cmd', '.bat', '.ts', '.js', '.php', '.py', '.rb', '.lua')

# https://github.com/opencontainers/distribution-spec/blob/main/spec.md#listing-referrers
REF_KEY = "manifests"


class AbacRoleAssignmentMode(Enum):
    ABAC = "rbac-abac"
    RBAC = "rbac"


def get_classic_sku(cmd):
    SkuName = cmd.get_models('SkuName')
    return [SkuName.classic.value]


def get_managed_sku(cmd):
    SkuName = cmd.get_models('SkuName')
    return [SkuName.basic.value, SkuName.standard.value, SkuName.premium.value]


def get_premium_sku(cmd):
    SkuName = cmd.get_models('SkuName')
    return [SkuName.premium.value]


def get_valid_os():
    from azure.mgmt.containerregistrytasks.models import OS
    return [item.value.lower() for item in OS]


def get_valid_architecture():
    from azure.mgmt.containerregistrytasks.models import Architecture
    return [item.value.lower() for item in Architecture]


def get_valid_variant():
    from azure.mgmt.containerregistrytasks.models import Variant
    return [item.value.lower() for item in Variant]


def get_finished_run_status():
    from azure.mgmt.containerregistrytasks.models import RunStatus
    return [RunStatus.succeeded.value,
            RunStatus.failed.value,
            RunStatus.canceled.value,
            RunStatus.error.value,
            RunStatus.timeout.value]


def get_succeeded_run_status():
    from azure.mgmt.containerregistrytasks.models import RunStatus
    return [RunStatus.succeeded.value]


def get_succeeded_agentpool_status():
    from azure.mgmt.containerregistrytasks.models import ProvisioningState
    return [ProvisioningState.succeeded.value]


def get_finished_agentpool_status():
    from azure.mgmt.containerregistrytasks.models import ProvisioningState
    return [ProvisioningState.succeeded.value,
            ProvisioningState.failed.value,
            ProvisioningState.canceled.value]
