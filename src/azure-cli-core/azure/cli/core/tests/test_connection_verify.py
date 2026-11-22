# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import logging
import unittest
from unittest.mock import MagicMock, patch
import tempfile

import azure.cli.core._debug as _debug
import azure.cli.core.util as cli_util


class Test_argparse(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Ensure initialization has occurred correctly
        logging.basicConfig(level=logging.DEBUG)

    @classmethod
    def tearDownClass(cls):
        logging.shutdown()

    def test_verify_client_connection(self):
        os.environ[cli_util.DISABLE_VERIFY_VARIABLE_NAME] = ""
        self.assertFalse(cli_util.should_disable_connection_verify())

        os.environ[cli_util.DISABLE_VERIFY_VARIABLE_NAME] = "1"
        self.assertTrue(cli_util.should_disable_connection_verify())

        clientMock = MagicMock()
        clientMock.config.connection.verify = True
        clientMock = _debug.change_ssl_cert_verification(clientMock)
        self.assertFalse(clientMock.config.connection.verify)

    def test_get_msal_http_client_respects_ca_bundle(self):
        """Test that get_msal_http_client() respects REQUESTS_CA_BUNDLE environment variable."""
        # Save original environment
        original_ca_bundle = os.environ.get(_debug.REQUESTS_CA_BUNDLE)
        original_disable_verify = os.environ.get(cli_util.DISABLE_VERIFY_VARIABLE_NAME)

        try:
            # Create a temporary file to act as a CA bundle
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pem') as tmp_file:
                tmp_file.write(b'# Test CA Bundle')
                tmp_file_path = tmp_file.name

            # Test 1: With REQUESTS_CA_BUNDLE set
            os.environ[_debug.REQUESTS_CA_BUNDLE] = tmp_file_path
            if cli_util.DISABLE_VERIFY_VARIABLE_NAME in os.environ:
                del os.environ[cli_util.DISABLE_VERIFY_VARIABLE_NAME]

            session = _debug.get_msal_http_client()
            self.assertEqual(session.verify, tmp_file_path)

            # Test 2: With connection verification disabled
            del os.environ[_debug.REQUESTS_CA_BUNDLE]
            os.environ[cli_util.DISABLE_VERIFY_VARIABLE_NAME] = "1"

            session = _debug.get_msal_http_client()
            self.assertFalse(session.verify)

            # Test 3: With neither set (default behavior)
            del os.environ[cli_util.DISABLE_VERIFY_VARIABLE_NAME]

            session = _debug.get_msal_http_client()
            self.assertTrue(session.verify)  # Default is True

        finally:
            # Cleanup
            os.unlink(tmp_file_path)
            # Restore original environment
            if original_ca_bundle:
                os.environ[_debug.REQUESTS_CA_BUNDLE] = original_ca_bundle
            elif _debug.REQUESTS_CA_BUNDLE in os.environ:
                del os.environ[_debug.REQUESTS_CA_BUNDLE]
            if original_disable_verify:
                os.environ[cli_util.DISABLE_VERIFY_VARIABLE_NAME] = original_disable_verify
            elif cli_util.DISABLE_VERIFY_VARIABLE_NAME in os.environ:
                del os.environ[cli_util.DISABLE_VERIFY_VARIABLE_NAME]


if __name__ == '__main__':
    unittest.main()
