# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.core.cloud import (
    AZURE_CHINA_CLOUD,
    AZURE_PUBLIC_CLOUD,
    AZURE_US_GOV_CLOUD,
    Cloud,
    CloudSuffixes,
)

from azure.cli.command_modules.keyvault._validators import validate_vault_uri


class _Config:
    def __init__(self, allowed_dns_suffixes=None):
        self._allowed_dns_suffixes = allowed_dns_suffixes

    def get(self, section, option, fallback=None):
        if section == 'keyvault' and option == 'allowed_dns_suffixes':
            return self._allowed_dns_suffixes or fallback
        return fallback


class _CliCtx:  # pylint: disable=too-few-public-methods
    def __init__(self, cloud=AZURE_PUBLIC_CLOUD, allowed_dns_suffixes=None):
        self.cloud = cloud
        self.config = _Config(allowed_dns_suffixes)


class VaultUriValidationTest(unittest.TestCase):

    def test_accepts_key_vault_and_mhsm_hosts(self):
        cli_ctx = _CliCtx()
        for uri in [
            'https://myvault.vault.azure.net',
            'https://myvault.vault.azure.net/',
            'https://myhsm.managedhsm.azure.net',
            # Managed HSM may use multi-level names for region support.
            'https://myhsm.eastus.managedhsm.azure.net',
        ]:
            self.assertTrue(validate_vault_uri(cli_ctx, uri).startswith('https://'))

    def test_normalizes_to_origin(self):
        cli_ctx = _CliCtx()
        self.assertEqual(
            validate_vault_uri(cli_ctx, 'https://myvault.vault.azure.net/secrets/s/version'),
            'https://myvault.vault.azure.net')

    def test_rejects_foreign_host(self):
        cli_ctx = _CliCtx()
        for uri in [
            'https://attacker.example/secrets/leak',
            'https://127.0.0.1:8443/secrets/leak',
            'https://vault.azure.net.attacker.example/secrets/leak',
        ]:
            with self.assertRaises(InvalidArgumentValueError):
                validate_vault_uri(cli_ctx, uri)

    def test_rejects_suffix_look_alike(self):
        # Must not match '.vault.azure.net' without the separating dot.
        cli_ctx = _CliCtx()
        with self.assertRaises(InvalidArgumentValueError):
            validate_vault_uri(cli_ctx, 'https://maliciousvault.azure.net/secrets/s')

    def test_rejects_vault_name_template_escape(self):
        # '--vault-name <name>' is concatenated as 'https://{name}.vault.azure.net'; a name
        # carrying URL syntax must not be able to select a different host.
        cli_ctx = _CliCtx()
        for name in ['attacker.example#', 'attacker.example?', 'attacker.example/', 'user@attacker.example#']:
            with self.assertRaises(InvalidArgumentValueError):
                validate_vault_uri(cli_ctx, 'https://{}.vault.azure.net'.format(name))

    def test_rejects_non_https(self):
        cli_ctx = _CliCtx()
        for uri in ['http://myvault.vault.azure.net', 'ftp://myvault.vault.azure.net']:
            with self.assertRaises(InvalidArgumentValueError):
                validate_vault_uri(cli_ctx, uri)

    def test_rejects_credentials_in_uri(self):
        cli_ctx = _CliCtx()
        with self.assertRaises(InvalidArgumentValueError):
            validate_vault_uri(cli_ctx, 'https://user:pass@myvault.vault.azure.net')

    def test_rejects_malformed(self):
        cli_ctx = _CliCtx()
        for uri in [None, '', 'not-a-uri', 'https://', 'https://myvault.vault.azure.net:notaport']:
            with self.assertRaises(InvalidArgumentValueError):
                validate_vault_uri(cli_ctx, uri)

    def test_sovereign_clouds(self):
        for cloud, uri in [
            (AZURE_CHINA_CLOUD, 'https://myvault.vault.azure.cn'),
            (AZURE_CHINA_CLOUD, 'https://myhsm.managedhsm.azure.cn'),
            (AZURE_US_GOV_CLOUD, 'https://myvault.vault.usgovcloudapi.net'),
            (AZURE_US_GOV_CLOUD, 'https://myhsm.managedhsm.usgovcloudapi.net'),
        ]:
            cli_ctx = _CliCtx(cloud=cloud)
            self.assertEqual(validate_vault_uri(cli_ctx, uri), uri)

    def test_rejects_other_clouds_suffix(self):
        cli_ctx = _CliCtx(cloud=AZURE_CHINA_CLOUD)
        with self.assertRaises(InvalidArgumentValueError):
            validate_vault_uri(cli_ctx, 'https://myvault.vault.azure.net')

    def test_configured_suffix_allow_list(self):
        cloud = Cloud('PrivateCloud', suffixes=CloudSuffixes())
        cli_ctx = _CliCtx(cloud=cloud, allowed_dns_suffixes='.vault.contoso.local,managedhsm.contoso.local')
        self.assertEqual(
            validate_vault_uri(cli_ctx, 'https://myvault.vault.contoso.local'),
            'https://myvault.vault.contoso.local')
        self.assertEqual(
            validate_vault_uri(cli_ctx, 'https://myhsm.managedhsm.contoso.local'),
            'https://myhsm.managedhsm.contoso.local')
        with self.assertRaises(InvalidArgumentValueError):
            validate_vault_uri(cli_ctx, 'https://attacker.example')

    def test_cloud_without_suffixes_rejects_everything(self):
        cloud = Cloud('PrivateCloud', suffixes=CloudSuffixes())
        cli_ctx = _CliCtx(cloud=cloud)
        with self.assertRaises(InvalidArgumentValueError):
            validate_vault_uri(cli_ctx, 'https://myvault.vault.azure.net')


if __name__ == '__main__':
    unittest.main()
