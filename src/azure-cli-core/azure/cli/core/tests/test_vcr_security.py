#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import os
import unittest

class Test_vcr_security(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.COMMAND_MODULE_PREFIX = 'azure-cli-'
        PATH_TO_COMMAND_MODULES = os.path.abspath(os.path.join(os.path.abspath(__file__),
                                                               '..', '..', '..', '..', '..', '..',
                                                               'command_modules'))
        cls.command_modules = []
        for name in os.listdir(PATH_TO_COMMAND_MODULES):
            full_module_path = os.path.join(PATH_TO_COMMAND_MODULES, name)
            if name.startswith(cls.COMMAND_MODULE_PREFIX) and os.path.isdir(full_module_path):
                cls.command_modules += [(name, full_module_path)]

    def test_cassettes_for_token_refresh(self):
        cls = Test_vcr_security
        for name, fullpath in cls.command_modules:
            path_to_recordings = os.path.join(fullpath, 'azure', 'cli', 'command_modules',
                                              name.replace(cls.COMMAND_MODULE_PREFIX, ''),
                                              'tests', 'recordings')
            if not os.path.isdir(path_to_recordings):
                continue
            insecure_cassettes = []
            for name in os.listdir(path_to_recordings):
                if not str.endswith(name, '.yaml'):
                    continue
                with open(os.path.join(path_to_recordings, name), 'r') as f:
                    for line in f:
                        if 'grant_type=refresh_token' in line.lower() or '/oauth2/token' in line.lower():
                            insecure_cassettes.append(name)
        self.assertFalse(insecure_cassettes, 'The following cassettes contain refresh tokens: {}'.format(insecure_cassettes))

    def test_deployment_name_scrub(self):
        from azure.cli.core.test_utils.vcr_test_base import _scrub_deployment_name as scrub_deployment_name
        uri1 = 'https://www.contoso.com/deployments/azurecli1466174372.33571889479?api-version=2015-11-01'
        uri2 = 'https://www.contoso.com/deployments/azurecli1466174372.33571889479/more'

        uri1 = scrub_deployment_name(uri1)
        uri2 = scrub_deployment_name(uri2)

        self.assertEqual(uri1, 'https://www.contoso.com/deployments/mock-deployment?api-version=2015-11-01')
        self.assertEqual(uri2, 'https://www.contoso.com/deployments/mock-deployment/more')

if __name__ == '__main__':
    unittest.main()
