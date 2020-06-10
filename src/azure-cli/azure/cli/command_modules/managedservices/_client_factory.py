# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_managedservices(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.managedservices import ManagedServicesClient
    return get_mgmt_service_client(cli_ctx, ManagedServicesClient, subscription_bound=False)


def cf_registration_definitions(cli_ctx, _):
    return cf_managedservices(cli_ctx).registration_definitions


def cf_registration_assignments(cli_ctx, _):
    return cf_managedservices(cli_ctx).registration_assignments
