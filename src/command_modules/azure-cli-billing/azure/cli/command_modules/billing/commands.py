# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.sdk.util import CliCommandType
from azure.cli.command_modules.billing._client_factory import (
    invoices_mgmt_client_factory, billing_periods_mgmt_client_factory)
from ._exception_handler import billing_exception_handler


def load_command_table(self, _):
    billing_invoice_util = CliCommandType(
        client_factory=invoices_mgmt_client_factory,
        exception_handler=billing_exception_handler
    )

    billing_period_util = CliCommandType(
        client_factory=billing_periods_mgmt_client_factory,
        exception_handler=billing_exception_handler
    )

    with self.command_group('billing invoice', billing_invoice_util) as g:
        g.custom_command('list', 'cli_billing_list_invoices')
        g.custom_command('show', 'cli_billing_get_invoice')

    usage_path = 'azure.mgmt.billing.operations.billing_periods_operations#BillingPeriodsOperations.{}'
    with self.command_group('billing period', billing_period_util) as g:
        g.custom_command('list', 'cli_billing_list_periods')
        g.command('show', 'get', operations_tmpl=usage_path)
