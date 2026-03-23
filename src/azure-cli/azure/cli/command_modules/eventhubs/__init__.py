# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader, get_logger

# pylint: disable=unused-import

from ._help import helps

logger = get_logger(__name__)

_OPTIMIZED_LOADING_CONFIG_SECTION = 'eventhubs'
_OPTIMIZED_LOADING_CONFIG_KEY = 'optimized_loading'


class EventhubCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core import ModExtensionSuppress
        from azure.cli.core.commands import CliCommandType
        from azure.cli.core.profiles import ResourceType
        eventhub_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.eventhubs.custom#{}')
        super().__init__(cli_ctx=cli_ctx,
                         custom_command_type=eventhub_custom,
                         resource_type=ResourceType.MGMT_EVENTHUB,
                         suppress_extension=ModExtensionSuppress(__name__, 'eventhubs', '0.0.1',
                                                                 reason='These commands are now in the CLI.',
                                                                 recommend_remove=True))

    def load_command_table(self, args):
        from azure.cli.command_modules.eventhubs.commands import load_command_table
        from azure.cli.core.aaz import load_aaz_command_table_optimized

        use_optimized = self.cli_ctx.config.getboolean(
            _OPTIMIZED_LOADING_CONFIG_SECTION, _OPTIMIZED_LOADING_CONFIG_KEY, fallback=True)

        # When optimized loading is disabled, still use the optimized loader but
        # pass args=None to force a full load (no trimming). The gutted __init__.py
        # files are incompatible with the old load_aaz_command_table loader, so we
        # cannot fall back to it.
        effective_args = args if use_optimized else None

        if use_optimized and args and args[0:1] == ['eventhubs']:
            logger.warning(
                "The eventhubs module is using optimized command loading for improved performance. "
                "If you encounter any issues, you can disable this by running: "
                "az config set %s.%s=false",
                _OPTIMIZED_LOADING_CONFIG_SECTION, _OPTIMIZED_LOADING_CONFIG_KEY)

        try:
            from . import aaz
        except ImportError:
            aaz = None
        if aaz:
            load_aaz_command_table_optimized(
                loader=self,
                aaz_pkg_name=aaz.__name__,
                args=effective_args
            )

        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.eventhubs._params import load_arguments_eh
        load_arguments_eh(self, command)


COMMAND_LOADER_CLS = EventhubCommandsLoader
