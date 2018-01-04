# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.decorators import Completer
from azure.cli.core._profile import Profile


def _get_token(cli_ctx, server, resource, scope):  # pylint: disable=unused-argument
    return Profile(cli_ctx=cli_ctx).get_login_credentials(resource)[0]._token_retriever()  # pylint: disable=protected-access


def get_keyvault_name_completion_list(resource_name):

    @Completer
    def completer(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
        from azure.keyvault import KeyVaultClient, KeyVaultAuthentication
        client = KeyVaultClient(KeyVaultAuthentication(_get_token))
        func_name = 'get_{}s'.format(resource_name)
        vault = namespace.vault_base_url
        items = []
        for y in list(getattr(client, func_name)(vault)):
            id_val = getattr(y, 'id', None) or getattr(y, 'kid', None)
            items.append(id_val.rsplit('/', 1)[1])
        return items

    return completer


def get_keyvault_version_completion_list(resource_name):

    @Completer
    def completer(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
        from azure.keyvault import KeyVaultClient, KeyVaultAuthentication
        client = KeyVaultClient(KeyVaultAuthentication(_get_token))
        func_name = 'get_{}_versions'.format(resource_name)
        vault = namespace.vault_base_url
        name = getattr(namespace, '{}_name'.format(resource_name))
        items = []
        for y in list(getattr(client, func_name)(vault, name)):
            id_val = getattr(y, 'id', None) or getattr(y, 'kid', None)
            items.append(id_val.rsplit('/', 1)[1])
        return items

    return completer
