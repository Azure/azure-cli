# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from requests.models import Response
from msrestazure.azure_exceptions import CloudError
from ..rule_decorators import command_rule
from ..linter import RuleError


@command_rule
def missing_command_help_rule(linter, command_name):
    if not linter.get_command_help(command_name):
        raise RuleError('Missing help')


@command_rule
def no_ids_for_list_commands_rule(linter, command_name):
    if command_name.split()[-1] == 'list' and 'ids' in linter.get_command_parameters(command_name):
        raise RuleError('List commands should not expose --ids argument')


@command_rule
def no_404_handler_for_show_commands_rule(linter, command_name):
    if not command_name.split()[-1] == 'show':
        return
    exception_handler = linter.get_exception_handler(command_name)
    if not exception_handler:
        raise RuleError('Show command is missing exception handler and should resolve a 404.')

    # create a CloudError to test exception handler
    response = Response()
    response.status_code = 404
    error = CloudError(response)

    try:
        exception_handler(error)
    except Exception:
        raise RuleError('Show command has exception handler %s, but did not handle 404 CloudError.' % exception_handler)
