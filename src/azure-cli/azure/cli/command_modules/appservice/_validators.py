# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from msrestazure.tools import is_valid_resource_id, parse_resource_id
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from ._client_factory import web_client_factory
from .utils import _normalize_sku


def validate_timeout_value(namespace):
    """Validates that zip deployment timeout is set to a reasonable min value"""
    if isinstance(namespace.timeout, int):
        if namespace.timeout <= 29:
            raise CLIError('--timeout value should be a positive value in seconds and should be atleast 30')


def validate_site_create(cmd, namespace):
    """Validate the SiteName that is being used to create is available
    This API requires that the RG is already created"""
    client = web_client_factory(cmd.cli_ctx)
    if isinstance(namespace.name, str) and isinstance(namespace.resource_group_name, str)\
            and isinstance(namespace.plan, str):
        resource_group_name = namespace.resource_group_name
        plan = namespace.plan
        if is_valid_resource_id(plan):
            parsed_result = parse_resource_id(plan)
            plan_info = client.app_service_plans.get(parsed_result['resource_group'], parsed_result['name'])
        else:
            plan_info = client.app_service_plans.get(resource_group_name, plan)
        # verify that the name is available for create
        validation_payload = {
            "name": namespace.name,
            "type": "Microsoft.Web/sites",
            "location": plan_info.location,
            "properties": {
                "serverfarmId": plan_info.id
            }
        }
        validation = client.validate(resource_group_name, validation_payload)
        if validation.status.lower() == "failure":
            raise CLIError(validation.error.message)


def validate_asp_create(cmd, namespace):
    """Validate the SiteName that is being used to create is available
    This API requires that the RG is already created"""
    client = web_client_factory(cmd.cli_ctx)
    if isinstance(namespace.name, str) and isinstance(namespace.resource_group_name, str):
        resource_group_name = namespace.resource_group_name
        if isinstance(namespace.location, str):
            location = namespace.location
        else:
            from azure.mgmt.resource import ResourceManagementClient
            rg_client = get_mgmt_service_client(cmd.cli_ctx, ResourceManagementClient)
            group = rg_client.resource_groups.get(resource_group_name)
            location = group.location
        validation_payload = {
            "name": namespace.name,
            "type": "Microsoft.Web/serverfarms",
            "location": location,
            "properties": {
                "skuName": _normalize_sku(namespace.sku) or 'B1',
                "capacity": namespace.number_of_workers or 1,
                "needLinuxWorkers": namespace.is_linux,
                "isXenon": namespace.hyper_v
            }
        }
        validation = client.validate(resource_group_name, validation_payload)
        if validation.status.lower() == "failure":
            raise CLIError(validation.error.message)
