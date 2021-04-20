# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from time import sleep

import jwt
from azure.cli.core.azclierror import AuthenticationError
from azure.cli.testsdk import LiveScenarioTest
from azure.cli.core.auth.util import decode_access_token
from msrestazure.azure_exceptions import CloudError

ARM_URL = "https://eastus2euap.management.azure.com/"  # ARM canary
ARM_RETRY_INTERVAL = 10


class CAEScenarioTest(LiveScenarioTest):

    def test_client_capabilities(self):
        self.cmd('login')

        # Verify the access token has CAE enabled
        out = self.cmd('account get-access-token').get_output_in_json()
        access_token = out['accessToken']
        decoded = jwt.decode(access_token, verify=False, algorithms=['RS256'])
        self.assertEqual(decoded['xms_cc'], ['CP1'])  # xms_cc: extension microsoft client capabilities
        self.assertEqual(decoded['xms_ssm'], '1')  # xms_ssm: extension microsoft smart session management

    def _test_revoke_session(self, command, expected_error, checks=None):
        self.test_client_capabilities()

        # Test access token is working
        self.cmd(command)

        self._revoke_sign_in_sessions()

        # CAE is currently only available in canary endpoint
        # with mock.patch.object(self.cli_ctx.cloud.endpoints, "resource_manager", ARM_URL):
        exit_code = 0
        with self.assertRaises(expected_error) as ex:
            while exit_code == 0:
                exit_code = self.cmd(command).exit_code
                sleep(ARM_RETRY_INTERVAL)
        if checks:
            checks(ex.exception)

    def test_revoke_session_track2(self):
        def check_aad_error_code(ex):
            self.assertIn('AADSTS50173', str(ex))

        self._test_revoke_session("storage account list", AuthenticationError, check_aad_error_code)

    def test_revoke_session_track1(self):
        def check_arm_error(ex):
            self.assertEqual(ex.status_code, 401)
            self.assertIsNotNone(ex.response.headers["WWW-Authenticate"])

        self._test_revoke_session('group list', CloudError, check_arm_error)

    def _revoke_sign_in_sessions(self):
        # Manually revoke sign in sessions
        self.cmd('rest -m POST -u https://graph.microsoft.com/v1.0/me/revokeSignInSessions')


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

        # endregion
