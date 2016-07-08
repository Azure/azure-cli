import os
import logging
import unittest
try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

import azure.cli._debug as _debug


class Test_argparse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure initialization has occurred correctly
        import azure.cli.main
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
        _debug.allow_debug_connection(clientMock)
        self.assertFalse(clientMock.config.connection.verify)


if __name__ == '__main__':
    unittest.main()
