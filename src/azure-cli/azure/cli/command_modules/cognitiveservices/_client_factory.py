# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def get_cognitiveservices_management_client(cli_ctx, *_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
    return get_mgmt_service_client(cli_ctx, CognitiveServicesManagementClient)


def cf_accounts(cli_ctx, *_):
    return get_cognitiveservices_management_client(cli_ctx).accounts


def cf_deleted_accounts(cli_ctx, *_):
    return get_cognitiveservices_management_client(cli_ctx).deleted_accounts


def cf_resource_skus(cli_ctx, *_):
    return get_cognitiveservices_management_client(cli_ctx).resource_skus
