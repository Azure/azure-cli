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
    if isinstance(namespace.name, str) and isinstance(namespace.resource_group_name, str) \
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
        if validation.status.lower() == "failure" and validation.error.code != 'SiteAlreadyExists':
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
        if validation.status.lower() == "failure" and validation.error.code != 'ServerFarmAlreadyExists':
            raise CLIError(validation.error.message)


def validate_app_or_slot_exists_in_rg(cmd, namespace):
    """Validate that the App/slot exists in the RG provided"""
    client = web_client_factory(cmd.cli_ctx)
    webapp = namespace.name
    resource_group_name = namespace.resource_group_name
    if isinstance(namespace.slot, str):
        app = client.web_apps.get_slot(resource_group_name, webapp, namespace.slot, raw=True)
    else:
        app = client.web_apps.get(resource_group_name, webapp, None, raw=True)
    if app.response.status_code != 200:
        raise CLIError(app.response.text)


def validate_app_exists_in_rg(cmd, namespace):
    client = web_client_factory(cmd.cli_ctx)
    webapp = namespace.name
    resource_group_name = namespace.resource_group_name
    app = client.web_apps.get(resource_group_name, webapp, None, raw=True)
    if app.response.status_code != 200:
        raise CLIError(app.response.text)


def validate_add_vnet(cmd, namespace):
    resource_group_name = namespace.resource_group_name
    from azure.cli.command_modules.network._client_factory import network_client_factory
    vnet_client = network_client_factory(cmd.cli_ctx)
    list_all_vnets = vnet_client.virtual_networks.list_all()
    vnet = namespace.vnet
    name = namespace.name
    slot = namespace.slot

    vnet_loc = ''
    for v in list_all_vnets:
        if v.name == vnet:
            vnet_loc = v.location
            break

    from ._appservice_utils import _generic_site_operation
    webapp = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)
    # converting geo region to geo location
    webapp_loc = webapp.location.lower().replace(" ", "")

    if vnet_loc != webapp_loc:
        raise CLIError("The app and the vnet resources are in different locations. \
                        Cannot integrate a regional VNET to an app in a different region")
