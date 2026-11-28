# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.client_factory import get_mgmt_service_client

REGISTRY_TENANT_USAGE_ERROR = \
    "--registry-tenant can only be used when --registry is a container registry resource ID."
REGISTRY_TENANT_AUTH_ERROR = \
    "--registry-tenant is not supported when signed in with managed identity or Cloud Shell. " \
    "Sign in with a user or service principal that has access to both tenants."


def get_acr_service_client(cli_ctx, api_version=None, aux_tenants=None):
    """Returns the client for managing container registries. """
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_CONTAINERREGISTRY, api_version=api_version,
                                   aux_tenants=aux_tenants)


def get_acr_tasks_service_client(cli_ctx, api_version=None):
    """Returns the client for managing container registry tasks."""
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_CONTAINERREGISTRYTASKS, api_version=api_version)


# The function is used in Azure and Edge and hybrid profile is used to support the different API versions.
def cf_acr_registries(cli_ctx, *_):
    return get_acr_service_client(cli_ctx).registries


def cf_acr_import(cli_ctx, command_args):
    from azure.cli.core.azclierror import ArgumentUsageError, ValidationError
    from azure.cli.core._profile import Profile
    from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id

    registry_tenant = command_args.pop('registry_tenant', None)
    source_registry = command_args.get('source_registry')

    if registry_tenant:
        if not is_valid_resource_id(source_registry):
            raise ArgumentUsageError(REGISTRY_TENANT_USAGE_ERROR)

        resource_id = parse_resource_id(source_registry)
        if (resource_id.get('namespace', '').lower() != 'microsoft.containerregistry' or
                resource_id.get('type', '').lower() != 'registries'):
            raise ArgumentUsageError(REGISTRY_TENANT_USAGE_ERROR)

        profile = Profile(cli_ctx=cli_ctx)
        account = profile.get_subscription()
        user = account.get('user', {})
        if user.get('name') in ('systemAssignedIdentity', 'userAssignedIdentity') or user.get('cloudShellID'):
            raise ValidationError(REGISTRY_TENANT_AUTH_ERROR)

    aux_tenants = [registry_tenant] if registry_tenant else None
    return get_acr_service_client(cli_ctx, aux_tenants=aux_tenants).registries


def cf_acr_cache(cli_ctx, *_):
    return get_acr_service_client(cli_ctx).cache_rules


def cf_acr_cred_sets(cli_ctx, *_):
    return get_acr_service_client(cli_ctx).credential_sets


def cf_acr_registries_tasks(cli_ctx, *_):
    return get_acr_tasks_service_client(cli_ctx).registries


def cf_acr_replications(cli_ctx, *_):
    return get_acr_service_client(cli_ctx).replications


def cf_acr_webhooks(cli_ctx, *_):
    return get_acr_service_client(cli_ctx).webhooks


def cf_acr_private_endpoint_connections(cli_ctx, *_):
    return get_acr_service_client(cli_ctx).private_endpoint_connections


def cf_acr_tasks(cli_ctx, *_):
    return get_acr_tasks_service_client(cli_ctx).tasks


def cf_acr_taskruns(cli_ctx, *_):
    return get_acr_tasks_service_client(cli_ctx).task_runs


def cf_acr_runs(cli_ctx, *_):
    return get_acr_tasks_service_client(cli_ctx).runs


def cf_acr_scope_maps(cli_ctx, *_):
    return get_acr_service_client(cli_ctx).scope_maps


def cf_acr_tokens(cli_ctx, *_):
    return get_acr_service_client(cli_ctx).tokens


def cf_acr_token_credentials(cli_ctx, *_):
    return get_acr_service_client(cli_ctx).registries


def cf_acr_agentpool(cli_ctx, *_):
    return get_acr_tasks_service_client(cli_ctx).agent_pools


def cf_acr_connected_registries(cli_ctx, *_):
    return get_acr_service_client(cli_ctx).connected_registries
