# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import importlib
from unittest import mock

# The path contains a reserved keyword 'import', so we need a workaround here
acr_import = importlib.import_module('azure.cli.command_modules.acr.import')


class TestRegionalEndpointUriConversion(unittest.TestCase):

    @mock.patch.object(acr_import.logger, 'warning')
    def test_valid_regional_endpoint_conversion(self, warning):
        """Test conversion of regional endpoint URIs to standard format."""
        login_server_suffix = '.azurecr.io'

        # Valid regional endpoints that should be converted
        test_cases = [
            ('myregistry.westus.geo.azurecr.io', 'myregistry.azurecr.io'),
            ('registry123.eastus2.geo.azurecr.io', 'registry123.azurecr.io'),
            ('prod-registry.centralus.geo.azurecr.io', 'prod-registry.azurecr.io'),
            # Mixed-case: hostnames are case-insensitive, output is normalized to lowercase
            ('MyRegistry.EastUS.Geo.azurecr.io', 'myregistry.azurecr.io'),
            ('MYREGISTRY.WESTUS.GEO.AZURECR.IO', 'myregistry.azurecr.io'),
        ]

        for regional_uri, expected in test_cases:
            result = acr_import._regional_endpoint_uri_to_login_server(regional_uri, login_server_suffix)
            self.assertEqual(result, expected)

        self.assertEqual(warning.call_count, len(test_cases))
        warning.assert_called_with(acr_import.REGIONAL_ENDPOINT_IMPORT_WARNING)

    @mock.patch.object(acr_import.logger, 'warning')
    def test_valid_regional_endpoint_conversion_multi_label_suffix(self, warning):
        """Regional endpoints in sovereign clouds whose login-server suffix has more than two
        labels (e.g. '.azurecr.sovcloud-azure.de') must still be converted."""
        test_cases = [
            ('registry123.deloscloudgermanycentral.geo.azurecr.sovcloud-azure.de',
             '.azurecr.sovcloud-azure.de', 'registry123.azurecr.sovcloud-azure.de'),
            ('myregistry.francecentral.geo.azurecr.sovcloud-azure.fr',
             '.azurecr.sovcloud-azure.fr', 'myregistry.azurecr.sovcloud-azure.fr'),
            # DNL registry (hash suffix) in a multi-label sovereign cloud
            ('myregistry-d7ezgzevdwfvc8ht.deloscloudgermanycentral.geo.azurecr.sovcloud-azure.de',
             '.azurecr.sovcloud-azure.de', 'myregistry-d7ezgzevdwfvc8ht.azurecr.sovcloud-azure.de'),
        ]

        for regional_uri, suffix, expected in test_cases:
            result = acr_import._regional_endpoint_uri_to_login_server(regional_uri, suffix)
            self.assertEqual(result, expected)

        self.assertEqual(warning.call_count, len(test_cases))
        warning.assert_called_with(acr_import.REGIONAL_ENDPOINT_IMPORT_WARNING)

    @mock.patch.object(acr_import.logger, 'warning')
    def test_non_regional_endpoint_uris_unchanged(self, warning):
        """Test that non-regional endpoint URIs are returned unchanged."""
        login_server_suffix = '.azurecr.io'

        # URIs that should remain unchanged
        test_cases = [
            'testregistry.azurecr.io',
            'external-registry.com',
            'testregistry.eastus.notgeo.azurecr.io',
            # Malformed: empty region label must NOT be converted
            'testregistry..geo.azurecr.io',
            'testregistry.azurecr.sovcloud-azure.de',
            'testregistry.deloscloudgermanycentral.notgeo.azurecr.sovcloud-azure.de'
        ]

        for uri in test_cases:
            result = acr_import._regional_endpoint_uri_to_login_server(uri, login_server_suffix)
            self.assertEqual(result, uri)

        warning.assert_not_called()

    @mock.patch.object(acr_import.logger, 'warning')
    @mock.patch.object(acr_import, 'get_registry_from_name_or_login_server')
    @mock.patch.object(acr_import, 'get_login_server_suffix', return_value='.azurecr.io')
    def test_get_azure_registry_matches_regional_suffix_case_insensitively(
            self, get_login_server_suffix, get_registry, warning):
        get_registry.return_value = mock.sentinel.registry
        cmd = mock.Mock(cli_ctx=mock.sentinel.cli_ctx)
        regional_endpoint = 'MyRegistry.WestUS.Geo.AzureCR.IO'

        result = acr_import._get_azure_registry(cmd, regional_endpoint)

        self.assertIs(result, mock.sentinel.registry)
        get_login_server_suffix.assert_called_once_with(mock.sentinel.cli_ctx)
        get_registry.assert_called_once_with(
            mock.sentinel.cli_ctx, 'myregistry.azurecr.io', regional_endpoint)
        warning.assert_called_once_with(acr_import.REGIONAL_ENDPOINT_IMPORT_WARNING)

    @mock.patch.object(acr_import, '_regional_endpoint_uri_to_login_server')
    @mock.patch.object(acr_import, 'get_registry_from_name_or_login_server')
    @mock.patch.object(acr_import, 'get_login_server_suffix', return_value='.azurecr.io')
    def test_get_azure_registry_does_not_convert_resource_id(
            self, get_login_server_suffix, get_registry, convert_regional_endpoint):
        get_registry.return_value = mock.sentinel.registry
        cmd = mock.Mock(cli_ctx=mock.sentinel.cli_ctx)
        resource_id = ('/subscriptions/000/resourceGroups/rg/providers/'
                       'Microsoft.ContainerRegistry/registries/source')

        result = acr_import._get_azure_registry(cmd, resource_id)

        self.assertIs(result, mock.sentinel.registry)
        get_login_server_suffix.assert_called_once_with(mock.sentinel.cli_ctx)
        convert_regional_endpoint.assert_not_called()
        get_registry.assert_called_once_with(
            mock.sentinel.cli_ctx, resource_id, resource_id)

    @staticmethod
    def _match_regional_endpoint(login_server, endpoint, regional_endpoint_host_names):
        """Replicate the matching logic from acr_login for unit testing."""
        login_server_name = login_server.split('.')[0]
        regional_endpoint_prefix = f"{login_server_name}.{endpoint}.geo.".lower()
        return next(
            (url for url in regional_endpoint_host_names
             if url.lower().strip().startswith(regional_endpoint_prefix)), None)

    def test_match_standard_registry(self):
        """Registry without DNL — login_server starts with registry name."""
        login_server = 'myregistry.azurecr.io'
        hosts = [
            'myregistry.eastus.geo.azurecr.io',
            'myregistry.westus.geo.azurecr.io',
        ]
        self.assertEqual(
            self._match_regional_endpoint(login_server, 'eastus', hosts),
            'myregistry.eastus.geo.azurecr.io')
        self.assertEqual(
            self._match_regional_endpoint(login_server, 'westus', hosts),
            'myregistry.westus.geo.azurecr.io')

    def test_match_dnl_registry(self):
        """Registry with DNL suffix — login_server has a hash appended."""
        login_server = 'myregistry-d7ezgzevdwfvc8ht.azurecr.io'
        hosts = [
            'myregistry-d7ezgzevdwfvc8ht.eastus.geo.azurecr.io',
            'myregistry-d7ezgzevdwfvc8ht.westus.geo.azurecr.io',
        ]
        self.assertEqual(
            self._match_regional_endpoint(login_server, 'eastus', hosts),
            'myregistry-d7ezgzevdwfvc8ht.eastus.geo.azurecr.io')
        self.assertEqual(
            self._match_regional_endpoint(login_server, 'westus', hosts),
            'myregistry-d7ezgzevdwfvc8ht.westus.geo.azurecr.io')

    def test_no_match_returns_none(self):
        """Endpoint region not in the host list returns None."""
        login_server = 'myregistry.azurecr.io'
        hosts = ['myregistry.eastus.geo.azurecr.io']
        self.assertIsNone(
            self._match_regional_endpoint(login_server, 'westus', hosts))

    def test_match_case_insensitive(self):
        """Matching is case-insensitive for both endpoint arg and host names."""
        login_server = 'MyRegistry.azurecr.io'
        hosts = ['MyRegistry.EastUS.geo.azurecr.io']
        self.assertEqual(
            self._match_regional_endpoint(login_server, 'eastus', hosts),
            'MyRegistry.EastUS.geo.azurecr.io')
