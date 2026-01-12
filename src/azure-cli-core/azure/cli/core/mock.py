# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCli


class DummyCli(AzCli):
    """A dummy CLI instance can be used to facilitate automation"""
    def __init__(self, commands_loader_cls=None, random_config_dir=False, **kwargs):
        import os
        from unittest.mock import patch

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
            # Knack prioritizes the AZURE_CONFIG_DIR env over the config_dir param, and other functions may call
            # get_config_dir directly. We need to set the env to make sure the config_dir is used.
            self.env_patch = patch.dict(os.environ, {'AZURE_CONFIG_DIR': config_dir})
            self.env_patch.start()

            # Always copy command index to avoid initializing it again
            files_to_copy = ['commandIndex.json']
            # In recording mode, copy login credentials from global config dir to the dummy config dir
            if os.getenv(ENV_VAR_TEST_LIVE, '').lower() == 'true':
                files_to_copy.extend([
                    'azureProfile.json', 'clouds.config',
                    'msal_token_cache.bin', 'msal_token_cache.json',
                    'service_principal_entries.bin', 'service_principal_entries.json'
                ])

            ensure_dir(config_dir)
            import shutil
            for file in files_to_copy:
                try:
                    shutil.copy(os.path.join(GLOBAL_CONFIG_DIR, file), config_dir)
                except FileNotFoundError:
                    pass

        super().__init__(
            cli_name='az',
            config_dir=GLOBAL_CONFIG_DIR,
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
