# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import importlib

# The path contains a reserved keyword 'import', so we need a workaround here
acr_import = importlib.import_module('azure.cli.command_modules.acr.import')


class TestRegionalEndpointUriConversion(unittest.TestCase):

    def test_valid_regional_endpoint_conversion(self):
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


    def test_non_regional_endpoint_uris_unchanged(self):
        """Test that non-regional endpoint URIs are returned unchanged."""
        login_server_suffix = '.azurecr.io'

        # URIs that should remain unchanged
        test_cases = [
            'testregistry.azurecr.io',
            'external-registry.com',
            'testregistry.eastus.notgeo.azurecr.io',
        ]

        for uri in test_cases:
            result = acr_import._regional_endpoint_uri_to_login_server(uri, login_server_suffix)
            self.assertEqual(result, uri)

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
