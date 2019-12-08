# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError

from azure.mgmt.network.models import (RouteTable, Route, NetworkSecurityGroup, SecurityRule)
from azure.mgmt.resource.resources.models import DeploymentProperties

from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.arm import ArmTemplateBuilder
from azure.cli.core.util import sdk_no_wait

from azure.cli.command_modules.network._client_factory import network_client_factory

VERSION_2019_02_01 = "2019-02-01"

logger = get_logger(__name__)


def list_appserviceenvironments(cmd, resource_group_name=None):
    ase_client = _get_ase_client_factory(cmd.cli_ctx, VERSION_2019_02_01)
    if resource_group_name is None:
        return ase_client.list()
    return ase_client.list_by_resource_group(resource_group_name)


def show_appserviceenvironment(cmd, name, resource_group_name=None):
    ase_client = _get_ase_client_factory(cmd.cli_ctx, VERSION_2019_02_01)
    if resource_group_name is None:
        resource_group_name = _get_resource_group_name_from_ase(ase_client, name)
    return ase_client.get(resource_group_name, name)


def create_appserviceenvironment_arm(cmd, resource_group_name, name, subnet, vnet_name=None, ignore_route_table=False,
                                     ignore_network_security_group=False, virtual_ip_type='Internal',
                                     front_end_scale_factor=None, front_end_sku=None, force_route_table=False,
                                     force_network_security_group=False, ignore_subnet_size_validation=False,
                                     location=None, no_wait=False):
    # The current SDK has a couple of challenges creating ASE. The current swagger version used,
    # did not have 201 as valid response code, and thus will fail with polling operations.
    # The Load Balancer Type is an Enum Flag, that is expressed as a simple string enum in swagger,
    # and thus will not allow you to define an Internal ASE (combining web and publishing flag).
    # Therefore the current method use direct ARM.
    location = location or _get_location_from_resource_group(cmd.cli_ctx, resource_group_name)
    subnet_id = _validate_subnet_id(cmd.cli_ctx, subnet, vnet_name, resource_group_name)

    _validate_subnet_empty(cmd.cli_ctx, subnet_id)
    if not ignore_subnet_size_validation:
        _validate_subnet_size(cmd.cli_ctx, subnet_id)
    if not ignore_route_table:
        _ensure_route_table(cmd.cli_ctx, resource_group_name, name, location, subnet_id, force_route_table)
    if not ignore_network_security_group:
        _ensure_network_security_group(cmd.cli_ctx, resource_group_name, name, location,
                                       subnet_id, force_network_security_group)

    logger.info('Create App Service Environment...')
    deployment_name = _get_unique_deployment_name('cli_ase_deploy_')
    ase_deployment_properties = _build_ase_deployment_properties(name, location, subnet_id, virtual_ip_type,
                                                                 front_end_scale_factor, front_end_sku, None)
    deployment_client = _get_deployment_client_factory(cmd.cli_ctx)
    return sdk_no_wait(no_wait, deployment_client.create_or_update,
                       resource_group_name, deployment_name, ase_deployment_properties)


def delete_appserviceenvironment(cmd, name, resource_group_name=None, no_wait=False):
    ase_client = _get_ase_client_factory(cmd.cli_ctx, VERSION_2019_02_01)
    if resource_group_name is None:
        resource_group_name = _get_resource_group_name_from_ase(ase_client, name)

    return sdk_no_wait(no_wait, ase_client.delete,
                       resource_group_name=resource_group_name, name=name)


def update_appserviceenvironment(cmd, name, resource_group_name=None, front_end_scale_factor=None,
                                 front_end_sku=None, no_wait=False):
    ase_client = _get_ase_client_factory(cmd.cli_ctx, VERSION_2019_02_01)
    if resource_group_name is None:
        resource_group_name = _get_resource_group_name_from_ase(ase_client, name)
    ase_def = ase_client.get(resource_group_name, name)
    worker_sku = _map_worker_sku(front_end_sku)
    ase_def.worker_pools = ase_def.worker_pools or []  # v1 feature, but cannot be null
    ase_def.internal_load_balancing_mode = None  # Workaround issue with flag enums in Swagger
    if worker_sku:
        ase_def.multi_size = worker_sku
    if front_end_scale_factor:
        ase_def.front_end_scale_factor = front_end_scale_factor

    return sdk_no_wait(no_wait, ase_client.create_or_update, resource_group_name=resource_group_name,
                       name=name, hosting_environment_envelope=ase_def)


def list_appserviceenvironment_addresses(cmd, name, resource_group_name=None):
    ase_client = _get_ase_client_factory(cmd.cli_ctx, VERSION_2019_02_01)
    if resource_group_name is None:
        resource_group_name = _get_resource_group_name_from_ase(ase_client, name)
    return ase_client.list_vips(resource_group_name, name)


def list_appserviceenvironment_plans(cmd, name, resource_group_name=None):
    ase_client = _get_ase_client_factory(cmd.cli_ctx, VERSION_2019_02_01)
    if resource_group_name is None:
        resource_group_name = _get_resource_group_name_from_ase(ase_client, name)

    return ase_client.list_app_service_plans(resource_group_name, name)


def _get_ase_client_factory(cli_ctx, api_version=None):
    from azure.mgmt.web import WebSiteManagementClient
    client = get_mgmt_service_client(cli_ctx, WebSiteManagementClient).app_service_environments
    if api_version:
        client.api_version = api_version
    return client


def _get_deployment_client_factory(cli_ctx):
    from azure.mgmt.resource import ResourceManagementClient
    client = get_mgmt_service_client(cli_ctx, ResourceManagementClient).deployments
    return client


def _get_network_client_factory(cli_ctx):
    from azure.mgmt.network import NetworkManagementClient
    client = get_mgmt_service_client(cli_ctx, NetworkManagementClient)
    return client


def _get_location_from_resource_group(cli_ctx, resource_group_name):
    from azure.mgmt.resource import ResourceManagementClient
    client = get_mgmt_service_client(cli_ctx, ResourceManagementClient)
    group = client.resource_groups.get(resource_group_name)
    return group.location


def _get_resource_group_name_from_ase(ase_client, ase_name):
    resource_group = None
    ase_list = ase_client.list()
    ase_found = False
    for ase in ase_list:
        if ase.name.lower() == ase_name.lower():
            resource_group = ase.resource_group
            ase_found = True
            break
    if not ase_found:
        raise CLIError("App service environment '{}' not found in subscription.".format(ase_name))
    return resource_group


def _validate_subnet_id(cli_ctx, subnet, vnet_name, resource_group_name):
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


def _map_worker_sku(sku_name):
    switcher = {
        'I1': 'Standard_D1_V2',
        'I2': 'Standard_D2_V2',
        'I3': 'Standard_D3_V2'
    }
    return switcher.get(sku_name, None)


def _validate_subnet_empty(cli_ctx, subnet_id):
    from msrestazure.tools import parse_resource_id
    subnet_id_parts = parse_resource_id(subnet_id)
    vnet_resource_group = subnet_id_parts['resource_group']
    vnet_name = subnet_id_parts['name']
    subnet_name = subnet_id_parts['resource_name']
    network_client = _get_network_client_factory(cli_ctx)
    subnet_obj = network_client.subnets.get(vnet_resource_group, vnet_name, subnet_name)
    if subnet_obj.resource_navigation_links:
        raise CLIError('Subnet is not empty.')


def _validate_subnet_size(cli_ctx, subnet_id):
    from msrestazure.tools import parse_resource_id
    subnet_id_parts = parse_resource_id(subnet_id)
    vnet_resource_group = subnet_id_parts['resource_group']
    vnet_name = subnet_id_parts['name']
    subnet_name = subnet_id_parts['resource_name']
    network_client = _get_network_client_factory(cli_ctx)
    subnet_obj = network_client.subnets.get(vnet_resource_group, vnet_name, subnet_name)
    address = subnet_obj.address_prefix
    size = int(address[address.index('/') + 1:])
    if size > 24:
        raise CLIError('Subnet is too small. Should be at least /24.')


def _ensure_route_table(cli_ctx, resource_group_name, ase_name, location, subnet_id, force):
    from msrestazure.tools import parse_resource_id
    subnet_id_parts = parse_resource_id(subnet_id)
    vnet_resource_group = subnet_id_parts['resource_group']
    vnet_name = subnet_id_parts['name']
    subnet_name = subnet_id_parts['resource_name']
    ase_route_table_name = ase_name + '-Route-Table'
    ase_route_name = ase_name + '-route'
    network_client = network_client_factory(cli_ctx)

    subnet_obj = network_client.subnets.get(vnet_resource_group, vnet_name, subnet_name)
    if subnet_obj.route_table is None or force:
        rt_list = network_client.route_tables.list(resource_group_name)
        rt_found = False
        for rt in list(rt_list):
            if rt.name.lower() == ase_route_table_name.lower():
                rt_found = True
                break

        if not rt_found:
            logger.info('Ensure Route Table...')
            ase_route_table = RouteTable(location=location)
            poller = network_client.route_tables.create_or_update(resource_group_name,
                                                                  ase_route_table_name, ase_route_table)
            LongRunningOperation(cli_ctx)(poller)

            logger.info('Ensure Internet Route...')
            internet_route = Route(address_prefix='0.0.0.0/0', next_hop_type='Internet')
            poller = network_client.routes.create_or_update(resource_group_name, ase_route_table_name,
                                                            ase_route_name, internet_route)
            LongRunningOperation(cli_ctx)(poller)

        rt = network_client.route_tables.get(resource_group_name, ase_route_table_name)
        if not subnet_obj.route_table or subnet_obj.route_table.id != rt.id:
            logger.info('Associate Route Table with Subnet...')
            subnet_obj.route_table = rt
            poller = network_client.subnets.create_or_update(
                vnet_resource_group, vnet_name,
                subnet_name, subnet_parameters=subnet_obj)
            LongRunningOperation(cli_ctx)(poller)
    else:
        route_table_id_parts = parse_resource_id(subnet_obj.route_table.id)
        rt_name = route_table_id_parts['name']
        if rt_name.lower() != ase_route_table_name.lower():
            raise CLIError('Route table already exists. \
                            Use --ignore-route-table to use existing route table. \
                            Use --force-route-table to replace existing route table')


def _ensure_network_security_group(cli_ctx, resource_group_name, ase_name, location, subnet_id, force):
    from msrestazure.tools import parse_resource_id
    subnet_id_parts = parse_resource_id(subnet_id)
    vnet_resource_group = subnet_id_parts['resource_group']
    vnet_name = subnet_id_parts['name']
    subnet_name = subnet_id_parts['resource_name']
    ase_nsg_name = ase_name + '-NSG'
    network_client = network_client_factory(cli_ctx)

    subnet_obj = network_client.subnets.get(vnet_resource_group, vnet_name, subnet_name)
    subnet_address_prefix = subnet_obj.address_prefix
    if subnet_obj.network_security_group is None or force:
        nsg_list = network_client.network_security_groups.list(resource_group_name)
        nsg_found = False
        for nsg in list(nsg_list):
            if nsg.name.lower() == ase_nsg_name.lower():
                nsg_found = True
                break

        if not nsg_found:
            logger.info('Ensure Network Security Group...')
            ase_nsg = NetworkSecurityGroup(location=location)
            poller = network_client.network_security_groups.create_or_update(resource_group_name, ase_nsg_name, ase_nsg)
            LongRunningOperation(cli_ctx)(poller)

            logger.info('Ensure Network Security Group Rules...')
            _create_nsg_rule(cli_ctx, resource_group_name, ase_nsg_name, 'Inbound-management',
                             100, 'Used to manage ASE from public VIP', '*', 'Allow', 'Inbound',
                             '*', 'AppServiceManagement', '454-455', '*')
            _create_nsg_rule(cli_ctx, resource_group_name, ase_nsg_name, 'Inbound-load-balancer-keep-alive',
                             105, 'Allow communication to ASE from Load Balancer', '*', 'Allow', 'Inbound',
                             '*', 'AzureLoadBalancer', '16001', '*')
            _create_nsg_rule(cli_ctx, resource_group_name, ase_nsg_name, 'ASE-internal-inbound',
                             110, 'ASE-internal-inbound', '*', 'Allow', 'Inbound',
                             '*', subnet_address_prefix, '*', '*')
            _create_nsg_rule(cli_ctx, resource_group_name, ase_nsg_name, 'Inbound-HTTP',
                             120, 'Allow HTTP', '*', 'Allow', 'Inbound',
                             '*', '*', '80', '*')
            _create_nsg_rule(cli_ctx, resource_group_name, ase_nsg_name, 'Inbound-HTTPS',
                             130, 'Allow HTTPS', '*', 'Allow', 'Inbound',
                             '*', '*', '443', '*')
            _create_nsg_rule(cli_ctx, resource_group_name, ase_nsg_name, 'Inbound-FTP',
                             140, 'Allow FTP', '*', 'Allow', 'Inbound',
                             '*', '*', '21', '*')
            _create_nsg_rule(cli_ctx, resource_group_name, ase_nsg_name, 'Inbound-FTPS',
                             150, 'Allow FTPS', '*', 'Allow', 'Inbound',
                             '*', '*', '990', '*')
            _create_nsg_rule(cli_ctx, resource_group_name, ase_nsg_name, 'Inbound-FTP-Data',
                             160, 'Allow FTP Data', '*', 'Allow', 'Inbound',
                             '*', '*', '10001-10020', '*')
            _create_nsg_rule(cli_ctx, resource_group_name, ase_nsg_name, 'Inbound-Remote-Debugging',
                             170, 'Visual Studio remote debugging', '*', 'Allow', 'Inbound',
                             '*', '*', '4016-4022', '*')
            _create_nsg_rule(cli_ctx, resource_group_name, ase_nsg_name, 'Outbound-443',
                             100, 'Azure Storage blob', '*', 'Allow', 'Outbound',
                             '*', '*', '443', '*')
            _create_nsg_rule(cli_ctx, resource_group_name, ase_nsg_name, 'Outbound-DB',
                             110, 'Database', '*', 'Allow', 'Outbound',
                             '*', '*', '1433', 'Sql')
            _create_nsg_rule(cli_ctx, resource_group_name, ase_nsg_name, 'Outbound-DNS',
                             120, 'DNS', '*', 'Allow', 'Outbound',
                             '*', '*', '53', '*')
            _create_nsg_rule(cli_ctx, resource_group_name, ase_nsg_name, 'ASE-internal-outbound',
                             130, 'Azure Storage queue', '*', 'Allow', 'Outbound',
                             '*', '*', '*', subnet_address_prefix)
            _create_nsg_rule(cli_ctx, resource_group_name, ase_nsg_name, 'Outbound-80',
                             140, 'Outbound 80', '*', 'Allow', 'Outbound',
                             '*', '*', '80', '*')
            _create_nsg_rule(cli_ctx, resource_group_name, ase_nsg_name, 'Outbound-monitor',
                             150, 'Azure Monitor', '*', 'Allow', 'Outbound',
                             '*', '*', 12000, '*')
            _create_nsg_rule(cli_ctx, resource_group_name, ase_nsg_name, 'Outbound-NTP',
                             160, 'Clock', '*', 'Allow', 'Outbound',
                             '*', '*', '123', '*')

        nsg = network_client.network_security_groups.get(resource_group_name, ase_nsg_name)
        if not subnet_obj.network_security_group or subnet_obj.network_security_group.id != nsg.id:
            logger.info('Associate Network Security Group with Subnet...')
            subnet_obj.network_security_group = NetworkSecurityGroup(id=nsg.id)
            poller = network_client.subnets.create_or_update(
                vnet_resource_group, vnet_name,
                subnet_name, subnet_parameters=subnet_obj)
            LongRunningOperation(cli_ctx)(poller)
    else:
        nsg_id_parts = parse_resource_id(subnet_obj.network_security_group.id)
        nsg_name = nsg_id_parts['name']
        if nsg_name.lower() != ase_nsg_name.lower():
            raise CLIError('Network Security Group already exists. \
                            Use --ignore-network-security-group to use existing NSG. \
                            Use --force-network-security-group to replace existing NSG')


def _get_unique_deployment_name(prefix):
    from azure.cli.core.util import random_string
    return prefix + random_string(16)


def _build_ase_deployment_properties(name, location, subnet_id, virtual_ip_type,
                                     front_end_scale_factor=None, front_end_sku=None, tags=None):
    # InternalLoadBalancingMode Enum: None 0, Web 1, Publishing 2.
    # External: 0 (None), Internal: 3 (Web + Publishing)
    ilb_mode = 3 if virtual_ip_type == 'Internal' else 0
    ase_properties = {
        'name': name,
        'location': location,
        'InternalLoadBalancingMode': ilb_mode,
        'virtualNetwork': {
            'Id': subnet_id
        }
    }
    if front_end_scale_factor:
        ase_properties['frontEndScaleFactor'] = front_end_scale_factor
    if front_end_sku:
        worker_sku = _map_worker_sku(front_end_sku)
        ase_properties['multiSize'] = worker_sku

    ase_resource = {
        'name': name,
        'type': 'Microsoft.Web/hostingEnvironments',
        'location': location,
        'apiVersion': '2019-02-01',
        'kind': 'ASEV2',
        'tags': tags,
        'properties': ase_properties
    }

    deployment_template = ArmTemplateBuilder()
    deployment_template.add_resource(ase_resource)
    template = deployment_template.build()
    parameters = deployment_template.build_parameters()

    deployment = DeploymentProperties(template=template, parameters=parameters, mode='incremental')
    return deployment


def _create_nsg_rule(cli_ctx, resource_group_name, network_security_group_name, security_rule_name,
                     priority, description=None, protocol=None, access=None, direction=None,
                     source_port_range='*', source_address_prefix='*',
                     destination_port_range=80, destination_address_prefix='*'):
    settings = SecurityRule(protocol=protocol, source_address_prefix=source_address_prefix,
                            destination_address_prefix=destination_address_prefix, access=access,
                            direction=direction,
                            description=description, source_port_range=source_port_range,
                            destination_port_range=destination_port_range, priority=priority,
                            name=security_rule_name)

    network_client = network_client_factory(cli_ctx)
    poller = network_client.security_rules.create_or_update(
        resource_group_name, network_security_group_name, security_rule_name, settings)
    LongRunningOperation(cli_ctx)(poller)
