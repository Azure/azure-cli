# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
from collections import OrderedDict
from urllib.parse import unquote

HEAD_PROPERTIES = {  # Convert response headers to properties.
    'Last-Modified': 'lastModified',
    'ocp-creation-time': 'creationTime',
    'ocp-batch-file-isdirectory': 'isDirectory',
    'ocp-batch-file-url': 'url',
    'ocp-batch-file-mode': 'fileMode',
    'Content-Length': 'contentLength',
    'Content-Type': 'contentType'
}


def _file_list_table_format(result):
    """Format file list as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Name'] = item.get('name', None)
        table_row['URL'] = item.get('url', None)
        table_row['Is Directory'] = str(item.get('isDirectory', None))
        table_row['Content Length'] = str(item.get('properties').get('contentLength', None)) \
            if item.get('properties', None) else ""
        table_row['Creation Time'] = item.get('properties').get('creationTime', None) \
            if item.get('properties', None) else ""
        table_output.append(table_row)
    return table_output


def _account_key_table_format(result):
    """Format account keys as a table."""
    table_output = []
    table_row = OrderedDict()
    table_row['Number'] = 'Primary'
    table_row['Key'] = result.get('primary', None)
    table_output.append(table_row)
    table_row = OrderedDict()
    table_row['Number'] = 'Secondary'
    table_row['Key'] = result.get('secondary', None)
    table_output.append(table_row)
    return table_output


def transform_response_headers(result):
    """Extract and format file property headers from ClientRawResponse object"""
    properties = {HEAD_PROPERTIES[k]: v for k, v in result.headers.items()
                  if k in HEAD_PROPERTIES}
    if properties.get('url'):
        properties['url'] = unquote(properties['url'])
    return properties


def task_file_list_table_format(result):
    """Format task file list as a table."""
    return _file_list_table_format(result)


def node_file_list_table_format(result):
    """Format node file list as a table."""
    return _file_list_table_format(result)


def application_list_table_format(result):
    """Format application list as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Id'] = item.get('id', None)
        table_row['Default Version'] = item.get('defaultVersion', None)
        table_row['Allow Updates'] = item.get('allowUpdates', None)
        table_row['Version Count'] = str(len(item['packages'])) if item.get('packages', None) else '0'
        table_output.append(table_row)
    return table_output


def application_summary_list_table_format(result):
    """Format application summary list as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Application Id'] = item.get('id', None)
        table_row['Display Name'] = item.get('displayName', None)
        table_row['Versions'] = json.dumps(item.get('versions', None))
        table_output.append(table_row)
    return table_output


def account_list_table_format(result):
    """Format account list as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Name'] = item.get('name', None)
        table_row['Location'] = item.get('location', None)
        table_row['Resource Group'] = item.get('resourceGroup', None)
        table_output.append(table_row)
    return table_output


def account_keys_list_table_format(result):
    """Format account keys list as a table."""
    return _account_key_table_format(result)


def account_keys_renew_table_format(result):
    """Format account keys renew as a table."""
    return _account_key_table_format(result)


def job_list_table_format(result):
    """Format job list as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Job Id'] = item.get('id', None)
        table_row['State'] = item.get('state', None)
        table_row['Previous State'] = item.get('previousState', None)
        table_row['Execution Pool'] = item.get('executionInfo').get('poolId', None) \
            if item.get('executionInfo', None) else ""
        table_output.append(table_row)
    return table_output


def job_prep_release_status_list_table_format(result):
    """Format job prep-release-status list as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Pool Id'] = item.get('poolId', None)
        table_row['Node Id'] = item.get('nodeId', None)
        table_row['Job Prep State'] = item.get('jobPreparationTaskExecutionInfo').get('state', None) \
            if item.get('jobPreparationTaskExecutionInfo', None) else ""
        table_row['Job Release State'] = item.get('jobReleaseTaskExecutionInfo').get('state', None) \
            if item.get('jobReleaseTaskExecutionInfo', None) else ""
        table_output.append(table_row)
    return table_output


def job_schedule_list_table_format(result):
    """Format job-schedule list as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Job Schedule Id'] = item.get('id', None)
        table_row['State'] = item.get('state', None)
        table_row['Previous State'] = item.get('previousState', None)
        table_output.append(table_row)
    return table_output


def node_list_table_format(result):
    """Format node list as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Node Id'] = item.get('id', None)
        table_row['State'] = item.get('state', None)
        table_row['VM Size'] = item.get('vmSize', None)
        table_row['IP Address'] = item.get('ipAddress', None)
        table_output.append(table_row)
    return table_output


def pool_node_agent_skus_list_table_format(result):
    """Format pool node-agent-skus list as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Agent Id'] = item.get('id', None)
        table_row['Publisher'] = item.get('publisher', None)
        table_row['Offer'] = item.get('offer', None)
        table_row['Sku'] = item.get('sku', None)
        table_output.append(table_row)
    return table_output


def pool_list_table_format(result):
    """Format pool list as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Pool Id'] = item.get('id', None)
        table_row['State'] = item.get('state', None)
        table_row['Allocation State'] = item.get('allocationState', None)
        table_row['VM Size'] = item.get('vmSize', None)
        table_row['Dedicated VM Count'] = item.get('currentDedicatedNodes', None)
        table_row['Low Priority VM Count'] = item.get('currentLowPriorityNodes', None)
        table_row['Type'] = 'IaaS' if item.get('virtualMachineConfiguration', None) else 'PaaS'
        table_output.append(table_row)
    return table_output


def pool_usage_metrics_list_table_format(result):
    """Format pool usage-metrics list as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Pool Id'] = item.get('poolId', None)
        table_row['Start Time'] = item.get('startTime') if item.get('startTime', None) else ""
        table_row['End Time'] = item.get('endTime') if item.get('endTime', None) else ""
        table_row['VM Size'] = item.get('vmSize', None)
        table_row['Total Core Hours'] = str(item.get('totalCoreHours', None))
        table_output.append(table_row)
    return table_output


def task_list_table_format(result):
    """Format task list as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Task Id'] = item.get('id', None)
        table_row['State'] = item.get('state', None)
        table_row['Exit Code'] = str(item.get('executionInfo').get('exitCode', None)) \
            if item.get('executionInfo', None) else ""
        table_row['Node Id'] = item.get('nodeInfo').get('nodeId', None) if item.get('nodeInfo', None) else ""
        table_row['Command Line'] = item.get('commandLine', None)
        table_output.append(table_row)
    return table_output


def task_create_table_format(result):
    """Format task create as a table."""
    table_output = []
    if not isinstance(result, list):
        table_row = OrderedDict()
        table_row['Task Id'] = result.get('id', None)
        table_row['Submission Status'] = "success"
        table_output.append(table_row)
    else:
        for item in result:
            table_row = OrderedDict()
            table_row['Task Id'] = item.get('taskId', None)
            table_row['Submission Status'] = item.get('status', None)
            table_row['Error'] = item.get('error').get('code', None) if item.get('error', None) else ""
            table_output.append(table_row)
    return table_output


def list_pool_node_counts_table_format(result):
    """Format account list pool node counts result as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Pool Id'] = item.get('poolId', None)
        table_row['Dedicated Starting'] = str(item.get('dedicated').get('starting', None)) \
            if item.get('dedicated', None) else ""
        table_row['Dedicated Idle'] = str(item.get('dedicated').get('idle', None)) \
            if item.get('dedicated', None) else ""
        table_row['Dedicated Running'] = str(item.get('dedicated').get('running', None)) \
            if item.get('dedicated', None) else ""
        table_row['Dedicated Total'] = str(item.get('dedicated').get('total', None)) \
            if item.get('dedicated', None) else ""
        table_row['LowPri Starting'] = str(item.get('lowPriority').get('starting', None)) \
            if item.get('lowPriority', None) else ""
        table_row['LowPri Idle'] = str(item.get('lowPriority').get('idle', None)) \
            if item.get('lowPriority', None) else ""
        table_row['LowPri Running'] = str(item.get('lowPriority').get('running', None)) \
            if item.get('lowPriority', None) else ""
        table_row['LowPri Total'] = str(item.get('lowPriority').get('total', None)) \
            if item.get('lowPriority', None) else ""
        table_output.append(table_row)
    return table_output


def list_supported_images_table_format(result):
    """Format account list node agent skus result as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['OS Type'] = item.get('osType', None)
        table_row['Node Agent Sku'] = item.get('nodeAgentSkuId', None)
        table_row['Publisher'] = item.get('imageReference').get('publisher', None) \
            if item.get('imageReference', None) else ""
        table_row['Offer'] = item.get('imageReference').get('offer', None) \
            if item.get('imageReference', None) else ""
        table_row['Sku'] = item.get('imageReference').get('sku', None) \
            if item.get('imageReference', None) else ""
        table_row['Version'] = item.get('imageReference').get('version', None) \
            if item.get('imageReference', None) else ""
        table_row['VerificationType'] = item.get('verificationType', None)
        table_output.append(table_row)
    return table_output
