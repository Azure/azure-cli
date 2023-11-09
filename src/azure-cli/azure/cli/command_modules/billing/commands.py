# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.billing._client_factory import (
    invoices_mgmt_client_factory,
    enrollment_accounts_mgmt_client_factory)
from ._exception_handler import billing_exception_handler


def load_command_table(self, _):
    billing_invoice_util = CliCommandType(
        operations_tmpl='azure.mgmt.billing.operations#InvoicesOperations.{}',
        client_factory=invoices_mgmt_client_factory,
        exception_handler=billing_exception_handler
    )

    enrollment_account_util = CliCommandType(
        operations_tmpl='azure.mgmt.billing.operations#EnrollmentAccountsOperations.{}',
        client_factory=enrollment_accounts_mgmt_client_factory,
        exception_handler=billing_exception_handler
    )

    with self.command_group('billing invoice', billing_invoice_util, client_factory=invoices_mgmt_client_factory) as g:
        g.custom_command('list', 'cli_billing_list_invoices')
        g.custom_show_command('show', 'cli_billing_get_invoice')

    with self.command_group('billing period'):
        from .custom import PeriodList, PeriodShow
        self.command_table['billing period list'] = PeriodList(loader=self)
        self.command_table['billing period show'] = PeriodShow(loader=self)

    with self.command_group('billing enrollment-account', enrollment_account_util, client_factory=enrollment_accounts_mgmt_client_factory) as g:
        g.command('list', 'list')
        g.show_command('show', 'get')
