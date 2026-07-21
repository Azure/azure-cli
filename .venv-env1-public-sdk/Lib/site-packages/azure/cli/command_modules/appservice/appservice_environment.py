# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Management Clients
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.privatedns import PrivateDnsManagementClient

# Models
from azure.mgmt.resource.deployments.models import (DeploymentProperties, Deployment)
from azure.mgmt.resource.resources.models import SubResource
from azure.mgmt.privatedns.models import (PrivateZone, VirtualNetworkLink, RecordSet, ARecord)

# Utils
from azure.mgmt.core.tools import (parse_resource_id, is_valid_resource_id, resource_id)
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.commands.client_factory import (get_mgmt_service_client, get_subscription_id)
from azure.cli.core.commands.arm import ArmTemplateBuilder
from azure.cli.core.util import (sdk_no_wait, random_string)
from azure.cli.core.azclierror import (ResourceNotFoundError, ValidationError,
                                       MutuallyExclusiveArgumentError)
from importlib import import_module
from knack.log import get_logger

VERSION_2019_08_01 = "2019-08-01"
VERSION_2019_10_01 = "2019-10-01"
# ad-hoc api version 2020-04-01
appservice = "azure.cli.command_modules.appservice"
NSG = import_module(".aaz.profile_2020_09_01_hybrid.network.nsg", package=appservice)
NSGRule = import_module(".aaz.profile_2020_09_01_hybrid.network.nsg.rule", package=appservice)
RouteTable = import_module(".aaz.profile_2020_09_01_hybrid.network.route_table", package=appservice)
RouteTableRoute = import_module(".aaz.profile_2020_09_01_hybrid.network.route_table.route", package=appservice)
Subnet = import_module(".aaz.profile_2020_09_01_hybrid.network.vnet.subnet", package=appservice)

logger = get_logger(__name__)


def list_appserviceenvironments(cmd, resource_group_name=None):
    ase_client = _get_ase_client_factory(cmd.cli_ctx)
    if resource_group_name is None:
        return ase_client.list()
    return ase_client.list_by_resource_group(resource_group_name)


def show_appserviceenvironment(cmd, name, resource_group_name=None):
    ase_client = _get_ase_client_factory(cmd.cli_ctx)
    if resource_group_name is None:
        resource_group_name = _get_resource_group_name_from_ase(ase_client, name)
    return ase_client.get(resource_group_name, name)


def create_appserviceenvironment_arm(cmd, resource_group_name, name, subnet, kind='ASEv3',
                                     vnet_name=None, virtual_ip_type='Internal', ignore_subnet_size_validation=False,
                                     location=None, no_wait=False, zone_redundant=None):
    # The current SDK has a couple of challenges creating ASE. The current swagger version used,
    # did not have 201 as valid response code, and thus will fail with polling operations.
    # The Load Balancer Type is an Enum Flag, that is expressed as a simple string enum in swagger,
    # and thus will not allow you to define an Internal ASE (combining web and publishing flag).
    # Therefore the current method use direct ARM.
    location = location or _get_location_from_resource_group(cmd.cli_ctx, resource_group_name)
    subnet_id = _validate_subnet_id(cmd.cli_ctx, subnet, vnet_name, resource_group_name)
    deployment_name = _get_unique_deployment_name('cli_ase_deploy_')
    _validate_subnet_empty(cmd.cli_ctx, subnet_id)
    if not ignore_subnet_size_validation:
        _validate_subnet_size(cmd.cli_ctx, subnet_id)

    if kind != 'ASEv3':
        raise ValidationError('Invalid App Service Environment kind. Only ASEv3 is supported.')

    _ensure_subnet_delegation(cmd.cli_ctx, subnet_id, 'Microsoft.Web/hostingEnvironments')
    ase_deployment_properties = _build_ase_deployment_properties(name=name, location=location,
                                                                 subnet_id=subnet_id, kind='ASEv3',
                                                                 virtual_ip_type=virtual_ip_type,
                                                                 zone_redundant=zone_redundant)
    logger.info('Create App Service Environment...')
    deployment_client = _get_resource_client_factory(cmd.cli_ctx).deployments
    return sdk_no_wait(no_wait, deployment_client.begin_create_or_update,
                       resource_group_name, deployment_name, ase_deployment_properties)


def delete_appserviceenvironment(cmd, name, resource_group_name=None, no_wait=False):
    ase_client = _get_ase_client_factory(cmd.cli_ctx)
    if resource_group_name is None:
        resource_group_name = _get_resource_group_name_from_ase(ase_client, name)

    return sdk_no_wait(no_wait, ase_client.begin_delete,
                       resource_group_name=resource_group_name, name=name)


def update_appserviceenvironment(cmd, name, resource_group_name=None, allow_new_private_endpoint_connections=None,
                                 allow_incoming_ftp_connections=None, allow_remote_debugging=None):
    ase_client = _get_ase_client_factory(cmd.cli_ctx)
    if resource_group_name is None:
        resource_group_name = _get_resource_group_name_from_ase(ase_client, name)
    ase_def = ase_client.get(resource_group_name, name)
    if ase_def.kind.lower() == 'asev3':
        ase_networking_conf = ase_client.get_ase_v3_networking_configuration(resource_group_name, name)
        config_update = False
        if allow_remote_debugging is not None or allow_incoming_ftp_connections is not None \
           or allow_new_private_endpoint_connections is not None:
            if ase_networking_conf.remote_debug_enabled != allow_remote_debugging:
                ase_networking_conf.remote_debug_enabled = allow_remote_debugging
                config_update = True
            if ase_networking_conf.ftp_enabled != allow_incoming_ftp_connections:
                ase_networking_conf.ftp_enabled = allow_incoming_ftp_connections
                config_update = True
            if ase_networking_conf.allow_new_private_endpoint_connections != allow_new_private_endpoint_connections:
                ase_networking_conf.allow_new_private_endpoint_connections = allow_new_private_endpoint_connections
                config_update = True
        if config_update:
            return ase_client.update_ase_networking_configuration(resource_group_name=resource_group_name,
                                                                  name=name,
                                                                  ase_networking_configuration=ase_networking_conf)

    raise ValidationError('No updates were applied. The version of ASE may not be \
                          applicable to this update or no valid updates where made.')


def upgrade_appserviceenvironment(cmd, name, resource_group_name=None, no_wait=False):
    ase_client = _get_ase_client_factory(cmd.cli_ctx)
    if resource_group_name is None:
        resource_group_name = _get_resource_group_name_from_ase(ase_client, name)
    ase_def = ase_client.get(resource_group_name, name)
    if ase_def.kind.lower() == 'asev3':
        if ase_def.upgrade_preference == "Manual":
            if ase_def.upgrade_availability == "Ready":
                sdk_no_wait(no_wait, ase_client.begin_upgrade,
                            resource_group_name=resource_group_name, name=name)
            else:
                raise ValidationError('An upgrade is not available for your ASEv3.')
        else:
            raise ValidationError('Upgrade preference in ASEv3 must be set to manual, please check \
https://learn.microsoft.com/azure/app-service/environment/how-to-upgrade-preference for more information.')
    else:
        raise ValidationError('No upgrade has been applied. This version of ASE not support upgrade.')


def send_test_notification_appserviceenvironment(cmd, name, resource_group_name=None):
    ase_client = _get_ase_client_factory(cmd.cli_ctx)
    if resource_group_name is None:
        resource_group_name = _get_resource_group_name_from_ase(ase_client, name)
    ase_def = ase_client.get(resource_group_name, name)
    if ase_def.kind.lower() == 'asev3':
        if ase_def.upgrade_preference == "Manual":
            ase_client.test_upgrade_available_notification(resource_group_name=resource_group_name,
                                                           name=name)
            logger.info('The test notification is being processed.')
        else:
            raise ValidationError('Upgrade preference in ASEv3 must be set to manual, please check \
https://learn.microsoft.com/azure/app-service/environment/how-to-upgrade-preference for more information.')
    else:
        raise ValidationError('The test notification has not been processed. \
This version of ASE does not support test notification.')


def list_appserviceenvironment_addresses(cmd, name, resource_group_name=None):
    ase_client = _get_ase_client_factory(cmd.cli_ctx)
    if resource_group_name is None:
        resource_group_name = _get_resource_group_name_from_ase(ase_client, name)
    ase = ase_client.get(resource_group_name, name)
    if ase.kind.lower() == 'asev3':
        return ase_client.get_ase_v3_networking_configuration(resource_group_name, name)
    return ase_client.get_vip_info(resource_group_name, name)


def list_appserviceenvironment_plans(cmd, name, resource_group_name=None):
    ase_client = _get_ase_client_factory(cmd.cli_ctx)
    if resource_group_name is None:
        resource_group_name = _get_resource_group_name_from_ase(ase_client, name)
    return ase_client.list_app_service_plans(resource_group_name, name)


def create_ase_inbound_services(cmd, resource_group_name, name, subnet, vnet_name=None, skip_dns=False):
    ase_client = _get_ase_client_factory(cmd.cli_ctx)
    ase = ase_client.get(resource_group_name, name)
    if not ase:
        raise ResourceNotFoundError("App Service Environment '{}' not found.".format(name))

    if ase.internal_load_balancing_mode == 'None':
        raise ValidationError('Private DNS Zone is not relevant for External ASE.')

    if ase.kind.lower() == 'asev3':
        ase_network_conf = ase_client.get_ase_v3_networking_configuration(resource_group_name, name)
        inbound_ip_address = ase_network_conf.internal_inbound_ip_addresses[0]

    inbound_subnet_id = _validate_subnet_id(cmd.cli_ctx, subnet, vnet_name, resource_group_name)
    inbound_vnet_id = _get_vnet_id_from_subnet(cmd.cli_ctx, inbound_subnet_id)

    if not skip_dns:
        _ensure_ase_private_dns_zone(cmd.cli_ctx, resource_group_name=resource_group_name, name=name,
                                     inbound_vnet_id=inbound_vnet_id, inbound_ip_address=inbound_ip_address)
    else:
        logger.warning('Parameter --skip-dns is deprecated.')


def _get_ase_client_factory(cli_ctx, api_version=None):
    client = get_mgmt_service_client(cli_ctx, WebSiteManagementClient).app_service_environments
    if api_version:
        client.api_version = api_version
    else:
        client.api_version = VERSION_2019_08_01
    return client


def _get_resource_client_factory(cli_ctx, api_version=None):
    client = get_mgmt_service_client(cli_ctx, ResourceManagementClient)
    if api_version:
        client.api_version = api_version
    else:
        client.api_version = VERSION_2019_10_01
    return client


def _get_private_dns_client_factory(cli_ctx):
    client = get_mgmt_service_client(cli_ctx, PrivateDnsManagementClient)
    return client


def _get_location_from_resource_group(cli_ctx, resource_group_name):
    resource_group_client = _get_resource_client_factory(cli_ctx).resource_groups
    group = resource_group_client.get(resource_group_name)
    return group.location


def _get_resource_group_name_from_ase(ase_client, ase_name):
    resource_group = None
    ase_list = ase_client.list()
    ase_found = False
    for ase in ase_list:
        if ase.name.lower() == ase_name.lower():
            ase_id_parts = parse_resource_id(ase.id)
            resource_group = ase_id_parts['resource_group']
            ase_found = True
            break
    if not ase_found:
        raise ResourceNotFoundError("App Service Environment '{}' not found in subscription.".format(ase_name))
    return resource_group


def _validate_subnet_id(cli_ctx, subnet, vnet_name, resource_group_name):
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
    raise MutuallyExclusiveArgumentError('Please specify either: --subnet ID or (--subnet NAME and --vnet-name NAME)')


def _get_vnet_id_from_subnet(cli_ctx, subnet_id):
    subnet_id_parts = parse_resource_id(subnet_id)
    vnet_resource_group = subnet_id_parts['resource_group']
    vnet_name = subnet_id_parts['name']
    return resource_id(
        subscription=get_subscription_id(cli_ctx),
        resource_group=vnet_resource_group,
        namespace='Microsoft.Network',
        type='virtualNetworks',
        name=vnet_name)


def _validate_subnet_empty(cli_ctx, subnet_id):
    subnet_id_parts = parse_resource_id(subnet_id)
    vnet_resource_group = subnet_id_parts['resource_group']
    vnet_name = subnet_id_parts['name']
    subnet_name = subnet_id_parts['resource_name']
    subnet_obj = Subnet.Show(cli_ctx=cli_ctx)(command_args={
        "name": subnet_name,
        "vnet_name": vnet_name,
        "resource_group": vnet_resource_group
    })
    if subnet_obj.get("resourceNavigationLinks", None) or subnet_obj.get("serviceAssociationLinks", None):
        raise ValidationError('Subnet is not empty.')


def _validate_subnet_size(cli_ctx, subnet_id):
    subnet_id_parts = parse_resource_id(subnet_id)
    vnet_resource_group = subnet_id_parts['resource_group']
    vnet_name = subnet_id_parts['name']
    subnet_name = subnet_id_parts['resource_name']
    subnet_obj = Subnet.Show(cli_ctx=cli_ctx)(command_args={
        "name": subnet_name,
        "vnet_name": vnet_name,
        "resource_group": vnet_resource_group
    })
    address = subnet_obj["addressPrefix"]
    size = int(address[address.index('/') + 1:])
    if size > 24:
        err_msg = 'Subnet size could cause scaling issues. Recommended size is at least /24.'
        rec_msg = 'Use --ignore-subnet-size-validation to skip size test.'
        validation_error = ValidationError(err_msg)
        validation_error.set_recommendation(rec_msg)
        raise validation_error


def _ensure_subnet_delegation(cli_ctx, subnet_id, delegation_service_name):
    subnet_id_parts = parse_resource_id(subnet_id)
    vnet_resource_group = subnet_id_parts['resource_group']
    vnet_name = subnet_id_parts['name']
    subnet_name = subnet_id_parts['resource_name']
    subnet_obj = Subnet.Show(cli_ctx=cli_ctx)(command_args={
        "name": subnet_name,
        "vnet_name": vnet_name,
        "resource_group": vnet_resource_group
    })

    delegations = subnet_obj["delegations"]
    delegated = False
    for d in delegations:
        if d["serviceName"].lower() == delegation_service_name.lower():
            delegated = True

    if not delegated:
        try:
            poller = Subnet.Update(cli_ctx=cli_ctx)(command_args={
                "name": subnet_name,
                "vnet_name": vnet_name,
                "resource_group": vnet_resource_group,
                "delegated_services": [{"name": "delegation", "service_name": delegation_service_name}]
            })
            LongRunningOperation(cli_ctx)(poller)
        except Exception:
            err_msg = 'Subnet must be delegated to {}.'.format(delegation_service_name)
            rec_msg = 'Use: az network vnet subnet update --delegations "{}"'.format(delegation_service_name)
            validation_error = ValidationError(err_msg)
            validation_error.set_recommendation(rec_msg)
            raise validation_error


def _get_unique_deployment_name(prefix):
    return prefix + random_string(16)


def _build_ase_deployment_properties(name, location, subnet_id, virtual_ip_type=None,
                                     tags=None, kind='ASEv3', zone_redundant=None):
    # InternalLoadBalancingMode Enum: None 0, Web 1, Publishing 2.
    # External: 0 (None), Internal: 3 (Web + Publishing)
    ilb_mode = 3 if virtual_ip_type == 'Internal' else 0
    ase_properties = {
        'name': name,
        'location': location,
        'InternalLoadBalancingMode': ilb_mode,
        'virtualNetwork': {
            'id': subnet_id
        }
    }
    if zone_redundant:
        ase_properties['zoneRedundant'] = zone_redundant

    ase_resource = {
        'name': name,
        'type': 'Microsoft.Web/hostingEnvironments',
        'location': location,
        'apiVersion': '2019-08-01',
        'kind': kind,
        'tags': tags,
        'properties': ase_properties
    }

    deployment_template = ArmTemplateBuilder()
    deployment_template.add_resource(ase_resource)
    template = deployment_template.build()
    parameters = deployment_template.build_parameters()

    deploymentProperties = DeploymentProperties(template=template, parameters=parameters, mode='Incremental')
    deployment = Deployment(properties=deploymentProperties)
    return deployment


def _ensure_ase_private_dns_zone(cli_ctx, resource_group_name, name, inbound_vnet_id, inbound_ip_address):
    # Private DNS Zone
    private_dns_client = _get_private_dns_client_factory(cli_ctx)
    zone_name = '{}.appserviceenvironment.net'.format(name)
    zone = PrivateZone(location='global', tags=None)
    poller = private_dns_client.private_zones.begin_create_or_update(resource_group_name, zone_name, zone)
    LongRunningOperation(cli_ctx)(poller)

    link_name = '{}_link'.format(name)
    link = VirtualNetworkLink(location='global', tags=None)
    link.virtual_network = SubResource(id=inbound_vnet_id)
    link.registration_enabled = False
    private_dns_client.virtual_network_links.begin_create_or_update(resource_group_name, zone_name,
                                                                    link_name, link, if_none_match='*')
    ase_record = ARecord(ipv4_address=inbound_ip_address)
    record_set = RecordSet(ttl=3600)
    record_set.a_records = [ase_record]
    private_dns_client.record_sets.create_or_update(resource_group_name, zone_name, 'a', '*', record_set)
    private_dns_client.record_sets.create_or_update(resource_group_name, zone_name, 'a', '@', record_set)
    private_dns_client.record_sets.create_or_update(resource_group_name, zone_name, 'a', '*.scm', record_set)
