# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ..rule_decorators import command_group_rule


@command_group_rule('Checking missing help for command-groups...')
def missing_group_help_rule(linter, command_group_name):
    if not linter.get_command_group_help(command_group_name):
        print('--Command-Group: `%s`- Missing help.' % command_group_name)
        linter.mark_rule_failure()
