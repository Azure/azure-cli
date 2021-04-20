# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access

import unittest
from ..util import _extract_claims, scopes_to_resource, resource_to_scopes


class TestUtil(unittest.TestCase):

    def test_extract_claims(self):
        challenge = 'Bearer ' \
                    'authorization_uri="https://login.windows.net/54826b22-38d6-4fb2-bad9-b7b93a3e9c5a", ' \
                    'error="invalid_token", ' \
                    'error_description="User session has been revoked", ' \
                    'claims="eyJhY2Nlc3NfdG9rZW4iOnsibmJmIjp7ImVzc2VudGlhbCI6dHJ1ZSwgInZhbHVlIjoiMTYxODgyNjE0OSJ9fX0="'
        expected = 'eyJhY2Nlc3NfdG9rZW4iOnsibmJmIjp7ImVzc2VudGlhbCI6dHJ1ZSwgInZhbHVlIjoiMTYxODgyNjE0OSJ9fX0='
        result = _extract_claims(challenge)
        assert expected == result

        # Multiple www-authenticate headers
        result = _extract_claims(', '.join((challenge, challenge)))
        assert result is None

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


if __name__ == '__main__':
    unittest.main()
