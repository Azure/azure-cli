# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_servicebus(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_SERVICEBUS)


def namespaces_mgmt_client_factory(cli_ctx, _):
    return cf_servicebus(cli_ctx).namespaces


def queues_mgmt_client_factory(cli_ctx, _):
    return cf_servicebus(cli_ctx).queues


def topics_mgmt_client_factory(cli_ctx, _):
    return cf_servicebus(cli_ctx).topics


def subscriptions_mgmt_client_factory(cli_ctx, _):
    return cf_servicebus(cli_ctx).subscriptions


def rules_mgmt_client_factory(cli_ctx, _):
    return cf_servicebus(cli_ctx).rules


def disaster_recovery_mgmt_client_factory(cli_ctx, _):
    return cf_servicebus(cli_ctx).disaster_recovery_configs


def migration_mgmt_client_factory(cli_ctx, _):
    return cf_servicebus(cli_ctx).migration_configs
