# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access

import unittest
from azure.cli.core.auth.util import scopes_to_resource, resource_to_scopes, _normalize_scopes, _generate_login_command


class TestUtil(unittest.TestCase):

    def test_scopes_to_resource(self):
        # scopes as a list
        self.assertEqual(scopes_to_resource(['https://management.core.windows.net//.default']),
                         'https://management.core.windows.net/')
        # scopes as a tuple
        self.assertEqual(scopes_to_resource(('https://storage.azure.com/.default',)),
                         'https://storage.azure.com')

        # resource with trailing slash
        self.assertEqual(scopes_to_resource(('https://management.azure.com//.default',)),
                         'https://management.azure.com/')
        self.assertEqual(scopes_to_resource(['https://datalake.azure.net//.default']),
                         'https://datalake.azure.net/')

        # resource without trailing slash
        self.assertEqual(scopes_to_resource(('https://managedhsm.azure.com/.default',)),
                         'https://managedhsm.azure.com')

        # VM SSH
        self.assertEqual(scopes_to_resource(["https://pas.windows.net/CheckMyAccess/Linux/.default"]),
                         'https://pas.windows.net/CheckMyAccess/Linux')
        self.assertEqual(scopes_to_resource(["https://pas.windows.net/CheckMyAccess/Linux/user_impersonation"]),
                         'https://pas.windows.net/CheckMyAccess/Linux')

    def test_resource_to_scopes(self):
        # resource converted to a scopes list
        self.assertEqual(resource_to_scopes('https://management.core.windows.net/'),
                         ['https://management.core.windows.net//.default'])

        # resource with trailing slash
        self.assertEqual(resource_to_scopes('https://management.azure.com/'),
                         ['https://management.azure.com//.default'])
        self.assertEqual(resource_to_scopes('https://datalake.azure.net/'),
                         ['https://datalake.azure.net//.default'])

        # resource without trailing slash
        self.assertEqual(resource_to_scopes('https://managedhsm.azure.com'),
                         ['https://managedhsm.azure.com/.default'])

    def test_normalize_scopes(self):
        # Test no scopes
        self.assertIsNone(_normalize_scopes(()))
        self.assertIsNone(_normalize_scopes([]))
        self.assertIsNone(_normalize_scopes(None))

        # Test multiple scopes, with the first one discarded
        scopes = _normalize_scopes(("https://management.core.windows.net//.default",
                                    "https://management.core.chinacloudapi.cn//.default"))
        self.assertEqual(list(scopes), ["https://management.core.chinacloudapi.cn//.default"])

        # Test single scopes (the correct usage)
        scopes = _normalize_scopes(("https://management.core.chinacloudapi.cn//.default",))
        self.assertEqual(list(scopes), ["https://management.core.chinacloudapi.cn//.default"])

    def test_generate_login_command(self):
        # No parameter is given
        assert _generate_login_command() == 'az login'

        # scopes
        actual = _generate_login_command(scopes=["https://management.core.windows.net//.default"])
        assert actual == 'az login --scope https://management.core.windows.net//.default'


if __name__ == '__main__':
    unittest.main()
