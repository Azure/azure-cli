# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
"""Table transformer for storage commands"""

from azure.cli.core.commands.transform import build_table_output
from azure.cli.core.profiles import get_sdk, ResourceType
from knack.log import get_logger

logger = get_logger(__name__)


def transform_container_list(result):
    return build_table_output(result, [
        ('Name', 'name'),
        ('Lease Status', 'properties.leaseStatus'),
        ('Last Modified', 'properties.lastModified')
    ])


def transform_container_show(result):
    return build_table_output(result, [
        ('Name', 'name'),
        ('Lease Status', 'properties.lease.status'),
        ('Last Modified', 'properties.lastModified')
    ])


def transform_blob_output(result):
    return build_table_output(result, [
        ('Name', 'name'),
        ('Blob Type', 'properties.blobType'),
        ('Blob Tier', 'properties.blobTier'),
        ('Length', 'properties.contentLength'),
        ('Content Type', 'properties.contentSettings.contentType'),
        ('Last Modified', 'properties.lastModified'),
        ('Snapshot', 'snapshot')
    ])


def transform_share_list(result):
    return build_table_output(result, [
        ('Name', 'name'),
        ('Quota', 'properties.quota'),
        ('Last Modified', 'properties.lastModified')
    ])


def transform_file_output(result):
    """ Transform to convert SDK file/dir list output to something that
    more clearly distinguishes between files and directories. """
    from collections import OrderedDict
    new_result = []

    iterable = result if isinstance(result, list) else result.get('items', result)
    for item in iterable:
        new_entry = OrderedDict()

        entity_type = item['type']  # type property is added by transform_file_directory_result
        is_dir = entity_type == 'dir'

        new_entry['Name'] = item['name'] + '/' if is_dir else item['name']
        new_entry['Content Length'] = ' ' if is_dir else item['properties']['contentLength']
        new_entry['Type'] = item['type']
        new_entry['Last Modified'] = item['properties']['lastModified'] or ' '
        new_result.append(new_entry)
    return sorted(new_result, key=lambda k: k['Name'])


def transform_entity_show(result):
    from collections import OrderedDict
    timestamp = result.pop('Timestamp')
    result.pop('etag')

    # Reassemble the output
    new_result = OrderedDict()
    new_result['Partition'] = result.pop('PartitionKey')
    new_result['Row'] = result.pop('RowKey')
    for key in sorted(result.keys()):
        new_result[key] = result[key]
    new_result['Timestamp'] = timestamp
    return new_result


def transform_message_show(result):
    from collections import OrderedDict
    ordered_result = []
    for item in result:
        new_result = OrderedDict()
        new_result['MessageId'] = item.pop('id')
        new_result['Content'] = item.pop('content')
        new_result['InsertionTime'] = item.pop('insertionTime')
        new_result['ExpirationTime'] = item.pop('expirationTime')
        for key in sorted(item.keys()):
            new_result[key] = item[key]
        ordered_result.append(new_result)
    return ordered_result


def transform_boolean_for_table(result):
    for key in result:
        result[key] = str(result[key])
    return result


def transform_file_directory_result(cli_ctx):
    """
    Transform a the result returned from file and directory listing API.

    This transformer add and remove properties from File and Directory objects in the given list
    in order to align the object's properties so as to offer a better view to the file and dir
    list.
    """
    def transformer(result):
        if getattr(result, 'next_marker', None):
            logger.warning('Next Marker:')
            logger.warning(result.next_marker)

        t_file, t_dir = get_sdk(cli_ctx, ResourceType.DATA_STORAGE, 'File', 'Directory', mod='file.models')
        return_list = []
        for each in result:
            if isinstance(each, t_file):
                delattr(each, 'content')
                setattr(each, 'type', 'file')
            elif isinstance(each, t_dir):
                setattr(each, 'type', 'dir')
            return_list.append(each)

        return return_list
    return transformer
