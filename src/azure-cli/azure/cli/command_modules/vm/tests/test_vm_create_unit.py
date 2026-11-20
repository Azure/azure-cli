# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import json
import os
import tempfile
import unittest
from unittest import mock

from azure.core.exceptions import HttpResponseError
from azure.core.pipeline.transport import HttpRequest, RequestsTransportResponse
from requests import Response

from azure.cli.core.azclierror import DeploymentError, InvalidTemplateError, logger as error_logger
from azure.cli.core.commands.arm import handle_template_based_exception
from azure.cli.core.mock import DummyCli


class VMCreateDispatchUnitTest(unittest.TestCase):

    def test_vm_create_consumed_response_error(self):
        errors = [
            ('SkuNotAvailable', 'Standard_B2s is unavailable in eastus. Try another size or zone.',
             DeploymentError),
            ('QuotaExceeded', 'standardDSv5Family: Current Limit: 0, Current Usage: 0, Additional Required: 2.',
             DeploymentError),
            ('InvalidTemplateDeployment', 'The template deployment is not valid.',
             InvalidTemplateError),
        ]
        for code, message, error_type in errors:
            with self.subTest(code=code):
                response = Response()
                response.status_code = 400
                response.reason = 'Bad Request'
                response.headers['Content-Type'] = 'application/json'
                response._content = json.dumps({'error': {'code': code, 'message': message}}).encode('utf-8')
                exception = HttpResponseError(response=RequestsTransportResponse(
                    HttpRequest('PUT', 'https://management.azure.com/deployments/test'), response))
                response._content = False
                response._content_consumed = True
                self.assertIsNone(exception.inner_exception)
                with self.assertRaisesRegex(RuntimeError, 'already consumed'):
                    _ = response.text

                with tempfile.TemporaryDirectory() as config_dir:
                    with mock.patch.dict(os.environ, {
                        'AZURE_CONFIG_DIR': config_dir,
                        'AZURE_CORE_COLLECT_TELEMETRY': 'false',
                    }):
                        cli = DummyCli()
                        cli.config.set_value('core', 'collect_telemetry', 'false')
                        stdout = io.StringIO()
                        with mock.patch('azure.cli.command_modules.vm.commands.process_vm_create_namespace'):
                            with mock.patch('azure.cli.command_modules.vm.custom.create_vm',
                                            autospec=True, side_effect=exception) as create_vm:
                                with mock.patch('azure.cli.core.azclierror.AzCLIError.send_telemetry'):
                                    with self.assertLogs(error_logger, level='WARNING') as logs:
                                        exit_code = cli.invoke(
                                            ['vm', 'create', '-g', 'testgroup', '-n', 'testvm'],
                                            out_file=stdout)

                create_vm.assert_called_once()
                self.assertIs(cli.invocation.commands_loader.command_table['vm create'].exception_handler,
                              handle_template_based_exception)
                self.assertEqual(exit_code, 1)
                self.assertEqual(stdout.getvalue(), '')
                self.assertIsNone(cli.result.result)
                self.assertIs(type(cli.result.error), error_type)
                self.assertEqual(str(cli.result.error), exception.message)
                output = '\n'.join(logs.output)
                self.assertIn(code, output)
                self.assertIn(message, output)
                for internal_error in ('Traceback', 'RuntimeError', 'already consumed', 'NoneType'):
                    self.assertNotIn(internal_error, output)
