import os
import unittest
from azure.cli.utils.command_test_util import CommandTestGenerator
from command_specs import TEST_DEF, ENV_VAR

class TestCommands(unittest.TestCase):
    pass

vcr_cassette_dir = os.path.join(os.path.dirname(__file__), 'recordings')
generator = CommandTestGenerator(vcr_cassette_dir, TEST_DEF)
tests = generator.generate_tests()
for test_name in tests:
    setattr(TestCommands, test_name, tests[test_name])

if __name__ == '__main__':
    unittest.main()
