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
