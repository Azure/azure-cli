# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import base64

from uuid import UUID
from dateutil import parser
from knack.log import get_logger
from knack.util import todict, to_camel_case
from .track2_util import _encode_bytes
from .url_quote_util import encode_url_path

storage_account_key_options = {'primary': 'key1', 'secondary': 'key2'}
logger = get_logger(__name__)


def transform_acl_list_output(result):
    """ Transform to convert SDK output into a form that is more readily
    usable by the CLI and tools such as jpterm. """
    from collections import OrderedDict
    new_result = []
    for key in sorted(result.keys()):
        new_entry = OrderedDict()
        new_entry['Name'] = key
        new_entry['Start'] = result[key]['start']
        new_entry['Expiry'] = result[key]['expiry']
        new_entry['Permissions'] = result[key]['permission']
        new_result.append(new_entry)
    return new_result


def transform_acl_edit(result):
    if "last_modified" in result.keys():
        result["lastModified"] = result.pop("last_modified")
    return result


def transform_acl_datetime(result):
    result = todict(result)
    if result['start']:
        result['start'] = result["start"].split('.')[0] + '+00:00'
    if result['expiry']:
        result['expiry'] = result["expiry"].split('.')[0] + '+00:00'
    return result


def transform_container_permission_output(result):
    return {'publicAccess': result.get('public_access', None) or 'off'}


def transform_cors_list_output(result):
    from collections import OrderedDict
    new_result = []
    for service in sorted(result.keys()):
        for i, rule in enumerate(result[service]):
            new_entry = OrderedDict()
            new_entry['Service'] = service
            new_entry['Rule'] = i + 1
            new_entry['AllowedMethods'] = rule.allowed_methods
            new_entry['AllowedOrigins'] = rule.allowed_origins
            new_entry['ExposedHeaders'] = rule.exposed_headers
            new_entry['AllowedHeaders'] = rule.allowed_headers
            new_entry['MaxAgeInSeconds'] = rule.max_age_in_seconds
            new_result.append(new_entry)
    return new_result


def transform_table_stats_output(result):
    if not isinstance(result, dict):
        return result
    output = {}
    for key, value in result.items():
        output[to_camel_case(key)] = transform_table_stats_output(value)
    return output


def transform_entity_query_output(result):
    from collections import OrderedDict
    new_results = []
    ignored_keys = ['etag', 'Timestamp', 'RowKey', 'PartitionKey']
    for row in result['items']:
        new_entry = OrderedDict()
        new_entry['PartitionKey'] = row['PartitionKey']
        new_entry['RowKey'] = row['RowKey']
        other_keys = sorted([x for x in row.keys() if x not in ignored_keys])
        for key in other_keys:
            new_entry[key] = row[key]
        new_results.append(new_entry)
    return new_results


def transform_entities_result(result):
    items = result['items'] if isinstance(result, dict) else result.items
    for entity in items:
        transform_entity_result(entity)
    return result


def transform_entity_result(entity):
    for key in entity.keys():
        entity_property = entity[key]
        if hasattr(entity_property, 'value') and isinstance(entity_property.value, bytes):
            entity_property.value = base64.b64encode(entity_property.value).decode()
        if isinstance(entity_property, bytes):
            entity[key] = base64.b64encode(entity_property).decode()
        if isinstance(entity_property, UUID):
            entity[key] = str(entity_property)
    if hasattr(entity, 'metadata'):
        entity['Timestamp'] = entity.metadata['timestamp']
        entity['etag'] = entity.metadata['etag']
    return entity


def transform_logging_list_output(result):
    from collections import OrderedDict
    new_result = []
    for key in sorted(result.keys()):
        new_entry = OrderedDict()
        new_entry['Service'] = key
        new_entry['Read'] = str(result[key]['read'])
        new_entry['Write'] = str(result[key]['write'])
        new_entry['Delete'] = str(result[key]['delete'])
        new_entry['RetentionPolicy'] = str(result[key]['retentionPolicy']['days'])
        new_result.append(new_entry)
    return new_result


def transform_metrics_list_output(result):
    from collections import OrderedDict
    new_result = []
    for service in sorted(result.keys()):
        service_name = service
        for interval in sorted(result[service].keys()):
            item = result[service][interval]
            new_entry = OrderedDict()
            new_entry['Service'] = service_name
            service_name = ''
            new_entry['Interval'] = str(interval)
            new_entry['Enabled'] = str(item['enabled'])
            new_entry['IncludeApis'] = str(item['includeApis'])
            new_entry['RetentionPolicy'] = str(item['retentionPolicy']['days'])
            new_result.append(new_entry)
    return new_result


def create_boolean_result_output_transformer(property_name):
    def _transformer(result):
        return {property_name: result}

    return _transformer


def transform_storage_list_output(result):
    if getattr(result, 'next_marker', None):
        logger.warning('Next Marker:')
        logger.warning(result.next_marker)
    return list(result)


def transform_url(result):
    """ Ensures the resulting URL string does not contain extra / characters """
    import re
    result = re.sub('//', '/', result)
    result = re.sub('/', '//', result, count=1)
    return encode_url_path(result)


def transform_url_without_encode(result):
    """ Ensures the resulting URL string does not contain extra / characters """
    import re
    result = re.sub('//', '/', result)
    result = re.sub('/', '//', result, count=1)
    return result


def transform_fs_access_output(result):
    """ Transform to convert SDK output into a form that is more readily
    usable by the CLI and tools such as jpterm. """

    new_result = {}
    useful_keys = ['acl', 'group', 'owner', 'permissions']
    for key in useful_keys:
        new_result[key] = result[key]
    return new_result


# TODO: Remove it when SDK is right for file system scenarios
def transform_fs_public_access_output(result):
    """ Transform to convert SDK output into a form that is more readily
    usable by the CLI and tools such as jpterm. """

    if result.public_access == 'blob':
        result.public_access = 'file'
    if result.public_access == 'container':
        result.public_access = 'filesystem'
    return result


# TODO: Remove it when SDK is right for file system scenarios
def transform_fs_list_public_access_output(result):
    """ Transform to convert SDK output into a form that is more readily
    usable by the CLI and tools such as jpterm. """

    new_result = list(result)
    for i, item in enumerate(new_result):
        new_result[i] = transform_fs_public_access_output(item)
    return new_result


def transform_metadata(result):
    return result.metadata


# ------------------Track2 Support-----------------------
def _transform_page_ranges(page_ranges):
    # in track 2 sdk, page ranges result is tuple(list(dict(str, str), list(dict(str, str))
    if page_ranges and len(page_ranges) == 2:
        result = page_ranges[0] if page_ranges[0] else [{}]
        result[0]['isCleared'] = bool(page_ranges[1])
        return result
    return None


def transform_blob_list_output(result):
    for i, item in enumerate(result):
        if isinstance(item, dict) and 'nextMarker' in item:
            continue
        try:
            result[i] = transform_blob_json_output(item)
        except KeyError:  # Deal with BlobPrefix object when there is delimiter specified
            result[i] = {"name": item.name}
    return result


def transform_blob_json_output(result):
    if result is None:
        return
    result = todict(result)
    new_result = {
        "content": "",
        "deleted": result.pop('deleted', None),
        "metadata": result.pop('metadata', None),
        "name": result.pop('name', None),
        "properties": {
            "appendBlobCommittedBlockCount": result.pop('appendBlobCommittedBlockCount', None),
            "blobTier": result.pop('blobTier', None),
            "blobTierChangeTime": result.pop('blobTierChangeTime', None),
            "blobTierInferred": result.pop('blobTierInferred', None),
            "blobType": result.pop('blobType', None),
            "contentLength": result.pop('size', None),
            "contentRange": result.pop('contentRange', None),
            "contentSettings": {
                "cacheControl": result['contentSettings']['cacheControl'],
                "contentDisposition": result['contentSettings']['contentDisposition'],
                "contentEncoding": result['contentSettings']['contentEncoding'],
                "contentLanguage": result['contentSettings']['contentLanguage'],
                "contentMd5": _encode_bytes(result['contentSettings']['contentMd5']),
                "contentType": result['contentSettings']['contentType']
            },
            "copy": result.pop('copy', None),
            "creationTime": result.pop('creationTime', None),
            "deletedTime": result.pop('deletedTime', None),
            "etag": result.pop('etag', None),
            "lastModified": result.pop('lastModified', None),
            "lease": result.pop('lease', None),
            "pageBlobSequenceNumber": result.pop('pageBlobSequenceNumber', None),
            "pageRanges": _transform_page_ranges(result.pop('pageRanges', None)),
            "rehydrationStatus": result.pop('archiveStatus', None),
            "remainingRetentionDays": result.pop('remainingRetentionDays', None),
            "serverEncrypted": result.pop('serverEncrypted', None)
        },
        "snapshot": result.pop('snapshot', None)
    }
    del result['contentSettings']
    new_result.update(result)
    return new_result


def transform_immutability_policy(result):
    # service returns policy with period value of "0" after it has been deleted
    # this only shows the policy if the property value is greater than 0
    if result.immutability_period_since_creation_in_days:
        return result
    return None


def transform_restore_policy_output(result):
    if hasattr(result, 'restore_policy') and hasattr(result.restore_policy, 'last_enabled_time'):
        del result.restore_policy.last_enabled_time
    return result


def transform_response_with_bytearray(response):
    """ transform bytearray to string """
    from msrest import Serializer
    for item in response:
        if response[item] and isinstance(response[item], (bytes, bytearray)):
            response[item] = Serializer.serialize_bytearray(response[item])
    return response


def transform_share_rm_output(result):
    if hasattr(result, 'snapshot_time') and result.snapshot_time:
        snapshot = result.snapshot_time
        result.snapshot_time = snapshot.strftime("%Y-%m-%dT%H:%M:%S.%f0Z")
    return result


def transform_share_rm_list_output(result):
    new_result = []
    for item in result:
        new_result.append(transform_share_rm_output(item))
    return new_result


def delete_blob_output_key(_, result):
    result.pop('additionalProperties', None)
    return result


def transform_blob_json_output_track2(result):
    result['logging'] = result.pop('analytics_logging')
    result['deleteRetentionPolicy'] = result.pop('delete_retention_policy')
    result['hourMetrics'] = result.pop('hour_metrics')
    result['minuteMetrics'] = result.pop('minute_metrics')
    result['staticWebsite'] = result.pop('static_website')
    for i in result['cors']:
        i.allowed_methods = i.allowed_methods.split(',') if i.allowed_methods else []
        i.allowed_origins = i.allowed_origins.split(',') if i.allowed_origins else []
        i.exposed_headers = i.exposed_headers.split(',') if i.exposed_headers else []
        i.allowed_headers = i.allowed_headers.split(',') if i.allowed_headers else []
    new_result = todict(result, delete_blob_output_key)
    new_result['staticWebsite']['errorDocument_404Path'] = new_result['staticWebsite'].pop('errorDocument404Path')
    return new_result


def transform_container_json_output(result):
    result = todict(result)
    new_result = {
        "metadata": result.pop('metadata', None),
        "name": result.pop('name', None),
        "properties": {
            "etag": result.pop('etag', None),
            "hasImmutabilityPolicy": result.pop('hasImmutabilityPolicy', None),
            "hasLegalHold": result.pop('hasLegalHold', None),
            "lastModified": result.pop('lastModified', None),
            "lease": result.pop('lease', None),
            "publicAccess": result.pop('publicAccess', None)
        }
    }
    new_result.update(result)
    return new_result


def transform_container_list_output(result):
    for i, item in enumerate(result):
        if isinstance(item, dict) and 'nextMarker' in item:
            continue
        try:
            result[i] = transform_container_json_output(item)
        except KeyError:  # Deal with BlobPrefix object when there is delimiter specified
            result[i] = {"name": item.name}
    return result


def transform_blob_upload_output(result):
    if "last_modified" in result:
        result["lastModified"] = result["last_modified"]
        del result["last_modified"]
    return result


def transform_queue_stats_output(result):
    if isinstance(result, dict):
        new_result = {}
        from azure.cli.core.commands.arm import make_camel_case
        for key in result.keys():
            new_key = make_camel_case(key)
            new_result[new_key] = transform_queue_stats_output(result[key])
        return new_result
    return result


def transform_message_list_output(result):
    for i, item in enumerate(result):
        result[i] = transform_message_output(item)
    return list(result)


def transform_message_output(result):
    result = todict(result)
    new_result = {'expirationTime': result.pop('expiresOn', None),
                  'insertionTime': result.pop('insertedOn', None),
                  'timeNextVisible': result.pop('nextVisibleOn', None)}
    from azure.cli.core.commands.arm import make_camel_case
    for key in sorted(result.keys()):
        new_result[make_camel_case(key)] = result[key]
    return new_result


def transform_queue_policy_json_output(result):
    new_result = {}
    for policy in sorted(result.keys()):
        new_result[policy] = transform_queue_policy_output(result[policy])
    return new_result


def transform_queue_policy_output(result):
    result = todict(result)
    if result['start']:
        result['start'] = parser.parse(result['start'])
    if result['expiry']:
        result['expiry'] = parser.parse(result['expiry'])
    return result


def transform_file_share_json_output(result):
    result = todict(result)
    new_result = {
        "metadata": result.pop('metadata', None),
        "name": result.pop('name', None),
        "properties": {
            "etag": result.pop('etag', None),
            "lastModified": result.pop('lastModified', None),
            "quota": result.pop('quota', None)
        },
        "snapshot": result.pop('snapshot', None)
    }
    new_result.update(result)
    return new_result


def transform_acl_edit(result):
    if "last_modified" in result.keys():
        result["lastModified"] = result.pop("last_modified")
    return result


def transform_acl_datetime(result):
    result = todict(result)
    if result['start']:
        result['start'] = result["start"].split('.')[0] + '+00:00'
    if result['expiry']:
        result['expiry'] = result["expiry"].split('.')[0] + '+00:00'
    return result


def transform_share_directory_json_output(result):
    result = todict(result)
    new_result = {
        "metadata": result.pop('metadata', None),
        "name": result.pop('name', None),
        "properties": {
            "etag": result.pop('etag', None),
            "lastModified": result.pop('lastModified', None),
            "serverEncrypted": result.pop('serverEncrypted', None)
        }
    }
    new_result.update(result)
    return new_result


def transform_share_file_json_output(result):
    result = todict(result)
    new_result = {
        "metadata": result.pop('metadata', None),
        "name": result.pop('name', None),
        "properties": {
            "etag": result.pop('etag', None),
            "lastModified": result.pop('lastModified', None),
            "serverEncrypted": result.pop('serverEncrypted', None),
            "contentLength": result.pop('size', None),
            "contentRange": result.pop('contentRange', None),
            "contentSettings": result.pop('contentSettings', None),
            "copy": result.pop("copy", None)
        }
    }
    new_result.update(result)
    return new_result


def transform_share_list_handle(result):
    for item in result["items"]:
        item["handleId"] = item.id
        delattr(item, "id")
    return result
