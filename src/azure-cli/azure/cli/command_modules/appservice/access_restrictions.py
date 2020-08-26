# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.commands import LongRunningOperation
from azure.mgmt.web.models import IpSecurityRestriction
from azure.mgmt.network.models import ServiceEndpointPropertiesFormat
from azure.cli.command_modules.appservice.custom import get_site_configs
from azure.cli.command_modules.appservice._appservice_utils import _generic_site_operation
from azure.cli.command_modules.network._client_factory import network_client_factory

logger = get_logger(__name__)

NETWORK_API_VERSION = '2019-02-01'


def show_webapp_access_restrictions(cmd, resource_group_name, name, slot=None):
    import json
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
        ignore_missing_vnet_service_endpoint=False, slot=None):
    configs = get_site_configs(cmd, resource_group_name, name, slot)

    if (ip_address and subnet) or (not ip_address and not subnet):
        raise CLIError('Usage error: --subnet | --ip-address')

    # get rules list
    access_rules = configs.scm_ip_security_restrictions if scm_site else configs.ip_security_restrictions
    # check for null
    access_rules = access_rules or []

    rule_instance = None
    if subnet or vnet_name:
        subnet_id = _validate_subnet(cmd.cli_ctx, subnet, vnet_name, resource_group_name)
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

    result = _generic_site_operation(
        cmd.cli_ctx, resource_group_name, name, 'update_configuration', slot, configs)
    return result.scm_ip_security_restrictions if scm_site else result.ip_security_restrictions


def remove_webapp_access_restriction(cmd, resource_group_name, name, rule_name=None, action='Allow',
                                     ip_address=None, subnet=None, vnet_name=None, scm_site=False, slot=None):
    configs = get_site_configs(cmd, resource_group_name, name, slot)
    rule_instance = None
    # get rules list
    access_rules = configs.scm_ip_security_restrictions if scm_site else configs.ip_security_restrictions

    for rule in list(access_rules):
        if rule_name:
            if rule.name and rule.name.lower() == rule_name.lower() and rule.action == action:
                rule_instance = rule
                break
        elif ip_address:
            if rule.ip_address == ip_address and rule.action == action:
                if rule_name and rule.name and rule.name.lower() != rule_name.lower():
                    continue
                rule_instance = rule
                break
        elif subnet:
            subnet_id = _validate_subnet(cmd.cli_ctx, subnet, vnet_name, resource_group_name)
            if rule.vnet_subnet_resource_id == subnet_id and rule.action == action:
                if rule_name and rule.name and rule.name.lower() != rule_name.lower():
                    continue
                rule_instance = rule
                break

    if rule_instance is None:
        raise CLIError('No rule found with the specified criteria')

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
    from msrestazure.tools import is_valid_resource_id
    subnet_is_id = is_valid_resource_id(subnet)

    if subnet_is_id and not vnet_name:
        return subnet
    if subnet and not subnet_is_id and vnet_name:
        from msrestazure.tools import resource_id
        from azure.cli.core.commands.client_factory import get_subscription_id
        return resource_id(
            subscription=get_subscription_id(cli_ctx),
            resource_group=resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=vnet_name,
            child_type_1='subnets',
            child_name_1=subnet)
    raise CLIError('Usage error: --subnet ID | --subnet NAME --vnet-name NAME')


def _ensure_subnet_service_endpoint(cli_ctx, subnet_id):
    from msrestazure.tools import parse_resource_id
    subnet_id_parts = parse_resource_id(subnet_id)
    subnet_resource_group = subnet_id_parts['resource_group']
    subnet_vnet_name = subnet_id_parts['name']
    subnet_name = subnet_id_parts['resource_name']

    vnet_client = network_client_factory(cli_ctx, api_version=NETWORK_API_VERSION)
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
        poller = vnet_client.subnets.create_or_update(
            subnet_resource_group, subnet_vnet_name,
            subnet_name, subnet_parameters=subnet_obj)
        # Ensure subnet is updated to avoid update conflict
        LongRunningOperation(cli_ctx)(poller)
