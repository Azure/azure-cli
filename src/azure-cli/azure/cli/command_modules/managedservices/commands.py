# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType

# pylint: disable=line-too-long
from azure.cli.command_modules.managedservices._client_factory import cf_registration_definitions, cf_registration_assignments


def load_command_table(self, _):
    msp_registration_definitions = CliCommandType(
        operations_tmpl='azure.mgmt.managedservices.operations#RegistrationDefinitionsOperations.{}',
        client_factory=cf_registration_definitions)

    msp_registration_assignments = CliCommandType(
        operations_tmpl='azure.mgmt.managedservices.operations#RegistrationAssignmentsOperations.{}',
        client_factory=cf_registration_assignments)

    with self.command_group('managedservices', is_preview=True) as g:
        pass

    with self.command_group('managedservices definition', msp_registration_definitions) as g:
        g.managedservices_custom('create', 'cli_definition_create', client_factory=cf_registration_definitions)
        g.managedservices_custom('list', 'cli_definition_list', client_factory=cf_registration_definitions)
        g.managedservices_custom('delete', 'cli_definition_delete', client_factory=cf_registration_definitions)
        g.managedservices_custom('show', 'cli_definition_get', client_factory=cf_registration_definitions)

    with self.command_group('managedservices assignment', msp_registration_assignments) as g:
        g.managedservices_custom('create', 'cli_assignment_create', client_factory=cf_registration_assignments)
        g.managedservices_custom('show', 'cli_assignment_get', client_factory=cf_registration_assignments)
        g.managedservices_custom('delete', 'cli_assignment_delete', client_factory=cf_registration_assignments)
        g.managedservices_custom('list', 'cli_assignment_list', client_factory=cf_registration_assignments)
