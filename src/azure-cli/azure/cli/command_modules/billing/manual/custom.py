# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines
# pylint: disable=too-many-statements

import json
import re
from datetime import datetime

from azure.core.exceptions import DeserializationError
from azure.core.pipeline.policies import ContentDecodePolicy


class _ProductListResponse:
    def __init__(self, response, content, encoding):
        self._response = response
        self._encoding = encoding or 'utf-8'
        self._body = json.dumps(content).encode(self._encoding)

    def __getattr__(self, name):
        return getattr(self._response, name)

    def body(self):
        return self._body

    def text(self, encoding=None):
        return self._body.decode(encoding or self._encoding)


def _normalize_product_dates(response):
    if response.http_response.status_code != 200:
        return

    encoding = response.context.get('response_encoding')
    content = ContentDecodePolicy.deserialize_from_http_generics(response.http_response, encoding)
    # Leave response shape validation to the SDK.
    if not isinstance(content, dict) or not isinstance(content.get('value'), list):
        return

    changed = False
    for product in content['value']:
        if not isinstance(product, dict):
            continue
        properties = product.get('properties')
        if not isinstance(properties, dict):
            continue
        for field in ('purchaseDate', 'endDate', 'lastChargeDate'):
            value = properties.get(field)
            if isinstance(value, str) and re.fullmatch(r'[0-9]{2}/[0-9]{2}/[0-9]{4}', value):
                try:
                    # The service's date-only values have no timezone.
                    properties[field] = datetime.strptime(value, '%m/%d/%Y').isoformat()
                except ValueError as ex:
                    raise DeserializationError("Invalid product {}: {!r}".format(field, value)) from ex
                changed = True

    if changed:
        # The raw hook runs before ContentDecodePolicy on every SDK pager request.
        response.http_response = _ProductListResponse(response.http_response, content, encoding)


def billing_product_list(client,
                         account_name,
                         profile_name=None,
                         invoice_section_name=None,
                         filter_=None,
                         customer_name=None):
    kwargs = {'billing_account_name': account_name, 'raw_response_hook': _normalize_product_dates}
    if account_name is not None and profile_name is not None and invoice_section_name is not None:
        return client.list_by_invoice_section(billing_profile_name=profile_name,
                                              invoice_section_name=invoice_section_name,
                                              filter=filter_,
                                              **kwargs)
    if account_name is not None and profile_name is not None:
        return client.list_by_billing_profile(billing_profile_name=profile_name, filter=filter_, **kwargs)
    if account_name is not None and customer_name is not None:
        return client.list_by_customer(customer_name=customer_name, **kwargs)
    return client.list_by_billing_account(filter=filter_, **kwargs)


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
        return client.begin_download_invoice(account_name, invoice_name, download_token)
    if account_name and download_urls:
        return client.begin_download_multiple_billing_profile_invoices(account_name, download_urls)

    if download_urls:
        return client.begin_download_multiple_billing_subscription_invoices(download_urls)

    if invoice_name and download_token:
        return client.begin_download_billing_subscription_invoice(
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
