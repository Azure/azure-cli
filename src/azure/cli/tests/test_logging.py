#pylint: skip-file
import unittest
import azure.cli._logging as _logging

class TestLogging(unittest.TestCase):

    # When running verbose level tests, we check that argv is empty
    # as we expect _determine_verbose_level to remove consumed arguments.

    def test_determine_verbose_level_default(self):
        argv = []
        actual_level = _logging._determine_verbose_level(argv)
        expected_level = 0
        self.assertEqual(actual_level, expected_level)
        self.assertFalse(argv)

    def test_determine_verbose_level_verbose(self):
        argv = ['--verbose']
        actual_level = _logging._determine_verbose_level(argv)
        expected_level = 1
        self.assertEqual(actual_level, expected_level)
        self.assertFalse(argv)

    def test_determine_verbose_level_debug(self):
        argv = ['--debug']
        actual_level = _logging._determine_verbose_level(argv)
        expected_level = 2
        self.assertEqual(actual_level, expected_level)
        self.assertFalse(argv)

    def test_determine_verbose_level_v_v_v_default(self):
        argv = ['--verbose', '--debug']
        actual_level = _logging._determine_verbose_level(argv)
        expected_level = 2
        self.assertEqual(actual_level, expected_level)
        # We still consumed the arguments
        self.assertFalse(argv)

    def test_determine_verbose_level_other_args_verbose(self):
        argv = ['account', '--verbose']
        actual_level = _logging._determine_verbose_level(argv)
        expected_level = 1
        self.assertEqual(actual_level, expected_level)
        # We consumed 1 argument
        self.assertEqual(argv, ['account'])

    def test_determine_verbose_level_other_args_debug(self):
        argv = ['account', '--debug']
        actual_level = _logging._determine_verbose_level(argv)
        expected_level = 2
        self.assertEqual(actual_level, expected_level)
        # We consumed 1 argument
        self.assertEqual(argv, ['account'])

    def test_get_az_logger(self):
        az_logger = _logging.get_az_logger()
        self.assertEqual(az_logger.name, 'az')

    def test_get_az_logger_module(self):
        az_module_logger = _logging.get_az_logger('azure.cli.module')
        self.assertEqual(az_module_logger.name, 'az.azure.cli.module')

if __name__ == '__main__':
    unittest.main()
