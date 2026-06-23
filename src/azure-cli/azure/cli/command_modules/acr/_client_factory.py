# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.client_factory import get_mgmt_service_client


def get_acr_service_client(cli_ctx, api_version=None):
    """Returns the client for managing container registries. """
    from azure.cli.core.profiles import ResourceType
    from azure.mgmt.containerregistry import ContainerRegistryManagementClient
    kwargs = {}
    # Older multi-API SDK packages (e.g., 14.x) expose a LATEST_PROFILE class attribute.
    # Explicitly passing it prevents failures when the global KnownProfiles.default is
    # overridden by other installed packages (e.g., Azure ML extensions), which can cause
    # a ValueError when accessing operation groups such as 'registries'.
    # New single-API packages (e.g., 15.x) do not have LATEST_PROFILE, so this is a no-op.
    if hasattr(ContainerRegistryManagementClient, 'LATEST_PROFILE'):
        kwargs['profile'] = ContainerRegistryManagementClient.LATEST_PROFILE
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_CONTAINERREGISTRY,
                                   api_version=api_version, **kwargs)


def get_acr_tasks_service_client(cli_ctx, api_version=None):
    """Returns the client for managing container registry tasks."""
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_CONTAINERREGISTRYTASKS, api_version=api_version)


# The function is used in Azure and Edge and hybrid profile is used to support the different API versions.
def cf_acr_registries(cli_ctx, *_):
    return get_acr_service_client(cli_ctx).registries


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
