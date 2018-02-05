# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def get_cognitiveservices_management_client(cli_ctx, *_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
    return get_mgmt_service_client(cli_ctx, CognitiveServicesManagementClient, location='notused')


def cf_cognitive_service_accounts(cli_ctx, *_):
    return get_cognitiveservices_management_client(cli_ctx).cognitive_services_accounts


def cf_accounts(cli_ctx, *_):
    return get_cognitiveservices_management_client(cli_ctx).accounts
