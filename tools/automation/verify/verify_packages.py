# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Verify the command modules by install them using PIP"""

import sys
import os.path
import subprocess
import glob
import filecmp
import logging
import unittest
from pkg_resources import working_set

import automation.utilities.path as automation_path
from automation.utilities.const import COMMAND_MODULE_PREFIX

logger = logging.getLogger('azdev.verify.package')


# The package verifications are organized in the form of unittests so as to gather better output and error handling.
# It also ensures all the items were ran and errors are collected.
class PackageVerifyTests(unittest.TestCase):
    def __init__(self, method_name, **kwargs):
        super(PackageVerifyTests, self).__init__(method_name)
        self.test_data = kwargs

    def test_azure_cli_module_manifest_and_azure_bdist(self):
        path = self.test_data['module_path']
        self.assertTrue(os.path.isdir(path), msg='Path {} does not exist'.format(path))

        manifest_file = os.path.join(path, 'MANIFEST.in')
        self.assertTrue(os.path.isfile(manifest_file), msg='Manifest file {} missing'.format(manifest_file))

        # Check azure_bdist_wheel.py file for module.
        # Assumption is that core has the correct file always so compare against that.
        core_azure_bdist_wheel = os.path.join(automation_path.get_repo_root(), 'src', 'azure-cli-core', 'azure_bdist_wheel.py')
        mod_azure_bdist_wheel = os.path.join(path, 'azure_bdist_wheel.py')
        if os.path.isfile(mod_azure_bdist_wheel):
            self.assertTrue(filecmp.cmp(core_azure_bdist_wheel, mod_azure_bdist_wheel), "Make sure {} is correct. It should look like {}".format(mod_azure_bdist_wheel, core_azure_bdist_wheel))
        
    def test_azure_cli_installation(self):
        az_output = subprocess.check_output(['az', '--debug'], stderr=subprocess.STDOUT, universal_newlines=True)
        self.assertNotIn('Error loading command module', az_output, msg='Module loading error message showed up.')

    def test_azure_cli_module_installation(self):
        expected_modules = set([n for n, _ in automation_path.get_command_modules_paths(include_prefix=True)])

        installed_command_modules = [dist.key for dist in list(working_set) if dist.key.startswith(COMMAND_MODULE_PREFIX)]

        logger.info('Installed command modules %s', installed_command_modules)

        missing_modules = expected_modules - set(installed_command_modules)
        self.assertFalse(missing_modules,
                         msg='Following modules are not installed successfully: {}'.format(', '.join(missing_modules)))


def init(root):
    parser = root.add_parser('package', help='Verify the basic requirements for command module packages.')
    parser.add_argument('build_folder', help='The path to the folder contains all wheel files.')
    parser.set_defaults(func=run_verifications)


def run_verifications(args):
    suite = unittest.TestSuite()
    suite.addTest(PackageVerifyTests('test_azure_cli_installation'))
    suite.addTest(PackageVerifyTests('test_azure_cli_module_installation'))
    for _, path in automation_path.get_all_module_paths():
        suite.addTest(PackageVerifyTests('test_azure_cli_module_manifest_and_azure_bdist', module_path=path))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())
