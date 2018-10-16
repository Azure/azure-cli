# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

from azure.cli.core import AzCommandsLoader


def start_shell(cmd, style=None):
    from .azclishell.app import AzInteractiveShell
    AzInteractiveShell(cmd.cli_ctx, style)()


helps['interactive'] = """
            type: command
            short-summary: Start interactive mode.
            long-summary: >
                For more information on interactive mode, see: https://azure.microsoft.com/en-us/blog/welcome-to-azure-cli-shell/
            """


class InteractiveCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        super(InteractiveCommandsLoader, self).__init__(cli_ctx=cli_ctx)

    def load_command_table(self, _):

        with self.command_group('', operations_tmpl='azure.cli.command_modules.interactive#{}') as g:
            g.command('interactive', 'start_shell')
        return self.command_table

    def load_arguments(self, _):

        from azure.cli.command_modules.interactive.azclishell.color_styles import get_options as style_options

        with self.argument_context('interactive') as c:
            c.argument('style', options_list=['--style', '-s'], help='The colors of the shell.',
                       choices=style_options())
            c.ignore('_subscription')  # hide global subscription param


COMMAND_LOADER_CLS = InteractiveCommandsLoader
