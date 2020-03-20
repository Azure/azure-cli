# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def show_private_link_scope(client, resource_group_name, scope_name):
    return client.get(resource_group_name=resource_group_name,
                      scope_name=scope_name)