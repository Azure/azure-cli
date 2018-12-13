# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_reservations(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.reservations.azure_reservation_api import AzureReservationAPI
    return get_mgmt_service_client(cli_ctx, AzureReservationAPI, subscription_bound=False)


def reservation_mgmt_client_factory(cli_ctx, kwargs):
    return cf_reservations(cli_ctx, **kwargs).reservation


def reservation_order_mgmt_client_factory(cli_ctx, kwargs):
    return cf_reservations(cli_ctx, **kwargs).reservation_order


def base_mgmt_client_factory(cli_ctx, kwargs):
    return cf_reservations(cli_ctx, **kwargs)
