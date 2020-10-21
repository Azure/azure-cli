# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines
# pylint: disable=too-many-statements

from azure.cli.core.commands import CliCommandType

from ._validators import billing_invoice_download_validator


def load_command_table(self, _):

    from ..generated._client_factory import cf_invoice_section
    billing_invoice_section = CliCommandType(
        operations_tmpl='azure.mgmt.billing.operations#InvoiceSectionsOperations.{}',
        client_factory=cf_invoice_section)
    with self.command_group('billing invoice section', billing_invoice_section,
                            client_factory=cf_invoice_section, is_preview=True):
        pass    # inherit commands from generated/

    from ..generated._client_factory import cf_invoice
    billing_invoice = CliCommandType(
        operations_tmpl='azure.mgmt.billing.operations#InvoicesOperations.{}',
        client_factory=cf_invoice)
    with self.command_group('billing invoice', billing_invoice, client_factory=cf_invoice) as g:
        g.custom_command('download', 'billing_invoice_download', validator=billing_invoice_download_validator)
