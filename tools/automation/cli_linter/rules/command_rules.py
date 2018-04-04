# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ..rule_decorators import command_rule


@command_rule('Checking missing help for commands...')
def missing_command_help_rule(linter, command_name):
    if not linter.get_command_help(command_name):
        print('--Command: `%s`- Missing help.' % command_name)
        linter.mark_rule_failure()


@command_rule('Checking for --ids parameter in list commands...')
def no_ids_for_list_commands_rule(linter, command_name):
    if command_name.split()[-1] == 'list' and 'ids' in linter.get_command_parameters(command_name):
        print('--Command: `%s`- List commands should not expose --ids argument.' % command_name)
