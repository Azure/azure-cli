# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument
from azure.cli.core.util import sdk_no_wait
from azure.mgmt.synapse.models import AzureADOnlyAuthentication


def synapse_create_adonly_auth(cmd, client, resource_group_name, workspace_name, azure_ad_only_authentication_name,
                    enable_azure_ad_only_authentication, no_wait=False):
    azure_ad_only_authentication_info = AzureADOnlyAuthentication(azure_ad_only_authentication=enable_azure_ad_only_authentication)

    return sdk_no_wait(no_wait, client.begin_create, resource_group_name, workspace_name, 
                       azure_ad_only_authentication_name, azure_ad_only_authentication_info)