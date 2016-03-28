import os
import unittest
from azure.cli.utils.test_commands import CommandTestGenerator
from command_specs import TEST_SPECS

class TestCommands(unittest.TestCase):
    pass

vcr_cassette_dir = os.path.join(os.path.dirname(__file__), 'recordings')
generator = CommandTestGenerator(vcr_cassette_dir, TEST_SPECS)
tests = generator.generate_tests()
for test_name in tests:
    setattr(TestCommands, test_name, tests[test_name])

if __name__ == '__main__':
    unittest.main()
