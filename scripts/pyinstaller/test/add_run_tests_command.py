# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import importlib
import pkgutil

INIT_TEMPLATE = '''
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
from azure.cli.core import AzCommandsLoader
from azure.cli.core.commands import CliCommandType

helps['run-tests'] = """
type: command
short-summary: Run all tests
examples:
  - name: Run acs module tests
    text: >
        az run-tests --path /path/to/installed/fulltests --module acs
"""


class PkgTestCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        super(PkgTestCommandsLoader, self).__init__(cli_ctx=cli_ctx)

    def load_command_table(self, args):
        pkgtest_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.pkgtest.custom#{}')
        with self.command_group('', pkgtest_custom) as g:
            g.command('run-tests', 'run_tests')

        return self.command_table

    def load_arguments(self, command):
        with self.argument_context('run-tests') as c:
            c.argument('path', help='The site-packages path of installed fulltests')
            c.argument('module', help='The module name to be tested')


COMMAND_LOADER_CLS = PkgTestCommandsLoader

'''

CUSTOM_TEMPLATE = '''
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys
import importlib
from knack.log import get_logger

logger = get_logger(__name__)


# pylint: disable=line-too-long
# pylint: disable=unused-argument
def run_tests(cmd, path, module):
    sys.path.append(path)
    logger.warning(str(sys.path))
    try:
        import azure.cli
        azure.cli.__path__.append(os.path.join(path, 'azure', 'cli'))
        logger.warning('azure.cli.__path__: {}'.format(str(azure.cli.__path__)))
        import azure.cli.testsdk
        logger.warning('success to import azure.cli.testsdk')
        module_imported = importlib.import_module('azure.cli.command_modules.{}'.format(module))
        if os.path.exists(os.path.join(path, 'azure', 'cli', 'command_modules', module)):
            module_imported.__path__.append(os.path.join(path, 'azure', 'cli', 'command_modules', module))
            logger.warning('[{}] path are {}'.format(module, str(module_imported.__path__)))
        else:
            logger.warning('[{}] does not have full tests.'.format(module))
    except Exception as ex:  # pylint: disable=broad-except
        import traceback
        traceback.print_tb(ex)
        logger.warning(str(ex))

    import pytest
    pytest_args = ['-x', '-v', '-p', 'no:warnings', '--log-level=WARN']
    pytest_parallel_args = pytest_args  #+ ['-n', 'auto']

    if module == 'core':
        module_args = pytest_args + ['--junit-xml', './azure_cli_test_result/azure-cli-core.xml', '--pyargs', 'azure.cli.core.tests']
        sys.exit(pytest.main(module_args))

    if module in ['botservice', 'network', 'configure', 'monitor']:
        module_args = pytest_args + ['--junit-xml', './azure_cli_test_result/{}.xml'.format(module), '--pyargs', 'azure.cli.command_modules.{}.tests'.format(module)]
        sys.exit(pytest.main(module_args))
    else:
        module_args = pytest_parallel_args + ['--junit-xml', './azure_cli_test_result/{}.xml'.format(module), '--pyargs', 'azure.cli.command_modules.{}.tests'.format(module)]
        sys.exit(pytest.main(module_args))

'''

mods_ns_pkg = importlib.import_module('azure.cli.command_modules')
command_modules = [modname for _, modname, _ in pkgutil.iter_modules(mods_ns_pkg.__path__)]

pkgtest_path = 'src/azure-cli/azure/cli/command_modules/pkgtest'
if not os.path.exists(pkgtest_path):
    os.mkdir(pkgtest_path)
with open(os.path.join(pkgtest_path, '__init__.py'), 'w') as fp:
    fp.write(INIT_TEMPLATE)
with open(os.path.join(pkgtest_path, 'custom.py'), 'w') as fp:
    fp.write(CUSTOM_TEMPLATE.replace('\'ALL_COMMAND_MODULES\'', str(command_modules)))