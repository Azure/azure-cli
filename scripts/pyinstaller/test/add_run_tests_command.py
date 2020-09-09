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
  - name: Run installed fulltests
    text: >
        az run-tests --path /path/to/installed/fulltests
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
def run_tests(cmd, path):
    path = os.path.abspath(path)
    logger.warning('fulltests abspath is {}'.format(path))
    mod_list = 'ALL_COMMAND_MODULES'
    sys.path.append(path)
    try:
        import azure.cli
        azure.cli.__path__.append(os.path.join(path, 'azure', 'cli'))
        import azure.cli.testsdk
        logger.warning('success to import azure.cli.testsdk')
        for mod in mod_list:
            mod_name = 'azure.cli.command_modules.{}'.format(mod)
            module = importlib.import_module(mod_name)
            if os.path.exists(os.path.join(path, 'azure', 'cli', 'command_modules', mod)):
                module.__path__.append(os.path.join(path, 'azure', 'cli', 'command_modules', mod))
                logger.warning('[{}] path are {}'.format(mod, str(module.__path__)))
            else:
                logger.warning('[{}] does not have full tests.'.format(mod))
    except Exception as ex:  # pylint: disable=broad-except
        logger.warning(str(ex))

    import pytest
    pytest_args = ['-x', '-v', '-p', 'no:warnings', '--log-level=WARN']
    pytest_parallel_args = pytest_args + ['-n', 'auto']

    for mod_name in mod_list:
        if mod_name in ['botservice', 'network', 'configure', 'monitor']:
            module_args = pytest_args + ['--junit-xml', './azure_cli_test_result/{}.xml'.format(mod_name), '--pyargs', 'azure/cli/command_modules/{}/tests'.format(mod_name)]
            pytest.main(module_args)
        else:
            module_args = pytest_parallel_args + ['--junit-xml', './azure_cli_test_result/{}.xml'.format(mod_name), '--pyargs', 'azure.cli.command_modules.{}.tests'.format(mod_name)]
            pytest.main(module_args)
    core_module_args = pytest_args + ['--junit-xml', './azure_cli_test_result/azure-cli-core.xml', '--pyargs', 'azure.cli.core']
    pytest.main(core_module_args)

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