import json
import os
import unittest
from six import StringIO

class Test_vcr_security(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.COMMAND_MODULE_PREFIX = 'azure-cli-'
        PATH_TO_COMMAND_MODULES = os.path.abspath(os.path.join(os.path.abspath(__file__), '..', '..', '..', '..', 'command_modules'))
        cls.command_modules = []
        for name in os.listdir(PATH_TO_COMMAND_MODULES):
            full_module_path = os.path.join(PATH_TO_COMMAND_MODULES, name)
            if name.startswith(cls.COMMAND_MODULE_PREFIX) and os.path.isdir(full_module_path):
                cls.command_modules += [(name, full_module_path)]        
    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.io = StringIO()
        
    def tearDown(self):
        self.io.close()

    def test_cassettes_for_token_refresh(self):
        cls = Test_vcr_security
        for name, fullpath in cls.command_modules:
            path_to_recordings = os.path.join(fullpath, 'azure', 'cli', 'command_modules', name.replace(cls.COMMAND_MODULE_PREFIX, ''), 'tests', 'recordings')
            if not os.path.isdir(path_to_recordings):
                continue
            insecure_cassettes = []
            for name in os.listdir(path_to_recordings):
                if not str.endswith(name, '.yaml'):
                    continue
                with open(os.path.join(path_to_recordings, name), 'r') as f:
                    for line in f:
                        if 'grant_type=refresh_token' in line or '/oauth2/token' in line:
                            insecure_cassettes.append(name)
        self.assertFalse(insecure_cassettes, 'The following cassettes contain refresh tokens: {}'.format(insecure_cassettes))

if __name__ == '__main__':
    unittest.main()
