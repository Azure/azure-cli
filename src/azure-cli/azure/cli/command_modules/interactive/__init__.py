# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

from azure.cli.core import AzCommandsLoader


helps['interactive'] = """
            type: command
            short-summary: Start interactive mode. Installs the Interactive extension if not installed already.
            long-summary: >
                For more information on interactive mode, see: https://azure.microsoft.com/blog/welcome-to-azure-cli-shell/
            """


class InteractiveCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core import ModExtensionSuppress
        super(InteractiveCommandsLoader, self).__init__(
            cli_ctx=cli_ctx,
            suppress_extension=ModExtensionSuppress(
                __name__, 'alias', '0.5.1',
                reason='Your version of the extension is not compatible with this version of the CLI.',
                recommend_update=True))

    def load_command_table(self, _):

        with self.command_group('', operations_tmpl='azure.cli.command_modules.interactive.custom#{}') as g:
            g.command('interactive', 'start_shell', is_preview=True)
        return self.command_table

    def load_arguments(self, _):

        with self.argument_context('interactive') as c:
            style_options = ['quiet', 'purple', 'default', 'none', 'contrast', 'pastel',
                             'halloween', 'grey', 'br', 'bg', 'primary', 'neon']
            c.argument('style', options_list=['--style', '-s'], help='The colors of the shell.',
                       choices=style_options)
            c.argument('update', help='Update the Interactive extension to the latest available.',
                       action='store_true')
            c.ignore('_subscription')  # hide global subscription param


COMMAND_LOADER_CLS = InteractiveCommandsLoader
