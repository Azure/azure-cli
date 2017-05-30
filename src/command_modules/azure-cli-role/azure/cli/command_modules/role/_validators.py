# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import uuid
from azure.cli.core.util import CLIError
from ._client_factory import _graph_client_factory

VARIANT_GROUP_ID_ARGS = ['object_id', 'group_id', 'group_object_id']


def validate_group(namespace):
    # For AD auto-commands, here we resolve logic names to object ids needed by SDK methods
    attr, value = next(((x, getattr(namespace, x)) for x in VARIANT_GROUP_ID_ARGS
                        if hasattr(namespace, x)))
    try:
        uuid.UUID(value)
    except ValueError:
        client = _graph_client_factory()
        sub_filters = []
        sub_filters.append("startswith(displayName,'{}')".format(value))
        sub_filters.append("displayName eq '{}'".format(value))
        result = list(client.groups.list(filter=' or '.join(sub_filters)))
        count = len(result)
        if count == 1:
            setattr(namespace, attr, result[0].object_id)
        elif count == 0:
            raise CLIError("No group matches the name of '{}'".format(value))
        else:
            raise CLIError("More than one groups match the name of '{}'".format(value))


def validate_member_id(namespace):
    from azure.cli.core._profile import Profile, CLOUD
    try:
        uuid.UUID(namespace.url)
        profile = Profile()
        _, _, tenant_id = profile.get_login_credentials()
        graph_url = CLOUD.endpoints.active_directory_graph_resource_id
        namespace.url = '{}{}/directoryObjects/{}'.format(graph_url, tenant_id,
                                                          namespace.url)
    except ValueError:
        pass  # let it go, invalid values will be caught by server anyway


def validate_cert(namespace):
    cred_usage_error = CLIError('Usage error: --cert STRING | --create-cert [--keyvault VAULT --cert NAME] | '
                                '--password STRING | --keyvault VAULT --cert NAME')
    cert = namespace.cert
    create_cert = namespace.create_cert
    keyvault = namespace.keyvault
    password = namespace.password

    # validate allowed parameter combinations
    if not any((cert, create_cert, password, keyvault)):
        # 1 - Simplest scenario. Use random password
        pass
    elif password and not any((cert, create_cert, keyvault)):
        # 2 - Password supplied -- no certs
        pass
    elif create_cert and not any((cert, keyvault, password)):
        # 3 - User-supplied public cert data
        pass
    elif cert and not any((create_cert, keyvault, password)):
        # 4 - Create local self-signed cert
        pass
    elif cert and keyvault and not password:
        # 5 - Create self-signed cert in KeyVault
        # 6 - Use existing cert from KeyVault
        pass
    else:
        raise cred_usage_error

    # validate cert parameter
    if cert and not keyvault:
        from azure.cli.command_modules.role.custom import _try_x509_pem, _try_x509_der
        x509 = _try_x509_pem(cert) or _try_x509_der(cert)
        if not x509:
            raise CLIError('usage error: --cert STRING | --cert NAME --keyvault VAULT')
        namespace.cert = x509
