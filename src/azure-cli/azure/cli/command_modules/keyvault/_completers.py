# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.decorators import Completer
from azure.cli.core._profile import Profile


def get_keyvault_name_completion_list(resource_name):

    @Completer
    def completer(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
        func_name = 'list_properties_of_{}s'.format(resource_name)
        vault = namespace.vault_base_url
        profile = Profile(cli_ctx=cmd.cli_ctx)
        credential, _, _ = profile.get_login_credentials(subscription_id=cmd.cli_ctx.data.get('subscription_id'))
        if resource_name == 'key':
            from azure.keyvault.keys import KeyClient
            from azure.cli.command_modules.keyvault._client_factory import is_azure_stack_profile
            version = '7.5-preview.1' if not is_azure_stack_profile(cmd=cmd) else '2016-10-01'
            client = KeyClient(vault_url=vault, credential=credential, api_version=version,
                               verify_challenge_resource=False)
        elif resource_name == 'secret':
            from azure.keyvault.secrets import SecretClient
            from azure.cli.command_modules.keyvault._client_factory import is_azure_stack_profile
            version = '7.4' if not is_azure_stack_profile(cmd=cmd) else '2016-10-01'
            client = SecretClient(vault_url=vault, credential=credential, api_version=version,
                                  verify_challenge_resource=False)
        else:
            from azure.keyvault.certificates import CertificateClient
            from azure.cli.command_modules.keyvault._client_factory import is_azure_stack_profile
            version = '7.4' if not is_azure_stack_profile(cmd=cmd) else '2016-10-01'
            client = CertificateClient(vault_url=vault, credential=credential, api_version=version,
                                       verify_challenge_resource=False)
        items = []
        for y in list(getattr(client, func_name)()):
            items.append(y.name)
        return items

    return completer


def get_keyvault_version_completion_list(resource_name):

    @Completer
    def completer(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
        func_name = 'list_properties_of_{}_versions'.format(resource_name)
        vault = namespace.vault_base_url
        profile = Profile(cli_ctx=cmd.cli_ctx)
        credential, _, _ = profile.get_login_credentials(subscription_id=cmd.cli_ctx.data.get('subscription_id'))
        if resource_name == 'key':
            from azure.keyvault.keys import KeyClient
            from azure.cli.command_modules.keyvault._client_factory import is_azure_stack_profile
            version = '7.5-preview.1' if not is_azure_stack_profile(cmd=cmd) else '2016-10-01'
            client = KeyClient(vault_url=vault, credential=credential, api_version=version,
                               verify_challenge_resource=False)
        elif resource_name == 'secret':
            from azure.keyvault.secrets import SecretClient
            from azure.cli.command_modules.keyvault._client_factory import is_azure_stack_profile
            version = '7.4' if not is_azure_stack_profile(cmd=cmd) else '2016-10-01'
            client = SecretClient(vault_url=vault, credential=credential, api_version=version,
                                  verify_challenge_resource=False)
        else:
            from azure.keyvault.certificates import CertificateClient
            from azure.cli.command_modules.keyvault._client_factory import is_azure_stack_profile
            version = '7.4' if not is_azure_stack_profile(cmd=cmd) else '2016-10-01'
            client = CertificateClient(vault_url=vault, credential=credential, api_version=version,
                                       verify_challenge_resource=False)
        items = []
        for y in list(getattr(client, func_name)()):
            items.append(y.version)
        return items

    return completer
