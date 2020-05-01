# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from collections import namedtuple
import os
import sys
import unittest
import mock
import tempfile
import json

from azure.cli.core.util import \
    (get_file_json, truncate_text, shell_safe_json_parse, b64_to_hex, hash_string, random_string,
     open_page_in_browser, can_launch_browser, handle_exception, ConfiguredDefaultSetter, send_raw_request,
     should_disable_connection_verify, parse_proxy_resource_id, get_az_user_agent)
from azure.cli.core.mock import DummyCli


class TestUtils(unittest.TestCase):

    def test_load_json_from_file(self):
        _, pathname = tempfile.mkstemp()

        # test good case
        with open(pathname, 'w') as good_file:
            good_file.write('{"key1":"value1", "key2":"value2"}')
        result = get_file_json(pathname)
        self.assertEqual('value2', result['key2'])

        # test error case
        with open(pathname, 'w') as bad_file:
            try:
                bad_file.write('{"key1":"value1" "key2":"value2"}')
                get_file_json(pathname)
                self.fail('expect throw on reading from badly formatted file')
            except Exception as ex:  # pylint: disable=broad-except
                self.assertTrue(str(ex).find(
                    'contains error: Expecting value: line 1 column 1 (char 0)'))

    def test_truncate_text(self):
        expected = 'stri [...]'
        actual = truncate_text('string to shorten', width=10)
        self.assertEqual(expected, actual)

    def test_truncate_text_not_needed(self):
        expected = 'string to shorten'
        actual = truncate_text('string to shorten', width=100)
        self.assertEqual(expected, actual)

    def test_truncate_text_zero_width(self):
        with self.assertRaises(ValueError):
            truncate_text('string to shorten', width=0)

    def test_truncate_text_negative_width(self):
        with self.assertRaises(ValueError):
            truncate_text('string to shorten', width=-1)

    def test_shell_safe_json_parse(self):
        dict_obj = {'a': 'b & c'}
        list_obj = [{'a': 'b & c'}]
        failed_strings = []

        valid_dict_strings = [
            '{"a": "b & c"}',
            "{'a': 'b & c'}",
            "{\"a\": \"b & c\"}"
        ]
        for string in valid_dict_strings:
            actual = shell_safe_json_parse(string)
            try:
                self.assertEqual(actual, dict_obj)
            except AssertionError:
                failed_strings.append(string)

        valid_list_strings = [
            '[{"a": "b & c"}]',
            "[{'a': 'b & c'}]",
            "[{\"a\": \"b & c\"}]"
        ]
        for string in valid_list_strings:
            actual = shell_safe_json_parse(string)
            try:
                self.assertEqual(actual, list_obj)
            except AssertionError:
                failed_strings.append(string)

        self.assertEqual(
            len(failed_strings), 0,
            'The following patterns failed: {}'.format(failed_strings))

    def test_hash_string(self):
        def _run_test(length, force_lower):
            import random
            # test a bunch of random strings for collisions
            test_values = []
            for x in range(100):
                rand_len = random.randint(50, 100)
                test_values.append(random_string(rand_len))

            # test each value against eachother to verify hashing properties
            equal_count = 0
            for val1 in test_values:
                result1 = hash_string(val1, length, force_lower)

                # test against the remaining values and against itself, but not those which have
                # come before...
                test_values2 = test_values[test_values.index(val1):]
                for val2 in test_values2:
                    result2 = hash_string(val2, length, force_lower)
                    if val1 == val2:
                        self.assertEqual(result1, result2)
                        equal_count += 1
                    else:
                        self.assertNotEqual(result1, result2)
            self.assertEqual(equal_count, len(test_values))

        # Test digest replication
        _run_test(100, False)

        # Test force_lower
        _run_test(16, True)

    def test_proxy_resource_parse(self):
        mock_proxy_resource_id = "/subscriptions/0000/resourceGroups/clirg/" \
                                 "providers/Microsoft.Network/privateEndpoints/cli/" \
                                 "privateLinkServiceConnections/cliPec/privateLinkServiceConnectionsSubTypes/cliPecSubName"
        result = parse_proxy_resource_id(mock_proxy_resource_id)
        valid_dict_values = {
            'subscription': '0000',
            'resource_group': 'clirg',
            'namespace': 'Microsoft.Network',
            'type': 'privateEndpoints',
            'name': 'cli',
            'child_type_1': 'privateLinkServiceConnections',
            'child_name_1': 'cliPec',
            'child_type_2': 'privateLinkServiceConnectionsSubTypes',
            'child_name_2': 'cliPecSubName',
            'last_child_num': 2
        }
        self.assertEqual(len(result.keys()), len(valid_dict_values.keys()))
        for key, value in valid_dict_values.items():
            self.assertEqual(result[key], value)

        invalid_proxy_resource_id = "invalidProxyResourceID"
        result = parse_proxy_resource_id(invalid_proxy_resource_id)
        self.assertIsNone(result)

    @mock.patch('webbrowser.open', autospec=True)
    @mock.patch('subprocess.Popen', autospec=True)
    def test_open_page_in_browser(self, sunprocess_open_mock, webbrowser_open_mock):
        platform = sys.platform.lower()
        open_page_in_browser('http://foo')
        if platform == 'darwin':
            sunprocess_open_mock.assert_called_once_with(['open', 'http://foo'])
        else:
            webbrowser_open_mock.assert_called_once_with('http://foo', 2)

    @mock.patch('azure.cli.core.util._get_platform_info', autospec=True)
    @mock.patch('webbrowser.get', autospec=True)
    def test_can_launch_browser(self, webbrowser_get_mock, get_platform_mock):
        # WSL is always fine
        get_platform_mock.return_value = ('linux', '4.4.0-17134-microsoft')
        result = can_launch_browser()
        self.assertTrue(result)

        # windows is always fine
        get_platform_mock.return_value = ('windows', '10')
        result = can_launch_browser()
        self.assertTrue(result)

        # osx is always fine
        get_platform_mock.return_value = ('darwin', '10')
        result = can_launch_browser()
        self.assertTrue(result)

        # now tests linux
        with mock.patch('os.environ', autospec=True) as env_mock:
            # when no GUI, return false
            get_platform_mock.return_value = ('linux', '4.15.0-1014-azure')
            env_mock.get.return_value = None
            result = can_launch_browser()
            self.assertFalse(result)

            # when there is gui, and browser is a good one, return True
            browser_mock = mock.MagicMock()
            browser_mock.name = 'goodone'
            env_mock.get.return_value = 'foo'
            result = can_launch_browser()
            self.assertTrue(result)

            # when there is gui, but the browser is text mode, return False
            browser_mock = mock.MagicMock()
            browser_mock.name = 'www-browser'
            webbrowser_get_mock.return_value = browser_mock
            env_mock.get.return_value = 'foo'
            result = can_launch_browser()
            self.assertFalse(result)

    def test_configured_default_setter(self):
        config = mock.MagicMock()
        config.use_local_config = None
        with ConfiguredDefaultSetter(config, True):
            self.assertEqual(config.use_local_config, True)
        self.assertIsNone(config.use_local_config)

        config.use_local_config = True
        with ConfiguredDefaultSetter(config, False):
            self.assertEqual(config.use_local_config, False)
        self.assertTrue(config.use_local_config)

    @mock.patch('azure.cli.core.__version__', '7.8.9')
    def test_get_az_user_agent(self):
        from azure.cli.core._environment import _ENV_AZ_INSTALLER
        with mock.patch.dict('os.environ', {_ENV_AZ_INSTALLER: 'PIP'}):
            actual = get_az_user_agent()
            self.assertEqual(actual, 'AZURECLI/7.8.9 (PIP)')

        actual = get_az_user_agent()
        self.assertEqual(actual, 'AZURECLI/7.8.9')

    @mock.patch.dict('os.environ')
    @mock.patch('azure.cli.core._profile.Profile.get_raw_token', autospec=True)
    @mock.patch('requests.Session.send', autospec=True)
    def test_send_raw_requests(self, send_mock, get_raw_token_mock):
        if 'AZURE_HTTP_USER_AGENT' in os.environ:
            del os.environ['AZURE_HTTP_USER_AGENT']  # Clear env var possibly added by DevOps

        return_val = mock.MagicMock()
        return_val.is_ok = True
        send_mock.return_value = return_val
        get_raw_token_mock.return_value = ("Bearer", "eyJ0eXAiOiJKV1", None), None, None

        cli_ctx = DummyCli()
        cli_ctx.data = {
            'command': 'rest',
            'safe_params': ['method', 'uri']
        }
        test_arm_active_directory_resource_id = 'https://management.core.windows.net/'
        test_arm_endpoint = 'https://management.azure.com/'
        arm_resource_id = '/subscriptions/01/resourcegroups/02?api-version=2019-07-01'
        full_arm_rest_url = test_arm_endpoint.rstrip('/') + arm_resource_id
        test_body = '{"b1": "v1"}'

        expected_header = {
            'User-Agent': get_az_user_agent(),
            'Accept-Encoding': 'gzip, deflate',
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'CommandName': 'rest',
            'ParameterSetName': 'method uri',
            'Content-Length': '12'
        }
        expected_header_with_auth = expected_header.copy()
        expected_header_with_auth['Authorization'] = 'Bearer eyJ0eXAiOiJKV1'

        # Test basic usage
        # Mock Put Blob https://docs.microsoft.com/en-us/rest/api/storageservices/put-blob
        # Authenticate with service SAS https://docs.microsoft.com/en-us/rest/api/storageservices/create-service-sas
        sas_token = ['sv=2019-02-02', '{"srt": "s"}', "{'ss': 'bf'}"]
        send_raw_request(cli_ctx, 'PUT', 'https://myaccount.blob.core.windows.net/mycontainer/myblob?timeout=30',
                         uri_parameters=sas_token, body=test_body,
                         generated_client_request_id_name=None)

        get_raw_token_mock.assert_not_called()
        request = send_mock.call_args.args[1]
        self.assertEqual(request.method, 'PUT')
        self.assertEqual(request.url, 'https://myaccount.blob.core.windows.net/mycontainer/myblob?timeout=30&sv=2019-02-02&srt=s&ss=bf')
        self.assertEqual(request.body, '{"b1": "v1"}')
        # Verify no Authorization header
        self.assertDictEqual(dict(request.headers), expected_header)
        self.assertEqual(send_mock.call_args.kwargs["verify"], not should_disable_connection_verify())

        # Test Authorization header is skipped
        send_raw_request(cli_ctx, 'GET', full_arm_rest_url, body=test_body, skip_authorization_header=True,
                         generated_client_request_id_name=None)

        get_raw_token_mock.assert_not_called()
        request = send_mock.call_args.args[1]
        self.assertDictEqual(dict(request.headers), expected_header)

        # Test Authorization header is already provided
        send_raw_request(cli_ctx, 'GET', full_arm_rest_url,
                         body=test_body, headers={'Authorization=Basic ABCDE'},
                         generated_client_request_id_name=None)

        get_raw_token_mock.assert_not_called()
        request = send_mock.call_args.args[1]
        self.assertDictEqual(dict(request.headers), {**expected_header, 'Authorization': 'Basic ABCDE'})

        # Test Authorization header is auto appended
        send_raw_request(cli_ctx, 'GET', full_arm_rest_url,
                         body=test_body,
                         generated_client_request_id_name=None)

        get_raw_token_mock.assert_called_with(mock.ANY, test_arm_active_directory_resource_id)
        request = send_mock.call_args.args[1]
        self.assertDictEqual(dict(request.headers), expected_header_with_auth)

        # Test ARM resource ID /subscriptions/01/resourcegroups/02?api-version=2019-07-01
        send_raw_request(cli_ctx, 'GET', arm_resource_id, body=test_body,
                         generated_client_request_id_name=None)

        get_raw_token_mock.assert_called_with(mock.ANY, test_arm_active_directory_resource_id)
        request = send_mock.call_args.args[1]
        self.assertEqual(request.url, 'https://management.azure.com/subscriptions/01/resourcegroups/02?api-version=2019-07-01')
        self.assertDictEqual(dict(request.headers), expected_header_with_auth)

        # Test full ARM URL https://management.azure.com/subscriptions/01/resourcegroups/02?api-version=2019-07-01
        send_raw_request(cli_ctx, 'GET', full_arm_rest_url)

        get_raw_token_mock.assert_called_with(mock.ANY, test_arm_active_directory_resource_id)
        request = send_mock.call_args.args[1]
        self.assertEqual(request.url, 'https://management.azure.com/subscriptions/01/resourcegroups/02?api-version=2019-07-01')

        # Test full ARM URL with port https://management.azure.com:443/subscriptions/01/resourcegroups/02?api-version=2019-07-01
        test_arm_endpoint_with_port = 'https://management.azure.com:443/'
        full_arm_rest_url_with_port = test_arm_endpoint_with_port.rstrip('/') + arm_resource_id
        send_raw_request(cli_ctx, 'GET', full_arm_rest_url_with_port)

        get_raw_token_mock.assert_called_with(mock.ANY, test_arm_active_directory_resource_id)
        request = send_mock.call_args.args[1]
        self.assertEqual(request.url, 'https://management.azure.com:443/subscriptions/01/resourcegroups/02?api-version=2019-07-01')

        # Test non-ARM API, such as MS Graph API https://graph.microsoft.com/beta/appRoleAssignments/01
        send_raw_request(cli_ctx, 'PATCH', 'https://graph.microsoft.com/beta/appRoleAssignments/01',
                         body=test_body, generated_client_request_id_name=None)

        get_raw_token_mock.assert_called_with(mock.ANY, 'https://graph.microsoft.com/')
        request = send_mock.call_args.args[1]
        self.assertEqual(request.method, 'PATCH')
        self.assertEqual(request.url, 'https://graph.microsoft.com/beta/appRoleAssignments/01')

        # Test custom case-insensitive User-Agent
        with mock.patch.dict('os.environ', {'AZURE_HTTP_USER_AGENT': "env-ua"}):
            send_raw_request(cli_ctx, 'GET', full_arm_rest_url, headers={'user-agent=ARG-UA'})

            get_raw_token_mock.assert_called_with(mock.ANY, test_arm_active_directory_resource_id)
            request = send_mock.call_args.args[1]
            self.assertEqual(request.headers['User-Agent'], get_az_user_agent() + ' env-ua ARG-UA')


class TestBase64ToHex(unittest.TestCase):

    def setUp(self):
        self.base64 = 'PvOJgaPq5R004GyT1tB0IW3XUyM='.encode('ascii')

    def test_b64_to_hex(self):
        self.assertEqual('3EF38981A3EAE51D34E06C93D6D074216DD75323', b64_to_hex(self.base64))

    def test_b64_to_hex_type(self):
        self.assertIsInstance(b64_to_hex(self.base64), str)


class TestHandleException(unittest.TestCase):

    @mock.patch('azure.cli.core.util.logger.error', autospec=True)
    def test_handle_exception_keyboardinterrupt(self, mock_logger_error):
        # create test KeyboardInterrupt Exception
        keyboard_interrupt_ex = KeyboardInterrupt("KeyboardInterrupt")

        # call handle_exception
        ex_result = handle_exception(keyboard_interrupt_ex)

        # test behavior
        self.assertFalse(mock_logger_error.called)
        self.assertEqual(ex_result, 1)

    @mock.patch('azure.cli.core.util.logger.error', autospec=True)
    def test_handle_exception_clierror(self, mock_logger_error):
        from knack.util import CLIError

        # create test CLIError Exception
        err_msg = "Error Message"
        cli_error = CLIError(err_msg)

        # call handle_exception
        ex_result = handle_exception(cli_error)

        # test behavior
        self.assertTrue(mock_logger_error.called)
        self.assertEqual(mock.call(err_msg), mock_logger_error.call_args)
        self.assertEqual(ex_result, 1)

    @mock.patch('azure.cli.core.util.logger.error', autospec=True)
    def test_handle_exception_clouderror(self, mock_logger_error):
        from msrestazure.azure_exceptions import CloudError

        # create test CloudError Exception
        err_detail = "There was a Cloud Error."
        err_msg = "CloudError"
        mock_cloud_error = mock.MagicMock(spec=CloudError)
        mock_cloud_error.args = (err_detail, err_msg)

        # call handle_exception
        ex_result = handle_exception(mock_cloud_error)

        # test behavior
        self.assertTrue(mock_logger_error.called)
        self.assertEqual(mock.call(mock_cloud_error.args[0]), mock_logger_error.call_args)
        self.assertEqual(ex_result, mock_cloud_error.args[1])

    @mock.patch('azure.cli.core.util.logger.error', autospec=True)
    def test_handle_exception_httpoperationerror_typical_response_error(self, mock_logger_error):
        # create test HttpOperationError Exception
        err_msg = "Bad Request because of some incorrect param"
        err_code = "BadRequest"
        err = dict(error=dict(code=err_code, message=err_msg))
        response_text = json.dumps(err)
        mock_http_error = self._get_mock_HttpOperationError(response_text)

        expected_call = mock.call("%s%s", "{} - ".format(err_code), err_msg)

        # call handle_exception
        ex_result = handle_exception(mock_http_error)

        # test behavior
        self.assertTrue(mock_logger_error.called)
        self.assertEqual(expected_call, mock_logger_error.call_args)
        self.assertEqual(ex_result, 1)

    @mock.patch('azure.cli.core.util.logger.error', autospec=True)
    def test_handle_exception_httpoperationerror_error_key_has_string_value(self, mock_logger_error):
        # test error in response, but has str value.

        # create test HttpOperationError Exception
        err_msg = "BadRequest"
        err = dict(error=err_msg)
        response_text = json.dumps(err)
        mock_http_error = self._get_mock_HttpOperationError(response_text)

        expected_message = "{}".format(err_msg)

        # call handle_exception
        ex_result = handle_exception(mock_http_error)

        # test behavior
        self.assertTrue(mock_logger_error.called)
        self.assertEqual(mock.call(expected_message), mock_logger_error.call_args)
        self.assertEqual(ex_result, 1)

    @mock.patch('azure.cli.core.util.logger.error', autospec=True)
    def test_handle_exception_httpoperationerror_no_error_key(self, mock_logger_error):
        # test error not in response

        # create test HttpOperationError Exception
        err_msg = "BadRequest"
        err = dict(foo=err_msg)
        response_text = json.dumps(err)
        mock_http_error = self._get_mock_HttpOperationError(response_text)

        # call handle_exception
        ex_result = handle_exception(mock_http_error)

        # test behavior
        self.assertTrue(mock_logger_error.called)
        self.assertEqual(mock.call(mock_http_error), mock_logger_error.call_args)
        self.assertEqual(ex_result, 1)

    @mock.patch('azure.cli.core.util.logger.error', autospec=True)
    def test_handle_exception_httpoperationerror_no_response_text(self, mock_logger_error):
        # test no response text

        # create test HttpOperationError Exception
        response_text = ""

        mock_http_error = self._get_mock_HttpOperationError(response_text)

        # call handle_exception
        ex_result = handle_exception(mock_http_error)

        # test behavior
        self.assertTrue(mock_logger_error.called)
        self.assertEqual(mock.call(mock_http_error), mock_logger_error.call_args)
        self.assertEqual(ex_result, 1)

    @staticmethod
    def _get_mock_HttpOperationError(response_text):
        from msrest.exceptions import HttpOperationError
        from requests import Response

        mock_response = mock.MagicMock(spec=Response)
        mock_response.text = response_text
        mock_http_error = mock.MagicMock(spec=HttpOperationError)
        mock_http_error.response = mock_response

        return mock_http_error


if __name__ == '__main__':
    unittest.main()
