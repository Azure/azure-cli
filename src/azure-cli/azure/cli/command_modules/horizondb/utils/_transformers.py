# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, raise-missing-from
from collections import OrderedDict


def table_transform_output(result):
    table_result = []
    for key in ('primary endpoint', 'username', 'password', 'location', 'configuration', 'resource group', 'id', 'version'):
        entry = OrderedDict()
        entry['Property'] = key
        entry['Value'] = result[key]
        table_result.append(entry)

    return table_result


def table_transform_output_list_clusters(result):

    table_result = []

    if not result:
        return table_result

    for key in result:
        new_entry = OrderedDict()
        new_entry['Name'] = key['name']
        new_entry['Resource Group'] = key['resourceGroup']
        new_entry['Location'] = key['location']
        new_entry['Version'] = key['version']

        table_result.append(new_entry)

    return table_result
