import os
import unittest
from azure.cli.utils.command_test_util import CommandTestGenerator
from command_specs import TEST_DEF

class TestCommands(unittest.TestCase):
    pass

vcr_cassette_dir = os.path.join(os.path.dirname(__file__), 'recordings')
generator = CommandTestGenerator(vcr_cassette_dir, TEST_DEF)
tests = generator.generate_tests()
for test_name in tests:
    setattr(TestCommands, test_name, tests[test_name])

if __name__ == '__main__':
    unittest.main()

# Declare test definitions in the definition portion of each test file
#TEST_DEF = []
#ENV_VARIABLES = {}

#def load_test_definitions(package_name, definition, env_variables=None):
#    for i in definition:
#        d = dict((k, i[k]) for k in i.keys() if k in ['test_name', 'command'])
#        test_key = '{}.{}'.format(package_name, d['test_name'])
#        TEST_DEF.append((test_key, d))
#    ENV_VARIABLES.update(env_variables or {})
