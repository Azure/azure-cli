# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict


def workspace_list_table_format(result):
    """Format workspace list as a table"""
    table = []
    for item in result:
        table.append(workspace_show_table_format(item))
    return table


def workspace_show_table_format(workspace):
    """Format the workspace as a table"""
    row = OrderedDict()
    row['Name'] = workspace['name']
    row['Resource Group'] = workspace['resourceGroup']
    row['Location'] = workspace['location']
    row['State'] = workspace['provisioningState']
    return row


def cluster_list_table_format(result):
    """Format cluster list as a table."""
    table = []
    for item in result:
        table.append(cluster_show_table_format(item))
    return table


def cluster_show_table_format(result):
    """Format cluster as a table."""
    from azure.mgmt.core.tools import parse_resource_id
    row = OrderedDict()
    row['Name'] = result['name']
    row['Resource Group'] = result['resourceGroup']
    row['Workspace'] = parse_resource_id(result['id'])['name']
    row['VM Size'] = result['vmSize']
    if result['provisioningState'] == 'deleting':
        row['State'] = 'deleting'
    else:
        row['State'] = result['allocationState']
    row['Idle'] = str(result['nodeStateCounts']['idleNodeCount'])
    row['Running'] = str(result['nodeStateCounts']['runningNodeCount'])
    row['Preparing'] = str(result['nodeStateCounts']['preparingNodeCount'])
    row['Leaving'] = str(result['nodeStateCounts']['leavingNodeCount'])
    row['Unusable'] = str(result['nodeStateCounts']['unusableNodeCount'])
    return row


def experiment_list_table_format(result):
    """Format experiment list as a table"""
    table = []
    for item in result:
        table.append(experiment_show_table_format(item))
    return table


def experiment_show_table_format(experiment):
    """Format the experiment as a table"""
    from azure.mgmt.core.tools import parse_resource_id
    row = OrderedDict()
    row['Name'] = experiment['name']
    row['Resource Group'] = experiment['resourceGroup']
    row['Workspace'] = parse_resource_id(experiment['id'])['name']
    row['State'] = experiment['provisioningState']
    return row


def job_list_table_format(result):
    """Format job list as a table."""
    table = []
    for item in result:
        table.append(job_show_table_format(item))
    return table


def job_show_table_format(job):
    """Format job as a table."""
    from azure.mgmt.core.tools import parse_resource_id
    row = OrderedDict()
    row['Name'] = job['name']
    cluster = parse_resource_id(job['cluster']['id'])
    row['Cluster'] = cluster['resource_name']
    row['Cluster RG'] = job['cluster']['resourceGroup']
    row['Cluster Workspace'] = cluster['name']
    row['Tool'] = job['toolType']
    row['Nodes'] = job['nodeCount']
    if job['provisioningState'] == 'deleting':
        row['State'] = 'deleting'
    else:
        row['State'] = job['executionState']
    if job['executionInfo'] and \
       job['executionInfo']['exitCode'] is not None:
        row['Exit code'] = str(job['executionInfo']['exitCode'])
    else:
        row['Exit code'] = ''
    return row


def file_list_table_format(result):
    """Format file list as a table."""
    table = []
    for item in result:
        row = OrderedDict()
        row['Name'] = item['name']
        row['Type'] = item['fileType']
        row['Size'] = '' if item['fileType'] == 'directory' else str(item['contentLength'])
        row['Modified'] = item['lastModified'] or ' '
        table.append(row)
    return table


def file_server_list_table_format(result):
    """Format file server list as a table."""
    table = []
    for item in result:
        table.append(file_server_show_table_format(item))
    return table


def file_server_show_table_format(result):
    """Format file server list as a table."""
    row = OrderedDict()
    row['Name'] = result['name']
    row['Resource Group'] = result['resourceGroup']
    row['Size'] = result['vmSize']
    disks = result['dataDisks']
    if disks:
        row['Disks'] = '{0} x {1} Gb'.format(disks['diskCount'], disks['diskSizeInGb'])
    mount_settings = result['mountSettings']
    if mount_settings:
        row['Public IP'] = mount_settings['fileServerPublicIp']
        row['Internal IP'] = mount_settings['fileServerInternalIp']
        row['Mount Point'] = mount_settings['mountPoint']
    return row


def remote_login_table_format(result):
    """Format remote login info list as a table."""
    table = []
    for item in result:
        row = OrderedDict()
        row['ID'] = item['nodeId']
        row['IP'] = item['ipAddress']
        row['SSH Port'] = int(item['port'])
        table.append(row)
    return table


def usage_table_format(result):
    """Format usage information as a table."""
    table = []
    for item in result:
        row = OrderedDict()
        row['Value'] = item['name']['localizedValue']
        row['Usage'] = item['currentValue'] or "0"
        row['Limit'] = item['limit'] or "0"
        table.append(row)
    return table


def node_setup_files_list_table_format(result):
    """Format list of node setup task files"""
    table = []
    for item in result:
        row = OrderedDict()
        row['Name'] = item['name']
        row['Is directory'] = 'yes' if item['is_directory'] else 'no'
        row['Size'] = '' if item['size'] is None else (item['size'] or '0')
        table.append(row)
    return table
