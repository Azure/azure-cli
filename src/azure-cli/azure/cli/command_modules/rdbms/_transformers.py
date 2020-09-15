# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict


def table_transform_output(result):
    table_result = []
    for key in ('host', 'username', 'password', 'location', 'skuname', 'resource group', 'id', 'version', 'connection string'):
        entry = OrderedDict()
        entry['Property'] = key
        entry['Value'] = result[key]
        table_result.append(entry)

    return table_result


def table_transform_output_list_servers(result):
    table_result = []
    for key in result:
        new_entry = OrderedDict()
        new_entry['Name'] = key['name']
        new_entry['Resource Group'] = key['resourceGroup']
        new_entry['Location'] = key['location']
        new_entry['Version'] = key['version']
        new_entry['Storage Size(GiB)'] = int(key['storageProfile']['storageMb']) / 1024.0
        new_entry['State'] = key['state']
        new_entry['Tier'] = key['sku']['tier']
        new_entry['SKU'] = key['sku']['name']
        new_entry['HA State'] = key['haState']
        new_entry['Availability zone'] = key['availabilityZone']
        table_result.append(new_entry)
    return table_result
