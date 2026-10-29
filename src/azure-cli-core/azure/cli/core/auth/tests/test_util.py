# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access

import unittest
from azure.cli.core.auth.util import (scopes_to_resource, resource_to_scopes, _generate_login_command,
                                      read_response_templates, WAM_ENABLEMENT_URL)


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

    def test_read_response_templates_without_wam_prompt(self):
        # By default, the WAM prompt is not included and the placeholder is removed.
        success_template, error_template = read_response_templates()
        assert '{{wam_prompt}}' not in success_template
        assert 'Web Account Manager (WAM)' not in success_template
        assert WAM_ENABLEMENT_URL not in success_template
        # error template is always returned
        assert '$error' in error_template

    def test_read_response_templates_with_wam_prompt(self):
        # When requested, the WAM prompt is injected with the enablement doc link.
        success_template, _ = read_response_templates(show_wam_prompt=True)
        assert '{{wam_prompt}}' not in success_template
        assert 'Web Account Manager (WAM)' in success_template
        assert WAM_ENABLEMENT_URL in success_template


if __name__ == '__main__':
    unittest.main()
