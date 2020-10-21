# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines
# pylint: disable=too-many-statements


def billing_invoice_download(client,
                             account_name=None,
                             invoice_name=None,
                             download_token=None,
                             download_urls=None
                             ):
    """
    Support download_invoice(account_name, invoice_name, download_token)
    Support download_billing_subscription_invoice(invoice_name, download_token)
    Support download_multiple_billing_subscription_invoice(download_urls)
    Support download_multiple_modern_invoice(account_name, download_urls)

    :param account_name: The ID that uniquely identifies a billing account.
    :param invoice_name: The ID that uniquely identifies an invoice.
    :param download_token: The download token with document source and document ID.
    :param download_urls: An array of download urls for individual.
    """
    if account_name and invoice_name and download_token:
        return client.download_invoice(account_name, invoice_name, download_token)
    if account_name and download_urls:
        return client.download_multiple_modern_invoice(account_name, download_urls)

    if download_urls:
        return client.download_multiple_billing_subscription_invoice(download_urls)

    if invoice_name and download_token:
        return client.download_billing_subscription_invoice(invoice_name, download_token)

    from azure.cli.core.azclierror import CLIInternalError
    raise CLIInternalError("Uncaught argument parameter combinations for Azure CLI to handle")
