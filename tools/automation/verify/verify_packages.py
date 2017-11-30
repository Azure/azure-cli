# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Verify the command modules by install them using PIP"""

import os.path
import subprocess
import pip
import imp
import glob
import zipfile
import logging
import unittest

import automation.utilities.path as automation_path
from automation.utilities.const import COMMAND_MODULE_PREFIX

EXCLUDE_MODULES = set(['azure-cli-taskhelp'])

logger = logging.getLogger('azdev.verify.package')


# The package verifications are organized in the form of unittests so as to gather better output and error handling.
# It also ensures all the items were ran and errors are collected.
class PackageVerifyTests(unittest.TestCase):
    def __init__(self, method_name, **kwargs):
        super(PackageVerifyTests, self).__init__(method_name)
        self.test_data = kwargs

    def test_azure_cli_module_manifest(self):
        path = self.test_data['module_path']
        self.assertTrue(os.path.isdir(path), msg='Path {} does not exist'.format(path))

        manifest_file = os.path.join(path, 'MANIFEST.in')
        self.assertTrue(os.path.isfile(manifest_file), msg='Manifest file {} missing'.format(manifest_file))

    def test_azure_cli_installation(self):
        az_output = subprocess.check_output(['az', '--debug'], stderr=subprocess.STDOUT, universal_newlines=True)
        self.assertNotIn('Error loading command module', az_output, msg='Module loading error message showed up.')

    def test_azure_cli_module_installation(self):
        expected_modules = set([n for n, _ in automation_path.get_command_modules_paths(include_prefix=True)])

        pip.utils.pkg_resources = imp.reload(pip.utils.pkg_resources)
        installed_command_modules = [dist.key for dist in
                                     pip.get_installed_distributions(local_only=True)
                                     if dist.key.startswith(COMMAND_MODULE_PREFIX)]

        logger.info('Installed command modules %s', installed_command_modules)

        missing_modules = expected_modules - set(installed_command_modules) - EXCLUDE_MODULES
        self.assertFalse(missing_modules,
                         msg='Following modules are not installed successfully: {}'.format(', '.join(missing_modules)))

    def test_azure_cli_module_wheel(self):
        wheel_path = self.test_data['wheel_path']
        self.assertTrue(os.path.isfile(wheel_path))

        if 'nspkg' in wheel_path:
            return

        wheel_zip = zipfile.ZipFile(wheel_path)
        wheel_file_list = wheel_zip.namelist()

        error_message = """
        The wheel {} is incorrect.
        A valid command module .whl for the CLI should:
         - Not contain any __init__.py files in directories above azure.cli.command_modules.
         
        Does the package have a azure_bdist_wheel.py file?
        Does the package have a setup.cfg file?
        Does setup.py include 'cmdclass=cmdclass'?
        """.format(wheel_path)

        self.assertTrue(wheel_file_list)
        self.assertNotIn('azure/__init__.py', wheel_file_list, msg=error_message)
        self.assertNotIn('azure/cli/__init__.py', wheel_file_list, msg=error_message)
        self.assertNotIn('azure/cli/command_modules/__init__.py', wheel_file_list, msg=error_message)


def init(root):
    parser = root.add_parser('package', help='Verify the basic requirements for command module packages.')
    parser.add_argument('build_folder', help='The path to the folder contains all wheel files.')
    parser.set_defaults(func=run_verifications)


def run_verifications(args):
    suite = unittest.TestSuite()
    suite.addTest(PackageVerifyTests('test_azure_cli_installation'))
    suite.addTest(PackageVerifyTests('test_azure_cli_module_installation'))
    for _, path in automation_path.get_all_module_paths():
        suite.addTest(PackageVerifyTests('test_azure_cli_module_manifest', module_path=path))
    for each in glob.glob(os.path.join(args.build_folder, '*.whl')):
        suite.addTest(PackageVerifyTests('test_azure_cli_module_wheel', wheel_path=each))
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
