# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from ._util import get_sql_management_client


def list_sql_server(resource_group_name):
    client = get_sql_management_client()
    return client.servers.list_by_resource_group(resource_group_name)
