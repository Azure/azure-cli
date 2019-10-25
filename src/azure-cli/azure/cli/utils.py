# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def get_default_cli():
    from azure.cli.core.azlogging import AzCliLogging
    from azure.cli.core.commands import AzCliCommandInvoker
    from azure.cli.core.parser import AzCliCommandParser
    from azure.cli.core._config import GLOBAL_CONFIG_DIR, ENV_VAR_PREFIX
    from azure.cli.core._help import AzCliHelp
    from azure.cli.core.__init__ import MainCommandsLoader, AzCli
    from azure.cli.core._output import AzOutputProducer

    from azure.cli.command_modules.find.custom import get_generated_examples
    AzCliHelp.get_generated_examples = get_generated_examples

    return AzCli(cli_name='az',
                 config_dir=GLOBAL_CONFIG_DIR,
                 config_env_var_prefix=ENV_VAR_PREFIX,
                 commands_loader_cls=MainCommandsLoader,
                 invocation_cls=AzCliCommandInvoker,
                 parser_cls=AzCliCommandParser,
                 logging_cls=AzCliLogging,
                 output_cls=AzOutputProducer,
                 help_cls=AzCliHelp)
