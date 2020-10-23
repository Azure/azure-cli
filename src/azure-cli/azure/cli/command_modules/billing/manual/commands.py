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
    billing_policy_update_validator
)


def load_command_table(self, _):

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
