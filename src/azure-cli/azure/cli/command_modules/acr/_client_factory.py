# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.client_factory import get_mgmt_service_client

VERSION_2019_05_01_PREVIEW = "2019-05-01-preview"
VERSION_2019_06_01_PREVIEW = "2019-06-01-preview"
VERSION_2020_11_01_PREVIEW = "2020-11-01-preview"
VERSION_2021_08_01_PREVIEW = "2021-08-01-preview"


def get_acr_service_client(cli_ctx, api_version=None):
    """Returns the client for managing container registries. """
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_CONTAINERREGISTRY, api_version=api_version)


def cf_acr_registries(cli_ctx, *_):
    return get_acr_service_client(cli_ctx).registries


def cf_acr_network_rules(cli_ctx, *_):
    return get_acr_service_client(cli_ctx, api_version=VERSION_2021_08_01_PREVIEW).registries


def cf_acr_registries_tasks(cli_ctx, *_):
    return get_acr_service_client(cli_ctx, api_version=VERSION_2019_06_01_PREVIEW).registries


def cf_acr_replications(cli_ctx, *_):
    return get_acr_service_client(cli_ctx).replications


def cf_acr_webhooks(cli_ctx, *_):
    return get_acr_service_client(cli_ctx).webhooks


def cf_acr_private_endpoint_connections(cli_ctx, *_):
    return get_acr_service_client(cli_ctx).private_endpoint_connections


def cf_acr_tasks(cli_ctx, *_):
    return get_acr_service_client(cli_ctx, VERSION_2019_06_01_PREVIEW).tasks


def cf_acr_taskruns(cli_ctx, *_):
    return get_acr_service_client(cli_ctx, VERSION_2019_06_01_PREVIEW).task_runs


def cf_acr_runs(cli_ctx, *_):
    return get_acr_service_client(cli_ctx, VERSION_2019_06_01_PREVIEW).runs


def cf_acr_scope_maps(cli_ctx, *_):
    return get_acr_service_client(cli_ctx, VERSION_2020_11_01_PREVIEW).scope_maps


def cf_acr_tokens(cli_ctx, *_):
    return get_acr_service_client(cli_ctx, VERSION_2020_11_01_PREVIEW).tokens


def cf_acr_token_credentials(cli_ctx, *_):
    return get_acr_service_client(cli_ctx, VERSION_2020_11_01_PREVIEW).registries


def cf_acr_agentpool(cli_ctx, *_):
    return get_acr_service_client(cli_ctx, VERSION_2019_06_01_PREVIEW).agent_pools


def cf_acr_connected_registries(cli_ctx, *_):
    return get_acr_service_client(cli_ctx, VERSION_2021_08_01_PREVIEW).connected_registries
