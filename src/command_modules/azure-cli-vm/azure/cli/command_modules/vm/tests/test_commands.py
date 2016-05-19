import os
import unittest
from azure.cli.utils.command_test_util import CommandTestGenerator
from azure.cli.command_modules.vm.tests.command_specs import TEST_DEF, ENV_VAR

class TestCommands(unittest.TestCase):
    pass

recording_dir = os.path.join(os.path.dirname(__file__), 'recordings')

generator = CommandTestGenerator(recording_dir, TEST_DEF, ENV_VAR)
tests = generator.generate_tests()

for test_name in tests:
    setattr(TestCommands, test_name, tests[test_name])

if __name__ == '__main__':
    unittest.main()
