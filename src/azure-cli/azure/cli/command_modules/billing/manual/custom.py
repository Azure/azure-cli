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
                             download_urls=None):
    """
    Get URL to download invoice

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
        return client.download_billing_subscription_invoice(
            invoice_name, download_token
        )

    from azure.cli.core.azclierror import CLIInternalError

    raise CLIInternalError(
        "Uncaught argument combinations for Azure CLI to handle. Please submit an issue"
    )


def billing_invoice_show(client, name, account_name=None, by_subscription=None):

    if account_name is not None and name is not None:
        return client.get(billing_account_name=account_name, invoice_name=name)

    if name is not None and not by_subscription:
        return client.get_by_id(name)

    if by_subscription and name:
        return client.get_by_subscription_and_invoice_id(name)

    from azure.cli.core.azclierror import CLIInternalError
    raise CLIInternalError(
        "Uncaught argument combinations for Azure CLI to handle. Please submit an issue"
    )


def billing_policy_show(client, account_name, profile_name=None, customer_name=None):
    if profile_name:
        return client.get_by_billing_profile(account_name, profile_name)

    if customer_name:
        return client.get_by_customer(account_name, customer_name)

    from azure.cli.core.azclierror import CLIInternalError
    return CLIInternalError(
        "Uncaught argument combinations for Azure CLI to handle. Please submit an issue"
    )


def billing_policy_update(client,
                          account_name,
                          profile_name=None,
                          customer_name=None,
                          marketplace_purchases=None,
                          reservation_purchases=None,
                          view_charges=None):
    if customer_name is None:
        parameters = {}
        parameters['marketplace_purchases'] = marketplace_purchases
        parameters['reservation_purchases'] = reservation_purchases
        parameters['view_charges'] = view_charges
        return client.update(billing_account_name=account_name,
                             billing_profile_name=profile_name,
                             parameters=parameters)

    if account_name is not None and customer_name is not None:
        return client.update_customer(billing_account_name=account_name,
                                      customer_name=customer_name,
                                      view_charges=view_charges)

    from azure.cli.core.azclierror import CLIInternalError
    return CLIInternalError(
        "Uncaught argument combinations for Azure CLI to handle. Please submit an issue"
    )


def billing_role_assignment_show(client,
                                 name,
                                 account_name,
                                 profile_name=None,
                                 invoice_section_name=None):
    if profile_name is not None and invoice_section_name is None:
        return client.get_by_billing_profile(billing_account_name=account_name,
                                             billing_profile_name=profile_name,
                                             billing_role_assignment_name=name)
    if profile_name is not None and invoice_section_name is not None:
        return client.get_by_invoice_section(billing_account_name=account_name,
                                             billing_profile_name=profile_name,
                                             invoice_section_name=invoice_section_name,
                                             billing_role_assignment_name=name)

    return client.get_by_billing_account(billing_account_name=account_name,
                                         billing_role_assignment_name=name)


def billing_role_definition_show(client,
                                 name,
                                 account_name,
                                 profile_name=None,
                                 invoice_section_name=None):
    if profile_name is not None and invoice_section_name is None:
        return client.get_by_billing_profile(billing_account_name=account_name,
                                             billing_profile_name=profile_name,
                                             billing_role_definition_name=name)

    if profile_name is not None and invoice_section_name is not None:
        return client.get_by_invoice_section(billing_account_name=account_name,
                                             billing_profile_name=profile_name,
                                             invoice_section_name=invoice_section_name,
                                             billing_role_definition_name=name)

    return client.get_by_billing_account(billing_account_name=account_name,
                                         billing_role_definition_name=name)


def billing_instruction_update(cmd,
                               instance,
                               amount=None,
                               start_date=None,
                               end_date=None,
                               creation_date=None):

    with cmd.update_context(instance) as c:
        c.set_param('amount', amount)
        c.set_param('start_date', start_date)
        c.set_param('end_date', end_date)
        c.set_param('creation_date', creation_date)

    return instance
