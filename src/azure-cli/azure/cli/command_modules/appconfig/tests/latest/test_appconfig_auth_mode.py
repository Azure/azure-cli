# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from azure.cli.testsdk import ScenarioTest
from azure.cli.core.azclierror import RequiredArgumentMissingError


class AppConfigAuthModeValidatorTests(ScenarioTest):

    def test_auth_mode(self):
        # Anonymous auth mode requires endpoint
        with self.assertRaisesRegex(RequiredArgumentMissingError, "App Configuration endpoint should be provided if auth mode is 'anonymous'."):
            self.cmd('appconfig kv list --auth-mode anonymous')

        # Anonymous auth mode doesn't support connection string
        with self.assertRaisesRegex(CLIError, "Auth mode 'anonymous' only supports the '--endpoint' argument. Connection string is not supported."):
            self.cmd('appconfig kv list --auth-mode anonymous --connection-string "Endpoint=https://example.azconfig.io;Id=test;Secret=test" --endpoint https://example.azconfig.io')

        # login auth mode with http endpoint should fail
        with self.assertRaisesRegex(CLIError, "HTTP endpoint is only supported when auth mode is 'anonymous'."):
            self.cmd('appconfig kv list --auth-mode login --endpoint http://localhost:8080')

        # key auth mode with http endpoint in connection string should fail
        with self.assertRaisesRegex(CLIError, "HTTP endpoint is only supported when auth mode is 'anonymous'."):
            self.cmd('appconfig kv list --auth-mode key --connection-string "Endpoint=http://localhost:8080;Id=test;Secret=test"')
