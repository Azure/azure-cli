# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.profiles import ResourceType


def create_acl_policy(cmd, client, policy_name, start=None, expiry=None, permission=None, **kwargs):
    """Create a stored access policy on the containing object"""
    t_access_policy = cmd.get_models('_models#AccessPolicy', resource_type=ResourceType.DATA_STORAGE_BLOB)
    acl = _get_acl(cmd, client, **kwargs)
    acl['signed_identifiers'][policy_name] = t_access_policy(permission, expiry, start)
    if 'public_access' in acl:
        kwargs['public_access'] = acl['public_access']

    return _set_acl(cmd, client, acl['signed_identifiers'], **kwargs)


def get_acl_policy(cmd, client, policy_name, **kwargs):
    """Show a stored access policy on a containing object"""
    acl = _get_acl(cmd, client, **kwargs)
    return acl['signed_identifiers'].get(policy_name)


def list_acl_policies(cmd, client, **kwargs):
    """List stored access policies on a containing object"""
    return _get_acl(cmd, client, **kwargs)['signed_identifiers']


def set_acl_policy(cmd, client, policy_name, start=None, expiry=None, permission=None, **kwargs):
    """Set a stored access policy on a containing object"""
    if not (start or expiry or permission):
        from knack.util import CLIError
        raise CLIError('Must specify at least one property when updating an access policy.')

    acl = _get_acl(cmd, client, **kwargs)

    try:
        policy = acl['signed_identifiers'][policy_name]
        if policy is None:
            t_access_policy = cmd.get_models('_models#AccessPolicy', resource_type=ResourceType.DATA_STORAGE_BLOB)
            acl['signed_identifiers'][policy_name] = t_access_policy(permission, expiry, start)
        else:
            policy.start = start if start else policy.start
            policy.expiry = expiry if expiry else policy.expiry
            policy.permission = permission or policy.permission
        if 'public_access' in acl:
            kwargs['public_access'] = acl['public_access']

    except KeyError:
        from knack.util import CLIError
        raise CLIError('ACL does not contain {}'.format(policy_name))
    return _set_acl(cmd, client, acl['signed_identifiers'], **kwargs)


def delete_acl_policy(cmd, client, policy_name, **kwargs):
    """ Delete a stored access policy on a containing object """
    acl = _get_acl(cmd, client, **kwargs)

    try:
        del acl['signed_identifiers'][policy_name]
    except KeyError:
        from knack.util import CLIError
        raise CLIError('ACL does not contain {}'.format(policy_name))
    if 'public_access' in acl:
        kwargs['public_access'] = acl['public_access']

    return _set_acl(cmd, client, acl['signed_identifiers'], **kwargs)


def _get_service_container_type(cmd, client):
    t_blob_svc = cmd.get_models('_container_client#ContainerClient', resource_type=ResourceType.DATA_STORAGE_BLOB)
    if isinstance(client, t_blob_svc):
        return "container"

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
        signed_identifiers = {}
        for identifier in result["signed_identifiers"]:
            if identifier.access_policy is not None:
                if getattr(identifier.access_policy, 'permission') is None:
                    setattr(identifier.access_policy, 'permission', '')
            signed_identifiers[identifier.id] = identifier.access_policy
        result['signed_identifiers'] = signed_identifiers
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
