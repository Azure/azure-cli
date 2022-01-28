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
        table_row['Name'] = item['name']
        table_row['URL'] = item['url']
        table_row['Is Directory'] = str(item['isDirectory'])
        table_row['Content Length'] = str(item['properties']['contentLength']) \
            if item['properties'] else ""
        table_row['Creation Time'] = item['properties']['creationTime'] \
            if item['properties'] else ""
        table_output.append(table_row)
    return table_output


def _account_key_table_format(result):
    """Format account keys as a table."""
    table_output = []
    table_row = OrderedDict()
    table_row['Number'] = 'Primary'
    table_row['Key'] = result['primary']
    table_output.append(table_row)
    table_row = OrderedDict()
    table_row['Number'] = 'Secondary'
    table_row['Key'] = result['secondary']
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
        table_row['Id'] = item['id']
        table_row['Default Version'] = item['defaultVersion']
        table_row['Allow Updates'] = item['allowUpdates']
        table_row['Version Count'] = str(len(item['packages'])) if item['packages'] else '0'
        table_output.append(table_row)
    return table_output


def application_summary_list_table_format(result):
    """Format application summary list as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Application Id'] = item['id']
        table_row['Display Name'] = item['displayName']
        table_row['Versions'] = json.dumps(item['versions'])
        table_output.append(table_row)
    return table_output


def account_list_table_format(result):
    """Format account list as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Name'] = item['name']
        table_row['Location'] = item['location']
        table_row['Resource Group'] = item['resourceGroup']
        table_output.append(table_row)
    return table_output


def account_keys_list_table_format(result):
    """Format account keys list as a table."""
    return _account_key_table_format(result)


def account_keys_renew_table_format(result):
    """Format account keys renew as a table."""
    return _account_key_table_format(result)


def certificate_list_table_format(result):
    """Format certificate list as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Thumbprint'] = item['thumbprint']
        table_row['State'] = item['state']
        table_row['Previous State'] = item['previousState']
        table_row['Deletion Error'] = 'True' if item['deleteCertificateError'] else 'False'
        table_output.append(table_row)
    return table_output


def job_list_table_format(result):
    """Format job list as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Job Id'] = item['id']
        table_row['State'] = item['state']
        table_row['Previous State'] = item['previousState']
        table_row['Execution Pool'] = item['executionInfo']['poolId'] \
            if item['executionInfo'] else ""
        table_output.append(table_row)
    return table_output


def job_prep_release_status_list_table_format(result):
    """Format job prep-release-status list as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Pool Id'] = item['poolId']
        table_row['Node Id'] = item['nodeId']
        table_row['Job Prep State'] = item['jobPreparationTaskExecutionInfo']['state'] \
            if item['jobPreparationTaskExecutionInfo'] else ""
        table_row['Job Release State'] = item['jobReleaseTaskExecutionInfo']['state'] \
            if item['jobReleaseTaskExecutionInfo'] else ""
        table_output.append(table_row)
    return table_output


def job_schedule_list_table_format(result):
    """Format job-schedule list as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Job Schedule Id'] = item['id']
        table_row['State'] = item['state']
        table_row['Previous State'] = item['previousState']
        table_output.append(table_row)
    return table_output


def node_list_table_format(result):
    """Format node list as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Node Id'] = item['id']
        table_row['State'] = item['state']
        table_row['VM Size'] = item['vmSize']
        table_row['IP Address'] = item['ipAddress']
        table_output.append(table_row)
    return table_output


def pool_node_agent_skus_list_table_format(result):
    """Format pool node-agent-skus list as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Agent Id'] = item['id']
        table_row['Publisher'] = item['publisher']
        table_row['Offer'] = item['offer']
        table_row['Sku'] = item['sku']
        table_output.append(table_row)
    return table_output


def pool_list_table_format(result):
    """Format pool list as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Pool Id'] = item['id']
        table_row['State'] = item['state']
        table_row['Allocation State'] = item['allocationState']
        table_row['VM Size'] = item['vmSize']
        table_row['Dedicated VM Count'] = item['currentDedicatedNodes']
        table_row['Low Priority VM Count'] = item['currentLowPriorityNodes']
        table_row['Type'] = 'IaaS' if item['virtualMachineConfiguration'] else 'PaaS'
        table_output.append(table_row)
    return table_output


def pool_usage_metrics_list_table_format(result):
    """Format pool usage-metrics list as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Pool Id'] = item['poolId']
        table_row['Start Time'] = item['startTime'] if item['startTime'] else ""
        table_row['End Time'] = item['endTime'] if item['endTime'] else ""
        table_row['VM Size'] = item['vmSize']
        table_row['Total Core Hours'] = str(item['totalCoreHours'])
        table_output.append(table_row)
    return table_output


def task_list_table_format(result):
    """Format task list as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Task Id'] = item['id']
        table_row['State'] = item['state']
        table_row['Exit Code'] = str(item['executionInfo']['exitCode']) \
            if item['executionInfo'] else ""
        table_row['Node Id'] = item['nodeInfo']['nodeId'] if item['nodeInfo'] else ""
        table_row['Command Line'] = item['commandLine']
        table_output.append(table_row)
    return table_output


def task_create_table_format(result):
    """Format task create as a table."""
    table_output = []
    if not isinstance(result, list):
        table_row = OrderedDict()
        table_row['Task Id'] = result['id']
        table_row['Submission Status'] = "success"
        table_output.append(table_row)
    else:
        for item in result:
            table_row = OrderedDict()
            table_row['Task Id'] = item['taskId']
            table_row['Submission Status'] = item['status']
            table_row['Error'] = item['error']['code'] if item['error'] else ""
            table_output.append(table_row)
    return table_output


def list_pool_node_counts_table_format(result):
    """Format account list pool node counts result as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Pool Id'] = item['poolId']
        table_row['Dedicated Starting'] = str(item['dedicated']['starting'])
        table_row['Dedicated Idle'] = str(item['dedicated']['idle'])
        table_row['Dedicated Running'] = str(item['dedicated']['running'])
        table_row['Dedicated Total'] = str(item['dedicated']['total'])
        table_row['LowPri Starting'] = str(item['lowPriority']['starting'])
        table_row['LowPri Idle'] = str(item['lowPriority']['idle'])
        table_row['LowPri Running'] = str(item['lowPriority']['running'])
        table_row['LowPri Total'] = str(item['lowPriority']['total'])
        table_output.append(table_row)
    return table_output


def list_supported_images_table_format(result):
    """Format account list node agent skus result as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['OS Type'] = item['osType']
        table_row['Node Agent Sku'] = item['nodeAgentSkuId']
        table_row['Publisher'] = item['imageReference']['publisher']
        table_row['Offer'] = item['imageReference']['offer']
        table_row['Sku'] = item['imageReference']['sku']
        table_row['Version'] = item['imageReference']['version']
        table_row['VerificationType'] = item['verificationType']
        table_output.append(table_row)
    return table_output
