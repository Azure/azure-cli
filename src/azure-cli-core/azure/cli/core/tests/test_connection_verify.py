# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import logging
import unittest
try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

import azure.cli.core._debug as _debug


class Test_argparse(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Ensure initialization has occurred correctly
        logging.basicConfig(level=logging.DEBUG)

    @classmethod
    def tearDownClass(cls):
        logging.shutdown()

    def test_verify_client_connection(self):
        os.environ[_debug.DISABLE_VERIFY_VARIABLE_NAME] = ""
        self.assertFalse(_debug.should_disable_connection_verify())

        os.environ[_debug.DISABLE_VERIFY_VARIABLE_NAME] = "1"
        self.assertTrue(_debug.should_disable_connection_verify())

        clientMock = MagicMock()
        clientMock.config.connection.verify = True
        clientMock = _debug.change_ssl_cert_verification(clientMock)
        self.assertFalse(clientMock.config.connection.verify)


if __name__ == '__main__':
    unittest.main()
