# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime
from azure.cli.core.profiles import ResourceType


def create_acl_policy(cmd, client, policy_name, start=None, expiry=None, permission=None, **kwargs):
    """Create a stored access policy on the containing object"""
    t_access_policy = cmd.get_models('_models#AccessPolicy', resource_type=ResourceType.DATA_STORAGE_BLOB)
    acl = _get_acl(cmd, client, **kwargs)
    if _get_service_container_type(cmd, client) == 'container':
        signed_identifiers = {}
        for identifier in acl["signed_identifiers"]:
            signed_identifiers[identifier.id] = identifier.access_policy
        acl = signed_identifiers
    acl[policy_name] = t_access_policy(permission if permission else '',
                                       _str_to_datetime(expiry) if expiry else datetime.max,
                                       _str_to_datetime(start) if start else datetime.utcnow())
    if hasattr(acl, 'public_access'):
        kwargs['public_access'] = getattr(acl, 'public_access')

    return _set_acl(cmd, client, acl, **kwargs)


def _str_to_datetime(time):
    form = '%Y-%m-%d'
    try:
        return datetime.strptime(time, form)
    except ValueError:
        pass
    return time


def get_acl_policy(cmd, client, policy_name, **kwargs):
    """Show a stored access policy on a containing object"""
    acl = _get_acl(cmd, client, **kwargs)
    if _get_service_container_type(cmd, client) == 'container':
        for identifier in acl['signed_identifiers']:
            if identifier.id == policy_name:
                return identifier.access_policy
    else:
        return acl.get(policy_name)


def list_acl_policies(cmd, client, **kwargs):
    """List stored access policies on a containing object"""
    return _get_acl(cmd, client, **kwargs)


def set_acl_policy(cmd, client, policy_name, start=None, expiry=None, permission=None, **kwargs):
    """Set a stored access policy on a containing object"""
    if not (start or expiry or permission):
        from knack.util import CLIError
        raise CLIError('Must specify at least one property when updating an access policy.')

    acl = _get_acl(cmd, client, **kwargs)
    try:
        if _get_service_container_type(cmd, client) == 'container':
            signed_identifiers = {}
            found = False
            for identifier in acl["signed_identifiers"]:
                signed_identifiers[identifier.id] = identifier.access_policy
                if identifier.id == policy_name:
                    policy = identifier.access_policy
                    found = True
            acl = signed_identifiers
            if not found:
                raise KeyError()
        else:
            policy = acl[policy_name]
        policy.start = _str_to_datetime(start) if start else policy.start
        policy.expiry = _str_to_datetime(expiry) if expiry else policy.expiry
        policy.permission = permission or policy.permission
        if hasattr(acl, 'public_access'):
            kwargs['public_access'] = getattr(acl, 'public_access')

    except KeyError:
        from knack.util import CLIError
        raise CLIError('ACL does not contain {}'.format(policy_name))
    return _set_acl(cmd, client, acl, **kwargs)


def delete_acl_policy(cmd, client, policy_name, **kwargs):
    """ Delete a stored access policy on a containing object """
    acl = _get_acl(cmd, client, **kwargs)
    if _get_service_container_type(cmd, client) == 'container':
        signed_identifiers = {}
        found = False
        for identifier in acl["signed_identifiers"]:
            if identifier.id == policy_name:
                found = True
                continue
            signed_identifiers[identifier.id] = identifier.access_policy
        acl = signed_identifiers
        if not found:
            from knack.util import CLIError
            raise CLIError('ACL does not contain {}'.format(policy_name))
    else:
        del acl[policy_name]
    if hasattr(acl, 'public_access'):
        kwargs['public_access'] = getattr(acl, 'public_access')

    return _set_acl(cmd, client, acl, **kwargs)


def _get_service_container_type(cmd, client):
    t_blob_svc = cmd.get_models('_container_client#ContainerClient', resource_type=ResourceType.DATA_STORAGE_BLOB)
    if isinstance(client, t_blob_svc):
        return "container"

    t_file_svc = cmd.get_models('_share_client#ShareClient', resource_type=ResourceType.DATA_STORAGE_FILESHARE)
    if isinstance(client, t_file_svc):
        return "share"

    t_queue_svc = cmd.get_models('_queue_client#QueueClient', resource_type=ResourceType.DATA_STORAGE_QUEUE)
    if isinstance(client, t_queue_svc):
        return "queue"

    from azure.data.tables._table_client import TableClient
    if isinstance(client, TableClient):
        return 'table'
    raise ValueError('Unsupported service {}'.format(type(client)))


def _get_acl(cmd, client, **kwargs):
    container = _get_service_container_type(cmd, client)
    get_acl_fn = getattr(client, 'get_{}_access_policy'.format(container))
    # When setting acl, sdk will validate that AccessPolicy.permission cannot be None, but '' is OK.
    # So we convert every permission=None to permission='' here.
    # This can be removed after sdk deprecate the validation.
    return convert_acl_permissions(get_acl_fn(**kwargs))


def convert_acl_permissions(result):
    if result is None:
        return None
    if 'signed_identifiers' in result:
        return result
    for policy in sorted(result.keys()):
        if getattr(result[policy], 'permission') is None:
            setattr(result[policy], 'permission', '')
    return result


def _set_acl(cmd, client, acl, **kwargs):
    from knack.util import CLIError
    method_name = 'set_{}_access_policy'.format(_get_service_container_type(cmd, client))
    try:
        method = getattr(client, method_name)
        return method(acl, **kwargs)
    except TypeError:
        raise CLIError("Failed to invoke SDK method {}. The installed azure SDK may not be"
                       "compatible to this version of Azure CLI.".format(method_name))
    except AttributeError:
        raise CLIError("Failed to get function {} from {}. The installed azure SDK may not be "
                       "compatible to this version of Azure CLI.".format(client.__class__.__name__, method_name))
