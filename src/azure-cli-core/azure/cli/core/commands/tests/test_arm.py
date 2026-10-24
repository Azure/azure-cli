# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import unittest
from types import SimpleNamespace
from unittest import mock

from azure.core.exceptions import HttpResponseError
from azure.core.pipeline.transport import HttpRequest, RequestsTransportResponse
from knack.util import CLIError
from requests import Response

from azure.cli.core.azclierror import DeploymentError, InvalidTemplateError
from azure.cli.core.commands.arm import handle_template_based_exception


class TestTemplateBasedException(unittest.TestCase):

    @staticmethod
    def _sdk_error(error=None, message=None, consumed=True):
        response = Response()
        response.status_code = 400
        response.reason = 'Bad Request'
        response.headers['Content-Type'] = 'application/json'
        response._content = json.dumps({'error': error} if error else {}).encode('utf-8')
        transport_response = RequestsTransportResponse(
            HttpRequest('PUT', 'https://management.azure.com/deployments/test'), response)
        exception = HttpResponseError(response=transport_response, message=message)
        if consumed:
            # Match a streamed requests response whose body was read without caching it.
            response._content = False
            response._content_consumed = True
        return exception

    def test_template_exception_consumed_sku_error(self):
        message = (
            "The requested VM size Standard_B2s is currently not available in location eastus. "
            "Please try another size or deploy to a different location or different zone.")
        exception = self._sdk_error({'code': 'SkuNotAvailable', 'message': message})
        self.assertIsNone(exception.inner_exception)
        with self.assertRaisesRegex(RuntimeError, 'already consumed'):
            _ = exception.response.internal_response.text

        with self.assertRaises(DeploymentError) as raised:
            handle_template_based_exception(exception)
        self.assertEqual(str(raised.exception), exception.message)
        self.assertIn('SkuNotAvailable', str(raised.exception))
        self.assertIn(message, str(raised.exception))

    def test_template_exception_consumed_sku_errors_across_regions_and_sizes(self):
        for region in ('eastus', 'westeurope', 'northeurope'):
            for size in ('Standard_B2s', 'Standard_B2ms', 'Standard_D2s_v3',
                         'Standard_D2s_v5', 'Standard_B1s'):
                with self.subTest(region=region, size=size):
                    message = (
                        'The requested VM size {} is currently not available in location {}. '
                        'Please try another size or deploy to a different location or different zone.'
                    ).format(size, region)
                    exception = self._sdk_error({'code': 'SkuNotAvailable', 'message': message})
                    self.assertIsNone(exception.inner_exception)

                    with self.assertRaises(DeploymentError) as raised:
                        handle_template_based_exception(exception)
                    self.assertEqual(str(raised.exception), exception.message)
                    self.assertIn('SkuNotAvailable', str(raised.exception))
                    self.assertIn(message, str(raised.exception))

    def test_template_exception_consumed_quota_error(self):
        message = (
            'Operation could not be completed as it results in exceeding approved '
            'standardDSv5Family Cores quota. Location: eastus, Current Limit: 0, Current Usage: 0, '
            'Additional Required: 2. Please request a quota increase.')
        exception = self._sdk_error({'code': 'QuotaExceeded', 'message': message})

        with self.assertRaises(DeploymentError) as raised:
            handle_template_based_exception(exception)
        self.assertEqual(str(raised.exception), exception.message)
        self.assertIn('QuotaExceeded', str(raised.exception))
        self.assertIn(message, str(raised.exception))

    def test_template_exception_consumed_nested_error(self):
        message = 'At least one resource deployment operation failed.'
        detail_message = 'Allocation failed. Please retry later or use a different VM size.'
        exception = self._sdk_error({
            'code': 'DeploymentFailed',
            'message': message,
            'details': [{
                'code': 'ResourceDeploymentFailure',
                'message': 'The resource write operation failed.',
                'details': [{'code': 'AllocationFailed', 'message': detail_message}]
            }]
        })

        with self.assertRaises(DeploymentError) as raised:
            handle_template_based_exception(exception)
        self.assertEqual(str(raised.exception), exception.message)
        for expected in ('DeploymentFailed', message, 'ResourceDeploymentFailure',
                         'The resource write operation failed.', 'AllocationFailed', detail_message):
            self.assertIn(expected, str(raised.exception))

    def test_template_exception_consumed_invalid_template(self):
        message = 'The template deployment is not valid.'
        exception = self._sdk_error({'code': 'InvalidTemplateDeployment', 'message': message})

        with self.assertRaises(InvalidTemplateError) as raised:
            handle_template_based_exception(exception)
        self.assertIn('InvalidTemplateDeployment', str(raised.exception))
        self.assertIn(message, str(raised.exception))

    def test_template_exception_consumed_message_without_parsed_error(self):
        message = '(QuotaExceeded) Current Limit: 0, Current Usage: 0, Additional Required: 2.'
        exception = self._sdk_error(message=message)
        self.assertIsNone(exception.error)

        with self.assertRaises(DeploymentError) as raised:
            handle_template_based_exception(exception)
        self.assertEqual(str(raised.exception), message)

    def test_template_exception_sdk_error_without_response(self):
        message = 'Deployment failed before a response was available.'
        exception = HttpResponseError(message=message)

        with self.assertRaises(DeploymentError) as raised:
            handle_template_based_exception(exception)
        self.assertEqual(str(raised.exception), message)

    def test_template_exception_sdk_error_does_not_reread_response(self):
        exception = self._sdk_error({'code': 'SkuNotAvailable', 'message': 'Try another VM size.'})
        with mock.patch.object(exception.response, 'text', side_effect=AssertionError('Body reread')) as text:
            with self.assertRaises(DeploymentError) as raised:
                handle_template_based_exception(exception)
        text.assert_not_called()
        self.assertEqual(str(raised.exception), exception.message)

    def test_template_exception_unconsumed_error(self):
        message = 'The deployment conflicts with an existing operation.'
        exception = self._sdk_error({'code': 'Conflict', 'message': message}, consumed=False)

        with self.assertRaises(DeploymentError) as raised:
            handle_template_based_exception(exception)
        self.assertIn('Conflict', str(raised.exception))
        self.assertIn(message, str(raised.exception))

    def test_template_exception_inner_error_preserved(self):
        exception = self._sdk_error({'code': 'DeploymentFailed', 'message': 'Outer failure.'})
        exception.inner_exception = SimpleNamespace(error=SimpleNamespace(message='Inner failure.'))

        with self.assertRaises(CLIError) as raised:
            handle_template_based_exception(exception)
        self.assertIs(type(raised.exception), CLIError)
        self.assertEqual(str(raised.exception), 'Inner failure.')

    def test_template_exception_legacy_response_preserved(self):
        for code, error_type in [('DeploymentFailed', DeploymentError),
                                 ('InvalidTemplateDeployment', InvalidTemplateError)]:
            with self.subTest(code=code):
                exception = SimpleNamespace(
                    inner_exception=None,
                    error=SimpleNamespace(code=code),
                    response=SimpleNamespace(internal_response=SimpleNamespace(text='Original response body.')))

                with self.assertRaises(error_type) as raised:
                    handle_template_based_exception(exception)
                self.assertEqual(str(raised.exception), 'Original response body.')

    def test_template_exception_unrelated_error_preserved(self):
        exception = ValueError('Unrelated VM error.')

        with self.assertRaises(CLIError) as raised:
            handle_template_based_exception(exception)
        self.assertIs(type(raised.exception), CLIError)
        self.assertEqual(str(raised.exception), 'Unrelated VM error.')
