# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from time import sleep

import jwt
from azure.cli.core.azclierror import AuthenticationError
from azure.cli.testsdk import LiveScenarioTest
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
