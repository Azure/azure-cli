# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_advisor(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.advisor import AdvisorManagementClient
    return get_mgmt_service_client(cli_ctx, AdvisorManagementClient)


def advisor_mgmt_client_factory(cli_ctx, kwargs):
    return cf_advisor(cli_ctx, **kwargs)


def recommendations_mgmt_client_factory(cli_ctx, kwargs):
    return cf_advisor(cli_ctx, **kwargs).recommendations


def suppressions_mgmt_client_factory(cli_ctx, kwargs):
    return cf_advisor(cli_ctx, **kwargs).suppressions


def configurations_mgmt_client_factory(cli_ctx, kwargs):
    return cf_advisor(cli_ctx, **kwargs).configurations
