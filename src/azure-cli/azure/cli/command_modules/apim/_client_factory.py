# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_apim(cli_ctx, *_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.apimanagement import ApiManagementClient
    return get_mgmt_service_client(cli_ctx, ApiManagementClient)


def cf_service(cli_ctx, *_):
    return cf_apim(cli_ctx).api_management_service


def cf_api(cli_ctx, *_):
    return cf_apim(cli_ctx).api
