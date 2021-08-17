# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
from unittest import mock
import unittest
from requests.exceptions import ConnectionError, HTTPError
from azure.cli.core.util import CLIError
from azure.cli.core.extension._index import (get_index, get_index_extensions, DEFAULT_INDEX_URL,
                                             ERR_TMPL_NON_200, ERR_TMPL_NO_NETWORK, ERR_TMPL_BAD_JSON,
                                             ERR_UNABLE_TO_GET_EXTENSIONS)


class MockResponse(object):
    def __init__(self, status_code, data):
        self.status_code = status_code
        self.data = data

    def json(self):
        if isinstance(self.data, Exception):
            raise self.data
        return self.data


def mock_index_get_generator(index_url, index_data):
    def mock_req_get(url, verify):
        if url == index_url:
            return MockResponse(200, index_data)
        return MockResponse(404, None)
    return mock_req_get


class TestExtensionIndexGet(unittest.TestCase):

    def test_get_index(self):
        with mock.patch('requests.get', side_effect=mock_index_get_generator(DEFAULT_INDEX_URL, {})):
            self.assertEqual(get_index(), {})

    def test_get_index_404(self):
        bad_index_url = 'http://contoso.com/cli-index'
        with mock.patch('requests.get', side_effect=mock_index_get_generator(DEFAULT_INDEX_URL, {})):
            with self.assertRaises(CLIError) as err:
                get_index(index_url=bad_index_url)
            self.assertEqual(str(err.exception), ERR_TMPL_NON_200.format(404, bad_index_url))

    def test_get_index_no_network(self):
        err_msg = 'Max retries exceeded with url...'
        with mock.patch('requests.get', side_effect=mock_index_get_generator(DEFAULT_INDEX_URL,
                                                                             ConnectionError(err_msg))):
            with self.assertRaises(CLIError) as err:
                get_index()
            self.assertEqual(str(err.exception), ERR_TMPL_NO_NETWORK.format(err_msg))

        err_msg = 'Max retries exceeded with url...'
        with mock.patch('requests.get', side_effect=mock_index_get_generator(DEFAULT_INDEX_URL, HTTPError(err_msg))):
            with self.assertRaises(CLIError) as err:
                get_index()
            self.assertEqual(str(err.exception), ERR_TMPL_NO_NETWORK.format(err_msg))

    def test_get_index_bad_json(self):
        err_msg = 'Unable to parse index data as JSON.'
        with mock.patch('requests.get', side_effect=mock_index_get_generator(DEFAULT_INDEX_URL, ValueError(err_msg))):
            with self.assertRaises(CLIError) as err:
                get_index()
            self.assertEqual(str(err.exception), ERR_TMPL_BAD_JSON.format(err_msg))

    def test_get_index_extensions(self):
        data = {'extensions': {}}
        with mock.patch('requests.get', side_effect=mock_index_get_generator(DEFAULT_INDEX_URL, data)):
            self.assertEqual(get_index_extensions(), {})

        obj = object()
        data = {'extensions': {'myext': obj}}
        with mock.patch('requests.get', side_effect=mock_index_get_generator(DEFAULT_INDEX_URL, data)):
            self.assertEqual(get_index_extensions().get('myext'), obj)

        with mock.patch('azure.cli.core.extension._index.logger.warning', autospec=True) as logger_mock:
            with mock.patch('requests.get', side_effect=mock_index_get_generator(DEFAULT_INDEX_URL, {})):
                self.assertEqual(get_index_extensions(), None)
                logger_mock.assert_called_once_with(ERR_UNABLE_TO_GET_EXTENSIONS)

        with mock.patch('azure.cli.core.extension._index.logger.warning', autospec=True) as logger_mock:
            with mock.patch('requests.get', side_effect=mock_index_get_generator(DEFAULT_INDEX_URL, {'v2extensions': []})):
                self.assertEqual(get_index_extensions(), None)
                logger_mock.assert_called_once_with(ERR_UNABLE_TO_GET_EXTENSIONS)

    # pylint: disable=line-too-long
    def test_get_index_cloud(self):

        from azure.cli.core.mock import DummyCli
        cli_ctx = DummyCli()

        default_data = {'extensions': {}}
        obj = object()
        cloud_data = {'extensions': {'myext': obj}}
        # cli_ctx not passed
        with mock.patch('requests.get', side_effect=mock_index_get_generator(DEFAULT_INDEX_URL, default_data)):
            self.assertEqual(get_index_extensions(), {})
        # cli_ctx passed but endpoint not set
        delattr(cli_ctx.cloud.endpoints, 'azmirror_storage_account_resource_id')
        with mock.patch('requests.get', side_effect=mock_index_get_generator(DEFAULT_INDEX_URL, default_data)):
            self.assertEqual(get_index_extensions(cli_ctx=cli_ctx), {})
        # cli_ctx passed and the endpoint is set
        cli_ctx.cloud.endpoints.azmirror_storage_account_resource_id = 'http://contoso.com'
        with mock.patch('requests.get', side_effect=mock_index_get_generator('http://contoso.com/extensions/index.json', cloud_data)):
            self.assertEqual(get_index_extensions(cli_ctx=cli_ctx).get('myext'), obj)


if __name__ == '__main__':
    unittest.main()
