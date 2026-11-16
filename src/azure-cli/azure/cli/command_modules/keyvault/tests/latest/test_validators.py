# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import unittest
from unittest import mock
from urllib.parse import parse_qs, urlparse

from knack.arguments import CLICommandArgument
from knack.util import CLIError

from azure.cli.command_modules.keyvault._validators import (
    validate_deleted_vault_or_hsm_name,
    validate_vault_name_and_hsm_name,
)


class _Command:
    def __init__(self, vault_name_options):
        self.arguments = {
            'vault_name': CLICommandArgument('vault_name', options_list=vault_name_options)
        }


class _Namespace:
    def __init__(self, vault_name_options=None, vault_name=None, hsm_name=None):
        if vault_name_options:
            self.cmd = _Command(vault_name_options)
        self.vault_name = vault_name
        self.hsm_name = hsm_name


class KeyVaultValidatorsTest(unittest.TestCase):
    def test_validate_vault_name_and_hsm_name(self):
        # the error message should match the option registered for the command
        with self.assertRaisesRegex(CLIError, r'Please specify --name/-n or --hsm-name\.'):
            validate_vault_name_and_hsm_name(_Namespace(vault_name_options=['--name', '-n']))

        with self.assertRaisesRegex(CLIError, r'--name/-n and --hsm-name are mutually exclusive\.'):
            validate_vault_name_and_hsm_name(
                _Namespace(vault_name_options=['--name', '-n'], vault_name='vault', hsm_name='hsm'))

        with self.assertRaisesRegex(CLIError, r'Please specify --vault-name or --hsm-name\.'):
            validate_vault_name_and_hsm_name(_Namespace(vault_name_options=['--vault-name']))

        # fall back to --vault-name when the vault name argument can't be resolved
        with self.assertRaisesRegex(CLIError, r'Please specify --vault-name or --hsm-name\.'):
            validate_vault_name_and_hsm_name(_Namespace())

        # no exception when just one of them is specified
        validate_vault_name_and_hsm_name(_Namespace(vault_name_options=['--name', '-n'], vault_name='vault'))
        validate_vault_name_and_hsm_name(_Namespace(vault_name_options=['--name', '-n'], hsm_name='hsm'))

    def test_validate_deleted_vault_or_hsm_name(self):
        ns = _Namespace(vault_name_options=['--name', '-n'])
        with self.assertRaisesRegex(CLIError, r'Please specify --name/-n or --hsm-name\.'):
            validate_deleted_vault_or_hsm_name(ns.cmd, ns)


_SUB = '00000000-0000-0000-0000-000000000000'


def _vault(rg, name):
    return {'id': f'/subscriptions/{_SUB}/resourceGroups/{rg}/providers/Microsoft.KeyVault/vaults/{name}',
            'name': name, 'type': 'Microsoft.KeyVault/vaults', 'location': 'eastus'}


def _two_page_vaults_list_client_factory(requested_urls):
    """Build the real KeyVaultManagementClient over a transport serving two pages from ARM /resources."""
    import io
    import requests
    import urllib3
    from azure.core.credentials import AccessToken
    from azure.core.pipeline.transport import RequestsTransport
    from azure.mgmt.keyvault import KeyVaultManagementClient

    next_link = (f'https://management.azure.com/subscriptions/{_SUB}/resources?'
                 '%24filter=resourceType+eq+%27Microsoft.KeyVault%2fvaults%27&api-version=2015-11-01&%24skiptoken=p2')
    pages = [{'value': [_vault('rg1', 'vault1')], 'nextLink': next_link},
             {'value': [_vault('rg2', 'vault2')]}]

    def _send(method, url, **kwargs):
        requested_urls.append(url)
        response = requests.Response()
        response.status_code = 200
        response.headers['Content-Type'] = 'application/json'
        response.raw = urllib3.HTTPResponse(body=io.BytesIO(json.dumps(pages[len(requested_urls) - 1]).encode()),
                                            status=200, preload_content=False)
        response.url = url
        return response

    session = mock.MagicMock()
    session.request.side_effect = _send

    class _Credential:
        def get_token(self, *scopes, **kwargs):
            return AccessToken('token', 9999999999)

    def _factory(cli_ctx, resource_type, **kwargs):
        client_kwargs = {'api_version': kwargs['api_version']} if kwargs.get('api_version') else {}
        return KeyVaultManagementClient(_Credential(), _SUB, transport=RequestsTransport(session=session),
                                        **client_kwargs)

    return _factory


class TestVaultsListPaging(unittest.TestCase):
    def test_list_vault_uses_2015_11_01_on_every_page(self):
        from azure.cli.command_modules.keyvault.custom import list_vault

        requested_urls = []
        with mock.patch('azure.cli.command_modules.keyvault._validators.get_mgmt_service_client',
                        _two_page_vaults_list_client_factory(requested_urls)):
            vaults = list_vault(mock.MagicMock(), client=None)

        self.assertEqual([v.name for v in vaults], ['vault1', 'vault2'])
        self.assertEqual(len(requested_urls), 2)
        for url in requested_urls:
            self.assertEqual(urlparse(url).path, f'/subscriptions/{_SUB}/resources')
            self.assertEqual(parse_qs(urlparse(url).query)['api-version'], ['2015-11-01'])


if __name__ == '__main__':
    unittest.main()
