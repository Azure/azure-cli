# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict


def transform_container(result):
    return OrderedDict([('Name', result['properties']['friendlyName']),
                        ('Resource Group', result['resourceGroup']),
                        ('Type', result['properties']['backupManagementType']),
                        ('Registration Status', result['properties']['registrationStatus'])])


def transform_item(result):
    return OrderedDict([('Name', result['properties']['friendlyName']),
                        ('Resource Group', result['resourceGroup']),
                        ('Type', result['properties']['workloadType']),
                        ('Last Backup Status', result['properties']['lastBackupStatus']),
                        ('Last Recovery Point', result['properties']['lastRecoveryPoint']),
                        ('Protection Status', result['properties']['protectionStatus'])])


def transform_job(result):
    return OrderedDict([('Name', result['name']),
                        ('Operation', result['properties']['operation']),
                        ('Status', result['properties']['status']),
                        ('Item Name', result['properties']['entityFriendlyName']),
                        ('Start Time UTC', result['properties']['startTime']),
                        ('Duration', result['properties']['duration'])])


def transform_policy(result):
    return OrderedDict([('Name', result['name']),
                        ('Resource Group', result['resourceGroup']),
                        ('Type', result['properties']['backupManagementType'])])


def transform_recovery_point(result):
    return OrderedDict([('Name', result['name']),
                        ('Time', result['properties']['recoveryPointTime']),
                        ('Consistency', result['properties']['recoveryPointType'])])


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
