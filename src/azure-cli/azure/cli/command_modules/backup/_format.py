# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict


def transform_container(result):
    return OrderedDict([('Name', result['name']),
                        ('Friendly Name', result['properties']['friendlyName']),
                        ('Resource Group', result['resourceGroup']),
                        ('Type', result['properties']['backupManagementType']),
                        ('Registration Status', result['properties']['registrationStatus'])])


def transform_item(result):
    columns = []
    columns.append(('Name', result['name']))
    columns.append(('Friendly Name', result['properties']['friendlyName']))
    columns.append(('Container name', result['properties']['containerName']))
    columns.append(('Resource Group', result['resourceGroup']))
    columns.append(('Type', result['properties']['workloadType']))
    columns.append(('Last Backup Status', result['properties']['lastBackupStatus']))
    columns.append(('Last Recovery Point', result['properties']['lastRecoveryPoint']))
    if 'protectionStatus' in result['properties']:
        columns.append(('Protection Status', result['properties']['protectionStatus']))
    if 'healthStatus' in result['properties']:
        columns.append(('Health Status', result['properties']['healthStatus']))

    if 'healthDetails' in result['properties'] and result['properties']['healthDetails'] is not None:
        recommendations = []
        for health_detail in result['properties']['healthDetails']:
            recommendations.append(', '.join(health_detail['recommendations']))
        columns.append(('Recommendations', ', '.join(recommendations)))

    return OrderedDict(columns)


def transform_job(result):
    columns = []
    columns.append(('Name', result['name']))
    columns.append(('Operation', result['properties']['operation']))
    columns.append(('Status', result['properties']['status']))
    columns.append(('Item Name', result['properties']['entityFriendlyName']))
    columns.append(('Backup Management Type', result['properties']['backupManagementType']))
    columns.append(('Start Time UTC', result['properties']['startTime']))
    duration = "0:00:00.000000"
    if result['properties']['duration'] is not None:
        duration = result['properties']['duration']
    columns.append(('Duration', duration))

    return OrderedDict(columns)


def transform_policy(result):
    return OrderedDict([('Name', result['name']),
                        ('Resource Group', result['resourceGroup']),
                        ('Type', result['properties']['backupManagementType'])])


def transform_recovery_point(result):
    if result['properties']['objectType'][:13] == "AzureWorkload":
        return OrderedDict([('Name', result['name']),
                            ('Time', result['properties']['recoveryPointTimeInUtc']),
                            ('BackupManagementType', 'AzureWorkload'),
                            ('Item Name', result['id'].split('/')[14]),
                            ('RecoveryPointType', result['properties']['type'])])
    return OrderedDict([('Name', result['name']),
                        ('Time', result['properties']['recoveryPointTime']),
                        ('Consistency', result['properties']['recoveryPointType'])])


def transform_log_chain(result):
    columns = []
    columns.append(('Name', result['name']))
    columns.append(('Resource Group', result['resourceGroup']))
    if result['properties']['timeRanges']:
        columns.append(('Start Time UTC', result['properties']['timeRanges'][0]['startTime']))
        columns.append(('End Time UTC', result['properties']['timeRanges'][0]['endTime']))
    return OrderedDict(columns)


def transform_protectable_item(result):
    columns = []
    columns.append(('Name', result['name']))
    columns.append(('Protectable Item Type', result['properties']['protectableItemType']))
    columns.append(('ParentName', result['properties']['parentName']))
    columns.append(('ServerName', result['properties']['serverName']))
    columns.append(('isProtected', result['properties']['protectionState']))

    return OrderedDict(columns)


def transform_container_list(container_list):
    return [transform_container(c) for c in container_list]


def transform_item_list(item_list):
    return [transform_item(i) for i in item_list]


def transform_job_list(job_list):
    return [transform_job(j) for j in job_list]


def transform_policy_list(policy_list):
    return [transform_policy(p) for p in policy_list]


def transform_recovery_point_list(recovery_point_list):
    return [transform_recovery_point(rp) for rp in recovery_point_list]


def transform_log_chain_list(log_chain_list):
    return [transform_log_chain(rp) for rp in log_chain_list]


def transform_protectable_item_list(protectable_item_list):
    return [transform_protectable_item(i) for i in protectable_item_list]
