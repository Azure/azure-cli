# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.configure._validators import validate_local_context, validate_local_context_for_delete


def load_command_table(self, _):

    configure_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.configure.custom#{}')

    with self.command_group('', configure_custom) as g:
        g.command('configure', 'handle_configure')

    with self.command_group('cache', configure_custom) as g:
        g.command('list', 'list_cache_contents')
        g.command('show', 'show_cache_contents')  # pylint: disable=show-command
        g.command('delete', 'delete_cache_contents')
        g.command('purge', 'purge_cache_contents')

    def _local_context_deprecate_message(self):
        msg = "This {} has been deprecated and will be removed in future release.".format(self.object_type)
        msg += " Use '{}' instead.".format(self.redirect)
        # msg += " For more information go to"
        # msg += " <Add param persist doc link here when it is ready.>"
        return msg

    with self.command_group('local-context', configure_custom, is_experimental=True,
                            deprecate_info=self.deprecate(redirect="config param-persist",
                                                          message_func=_local_context_deprecate_message)) as g:
        g.command('on', 'turn_local_context_on')
        g.command('off', 'turn_local_context_off')
        g.command('show', 'show_local_context', validator=validate_local_context)  # pylint: disable=show-command
        g.command('delete', 'delete_local_context', validator=validate_local_context_for_delete)
