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


def transform_certificate_create(result, **command_args):
    if not isinstance(result, dict):
        import base64
        csr = getattr(result, "csr", None)
        ret = {
            "cancellationRequested": getattr(result, "cancellation_requested", None),
            "csr": base64.b64encode(csr).decode('utf-8') if csr else None,
            "error": getattr(result, "error", None),
            "id": getattr(result, "id", None),
            "issuerParameters": {
                "certificateTransparency": getattr(result, "certificate_transparency", None),
                "certificateType": getattr(result, "certificate_type", None),
                "name": getattr(result, "issuer_name", None)
            },
            "name": getattr(result, "name", None),
            "requestId": getattr(result, "request_id", None),
            "status": getattr(result, "status", None),
            "statusDetails": getattr(result, "status_details", None),
            "target": getattr(result, "target", None)
        }
        return ret
    return result


def transform_certificate_list(result, **command_args):
    return [transform_certificate_properties(certificate) for certificate in result]


def transform_certificate_properties(result):
    import base64
    if not isinstance(result, dict):
        x509_thumbprint = getattr(result, "x509_thumbprint", None)
        ret = {
            "attributes": {
                "created": getattr(result, "created_on", None),
                "enabled": getattr(result, "enabled", None),
                "expires": getattr(result, "expires_on", None),
                "notBefore": getattr(result, "not_before", None),
                "recoveryLevel": getattr(result, "recovery_level", None),
                "updated": getattr(result, "updated_on", None)
            },
            "id": getattr(result, "id", None),
            "name": getattr(result, "name", None),
            "subject": getattr(result, "subject", ""),
            "tags": getattr(result, "tags", None),
            "x509Thumbprint": base64.b64encode(x509_thumbprint).decode('utf-8') if x509_thumbprint else None,
            "x509ThumbprintHex": x509_thumbprint.hex().upper()
        }
        return ret
    return result


def transform_certificate_list_deleted(result, **command_args):
    return [transform_deleted_certificate(certificate) for certificate in result]


def transform_deleted_certificate(result):
    if not isinstance(result, dict):
        ret = transform_certificate_properties(getattr(result, "properties", None))
        ret.update({
            "deletedDate": getattr(result, "deleted_on", None),
            "recoveryId": getattr(result, "recovery_id", None),
            "scheduledPurgeDate": getattr(result, "scheduled_purge_date", None)
        })
        del ret["subject"]
        return ret
    return result

def transform_certificate_show(result, **command_args):
    import base64
    if not isinstance(result, dict):
        ret = transform_certificate_properties(getattr(result, "properties", None))
        id = getattr(result, "id", None)
        cer = getattr(result, "cer", None)
        ret.update({
            "cer": base64.b64encode(cer).decode('utf-8') if cer else None,
            "contentType": getattr(result, "content_type", None),
            "kid": getattr(result, "key_id", None),
            "pending": {
                "id": '/'.join(id.split('/')[:-1] + ['pending']) if id else None
            },
            "policy": transform_certificate_policy(policy=getattr(result, "policy", None),
                                                   id='/'.join(id.split('/')[:-1] + ['policy'])),
            "sid": getattr(result, "secret_id", None)
        })
        del ret["subject"]
        return ret
    return result

# pylint: disable=line-too-long
def transform_certificate_policy(policy, id):
    if not isinstance(policy, dict):
        san_emails = getattr(policy, "san_emails", None)
        san_dns_names = getattr(policy, "san_dns_names", None)
        san_upns = getattr(policy, "san_user_principal_names", None)
        subject_alternative_names = None
        if san_emails and san_dns_names and san_upns:
            subject_alternative_names = {
                "emails": san_emails,
                "upns": san_upns,
                "dns_names": san_dns_names
            }
        policy = {
            "attributes": {
                "created": getattr(policy, "created_on", None),
                "enabled": getattr(policy, "enabled", None),
                "expires": getattr(policy, "expires_on", None),
                "notBefore": getattr(policy, "not_before", None),
                "recoveryLevel": getattr(policy, "recovery_level", None),
                "updated": getattr(policy, "updated_on", None)
            },
            "id": id,
            "issuerParameters": {
                "certificateTransparency": getattr(policy, "certificate_transparency", None),
                "certificateType": getattr(policy, "certificate_type", None),
                "name": getattr(policy, "issuer_name", None)
            },
            "keyProperties": {
                "curve": getattr(policy, "curve", None),
                "exportable": getattr(policy, "exportable", None),
                "keySize": getattr(policy, "key_size", None),
                "keyType": getattr(policy, "key_type", None),
                "reuseKey": getattr(policy, "reuse_key", None)
            },
            "lifetimeActions": [{
                "action": {
                    "actionType": getattr(action, "action", None)
                },
                "trigger": {
                    "daysBeforeExpiry": getattr(action, "days_before_expiry", None),
                    "lifetimePercentage": getattr(action, "lifetime_percentage", None)
                }
            } for action in getattr(policy, "lifetime_actions", None)],
            "secretProperties": {
                "contentType": getattr(policy, "content_type", None)
            },
            "x509CertificateProperties": {
                "basic_constraints": {
                    "ca": getattr(policy, "ca", False)
                },
                "ekus": getattr(policy, "enhanced_key_usage", None),
                "keyUsage": getattr(policy, "key_usage", None),
                "subject": getattr(policy, "subject", None),
                "subjectAlternativeNames": subject_alternative_names,
                "validityInMonths": getattr(policy, "validity_in_months", None)
            }
        }
        return policy
    return policy


def transform_certificate_show_deleted(result, **command_args):
    if not isinstance(result, dict):
        ret = transform_certificate_show(result)
        ret.update({
            "deletedDate": getattr(result, "deleted_on", None),
            "recoveryId": getattr(result, "recovery_id", None),
            "scheduledPurgeDate": getattr(result, "scheduled_purge_date", None)
        })
        return ret
    return result
