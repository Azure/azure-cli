# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.mgmt.synapse.models import AzureADOnlyAuthentication


def synapse_enable_adonly_auth(client, resource_group_name, workspace_name):
    azure_ad_only_authentication_name = "default"
    azure_ad_only_authentication_info = AzureADOnlyAuthentication(azure_ad_only_authentication=True)

    return client.begin_create(resource_group_name, workspace_name,
                               azure_ad_only_authentication_name, azure_ad_only_authentication_info)


def synapse_disable_adonly_auth(client, resource_group_name, workspace_name):
    azure_ad_only_authentication_name = "default"
    azure_ad_only_authentication_info = AzureADOnlyAuthentication(azure_ad_only_authentication=False)

    return client.begin_create(resource_group_name, workspace_name,
                               azure_ad_only_authentication_name, azure_ad_only_authentication_info)
