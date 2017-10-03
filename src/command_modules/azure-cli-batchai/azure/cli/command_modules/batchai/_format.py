# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict


def cluster_list_table_format(result):
    """Format cluster list as a table."""
    table = []
    for item in result:
        row = OrderedDict()
        row['Name'] = item['name']
        row['Resource Group'] = item['resourceGroup']
        row['VM Size'] = item['vmSize']
        row['State'] = item['allocationState']
        row['Idle'] = str(item['nodeStateCounts']['idleNodeCount'])
        row['Running'] = str(item['nodeStateCounts']['runningNodeCount'])
        row['Preparing'] = str(item['nodeStateCounts']['preparingNodeCount'])
        row['Leaving'] = str(item['nodeStateCounts']['leavingNodeCount'])
        row['Unusable'] = str(item['nodeStateCounts']['unusableNodeCount'])
        table.append(row)
    return table


def job_list_table_format(result):
    """Format job list as a table."""
    table = []
    for item in result:
        row = OrderedDict()
        row['Name'] = item['name']
        row['Resource Group'] = item['resourceGroup']
        cluster = item['cluster']['id'].split('/')[8]
        row['Cluster'] = cluster
        row['Cluster RG'] = item['cluster']['resourceGroup']
        row['Tool'] = item['toolType']
        row['Nodes'] = item['nodeCount']
        row['State'] = item['executionState']
        if item['executionInfo'] and \
           item['executionInfo']['exitCode'] is not None:
            row['Exit code'] = str(item['executionInfo']['exitCode'])
        else:
            row['Exit code'] = ''
        table.append(row)
    return table


def file_list_table_format(result):
    """Format file list as a table."""
    table = []
    for item in result:
        row = OrderedDict()
        row['Name'] = item['name']
        row['Size'] = str(item['contentLength'])
        row['URL'] = item['downloadUrl']
        table.append(row)
    return table


def file_server_table_format(result):
    """Format file server list as a table."""
    table = []
    for item in result:
        row = OrderedDict()
        row['Name'] = item['name']
        row['Resource Group'] = item['resourceGroup']
        row['Size'] = item['vmSize']
        disks = item['dataDisks']
        if disks:
            row['Disks'] = '{0} x {1} Gb'.format(disks['diskCount'], disks['diskSizeInGb'])
        mount_settings = item['mountSettings']
        if mount_settings:
            row['Public IP'] = mount_settings['fileServerPublicIp']
            row['Internal IP'] = mount_settings['fileServerInternalIp']
            row['Type'] = mount_settings['fileServerType']
            row['Mount Point'] = mount_settings['mountPoint']
        table.append(row)
    return table


def remote_login_table_format(result):
    """Format remote login info list as a table."""
    table = []
    for item in result:
        row = OrderedDict()
        row['ID'] = item['nodeId']
        row['IP'] = item['ipAddress']
        row['Port'] = int(item['port'])
        table.append(row)
    return table
