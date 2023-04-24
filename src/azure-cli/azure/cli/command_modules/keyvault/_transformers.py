# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from collections.abc import Iterable
from azure.cli.command_modules.keyvault._validators import KeyEncryptionDataType


def multi_transformers(*transformers):
    def _multi_transformers(output, **command_args):
        for t in transformers:
            output = t(output, **command_args)
        return output
    return _multi_transformers


def keep_max_results(output, **command_args):
    maxresults = command_args.get('maxresults', command_args.get('max_page_size', None))
    if maxresults:
        return list(output)[:maxresults]
    return output


def filter_out_managed_resources(output, **command_args):  # pylint: disable=unused-argument
    is_kv_transform = command_args.get('kv_transform')
    if is_kv_transform:
        if command_args.get('include_managed'):
            return output
        return [_ for _ in output if not getattr(_, 'managed')] if output else output
    return output


def _extract_subresource_name_from_single_output(output, id_parameter):
    if not getattr(output, id_parameter):
        resource_name = None
    else:
        items = getattr(output, id_parameter).split('/')
        resource_name = items[4] if len(items) > 4 else None

    setattr(output, 'name', resource_name)
    return output


def extract_subresource_name(id_parameter='id'):
    def _extract_subresource_name(output, **command_args):  # pylint: disable=unused-argument
        if isinstance(output, Iterable):
            return [_extract_subresource_name_from_single_output(item, id_parameter) for item in output]
        return _extract_subresource_name_from_single_output(output, id_parameter)
    return _extract_subresource_name


def transform_key_encryption_output(result, **command_args):  # pylint: disable=unused-argument
    if not result or isinstance(result, dict):
        return result

    # transform EncryptResult to dict
    import base64
    import binascii
    output = {
        'kid': result.key_id,
        'result': base64.b64encode(result.ciphertext).decode('utf-8'),
        'algorithm': result.algorithm,
        'iv': binascii.hexlify(result.iv) if result.iv else None,
        'tag': binascii.hexlify(result.tag) if result.tag else None,
        'aad': binascii.hexlify(result.aad) if result.aad else None
    }
    return output


def transform_key_decryption_output(result, **command_args):
    if not result or isinstance(result, dict):
        return result

    # transform DecryptResult to dict
    import base64
    output = {
        'kid': result.key_id,
        'result': result.plaintext,
        'algorithm': result.algorithm
    }
    data_type = command_args.get('data_type')
    if data_type == KeyEncryptionDataType.BASE64:
        output['result'] = base64.b64encode(result.plaintext).decode('utf-8')
    return output


# pylint: disable=unused-argument, protected-access
def transform_key_output(result, **command_args):
    from azure.keyvault.keys import KeyVaultKey, JsonWebKey
    import base64

    if not isinstance(result, KeyVaultKey):
        return result

    if result.key and isinstance(result.key, JsonWebKey):
        for attr in result.key._FIELDS:
            value = getattr(result.key, attr)
            if value and isinstance(value, bytes):
                setattr(result.key, attr, base64.b64encode(value))

    output = {
        'attributes': result.properties._attributes,
        'key': result.key,
        'managed': result.properties.managed,
        'tags': result.properties.tags,
        'releasePolicy': result.properties.release_policy
    }
    return output


# pylint: disable=unused-argument
def transform_key_random_output(result, **command_args):
    if result and isinstance(result, bytes):
        import base64
        return {"value": base64.b64encode(result)}

    return result


def transform_secret_list(result, **command_args):
    return [transform_secret_base_properties(secret) for secret in result]


def transform_secret_base_properties(result, **command_args):
    if not isinstance(result, dict):
        ret = {
            "attributes": getattr(result, "_attributes", None),
            "contentType": getattr(result, "content_type", None),
            "id": getattr(result, "id", None),
            "managed": getattr(result, "managed", None),
            "name": getattr(result, "name", None),
            "tags": getattr(result, "tags", None)
        }
        return ret
    return result


def transform_deleted_secret_list(result, **command_args):
    return [transform_deleted_secret_properties(secret) for secret in result]


def transform_deleted_secret_properties(result):
    if not isinstance(result, dict):
        ret = transform_secret_base_properties(getattr(result, "properties", None))
        ret.update({
            "deletedDate": getattr(result, "deleted_date", None),
            "recoveryId": getattr(result, "recovery_id", None),
            "scheduledPurgeDate": getattr(result, "scheduled_purge_date", None)
        })
        return ret
    return result


def transform_secret_set(result, **command_args):
    if not isinstance(result, dict):
        properties = getattr(result, "properties", None)
        ret = transform_secret_base_properties(properties)
        ret.update({
            "kid": getattr(properties, "key_id", None),
            "value": getattr(result, "value", None)
        })
        return ret
    return result


def transform_secret_set_attributes(result, **command_args):
    if not isinstance(result, dict):
        ret = transform_secret_base_properties(result)
        ret.update({
            "kid": getattr(result, "key_id", None),
            "value": None
        })
        return ret
    return result


def transform_secret_show_deleted(result, **command_args):
    if not isinstance(result, dict):
        properties = getattr(result, "properties", None)
        ret = transform_secret_base_properties(properties)
        ret.update({
            "kid": getattr(properties, "key_id", None),
            "value": None,
            "deletedDate": getattr(result, "deleted_date", None),
            "recoveryId": getattr(result, "recovery_id", None),
            "scheduledPurgeDate": getattr(result, "scheduled_purge_date", None)
        })
        return ret
    return result


def transform_secret_delete(result, **command_args):
    if not isinstance(result, dict):
        ret = transform_secret_show_deleted(result.result())
        return ret
    return result


def transform_secret_recover(result, **command_args):
    if not isinstance(result, dict):
        ret = transform_secret_set_attributes(result.result())
        return ret
    return result

