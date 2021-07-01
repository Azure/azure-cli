# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import ipaddress

from azure.cli.core.azclierror import (InvalidArgumentValueError, ArgumentUsageError)
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.profiles import ResourceType
from knack.log import get_logger
from knack.util import CLIError
from msrestazure.tools import is_valid_resource_id, parse_resource_id

from ._appservice_utils import _generic_site_operation
from ._client_factory import web_client_factory
from .utils import _normalize_sku

logger = get_logger(__name__)


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
        if not plan_info:
            raise CLIError("The plan '{}' doesn't exist in the resource group '{}'".format(plan, resource_group_name))
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
        if vnet in (v.name, v.id):
            vnet_loc = v.location
            break

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


def validate_ip_address(cmd, namespace):
    if namespace.ip_address is not None:
        _validate_ip_address_format(namespace)
        # For prevention of adding the duplicate IPs.
        if 'add' in cmd.name:
            _validate_ip_address_existence(cmd, namespace)


def validate_onedeploy_params(namespace):
    if namespace.src_path and namespace.src_url:
        raise CLIError('Only one of --src-path and --src-url can be specified')

    if not namespace.src_path and not namespace.src_url:
        raise CLIError('Either of --src-path or --src-url must be specified')

    if namespace.src_url and not namespace.artifact_type:
        raise CLIError('Deployment type is mandatory when deploying from URLs. Use --type')


def _validate_ip_address_format(namespace):
    if namespace.ip_address is not None:
        input_value = namespace.ip_address
        if ' ' in input_value:
            raise InvalidArgumentValueError("Spaces not allowed: '{}' ".format(input_value))
        input_ips = input_value.split(',')
        if len(input_ips) > 8:
            raise InvalidArgumentValueError('Maximum 8 IP addresses are allowed per rule.')
        validated_ips = ''
        for ip in input_ips:
            # Use ipaddress library to validate ip network format
            ip_obj = ipaddress.ip_network(ip)
            validated_ips += str(ip_obj) + ','
        namespace.ip_address = validated_ips[:-1]


def _validate_ip_address_existence(cmd, namespace):
    resource_group_name = namespace.resource_group_name
    name = namespace.name
    slot = namespace.slot
    scm_site = namespace.scm_site
    configs = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get_configuration', slot)
    access_rules = configs.scm_ip_security_restrictions if scm_site else configs.ip_security_restrictions
    ip_exists = [(lambda x: x.ip_address == namespace.ip_address)(x) for x in access_rules]
    if True in ip_exists:
        raise ArgumentUsageError('IP address: ' + namespace.ip_address + ' already exists. '
                                 'Cannot add duplicate IP address values.')


def validate_service_tag(cmd, namespace):
    if namespace.service_tag is not None:
        _validate_service_tag_format(cmd, namespace)
        # For prevention of adding the duplicate IPs.
        if 'add' in cmd.name:
            _validate_service_tag_existence(cmd, namespace)


def _validate_service_tag_format(cmd, namespace):
    if namespace.service_tag is not None:
        input_value = namespace.service_tag
        if ' ' in input_value:
            raise InvalidArgumentValueError("Spaces not allowed: '{}' ".format(input_value))
        input_tags = input_value.split(',')
        if len(input_tags) > 8:
            raise InvalidArgumentValueError('Maximum 8 service tags are allowed per rule.')
        network_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_NETWORK)
        resource_group_name = namespace.resource_group_name
        name = namespace.name
        webapp = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get')
        service_tag_full_list = network_client.service_tags.list(webapp.location).values
        if service_tag_full_list is None:
            logger.warning('Not able to get full Service Tag list. Cannot validate Service Tag.')
            return
        for tag in input_tags:
            valid_tag = False
            for tag_full_list in service_tag_full_list:
                if tag.lower() == tag_full_list.name.lower():
                    valid_tag = True
                    continue
            if not valid_tag:
                raise InvalidArgumentValueError('Unknown Service Tag: ' + tag)


def _validate_service_tag_existence(cmd, namespace):
    resource_group_name = namespace.resource_group_name
    name = namespace.name
    slot = namespace.slot
    scm_site = namespace.scm_site
    input_tag_value = namespace.service_tag.replace(' ', '')
    configs = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get_configuration', slot)
    access_rules = configs.scm_ip_security_restrictions if scm_site else configs.ip_security_restrictions
    for rule in access_rules:
        if rule.ip_address and rule.ip_address.lower() == input_tag_value.lower():
            raise ArgumentUsageError('Service Tag: ' + namespace.service_tag + ' already exists. '
                                     'Cannot add duplicate Service Tag values.')
