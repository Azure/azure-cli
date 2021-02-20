# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import LiveScenarioTest
from azure.cli.core.azclierror import AuthenticationError
from time import sleep
from unittest import mock
import jwt


ARM_URL = "https://eastus2euap.management.azure.com/"  # ARM canary

class CAEScenarioTest(LiveScenarioTest):

    def test_revoke_session(self):
        with mock.patch.object(self.cli_ctx.cloud.endpoints, "resource_manager", ARM_URL):
            self.cmd('login')

            # Verify the token issued with CAE enabled
            out = self.cmd('account get-access-token').get_output_in_json()
            access_token = out['accessToken']
            decoded = jwt.decode(access_token, verify=False, algorithms=['RS256'])
            self.assertEqual(decoded['xms_cc'], ['CP1'])  # xms_cc: extension microsoft Client Capability
            self.assertEqual(decoded['xms_ssm'], '1')  # xms_ssm: extension microsoft Smart Session Management

            # Manaully revoke sign in sessions
            self.cmd('rest -m POST -u https://graph.microsoft.com/v1.0/me/revokeSignInSessions')

            exit_code = 0
            with self.assertRaises(AuthenticationError):
                while exit_code == 0:
                    sleep(5)
                    exit_code = self.cmd('storage account list').exit_code
