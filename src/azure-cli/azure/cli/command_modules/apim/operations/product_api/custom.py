# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.util import sdk_no_wait


def list_product_api(client, resource_group_name, service_name, product_id):
    return client.list_by_product(resource_group_name, service_name, product_id)


def check_product_exists(client, resource_group_name, service_name, product_id, api_id):
    return client.check_entity_exists(resource_group_name, service_name, product_id, api_id)


def add_product_api(client, resource_group_name, service_name, product_id, api_id, no_wait=False):

    return sdk_no_wait(
        no_wait,
        client.create_or_update,
        resource_group_name=resource_group_name,
        service_name=service_name,
        product_id=product_id,
        api_id=api_id)


def delete_product_api(client, resource_group_name, service_name, product_id, api_id, no_wait=False):

    return sdk_no_wait(
        no_wait,
        client.delete,
        resource_group_name=resource_group_name,
        service_name=service_name,
        product_id=product_id,
        api_id=api_id)
