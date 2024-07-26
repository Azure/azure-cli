# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.azclierror import InvalidArgumentValueError
from ._utils import get_resource_group_name_by_registry_name


def acr_cred_set_show(cmd,
                      client,
                      registry_name,
                      name,
                      resource_group_name=None):

    rg = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    return client.get(resource_group_name=rg,
                      registry_name=registry_name,
                      credential_set_name=name)


def acr_cred_set_list(cmd,
                      client,
                      registry_name,
                      resource_group_name=None):

    rg = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    return client.list(resource_group_name=rg,
                       registry_name=registry_name)


def acr_cred_set_delete(cmd,
                        client,
                        registry_name,
                        name,
                        resource_group_name=None):

    rg = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    return client.begin_delete(resource_group_name=rg,
                               registry_name=registry_name,
                               credential_set_name=name)


def acr_cred_set_create(cmd,
                        client,
                        registry_name,
                        name,
                        password_id,
                        username_id,
                        login_server,
                        resource_group_name=None):

    rg = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    CredSet = cmd.get_models('CredentialSet', operation_group='credential_sets')
    AuthCred = cmd.get_models('AuthCredential', operation_group='credential_sets')
    IdentityProperties = cmd.get_models('IdentityProperties', operation_group='credential_sets')

    identity_props = IdentityProperties(type='SystemAssigned')

    auth_creds = AuthCred(name='Credential1')
    auth_creds.username_secret_identifier = username_id
    auth_creds.password_secret_identifier = password_id

    cred_set = CredSet()
    cred_set.name = name
    cred_set.login_server = login_server
    cred_set.auth_credentials = [auth_creds]
    cred_set.identity = identity_props

    return client.begin_create(resource_group_name=rg,
                               registry_name=registry_name,
                               credential_set_name=name,
                               credential_set_create_parameters=cred_set)


def acr_cred_set_update_custom(cmd,
                               client,
                               instance,
                               registry_name,
                               name,
                               resource_group_name=None,
                               password_id=None,
                               username_id=None):

    if password_id is None and username_id is None:
        raise InvalidArgumentValueError("You must update either the username secret ID, password secret ID, or both.")

    rg = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    cred_set = client.get(resource_group_name=rg,
                          registry_name=registry_name,
                          credential_set_name=name)

    password_id = password_id if password_id is not None else cred_set.auth_credentials[0].password_secret_identifier
    username_id = username_id if username_id is not None else cred_set.auth_credentials[0].username_secret_identifier

    auth_creds = cred_set.auth_credentials[0]
    auth_creds.username_secret_identifier = username_id
    auth_creds.password_secret_identifier = password_id
    instance.auth_credentials = [auth_creds]

    return instance


def acr_cred_set_update_get(cmd):
    """Returns an empty CredentialSetUpdateParameters object.
    """

    CredSetUpdateParameters = cmd.get_models('CredentialSetUpdateParameters', operation_group='credential_sets')

    return CredSetUpdateParameters()


def acr_cred_set_update_set(cmd,
                            client,
                            registry_name,
                            name,
                            resource_group_name=None,
                            parameters=None):

    rg = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)
    return client.begin_update(resource_group_name=rg,
                               registry_name=registry_name,
                               credential_set_name=name,
                               credential_set_update_parameters=parameters)
