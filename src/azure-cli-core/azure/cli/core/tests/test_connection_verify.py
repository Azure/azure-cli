# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import logging
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from knack.util import CLIError

import azure.cli.core._debug as _debug
import azure.cli.core.util as cli_util


@patch.dict(os.environ, {}, clear=True)
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

    def test_ca_bundle_unset_or_empty(self):
        for value in (None, ''):
            with self.subTest(ca_bundle=value):
                if value is not None:
                    os.environ[_debug.REQUESTS_CA_BUNDLE] = value

                client = MagicMock()
                client.config.connection.verify = True
                self.assertIs(_debug.change_ssl_cert_verification(client), client)
                self.assertTrue(client.config.connection.verify)
                self.assertEqual(_debug.change_ssl_cert_verification_track2(), {})

    def test_ca_bundle_file(self):
        with tempfile.NamedTemporaryFile() as ca_bundle:
            os.environ[_debug.REQUESTS_CA_BUNDLE] = ca_bundle.name

            client = MagicMock()
            client.config.connection.verify = True
            _debug.change_ssl_cert_verification(client)
            self.assertEqual(client.config.connection.verify, ca_bundle.name)
            self.assertEqual(_debug.change_ssl_cert_verification_track2(),
                             {'connection_verify': ca_bundle.name})

    def test_ca_bundle_invalid_path(self):
        with tempfile.TemporaryDirectory() as directory:
            os.environ[_debug.REQUESTS_CA_BUNDLE] = os.path.join(directory, 'missing.pem')

            with self.assertRaisesRegex(CLIError, 'invalid file path'):
                _debug.change_ssl_cert_verification(MagicMock())
            with self.assertRaisesRegex(CLIError, 'invalid file path'):
                _debug.change_ssl_cert_verification_track2()


if __name__ == '__main__':
    unittest.main()
