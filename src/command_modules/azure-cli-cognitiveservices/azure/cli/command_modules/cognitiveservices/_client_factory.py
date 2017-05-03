# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# management client factories


def get_cognitiveservices_management_client(_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
    return get_mgmt_service_client(CognitiveServicesManagementClient, location='notused')


def get_cognitiveservices_account_operations(kwargs):
    return get_cognitiveservices_management_client(kwargs).cognitive_services_accounts


def get_cognitiveservices_operations(kwargs):
    return get_cognitiveservices_management_client(kwargs).accounts
