# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict

from six.moves.urllib.parse import unquote  # pylint: disable=import-error


HEAD_PROPERTIES = {  # Convert response headers to properties.
    'Last-Modified': 'lastModified',
    'ocp-creation-time': 'creationTime',
    'ocp-batch-file-isdirectory': 'isDirectory',
    'ocp-batch-file-url': 'url',
    'ocp-batch-file-mode': 'fileMode',
    'Content-Length': 'contentLength',
    'Content-Type': 'contentType'
}


def transform_response_headers(result):
    """Extract and format file property headers from ClientRawResponse object"""
    properties = {HEAD_PROPERTIES[k]: v for k, v in result.headers.items() \
        if k in HEAD_PROPERTIES}
    if properties.get('url'):
        properties['url'] = unquote(properties['url'])
    return properties


def task_file_list_table_format(result):
    """Format file list as a table."""
    table_output = []
    for item in result:
        table_row = OrderedDict()
        table_row['Name'] = item['name']
        table_row['URL'] = item['url']
        table_row['IsDirectory'] = item['isDirectory']
        table_row['ContentLength'] = item['properties']['contentLength'] \
            if item['properties'] else ""
        table_row['ContentType'] = item['properties']['contentType'] \
            if item['properties'] else ""
        table_row['CreationTime'] = item['properties']['creationTime'] \
            if item['properties'] else ""
        table_row['LastModified'] = item['properties']['lastModified'] \
            if item['properties'] else ""
        table_row['FileMode'] = item['properties']['fileMode'] \
            if item['properties'] and item['properties']['fileMode'] else ""
        table_output.append(table_row)
    return table_output