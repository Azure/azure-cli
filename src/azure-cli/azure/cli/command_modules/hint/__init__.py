# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.hint.custom import login_hinter, demo_hint_hinter
from azure.cli.core import AzCommandsLoader

hinters = {
    # The hinters are matched based on the order they appear in the dict
    # https://docs.python.org/3/library/stdtypes.html#dict
    #   Changed in version 3.7: Dictionary order is guaranteed to be insertion order.
    #   This behavior was an implementation detail of CPython from 3.6.
    'login': login_hinter,
    'demo hint': demo_hint_hinter
}


class HintCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        hint_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.hint.custom#{}')
        super(HintCommandsLoader, self).__init__(cli_ctx=cli_ctx, custom_command_type=hint_custom)

    def load_command_table(self, args):
        self._register_hinters(args)
        return self.command_table

    def _register_hinters(self, args):
        import re
        from knack.events import EVENT_CLI_SUCCESSFUL_EXECUTE
        from knack.log import get_logger
        logger = get_logger(__name__)

        from azure.cli.core.util import roughly_parse_command
        command_line = roughly_parse_command(args)
        for command_regex, hinter in hinters.items():
            if re.fullmatch(command_regex, command_line):
                logger.debug("Registering hinter: %s: %s", command_regex, hinter.__name__)
                self.cli_ctx.register_event(EVENT_CLI_SUCCESSFUL_EXECUTE, hinter)
                # Improve if more than one hinters are needed
                break


COMMAND_LOADER_CLS = HintCommandsLoader
