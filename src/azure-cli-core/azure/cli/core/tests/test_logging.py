# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from azure.cli.core.azlogging import AzCliLogging, AzLoggingLevelManager, CLI_LOGGER_NAME

from knack.log import get_logger

class TestLogging(unittest.TestCase):

    # When running verbose level tests, we check that argv is empty
    # as we expect determine_verbose_level to remove consumed arguments.

    def test_determine_verbose_level_default(self):
        argv = []
        actual_level = AzLoggingLevelManager.determine_verbose_level(argv)  # pylint: disable=protected-access
        expected_level = 0
        self.assertEqual(actual_level, expected_level)
        self.assertFalse(argv)

    def test_determine_verbose_level_verbose(self):
        argv = ['--verbose']
        actual_level = AzLoggingLevelManager.determine_verbose_level(argv)  # pylint: disable=protected-access
        expected_level = 1
        self.assertEqual(actual_level, expected_level)
        self.assertFalse(argv)

    def test_determine_verbose_level_debug(self):
        argv = ['--debug']
        actual_level = AzLoggingLevelManager.determine_verbose_level(argv)  # pylint: disable=protected-access
        expected_level = 2
        self.assertEqual(actual_level, expected_level)
        self.assertFalse(argv)

    def test_determine_verbose_level_v_v_v_default(self):
        argv = ['--verbose', '--debug']
        actual_level = AzLoggingLevelManager.determine_verbose_level(argv)  # pylint: disable=protected-access
        expected_level = 2
        self.assertEqual(actual_level, expected_level)
        # We still consumed the arguments
        self.assertFalse(argv)

    def test_determine_verbose_level_other_args_verbose(self):
        argv = ['account', '--verbose']
        actual_level = AzLoggingLevelManager.determine_verbose_level(argv)  # pylint: disable=protected-access
        expected_level = 1
        self.assertEqual(actual_level, expected_level)
        # We consumed 1 argument
        self.assertEqual(argv, ['account'])

    def test_determine_verbose_level_other_args_debug(self):
        argv = ['account', '--debug']
        actual_level = AzLoggingLevelManager.determine_verbose_level(argv)  # pylint: disable=protected-access
        expected_level = 2
        self.assertEqual(actual_level, expected_level)
        # We consumed 1 argument
        self.assertEqual(argv, ['account'])

    def test_get_az_logger(self):
        logger = get_logger()
        self.assertEqual(logger.name, 'az')

    def test_get_az_logger_module(self):
        logger = get_logger('azure.cli.module')
        self.assertEqual(logger.name, 'az.azure.cli.module')


if __name__ == '__main__':
    unittest.main()
