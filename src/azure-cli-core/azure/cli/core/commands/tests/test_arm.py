# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from io import BytesIO
import json
from types import SimpleNamespace
import unittest
from unittest import mock

from azure.core.exceptions import (
    DecodeError, HttpResponseError, ODataV4Format, ResponseNotReadError, ServiceRequestError, ServiceResponseError,
    StreamClosedError, StreamConsumedError as AzureStreamConsumedError)
from azure.core.pipeline import PipelineContext, PipelineResponse
from azure.core.pipeline.transport import HttpRequest, RequestsTransportResponse
from azure.core.polling import LROPoller, PollingMethod
from azure.core.polling.base_polling import LROBasePolling
from knack.util import CLIError
from requests import Response
from requests.exceptions import ChunkedEncodingError, ContentDecodingError, HTTPError, StreamConsumedError

from azure.cli.core.azclierror import DeploymentError, InvalidTemplateError
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.commands.arm import handle_template_based_exception


ERROR_MESSAGES = {
    'SkuNotAvailable': 'The requested VM size Standard_D2s_v3 is not available in eastus.',
    'QuotaExceeded': 'The deployment exceeds the approved regional core quota. Request a quota increase.'
}


class TestTemplateBasedException(unittest.TestCase):

    @staticmethod
    def _error_body(code, deployment_code='DeploymentFailed'):
        return {
            'error': {
                'code': deployment_code,
                'message': 'The deployment could not be completed.',
                'target': 'test-deployment',
                'details': [
                    {
                        'code': 'ResourceDeploymentFailure',
                        'message': 'The virtual machine could not be provisioned.',
                        'target': 'test-vm',
                        'details': [{'code': code, 'message': ERROR_MESSAGES[code], 'target': 'vmSize'}]
                    },
                    {'code': 'AdditionalFailure', 'message': 'Review all failed deployment operations.'}
                ],
                'innererror': {'requestId': 'offline-request-id'}
            }
        }

    @staticmethod
    def _response(body, status_code=400):
        response = Response()
        response.status_code = status_code
        response.reason = 'Bad Request' if status_code >= 400 else 'OK'
        response.encoding = 'utf-8'
        response.headers['content-type'] = 'application/json'
        response.raw = BytesIO(body.encode('utf-8'))
        request = HttpRequest('PUT', 'https://management.azure.invalid/deployments/test')
        return RequestsTransportResponse(request, response)

    def _consumed_error(self, code, parsed=True, deployment_code='DeploymentFailed'):
        response = self._response(json.dumps(self._error_body(code, deployment_code)))
        content = b''.join(response.internal_response.iter_content(chunk_size=32))
        with self.assertRaisesRegex(RuntimeError, 'The content for this response was already consumed'):
            _ = response.internal_response.text

        # SDKs can retain a parsed error or its message after a response stream has been consumed.
        parsed_error = ODataV4Format(json.loads(content))
        error = HttpResponseError(message=str(parsed_error), response=response)
        self.assertIsNone(error.error)
        if parsed:
            error.error = parsed_error
        return error

    def _handle(self, error, error_type=DeploymentError):
        with self.assertRaises(error_type) as caught:
            handle_template_based_exception(error)
        self.assertIs(type(caught.exception), error_type)
        return caught.exception

    def _assert_service_details(self, message, code):
        for detail in (
                code, ERROR_MESSAGES[code], 'The deployment could not be completed.',
                'test-deployment', 'ResourceDeploymentFailure', 'test-vm', 'vmSize',
                'AdditionalFailure', 'Review all failed deployment operations.', 'offline-request-id'):
            self.assertIn(detail, message)
        self.assertNotIn('The content for this response was already consumed', message)

    @staticmethod
    def _run_cli_poller(poller):
        cli_ctx = mock.Mock()
        cli_ctx.config.getboolean.return_value = True
        cli_ctx.only_show_errors = True
        cli_ctx.data = {'command': 'vm create'}
        with mock.patch('azure.cli.core.commands.telemetry.poll_start'), \
                mock.patch('azure.cli.core.commands.telemetry.poll_end'):
            return LongRunningOperation(cli_ctx, poller_done_interval_ms=1)(poller)

    def _sdk_polling_error(self, error_body):
        initial_response = self._response('{"status": "InProgress"}', status_code=202)
        initial_response.headers['operation-location'] = 'https://management.azure.invalid/operations/test'
        initial = PipelineResponse(initial_response.request, initial_response, PipelineContext(None))
        response = self._response(json.dumps(dict(error_body, status='Failed')), status_code=200)
        failed = PipelineResponse(response.request, response, PipelineContext(None))
        polling = LROBasePolling(timeout=0)
        with mock.patch.object(polling, 'request_status', return_value=failed) as request_status:
            poller = LROPoller(None, initial, lambda result: result, polling)
            with self.assertRaises(HttpResponseError) as caught:
                self._run_cli_poller(poller)
        self.assertTrue(poller.done())
        request_status.assert_called_once_with('https://management.azure.invalid/operations/test')
        self.assertIs(caught.exception.response, response)
        return caught.exception

    def test_template_error_readable_response_with_parsed_data(self):
        for code in ERROR_MESSAGES:
            with self.subTest(code=code):
                body = json.dumps(self._error_body(code))
                error = HttpResponseError(response=self._response(body))
                with mock.patch.object(error.response.internal_response.raw, 'read',
                                       side_effect=AssertionError('Do not reread the response stream')) as read:
                    message = self._handle(error).error_msg
                read.assert_not_called()
                self.assertEqual(body, message)
                self._assert_service_details(message, code)

    def test_template_error_consumed_response_with_parsed_data(self):
        for code in ERROR_MESSAGES:
            with self.subTest(code=code):
                error = self._consumed_error(code)
                error.message = 'Operation failed.'
                with mock.patch.object(error.response, 'text', wraps=error.response.text) as read:
                    message = self._handle(error).error_msg
                read.assert_called_once()
                self.assertEqual(str(error.error), message)
                self._assert_service_details(message, code)

    def test_template_error_consumed_response_with_cached_message(self):
        for code in ERROR_MESSAGES:
            with self.subTest(code=code):
                error = self._consumed_error(code, parsed=False)
                with mock.patch.object(HttpResponseError, '__str__', side_effect=AssertionError('Do not reread')):
                    message = self._handle(error).error_msg
                self.assertEqual(error.message, message)
                self._assert_service_details(message, code)

    def test_template_error_consumed_top_level_service_error(self):
        for code in ERROR_MESSAGES:
            for parsed in (False, True):
                with self.subTest(code=code, parsed=parsed):
                    body = {'error': {'code': code, 'message': ERROR_MESSAGES[code]}}
                    response = self._response(json.dumps(body))
                    content = b''.join(response.internal_response.iter_content(chunk_size=32))
                    service_error = ODataV4Format(json.loads(content))
                    error = HttpResponseError(message=str(service_error), response=response)
                    if parsed:
                        error.error = service_error
                    message = self._handle(error).error_msg
                    self.assertIn(code, message)
                    self.assertIn(ERROR_MESSAGES[code], message)
                    self.assertNotIn('already consumed', message)

    def test_template_error_invalid_template_classification(self):
        for code in ERROR_MESSAGES:
            for consumed in (False, True):
                with self.subTest(code=code, consumed=consumed):
                    if consumed:
                        error = self._consumed_error(code, deployment_code='InvalidTemplateDeployment')
                    else:
                        body = self._error_body(code, 'InvalidTemplateDeployment')
                        error = HttpResponseError(response=self._response(json.dumps(body)))
                    message = self._handle(error, InvalidTemplateError).error_msg
                    self.assertIn('InvalidTemplateDeployment', message)
                    self._assert_service_details(message, code)

    def test_template_error_readable_body_preserves_all_details(self):
        for code in ERROR_MESSAGES:
            with self.subTest(code=code):
                body = json.dumps({'diagnostics': self._error_body(code), 'padding': 'x' * 4096,
                                   'lastDetail': 'Do not truncate this final diagnostic.'})
                error = HttpResponseError(message='Original summary', response=self._response(body))
                self.assertIsNone(error.error)
                message = self._handle(error).error_msg
                self.assertEqual(body, message)
                self._assert_service_details(message, code)

    def test_template_error_malformed_body_is_preserved(self):
        for body in ('{"error":', '<html>QuotaExceeded: request a quota increase.</html>', 'SkuNotAvailable'):
            with self.subTest(body=body):
                error = HttpResponseError(message='Original summary', response=self._response(body))
                self.assertIsNone(error.error)
                self.assertEqual(body, self._handle(error).error_msg)

    def test_template_error_empty_body_uses_original_message(self):
        for code in ERROR_MESSAGES:
            with self.subTest(code=code):
                message = '{}: {}'.format(code, ERROR_MESSAGES[code])
                error = HttpResponseError(message=message, response=self._response(''))
                self.assertEqual(message, self._handle(error).error_msg)

    def test_template_error_missing_or_none_error(self):
        for missing in (False, True):
            with self.subTest(missing=missing):
                body = json.dumps(self._error_body('QuotaExceeded'))
                error = HttpResponseError(response=self._response(body))
                if missing:
                    del error.error
                else:
                    error.error = None
                self.assertEqual(body, self._handle(error).error_msg)

    def test_template_error_missing_or_none_response(self):
        for missing_response in (False, True):
            for missing_error in (False, True):
                with self.subTest(missing_response=missing_response, missing_error=missing_error):
                    error = HttpResponseError(message='Original deployment failure', response=None)
                    if missing_response:
                        del error.response
                    if missing_error:
                        del error.error
                    caught = self._handle(error, CLIError)
                    self.assertIs(caught.args[0], error)
                    self.assertEqual(error.message, str(caught))

    def test_template_error_no_response_preserves_parsed_details(self):
        error = HttpResponseError(response=self._response(json.dumps(self._error_body('QuotaExceeded'))))
        error.response = None
        caught = self._handle(error, CLIError)
        self.assertIs(caught.args[0], error)
        self._assert_service_details(str(caught), 'QuotaExceeded')

    def test_template_error_service_request_failure_before_response(self):
        error = ServiceRequestError('Unable to connect to the deployment service.')
        caught = self._handle(error, CLIError)
        self.assertIs(caught.args[0], error)
        self.assertEqual(error.message, str(caught))

    def test_template_error_service_response_failure_without_response(self):
        error = ServiceResponseError('The service connection closed before a response was received.')
        caught = self._handle(error, CLIError)
        self.assertIs(caught.args[0], error)
        self.assertEqual(error.message, str(caught))

    def test_template_error_original_unrelated_runtime_error(self):
        for response_present in (False, True):
            with self.subTest(response_present=response_present):
                error = RuntimeError('Unexpected deployment client state.')
                if response_present:
                    error.response = None
                caught = self._handle(error, CLIError)
                self.assertIs(caught.args[0], error)
                self.assertEqual('Unexpected deployment client state.', str(caught))

    def test_template_error_falsey_requests_response(self):
        body = json.dumps(self._error_body('SkuNotAvailable'))
        response = self._response(body).internal_response
        self.assertFalse(response)
        error = HTTPError('Bad Request', response=response)
        self.assertEqual(body, self._handle(error).error_msg)

    def test_template_error_consumed_requests_response_without_message_attribute(self):
        for code in ERROR_MESSAGES:
            with self.subTest(code=code):
                response = self._response(json.dumps(self._error_body(code))).internal_response
                list(response.iter_content(chunk_size=32))
                message = '{}: {}'.format(code, ERROR_MESSAGES[code])
                error = HTTPError(message, response=response)
                self.assertEqual(message, self._handle(error).error_msg)

    def test_template_error_missing_or_none_internal_response(self):
        for missing in (False, True):
            with self.subTest(missing=missing):
                response = self._response('')
                if missing:
                    del response.internal_response
                else:
                    response.internal_response = None
                error = HttpResponseError(message='Original deployment failure', response=response)
                self.assertEqual(error.message, self._handle(error).error_msg)

    def test_template_error_legacy_response_wrapper_and_error_model(self):
        body = json.dumps(self._error_body('SkuNotAvailable', 'InvalidTemplateDeployment'))
        error = Exception('Original deployment failure')
        error.response = SimpleNamespace(internal_response=self._response(body).internal_response)
        error.error = SimpleNamespace(code='InvalidTemplateDeployment', message='Legacy error model')
        self.assertEqual(body, self._handle(error, InvalidTemplateError).error_msg)

    def test_template_error_optional_body_read_failures(self):
        response = self._response('')
        failures = (
            ServiceRequestError('Connection failed while reading'),
            ServiceResponseError('Connection closed while reading'),
            DecodeError('Unable to decode response'),
            ResponseNotReadError(response),
            StreamClosedError(response),
            AzureStreamConsumedError(response),
            OSError('Response stream is unavailable'),
            ChunkedEncodingError('Incomplete response body'),
            ContentDecodingError('Invalid compressed response'),
            StreamConsumedError('Response stream already consumed'),
            UnicodeDecodeError('utf-8', b'\xff', 0, 1, 'invalid start byte'),
            ValueError('I/O operation on closed file')
        )
        for code in ERROR_MESSAGES:
            for failure in failures:
                with self.subTest(code=code, failure=type(failure).__name__):
                    response = self._response('unreadable')
                    message = '{}: {}'.format(code, ERROR_MESSAGES[code])
                    with mock.patch.object(response.internal_response.raw, 'read', side_effect=failure) as read:
                        error = HttpResponseError(message=message, response=response)
                        read.reset_mock()
                        self.assertEqual(message, self._handle(error).error_msg)
                        read.assert_called_once()

    def test_template_error_unexpected_formatter_failure_is_not_swallowed(self):
        error = self._consumed_error('SkuNotAvailable')
        failure = RuntimeError('Unexpected SDK formatter failure')
        with mock.patch.object(ODataV4Format, '__str__', side_effect=failure):
            with self.assertRaises(RuntimeError) as caught:
                handle_template_based_exception(error)
        self.assertIs(caught.exception, failure)

    def test_template_error_unexpected_body_failure_is_not_swallowed(self):
        error = HttpResponseError(message='Original failure', response=self._response('not JSON'))
        failure = TypeError('Unexpected transport programming error')
        with mock.patch.object(error.response, 'text', side_effect=failure):
            with self.assertRaises(TypeError) as caught:
                handle_template_based_exception(error)
        self.assertIs(caught.exception, failure)

    def test_template_error_legacy_inner_exception(self):
        for code in ERROR_MESSAGES:
            with self.subTest(code=code):
                body = json.dumps({'error': {'code': code, 'message': ERROR_MESSAGES[code]}})
                inner = HttpResponseError(response=self._response(body))
                response = self._consumed_error(code).response
                error = HttpResponseError(message='Outer failure', response=response, error=inner)
                caught = self._handle(error, CLIError)
                self.assertEqual(ERROR_MESSAGES[code], str(caught))

    def test_template_error_incomplete_legacy_inner_exception(self):
        for inner in (None, ValueError('Inner failure'), HttpResponseError(message='No parsed inner error')):
            with self.subTest(inner=type(inner).__name__):
                body = 'SkuNotAvailable: the requested VM size is not available.'
                error = HttpResponseError(message='Outer failure', response=self._response(body), error=inner)
                self.assertEqual(body, self._handle(error).error_msg)

    def test_template_error_initial_deployment_creation_failure(self):
        for code in ERROR_MESSAGES:
            with self.subTest(code=code):
                response = self._response(json.dumps(self._error_body(code, 'InvalidTemplateDeployment')))
                initial = PipelineResponse(response.request, response, PipelineContext(None))
                with self.assertRaises(HttpResponseError) as caught:
                    LROPoller(None, initial, lambda result: result, LROBasePolling(timeout=0))
                self.assertIs(caught.exception.response, response)
                message = self._handle(caught.exception, InvalidTemplateError).error_msg
                self._assert_service_details(message, code)

    def test_template_error_sdk_polling_failure_through_cli(self):
        for code in ERROR_MESSAGES:
            with self.subTest(code=code):
                error = self._sdk_polling_error(self._error_body(code))
                message = self._handle(error).error_msg
                self._assert_service_details(message, code)

    def test_template_error_sdk_polling_preserves_unmodeled_arm_diagnostics(self):
        assignment_id = '/providers/Microsoft.Authorization/policyAssignments/require-cost-center'
        body = self._error_body('SkuNotAvailable')
        body['error']['details'][0]['details'].append({
            'code': 'RequestDisallowedByPolicy',
            'message': 'The virtual machine was disallowed by policy.',
            'additionalInfo': [{
                'type': 'PolicyViolation',
                'info': {
                    'policyAssignmentId': assignment_id,
                    'evaluationDetails': {
                        'evaluatedExpressions': [{
                            'expression': 'tags[CostCenter]',
                            'operator': 'Exists',
                            'targetValue': 'true',
                            'result': 'False'
                        }]
                    }
                }
            }]
        })
        error = self._sdk_polling_error(body)
        self.assertIs(type(error.error), ODataV4Format)
        self.assertNotIn(assignment_id, str(error.error))
        message = self._handle(error).error_msg
        self.assertEqual(error.response.internal_response.text, message)
        self._assert_service_details(message, 'SkuNotAvailable')
        for detail in ('RequestDisallowedByPolicy', 'PolicyViolation', assignment_id, 'tags[CostCenter]'):
            self.assertIn(detail, message)

    def test_template_error_consumed_sdk_poller_failure_through_cli(self):
        for code in ERROR_MESSAGES:
            for parsed in (False, True):
                with self.subTest(code=code, parsed=parsed):
                    error = self._consumed_error(code, parsed=parsed)
                    polling = mock.Mock(spec=PollingMethod)
                    polling.finished.return_value = False
                    polling.run.side_effect = error
                    polling.get_continuation_token.return_value = 'offline-continuation-token'
                    poller = LROPoller(None, error.response, lambda result: result, polling)
                    with self.assertRaises(HttpResponseError) as caught:
                        self._run_cli_poller(poller)
                    self.assertTrue(poller.done())
                    self.assertIs(caught.exception, error)
                    message = self._handle(caught.exception).error_msg
                    self.assertEqual(error.message, message)
                    self._assert_service_details(message, code)


if __name__ == '__main__':
    unittest.main()
