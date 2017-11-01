# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCli

from azure_devtools.scenario_tests import live_only, record_only, get_sha1_hash

from knack.commands import CLICommandsLoader

from .base import ScenarioTest, LiveScenarioTest
from .preparers import (StorageAccountPreparer, ResourceGroupPreparer, RoleBasedServicePrincipalPreparer,
                        KeyVaultPreparer)
from .exceptions import CliTestError
from .checkers import (JMESPathCheck, JMESPathCheckExists, JMESPathCheckGreaterThan, NoneCheck, StringCheck,
                       StringContainCheck)
from .decorators import api_version_constraint
from .utilities import get_active_api_profile, create_random_name

__all__ = ['ScenarioTest', 'LiveScenarioTest', 'ResourceGroupPreparer', 'StorageAccountPreparer',
           'RoleBasedServicePrincipalPreparer', 'CliTestError', 'JMESPathCheck', 'JMESPathCheckExists', 'NoneCheck',
           'live_only', 'record_only', 'StringCheck', 'StringContainCheck', 'get_sha1_hash', 'KeyVaultPreparer',
           'JMESPathCheckGreaterThan', 'api_version_constraint', 'get_active_api_profile', 'create_random_name']


class TestCli(AzCli):

    def __init__(self, commands_loader_cls=None, **kwargs):
        import os

        from azure.cli.core import MainCommandsLoader, AzCli
        from azure.cli.core.commands import AzCliCommandInvoker
        from azure.cli.core.azlogging import AzCliLogging
        from azure.cli.core.cloud import get_active_cloud
        from azure.cli.core.parser import AzCliCommandParser
        from azure.cli.core._config import GLOBAL_CONFIG_DIR, ENV_VAR_PREFIX
        from azure.cli.core._help import AzCliHelp
        from azure.cli.core._profile import Profile

        from knack.completion import ARGCOMPLETE_ENV_NAME
        from knack.log import get_logger

        super(TestCli, self).__init__(
            cli_name='az',
            config_dir=GLOBAL_CONFIG_DIR,
            config_env_var_prefix=ENV_VAR_PREFIX,
            commands_loader_cls=commands_loader_cls or MainCommandsLoader,
            parser_cls=AzCliCommandParser,
            logging_cls=AzCliLogging,
            help_cls=AzCliHelp,
            invocation_cls=AzCliCommandInvoker)

        self.data['headers'] = {}  # the x-ms-client-request-id is generated before a command is to execute
        self.data['command'] = 'unknown'
        self.data['completer_active'] = ARGCOMPLETE_ENV_NAME in os.environ
        self.data['query_active'] = False
        self.cloud = get_active_cloud(self)

    def get_cli_version(self):
        from azure.cli.core.util import get_az_version_string
        return get_az_version_string()


__version__ = '0.1.0'
