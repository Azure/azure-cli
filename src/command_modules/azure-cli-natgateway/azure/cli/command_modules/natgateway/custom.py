# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def create_natgateway(cmd, natgateway_name, resource_group_name, location=None):
    from azure.mgmt.example.network import natgateway
    from ._client_factory import get_devtestlabs_lab_operation

    client = cf_natgateway(cmd.cli_ctx)

    foo = MyFoo(location=location)
    return client.create_or_update(natgateway_name, resource_group_name, foo)

def list_natgateways(client, resource_group_name=None):
    # Retrieve accounts via subscription
    if resource_group_name is None:
        return client.list_by_subscription()
    # Retrieve accounts via resource group
    return client.list_by_resource_group(resource_group_name)
