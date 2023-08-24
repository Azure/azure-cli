# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCli


class DummyCli(AzCli):
    """A dummy CLI instance can be used to facilitate automation"""
    def __init__(self, commands_loader_cls=None, random_config_dir=False, **kwargs):
        import os

        from azure.cli.core import MainCommandsLoader
        from azure.cli.core.commands import AzCliCommandInvoker
        from azure.cli.core.azlogging import AzCliLogging
        from azure.cli.core.cloud import get_active_cloud
        from azure.cli.core.parser import AzCliCommandParser
        from azure.cli.core.util import random_string
        from azure.cli.core._config import GLOBAL_CONFIG_DIR, ENV_VAR_PREFIX, ENV_VAR_TEST_LIVE
        from azure.cli.core._help import AzCliHelp
        from azure.cli.core._output import AzOutputProducer

        from knack.completion import ARGCOMPLETE_ENV_NAME
        from knack.util import ensure_dir

        if random_config_dir:
            config_dir = os.path.join(GLOBAL_CONFIG_DIR, 'dummy_cli_config_dir', random_string())

            # In recording mode, copy login credentials from global config dir to the dummy config dir
            if os.getenv(ENV_VAR_TEST_LIVE, '').lower() == 'true':
                if os.path.exists(GLOBAL_CONFIG_DIR):
                    ensure_dir(config_dir)
                    import shutil
                    for file in ['azureProfile.json', 'msal_token_cache.bin', 'clouds.config', 'msal_token_cache.json',
                                 'service_principal_entries.json']:
                        try:
                            shutil.copy(os.path.join(GLOBAL_CONFIG_DIR, file), config_dir)
                        except FileNotFoundError:
                            pass
        else:
            config_dir = GLOBAL_CONFIG_DIR

        super(DummyCli, self).__init__(
            cli_name='az',
            config_dir=config_dir,
            config_env_var_prefix=ENV_VAR_PREFIX,
            commands_loader_cls=commands_loader_cls or MainCommandsLoader,
            parser_cls=AzCliCommandParser,
            logging_cls=AzCliLogging,
            output_cls=AzOutputProducer,
            help_cls=AzCliHelp,
            invocation_cls=AzCliCommandInvoker)

        self.data['headers'] = {}  # the x-ms-client-request-id is generated before a command is to execute
        self.data['command'] = 'unknown'
        self.data['completer_active'] = ARGCOMPLETE_ENV_NAME in os.environ
        self.data['query_active'] = False

        loader = self.commands_loader_cls(self)
        setattr(self, 'commands_loader', loader)

        self.cloud = get_active_cloud(self)

    def get_cli_version(self):
        from azure.cli.core import __version__ as cli_version
        return cli_version
