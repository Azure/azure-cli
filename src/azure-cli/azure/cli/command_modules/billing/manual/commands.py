# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines
# pylint: disable=too-many-statements

from azure.cli.core.commands import CliCommandType

from ._validators import (
    billing_invoice_download_validator,
    billing_invoice_show_validator,
    billing_profile_show_validator,
    billing_policy_update_validator,
    billing_permission_list_validator
)


def load_command_table(self, _):

    from ..generated._client_factory import cf_instruction
    billing_instruction = CliCommandType(
        operations_tmpl='azure.mgmt.billing.operations#InstructionsOperations.{}',
        client_factory=cf_instruction)
    with self.command_group('billing instruction', billing_instruction, client_factory=cf_instruction,
                            is_preview=True) as g:
        g.generic_update_command('update',
                                 operations_tmpl='azure.cli.command_modules.billing.manual.custom#{}',
                                 getter_type=billing_instruction,
                                 setter_name='put',
                                 setter_type=billing_instruction,
                                 custom_func_name='billing_instruction_update')

    from ..generated._client_factory import cf_invoice_section
    billing_invoice_section = CliCommandType(
        operations_tmpl="azure.mgmt.billing.operations#InvoiceSectionsOperations.{}",
        client_factory=cf_invoice_section,
    )
    with self.command_group("billing invoice section",
                            billing_invoice_section,
                            client_factory=cf_invoice_section,
                            is_preview=True):
        pass  # inherit commands from generated/ and add is_preview=True

    from ..generated._client_factory import cf_invoice
    billing_invoice = CliCommandType(
        operations_tmpl="azure.mgmt.billing.operations#InvoicesOperations.{}",
        client_factory=cf_invoice,
    )
    with self.command_group("billing invoice", billing_invoice, client_factory=cf_invoice) as g:
        g.custom_command(
            "download",
            "billing_invoice_download",
            validator=billing_invoice_download_validator,
            is_preview=True
        )
        g.custom_show_command(
            "show", "billing_invoice_show", validator=billing_invoice_show_validator
        )

    from ..generated._client_factory import cf_policy
    billing_policy = CliCommandType(
        operations_tmpl='azure.mgmt.billing.operations#PoliciesOperations.{}',
        client_factory=cf_policy)
    with self.command_group('billing policy', billing_policy, client_factory=cf_policy, is_preview=True) as g:
        g.custom_show_command('show', 'billing_policy_show', validator=billing_profile_show_validator)
        g.custom_command('update', 'billing_policy_update', validator=billing_policy_update_validator)

    from ..generated._client_factory import cf_permission
    billing_permission = CliCommandType(
        operations_tmpl='azure.mgmt.billing.operations#BillingPermissionsOperations.{}',
        client_factory=cf_permission)
    with self.command_group('billing permission', billing_permission, client_factory=cf_permission,
                            is_preview=True) as g:
        g.custom_command('list', 'billing_permission_list', validator=billing_permission_list_validator)

    from ..generated._client_factory import cf_role_assignment
    billing_role_assignment = CliCommandType(
        operations_tmpl='azure.mgmt.billing.operations#BillingRoleAssignmentsOperations.{}',
        client_factory=cf_role_assignment)
    with self.command_group('billing role-assignment', billing_role_assignment, client_factory=cf_role_assignment,
                            is_preview=True) as g:
        g.custom_show_command('show', 'billing_role_assignment_show')

    from ..generated._client_factory import cf_role_definition
    billing_role_definition = CliCommandType(
        operations_tmpl='azure.mgmt.billing.operations#BillingRoleDefinitionsOperations.{}',
        client_factory=cf_role_definition)
    with self.command_group('billing role-definition', billing_role_definition, client_factory=cf_role_definition,
                            is_preview=True) as g:
        g.custom_show_command('show', 'billing_role_definition_show')
