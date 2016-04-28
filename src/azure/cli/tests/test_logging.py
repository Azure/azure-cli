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

    def test_determine_verbose_level_v(self):
        argv = ['-v']
        actual_level = _logging._determine_verbose_level(argv)
        expected_level = 1
        self.assertEqual(actual_level, expected_level)
        self.assertFalse(argv)

    def test_determine_verbose_level_v_v(self):
        argv = ['-v', '-v']
        actual_level = _logging._determine_verbose_level(argv)
        expected_level = 2
        self.assertEqual(actual_level, expected_level)
        self.assertFalse(argv)

    def test_determine_verbose_level_verbose_verbose(self):
        argv = ['--verbose', '--verbose']
        actual_level = _logging._determine_verbose_level(argv)
        expected_level = 2
        self.assertEqual(actual_level, expected_level)
        self.assertFalse(argv)

    def test_determine_verbose_level_vv(self):
        argv = ['-vv']
        actual_level = _logging._determine_verbose_level(argv)
        expected_level = 2
        self.assertEqual(actual_level, expected_level)
        self.assertFalse(argv)

    def test_determine_verbose_level_v_v_v_default(self):
        # User specified verbose 3 times (we only support 2)
        # So default to verbose level of 0
        argv = ['-v', '-v', '-v']
        actual_level = _logging._determine_verbose_level(argv)
        expected_level = 0
        self.assertEqual(actual_level, expected_level)
        # We still consumed the arguments
        self.assertFalse(argv)

    def test_determine_verbose_level_v_vv(self):
        # Too much verbosity specified
        argv = ['-v', '-vv']
        actual_level = _logging._determine_verbose_level(argv)
        expected_level = 0
        self.assertEqual(actual_level, expected_level)
        # We still consumed the arguments
        self.assertFalse(argv)

    def test_determine_verbose_level_vv_v(self):
        # Too much verbosity specified
        argv = ['-vv', '-v']
        actual_level = _logging._determine_verbose_level(argv)
        expected_level = 0
        self.assertEqual(actual_level, expected_level)
        # We still consumed the arguments
        self.assertFalse(argv)

    def test_determine_verbose_level_other_args(self):
        argv = ['account', '-v']
        actual_level = _logging._determine_verbose_level(argv)
        expected_level = 1
        self.assertEqual(actual_level, expected_level)
        # We consumed 1 argument
        self.assertEqual(argv, ['account'])

    def test_get_az_logger(self):
        az_logger = _logging.getAzLogger()
        self.assertEqual(az_logger.name, 'az')

    def test_get_az_logger_module(self):
        az_module_logger = _logging.getAzLogger('azure.cli.module')
        self.assertEqual(az_module_logger.name, 'az.azure.cli.module')

if __name__ == '__main__':
    unittest.main()
