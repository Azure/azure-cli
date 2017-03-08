# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.mgmt.cognitiveservices.models import CognitiveServicesAccountCreateParameters, Sku, SkuName


def list(client, resource_group_name=None):
    if resource_group_name: 
       return client.list_by_resource_group(resource_group_name)
    else:
       return client.list()

def create(client, resource_group_name, account_name, sku_name, kind, location, tags=None):
    sku =  Sku(sku_name)
    properties= {}
    params = CognitiveServicesAccountCreateParameters(sku, kind, location, properties, tags)
    return client.create(resource_group_name, account_name, params)

    