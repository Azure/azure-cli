# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access

import base64
import unittest
from azure.cli.core.auth.util import (scopes_to_resource, resource_to_scopes, _generate_login_command,
                                      parse_claims_challenge)


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

    def test_generate_login_command(self):
        # No parameter is given
        assert _generate_login_command() == 'az login'

        # tenant
        actual = _generate_login_command(tenant='21987a97-4e85-47c5-9a13-9dc3e11b2a9a')
        assert actual == 'az login --tenant "21987a97-4e85-47c5-9a13-9dc3e11b2a9a"'

        # scope
        actual = _generate_login_command(scopes=["https://management.core.windows.net//.default"])
        assert actual == 'az login --scope "https://management.core.windows.net//.default"'

        # tenant and scopes
        actual = _generate_login_command(tenant='21987a97-4e85-47c5-9a13-9dc3e11b2a9a',
                                         scopes=["https://management.core.windows.net//.default"])
        assert actual == ('az login --tenant "21987a97-4e85-47c5-9a13-9dc3e11b2a9a" '
                          '--scope "https://management.core.windows.net//.default"')

        # tenant, scopes and claims_challenge
        actual = _generate_login_command(
            tenant='21987a97-4e85-47c5-9a13-9dc3e11b2a9a',
            scopes=["https://management.core.windows.net//.default"],
            claims_challenge='{"access_token":{"acrs":{"essential":true,"values":["p1"]}}}')
        assert actual == ('az logout\n'
                          'az login --tenant "21987a97-4e85-47c5-9a13-9dc3e11b2a9a" '
                          '--scope "https://management.core.windows.net//.default" '
                          '--claims-challenge "eyJhY2Nlc3NfdG9rZW4iOnsiYWNycyI6eyJlc3NlbnRpYWwiOnRydWUsInZhbHVlcyI6WyJwMSJdfX19"')

    def test_parse_claims_challenge(self):
        claims = '{"access_token":{"nbf":{"essential":true,"value":"1603742800"}}}'
        # Microsoft Graph sends the claims without base64 padding
        encoded_claims = base64.urlsafe_b64encode(claims.encode()).decode().rstrip('=')
        challenge = ('Bearer realm="", authorization_uri="https://login.microsoftonline.com/common/oauth2/authorize", '
                     'error="insufficient_claims", claims="{}"'.format(encoded_claims))
        self.assertEqual(parse_claims_challenge(challenge), claims)

        # No claims
        self.assertIsNone(parse_claims_challenge('Bearer error="invalid_token"'))
        self.assertIsNone(parse_claims_challenge(''))
        # Multiple claims
        self.assertIsNone(parse_claims_challenge('Bearer claims="{0}", Bearer claims="{0}"'.format(encoded_claims)))
        # Claims which are not valid UTF-8 after decoding
        self.assertIsNone(parse_claims_challenge('Bearer claims="_w"'))


if __name__ == '__main__':
    unittest.main()
