# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from unittest import TestCase
from unittest.mock import Mock, patch

from knack.util import CLIError
from azure.cli.testsdk import ScenarioTest
from azure.cli.core.azclierror import AzureResponseError, InvalidArgumentValueError, RequiredArgumentMissingError, ResourceNotFoundError, ValidationError
from azure.cli.command_modules.appconfig._utils import get_appconfig_feature_flag_client, resolve_login_credential


class AppConfigClientErrorTests(TestCase):

    def test_feature_flag_client_invalid_arguments(self):
        for auth_mode in ('anonymous', 'key', 'login'):
            for exception_type in (ValueError, TypeError):
                with self.subTest(auth_mode=auth_mode, exception_type=exception_type):
                    error = exception_type('Invalid client configuration')
                    with patch('azure.cli.command_modules.appconfig._utils.FeatureFlagClient') as client_type, \
                            patch('azure.cli.command_modules.appconfig._utils.resolve_connection_string', return_value='connection'), \
                            patch('azure.cli.command_modules.appconfig._utils.resolve_login_credential', return_value=(Mock(), 'endpoint')):
                        client_type.side_effect = error
                        client_type.from_connection_string.side_effect = error
                        with self.assertRaisesRegex(InvalidArgumentValueError,
                                                    'Failed to initialize FeatureFlagClient.*Invalid client configuration'):
                            get_appconfig_feature_flag_client(Mock(), None, None, auth_mode, 'endpoint')

    def test_login_metadata_error_preserves_type_and_guidance(self):
        for error_type in (AzureResponseError, ResourceNotFoundError, ValidationError):
            with self.subTest(error_type=error_type):
                original = error_type('Store lookup failed', recommendation='Original recommendation')
                with patch('azure.cli.command_modules.appconfig._utils.resolve_store_metadata', side_effect=original):
                    with self.assertRaises(error_type) as error:
                        resolve_login_credential(Mock(), 'store', None)

                self.assertIs(error.exception, original)
                self.assertEqual(str(error.exception), 'Store lookup failed')
                self.assertIn('Original recommendation', error.exception.recommendations)
                self.assertIn('--endpoint', error.exception.recommendations[-1])

    def test_login_missing_endpoint_and_name(self):
        with self.assertRaisesRegex(RequiredArgumentMissingError, 'App Configuration endpoint or name should be provided') as error:
            resolve_login_credential(Mock(), None, None)

        self.assertIn('--endpoint', error.exception.recommendations[-1])


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
