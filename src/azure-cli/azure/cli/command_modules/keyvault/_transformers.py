# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import base64

from collections.abc import Iterable


def multi_transformers(*transformers):
    def _multi_transformers(output):
        for t in transformers:
            output = t(output)
        return output
    return _multi_transformers


def filter_out_managed_resources(output):
    new_output = []
    for item in output:
        managed = item.get('managed') if isinstance(item, dict) else getattr(item, 'managed')
        if not managed:
            new_output.append(item)
    return new_output


def _extract_subresource_name_from_single_output(output, id_parameter):
    if not getattr(output, id_parameter):
        resource_name = None
    else:
        items = getattr(output, id_parameter).split('/')
        resource_name = items[4] if len(items) > 4 else None

    setattr(output, 'name', resource_name)
    return output


def extract_subresource_name(id_parameter='id'):
    def _extract_subresource_name(output):
        if isinstance(output, Iterable):
            return [_extract_subresource_name_from_single_output(item, id_parameter) for item in output]
        return _extract_subresource_name_from_single_output(output, id_parameter)
    return _extract_subresource_name


def transform_key_bundle(key_bundle):
    if isinstance(key_bundle, dict):
        return key_bundle

    def encode_bytes(b):
        if isinstance(b, (bytes, bytearray)):
            return base64.b64encode(b).decode('utf-8')

    result = {
        'attributes': {
            'created': key_bundle.properties.created_on,
            'enabled': key_bundle.properties.enabled,
            'expires': key_bundle.properties.expires_on,
            'notBefore': key_bundle.properties.not_before,
            'recoveryLevel': key_bundle.properties.recovery_level,
            'updated': key_bundle.properties.updated_on
        },
        'key': {
            k: encode_bytes(v)
            for k, v in key_bundle.key.__dict__.items()
            if not callable(v) and not k.startswith('_')
        },
        'managed': key_bundle.properties.managed,
        'tags': key_bundle.properties.tags,
        'name': key_bundle.properties.name
    }
    result['key']['keyOps'] = key_bundle.key_operations
    result['key']['kid'] = key_bundle.id

    return result


def transform_deleted_key(deleted_key):
    if isinstance(deleted_key, dict):
        return deleted_key

    result = {
        'attributes': {
            'created': deleted_key.properties.created_on,
            'enabled': deleted_key.properties.enabled,
            'expires': deleted_key.properties.expires_on,
            'notBefore': deleted_key.properties.not_before,
            'recoveryLevel': deleted_key.properties.recovery_level,
            'updated': deleted_key.properties.updated_on
        },
        'kid': deleted_key.properties.id,
        'managed': deleted_key.properties.managed,
        'tags': deleted_key.properties.tags,
        'name': deleted_key.properties.name,
        'deletedDate': deleted_key.deleted_date,
        'recoveryId': deleted_key.recovery_id,
        'scheduledPurgeDate': deleted_key.scheduled_purge_date
    }

    return result


def transform_key_property(key_property):
    if isinstance(key_property, dict):
        return key_property

    result = {
        'attributes': {
            'created': key_property.created_on,
            'enabled': key_property.enabled,
            'expires': key_property.expires_on,
            'notBefore': key_property.not_before,
            'recoveryLevel': key_property.recovery_level,
            'updated': key_property.updated_on
        },
        'kid': key_property.id,
        'managed': key_property.managed,
        'tags': key_property.tags,
        'name': key_property.name
    }

    return result


def transform_key_property_list(deleted=False):
    def inner(key_property_list):
        new_list = []
        for key_property in list(key_property_list):
            new_list.append(transform_deleted_key(key_property) if deleted else transform_key_property(key_property))
        return new_list
    return inner
