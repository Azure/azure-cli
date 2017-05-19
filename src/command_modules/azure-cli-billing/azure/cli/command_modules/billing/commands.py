# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=line-too-long

from azure.cli.core.commands import cli_command
from azure.cli.command_modules.billing._client_factory import \
    (invoices_mgmt_client_factory,
     billing_periods_mgmt_client_factory)
from azure.cli.command_modules.billing._transformers import \
    (transform_invoice_list_output, 
     transform_invoice_output, 
     transform_billing_period_output, 
     transform_billing_period_list_output)

invoices_path = 'azure.mgmt.billing.operations.invoices_operations#{}'
billing_periods_path = 'azure.mgmt.billing.operations.billing_periods_operations#{}'
custom_path = 'azure.cli.command_modules.billing.custom#'

cli_command(__name__, 'billing invoice list', custom_path + 'cli_billing_list_invoices', invoices_mgmt_client_factory, transform=transform_invoice_list_output)
cli_command(__name__, 'billing invoice show', custom_path + 'cli_billing_get_invoice', invoices_mgmt_client_factory, transform=transform_invoice_output)
cli_command(__name__, 'billing invoice show-latest', invoices_path.format('InvoicesOperations.get_latest'), invoices_mgmt_client_factory, transform=transform_invoice_output)
cli_command(__name__, 'billing period list', custom_path + 'cli_billing_list_billing_periods', billing_periods_mgmt_client_factory, transform=transform_billing_period_list_output)
cli_command(__name__, 'billing period show', custom_path + 'cli_billing_get_billing_period', billing_periods_mgmt_client_factory, transform=transform_billing_period_output)