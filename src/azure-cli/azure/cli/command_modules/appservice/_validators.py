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
            raise CLIError('--timeout value should be a positive value in seconds and should be at least 30')


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


def validate_ase_create(cmd, namespace):
    # Validate the ASE Name availability
    client = web_client_factory(cmd.cli_ctx)
    resource_type = 'Microsoft.Web/hostingEnvironments'
    if isinstance(namespace.name, str):
        name_validation = client.check_name_availability(namespace.name, resource_type)
        if not name_validation.name_available:
            raise CLIError(name_validation.message)


def validate_asp_create(cmd, namespace):
    """Validate the SiteName that is being used to create is available
    This API requires that the RG is already created"""
    client = web_client_factory(cmd.cli_ctx)
    if isinstance(namespace.name, str) and isinstance(namespace.resource_group_name, str):
        resource_group_name = namespace.resource_group_name
        if isinstance(namespace.location, str):
            location = namespace.location
        else:
            from azure.cli.core.profiles import ResourceType
            rg_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)

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


def validate_front_end_scale_factor(namespace):
    if namespace.front_end_scale_factor:
        min_scale_factor = 5
        max_scale_factor = 15
        scale_error_text = "Frontend Scale Factor '{}' is invalid. Must be between {} and {}"
        scale_factor = namespace.front_end_scale_factor
        if scale_factor < min_scale_factor or scale_factor > max_scale_factor:
            raise CLIError(scale_error_text.format(scale_factor, min_scale_factor, max_scale_factor))


def validate_asp_sku(cmd, namespace):
    import json
    client = web_client_factory(cmd.cli_ctx)
    serverfarm = namespace.name
    resource_group_name = namespace.resource_group_name
    asp = client.app_service_plans.get(resource_group_name, serverfarm, None, raw=True)
    if asp.response.status_code != 200:
        raise CLIError(asp.response.text)
    # convert byte array to json
    output_str = asp.response.content.decode('utf8')
    res = json.loads(output_str)

    # Isolated SKU is supported only for ASE
    if namespace.sku in ['I1', 'I2', 'I3']:
        if res.get('properties').get('hostingEnvironment') is None:
            raise CLIError("The pricing tier 'Isolated' is not allowed for this app service plan. Use this link to "
                           "learn more: https://docs.microsoft.com/en-us/azure/app-service/overview-hosting-plans")
    else:
        if res.get('properties').get('hostingEnvironment') is not None:
            raise CLIError("Only pricing tier 'Isolated' is allowed in this app service plan. Use this link to "
                           "learn more: https://docs.microsoft.com/en-us/azure/app-service/overview-hosting-plans")


def validate_ip_address(namespace):
    if namespace.ip_address is not None:
        # IPv6
        if ':' in namespace.ip_address:
            if namespace.ip_address.count(':') > 1:
                if '/' not in namespace.ip_address:
                    namespace.ip_address = namespace.ip_address + '/128'
                    return
                return
        # IPv4
        elif '.' in namespace.ip_address:
            if namespace.ip_address.count('.') == 3:
                if '/' not in namespace.ip_address:
                    namespace.ip_address = namespace.ip_address + '/32'
                    return
                return

        raise CLIError('Invalid IP address')
