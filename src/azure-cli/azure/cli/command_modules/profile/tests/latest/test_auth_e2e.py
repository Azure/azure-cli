# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.auth.util import decode_access_token
from azure.cli.core.azclierror import AuthenticationError
from azure.cli.testsdk import LiveScenarioTest

ARM_URL = "https://eastus2euap.management.azure.com/"  # ARM canary
ARM_MAX_RETRY = 30
ARM_RETRY_INTERVAL = 10


class ConditionalAccessScenarioTest(LiveScenarioTest):

    def setUp(self):
        super().setUp()
        # Clear MSAL cache to avoid unexpected tokens from cache
        self.cmd('az account clear')

    def test_conditional_access_mfa(self):
        """
        This test should be run using a user account that
          - doesn't require MFA for ARM
          - requires MFA for data-plane resource

        The result ATs are checked per
          Microsoft identity platform access tokens
          https://docs.microsoft.com/en-us/azure/active-directory/develop/access-tokens

        Following claims are checked:
          - aud (Audience): https://tools.ietf.org/html/rfc7519#section-4.1.3
          - amr (Authentication Method Reference): https://tools.ietf.org/html/rfc8176
        """

        scope = 'https://pas.windows.net/CheckMyAccess/Linux/.default'
        self.kwargs['scope'] = scope

        # region non-MFA session

        # Login to ARM (MFA not required)
        # In the browser, if the user already exists, make sure to logout first and re-login to clear browser cache
        self.cmd('az login')

        # Getting ARM AT and check claims
        result = self.cmd('az account get-access-token').get_output_in_json()
        decoded = decode_access_token(result['accessToken'])
        assert decoded['aud'] == self.cli_ctx.cloud.endpoints.active_directory_resource_id
        assert decoded['amr'] == ['pwd']

        # Getting data-plane AT with ARM RT (step-up) fails
        with self.assertRaises(AuthenticationError) as cm:
            self.cmd('az account get-access-token --scope {scope}')

        # Check re-login recommendation
        re_login_command = 'az login --scope {scope}'.format(**self.kwargs)
        assert 'AADSTS50076' in cm.exception.error_msg
        assert re_login_command in cm.exception.recommendations[0]

        # endregion

        # region MFA session

        # Re-login with data-plane scope (MFA required)
        # Getting ARM AT with data-plane RT (step-down) succeeds
        self.cmd(re_login_command)

        # Getting ARM AT and check claims
        result = self.cmd('az account get-access-token').get_output_in_json()
        decoded = decode_access_token(result['accessToken'])
        assert decoded['aud'] == self.cli_ctx.cloud.endpoints.active_directory_resource_id
        assert decoded['amr'] == ['pwd']

        # Getting data-plane AT and check claims
        result = self.cmd('az account get-access-token --scope {scope}').get_output_in_json()
        decoded = decode_access_token(result['accessToken'])
        assert decoded['aud'] in scope
        assert decoded['amr'] == ['pwd', 'mfa']

        self.cmd('logout')
        # endregion
