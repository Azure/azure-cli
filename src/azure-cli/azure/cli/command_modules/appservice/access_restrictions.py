# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json

from azure.cli.command_modules.network._client_factory import network_client_factory
from azure.cli.core.azclierror import (ResourceNotFoundError, ArgumentUsageError, InvalidArgumentValueError,
                                       MutuallyExclusiveArgumentError)
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.mgmt.network.models import ServiceEndpointPropertiesFormat
from azure.mgmt.web.models import IpSecurityRestriction
from knack.log import get_logger
from msrestazure.tools import is_valid_resource_id, resource_id, parse_resource_id

from ._appservice_utils import _generic_site_operation
from .custom import get_site_configs

logger = get_logger(__name__)

ALLOWED_HTTP_HEADER_NAMES = ['x-forwarded-host', 'x-forwarded-for', 'x-azure-fdid', 'x-fd-healthprobe']


def show_webapp_access_restrictions(cmd, resource_group_name, name, slot=None):
    configs = get_site_configs(cmd, resource_group_name, name, slot)
    access_restrictions = json.dumps(configs.ip_security_restrictions, default=lambda x: x.__dict__)
    scm_access_restrictions = json.dumps(configs.scm_ip_security_restrictions, default=lambda x: x.__dict__)
    access_rules = {
        "scmIpSecurityRestrictionsUseMain": configs.scm_ip_security_restrictions_use_main,
        "ipSecurityRestrictions": json.loads(access_restrictions),
        "scmIpSecurityRestrictions": json.loads(scm_access_restrictions)
    }
    return access_rules


def add_webapp_access_restriction(
        cmd, resource_group_name, name, priority, rule_name=None,
        action='Allow', ip_address=None, subnet=None,
        vnet_name=None, description=None, scm_site=False,
        ignore_missing_vnet_service_endpoint=False, slot=None, vnet_resource_group=None,
        service_tag=None, http_headers=None):
    configs = get_site_configs(cmd, resource_group_name, name, slot)
    if (int(service_tag is not None) + int(ip_address is not None) +
            int(subnet is not None) != 1):
        err_msg = 'Please specify either: --subnet or --ip-address or --service-tag'
        raise MutuallyExclusiveArgumentError(err_msg)

    # get rules list
    access_rules = configs.scm_ip_security_restrictions if scm_site else configs.ip_security_restrictions
    # check for null
    access_rules = access_rules or []

    rule_instance = None
    if subnet:
        vnet_rg = vnet_resource_group if vnet_resource_group else resource_group_name
        subnet_id = _validate_subnet(cmd.cli_ctx, subnet, vnet_name, vnet_rg)
        if not ignore_missing_vnet_service_endpoint:
            _ensure_subnet_service_endpoint(cmd.cli_ctx, subnet_id)

        rule_instance = IpSecurityRestriction(
            name=rule_name, vnet_subnet_resource_id=subnet_id,
            priority=priority, action=action, tag='Default', description=description)
        access_rules.append(rule_instance)
    elif ip_address:
        rule_instance = IpSecurityRestriction(
            name=rule_name, ip_address=ip_address,
            priority=priority, action=action, tag='Default', description=description)
        access_rules.append(rule_instance)
    elif service_tag:
        rule_instance = IpSecurityRestriction(
            name=rule_name, ip_address=service_tag,
            priority=priority, action=action, tag='ServiceTag', description=description)
        access_rules.append(rule_instance)
    if http_headers:
        logger.info(http_headers)
        rule_instance.headers = _parse_http_headers(http_headers=http_headers)

    result = _generic_site_operation(
        cmd.cli_ctx, resource_group_name, name, 'update_configuration', slot, configs)
    return result.scm_ip_security_restrictions if scm_site else result.ip_security_restrictions


def remove_webapp_access_restriction(cmd, resource_group_name, name, rule_name=None, action='Allow',
                                     ip_address=None, subnet=None, vnet_name=None, scm_site=False, slot=None,
                                     service_tag=None):
    configs = get_site_configs(cmd, resource_group_name, name, slot)
    input_rule_types = (int(service_tag is not None) + int(ip_address is not None) +
                        int(subnet is not None))
    if input_rule_types > 1:
        err_msg = 'Please specify either: --subnet or --ip-address or --service-tag'
        raise MutuallyExclusiveArgumentError(err_msg)
    rule_instance = None
    # get rules list
    access_rules = configs.scm_ip_security_restrictions if scm_site else configs.ip_security_restrictions
    for rule in list(access_rules):
        if rule_name and input_rule_types == 0:
            if rule.name and rule.name.lower() == rule_name.lower() and rule.action == action:
                rule_instance = rule
                break
        elif ip_address:
            if rule.ip_address == ip_address and rule.action == action:
                if rule_name and (not rule.name or (rule.name and rule.name.lower() != rule_name.lower())):
                    continue
                rule_instance = rule
                break
        elif service_tag:
            if rule.ip_address and rule.ip_address.lower() == service_tag.lower() and rule.action == action:
                if rule_name and (not rule.name or (rule.name and rule.name.lower() != rule_name.lower())):
                    continue
                rule_instance = rule
                break
        elif subnet:
            subnet_id = _validate_subnet(cmd.cli_ctx, subnet, vnet_name, resource_group_name)
            if rule.vnet_subnet_resource_id == subnet_id and rule.action == action:
                if rule_name and (not rule.name or (rule.name and rule.name.lower() != rule_name.lower())):
                    continue
                rule_instance = rule
                break

    if rule_instance is None:
        raise ResourceNotFoundError('No rule found with the specified criteria.\n'
                                    '- If you specify rule name and source, both must match.\n'
                                    '- If you are trying to remove a Deny rule, '
                                    'you must explicitly specify --action Deny')

    access_rules.remove(rule_instance)

    result = _generic_site_operation(
        cmd.cli_ctx, resource_group_name, name, 'update_configuration', slot, configs)
    return result.scm_ip_security_restrictions if scm_site else result.ip_security_restrictions


def set_webapp_access_restriction(cmd, resource_group_name, name, use_same_restrictions_for_scm_site, slot=None):
    configs = get_site_configs(cmd, resource_group_name, name, slot)
    setattr(configs, 'scm_ip_security_restrictions_use_main', bool(use_same_restrictions_for_scm_site))

    use_main = _generic_site_operation(
        cmd.cli_ctx, resource_group_name, name, 'update_configuration',
        slot, configs).scm_ip_security_restrictions_use_main
    use_main_json = {
        "scmIpSecurityRestrictionsUseMain": use_main
    }
    return use_main_json


def _validate_subnet(cli_ctx, subnet, vnet_name, resource_group_name):
    subnet_is_id = is_valid_resource_id(subnet)
    if subnet_is_id and not vnet_name:
        return subnet
    if subnet and not subnet_is_id and vnet_name:
        return resource_id(
            subscription=get_subscription_id(cli_ctx),
            resource_group=resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=vnet_name,
            child_type_1='subnets',
            child_name_1=subnet)
    err_msg = 'Please specify either: --subnet ID or (--subnet NAME and --vnet-name NAME)'
    raise MutuallyExclusiveArgumentError(err_msg)


def _ensure_subnet_service_endpoint(cli_ctx, subnet_id):
    from azure.cli.core.profiles import AD_HOC_API_VERSIONS, ResourceType
    subnet_id_parts = parse_resource_id(subnet_id)
    subnet_subscription_id = subnet_id_parts['subscription']
    subnet_resource_group = subnet_id_parts['resource_group']
    subnet_vnet_name = subnet_id_parts['name']
    subnet_name = subnet_id_parts['resource_name']

    if get_subscription_id(cli_ctx).lower() != subnet_subscription_id.lower():
        raise ArgumentUsageError('Cannot validate subnet in different subscription for missing service endpoint.'
                                 ' Use --ignore-missing-endpoint or -i to'
                                 ' skip validation and manually verify service endpoint.')

    vnet_client = network_client_factory(cli_ctx, api_version=AD_HOC_API_VERSIONS[ResourceType.MGMT_NETWORK]
                                         ['appservice_ensure_subnet'])
    subnet_obj = vnet_client.subnets.get(subnet_resource_group, subnet_vnet_name, subnet_name)
    subnet_obj.service_endpoints = subnet_obj.service_endpoints or []
    service_endpoint_exists = False
    for s in subnet_obj.service_endpoints:
        if s.service == "Microsoft.Web":
            service_endpoint_exists = True
            break

    if not service_endpoint_exists:
        web_service_endpoint = ServiceEndpointPropertiesFormat(service="Microsoft.Web")
        subnet_obj.service_endpoints.append(web_service_endpoint)
        poller = vnet_client.subnets.begin_create_or_update(
            subnet_resource_group, subnet_vnet_name,
            subnet_name, subnet_parameters=subnet_obj)
        # Ensure subnet is updated to avoid update conflict
        LongRunningOperation(cli_ctx)(poller)


def _parse_http_headers(http_headers):
    logger.info(http_headers)
    header_dict = {}
    for header_str in http_headers:
        header = header_str.split('=')
        if len(header) != 2:
            err_msg = 'Http headers must have a format of `<name>=<value>`: "{}"'.format(header_str)
            raise InvalidArgumentValueError(err_msg)
        header_name = header[0].strip().lower()
        header_value = header[1].strip()

        if header_name not in ALLOWED_HTTP_HEADER_NAMES:
            raise InvalidArgumentValueError('Invalid http-header name: "{}"'.format(header_name))

        if header_value:
            if header_name in header_dict:
                if len(header_dict[header_name]) > 7:
                    err_msg = 'Only 8 values are allowed for each http-header: "{}"'.format(header_name)
                    raise ArgumentUsageError(err_msg)
                header_dict[header_name].append(header_value)
            else:
                header_dict[header_name] = [header_value]
    return header_dict
