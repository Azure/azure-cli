# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint:disable=line-too-long

from collections import OrderedDict

def build_table_output(result, projection):

    final_list = []
    for item in result:

        def _value_from_path(path):
            obj = item
            try:
                for part in path.split('.'):
                    obj = obj.get(part, None)
            except AttributeError:
                obj = None
            return obj or ' '

        item_dict = OrderedDict()
        for element in projection:
            item_dict[element[0]] = _value_from_path(element[1])
        final_list.append(item_dict)
    return final_list

def transform_container_list(result):
    return build_table_output(result, [
        ('Name', 'name'),
        ('Lease Status', 'properties.leaseStatus'),
        ('Last Modified', 'properties.lastModified')
    ])

def transform_blob_list(result):
    return build_table_output(result, [
        ('Name', 'name'),
        ('Blob Type', 'properties.blobType'),
        ('Length', 'properties.contentLength'),
        ('Content Type', 'properties.contentSettings.contentType'),
        ('Last Modified', 'properties.lastModified'),
        ('Snapshot Time', 'snapshot')
    ])

def transform_share_list(result):
    return build_table_output(result, [
        ('Name', 'name'),
        ('Quota', 'properties.quota'),
        ('Last Modified', 'properties.lastModified')
    ])

def transform_file_list(result):
    """ Transform to convert SDK file/dir list output to something that
    more clearly distinguishes between files and directories. """
    new_result = []
    for item in result['items']:
        new_entry = OrderedDict()
        item_name = item['name']
        try:
            _ = item['properties']['contentLength']
            is_dir = False
        except KeyError:
            item_name = '{}/'.format(item_name)
            is_dir = True
        new_entry['Name'] = item_name
        new_entry['Content Length'] = ' ' if is_dir else item['properties']['contentLength']
        new_entry['Type'] = 'dir' if is_dir else 'file'
        new_entry['Last Modified'] = item['properties']['lastModified'] or ' '
        new_result.append(new_entry)
    return sorted(new_result, key=lambda k: k['Name'])
