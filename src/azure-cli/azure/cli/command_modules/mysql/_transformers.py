# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, raise-missing-from
from collections import OrderedDict
from azure.cli.core.util import CLIError


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

    if not result:
        return table_result

    for key in result:
        new_entry = OrderedDict()
        new_entry['Name'] = key['name']
        new_entry['Resource Group'] = key['resourceGroup']
        new_entry['Location'] = key['location']
        new_entry['Version'] = key['version']
        new_entry['Storage Size(GiB)'] = int(key['storage']['storageSizeGb'])
        new_entry['Tier'] = key['sku']['tier']
        new_entry['SKU'] = key['sku']['name']

        if 'flexibleServers' in result[0]['id']:
            new_entry['State'] = key['state']
            new_entry['HA State'] = key['highAvailability']['state']
            new_entry['Availability zone'] = key['availabilityZone']

        table_result.append(new_entry)

    return table_result


def mysql_table_transform_output_list_skus(result):
    table_result = []
    if len(result) > 1:
        skus_tiers = result[0]["supportedFlexibleServerEditions"]
        for skus in skus_tiers:
            tier_name = skus["name"]
            try:
                keys = skus["supportedServerVersions"][0]["supportedSkus"]
                for key in keys:
                    new_entry = OrderedDict()
                    new_entry['SKU'] = key['name']
                    new_entry['Tier'] = tier_name
                    new_entry['vCore'] = key['vCores']
                    new_entry['Memory'] = str(int(key['supportedMemoryPerVCoreMb']) * int(key['vCores']) // 1024) + " GiB"
                    new_entry['Max Disk IOPS'] = key['supportedIops']
                    table_result.append(new_entry)
            except:
                raise CLIError("There is no sku available for this location.")

    return table_result


def table_transform_output_parameters(result):

    table_result = []

    if not result:
        return table_result

    for key in result:
        new_entry = OrderedDict()
        new_entry['Name'] = key['name']
        new_entry['DataType'] = key['dataType']
        new_entry['DefaultValue'] = key['defaultValue']
        new_entry['Source'] = key['source']
        new_entry['AllowedValues'] = key['allowedValues']

        table_result.append(new_entry)

    return table_result


def transform_backup(result):
    if result.type == 'Microsoft.DBforMySQL/flexibleServers/backups' and len(result.name) > 62:
        result.name = result.name[62:]

    if hasattr(result, 'system_data'):
        delattr(result, 'system_data')

    return result


def transform_backups_list(results):
    return [transform_backup(result) for result in results]
