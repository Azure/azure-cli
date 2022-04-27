# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from collections import Counter, OrderedDict

from msrestazure.tools import parse_resource_id, is_valid_resource_id, resource_id

from knack.log import get_logger

from azure.mgmt.trafficmanager.models import MonitorProtocol, ProfileStatus

# pylint: disable=no-self-use,no-member,too-many-lines,unused-argument
from azure.cli.core.commands import cached_get, cached_put, upsert_to_collection, get_property
from azure.cli.core.commands.client_factory import get_subscription_id, get_mgmt_service_client

from azure.cli.core.util import CLIError, sdk_no_wait, find_child_item, find_child_collection
from azure.cli.core.azclierror import InvalidArgumentValueError, RequiredArgumentMissingError, \
    UnrecognizedArgumentError, ResourceNotFoundError, CLIInternalError, ArgumentUsageError
from azure.cli.core.profiles import ResourceType, supported_api_version

from azure.cli.command_modules.network._client_factory import network_client_factory
from azure.cli.command_modules.network.zone_file.parse_zone_file import parse_zone_file
from azure.cli.command_modules.network.zone_file.make_zone_file import make_zone_file

import threading
import time
import platform
import subprocess
import tempfile

logger = get_logger(__name__)


# region Utility methods
def _log_pprint_template(template):
    import json
    logger.info('==== BEGIN TEMPLATE ====')
    logger.info(json.dumps(template, indent=2))
    logger.info('==== END TEMPLATE ====')


def _get_default_name(balancer, property_name, option_name):
    return _get_default_value(balancer, property_name, option_name, True)


def _get_default_id(balancer, property_name, option_name):
    return _get_default_value(balancer, property_name, option_name, False)


def _get_default_value(balancer, property_name, option_name, return_name):
    values = [x.id for x in getattr(balancer, property_name)]
    if len(values) > 1:
        raise CLIError("Multiple possible values found for '{0}': {1}\nSpecify '{0}' "
                       "explicitly.".format(option_name, ', '.join(values)))
    if not values:
        raise CLIError("No existing values found for '{0}'. Create one first and try "
                       "again.".format(option_name))
    return values[0].rsplit('/', 1)[1] if return_name else values[0]

# endregion


# region Generic list commands
def _generic_list(cli_ctx, operation_name, resource_group_name):
    ncf = network_client_factory(cli_ctx)
    operation_group = getattr(ncf, operation_name)
    if resource_group_name:
        return operation_group.list(resource_group_name)

    return operation_group.list_all()


def list_vnet(cmd, resource_group_name=None):
    return _generic_list(cmd.cli_ctx, 'virtual_networks', resource_group_name)


def list_express_route_circuits(cmd, resource_group_name=None):
    return _generic_list(cmd.cli_ctx, 'express_route_circuits', resource_group_name)


def create_express_route_auth(cmd, resource_group_name, circuit_name, authorization_name):
    ExpressRouteCircuitAuthorization = cmd.get_models('ExpressRouteCircuitAuthorization')

    client = network_client_factory(cmd.cli_ctx).express_route_circuit_authorizations
    return client.begin_create_or_update(resource_group_name,
                                         circuit_name,
                                         authorization_name,
                                         ExpressRouteCircuitAuthorization())


def list_lbs(cmd, resource_group_name=None):
    return _generic_list(cmd.cli_ctx, 'load_balancers', resource_group_name)


def list_nics(cmd, resource_group_name=None):
    return _generic_list(cmd.cli_ctx, 'network_interfaces', resource_group_name)


def list_nsgs(cmd, resource_group_name=None):
    return _generic_list(cmd.cli_ctx, 'network_security_groups', resource_group_name)


def list_nsg_rules(cmd, resource_group_name, network_security_group_name, include_default=False):
    client = network_client_factory(cmd.cli_ctx).network_security_groups
    nsg = client.get(resource_group_name, network_security_group_name)
    rules = nsg.security_rules
    if include_default:
        rules = rules + nsg.default_security_rules
    return rules


def list_custom_ip_prefixes(cmd, resource_group_name=None):
    return _generic_list(cmd.cli_ctx, 'custom_ip_prefixes', resource_group_name)


def list_public_ips(cmd, resource_group_name=None):
    return _generic_list(cmd.cli_ctx, 'public_ip_addresses', resource_group_name)


def list_public_ip_prefixes(cmd, resource_group_name=None):
    return _generic_list(cmd.cli_ctx, 'public_ip_prefixes', resource_group_name)


def list_route_tables(cmd, resource_group_name=None):
    return _generic_list(cmd.cli_ctx, 'route_tables', resource_group_name)


def list_application_gateways(cmd, resource_group_name=None):
    return _generic_list(cmd.cli_ctx, 'application_gateways', resource_group_name)


def list_network_watchers(cmd, resource_group_name=None):
    return _generic_list(cmd.cli_ctx, 'network_watchers', resource_group_name)

# endregion


# region ApplicationGateways
# pylint: disable=too-many-locals
def _is_v2_sku(sku):
    return 'v2' in sku


# pylint: disable=too-many-statements
def create_application_gateway(cmd, application_gateway_name, resource_group_name, location=None,
                               tags=None, no_wait=False, capacity=2,
                               cert_data=None, cert_password=None, key_vault_secret_id=None,
                               frontend_port=None, http_settings_cookie_based_affinity='disabled',
                               http_settings_port=80, http_settings_protocol='Http',
                               routing_rule_type='Basic', servers=None,
                               sku=None,
                               private_ip_address=None, public_ip_address=None,
                               public_ip_address_allocation=None,
                               subnet='default', subnet_address_prefix='10.0.0.0/24',
                               virtual_network_name=None, vnet_address_prefix='10.0.0.0/16',
                               public_ip_address_type=None, subnet_type=None, validate=False,
                               connection_draining_timeout=0, enable_http2=None, min_capacity=None, zones=None,
                               custom_error_pages=None, firewall_policy=None, max_capacity=None,
                               user_assigned_identity=None,
                               enable_private_link=False,
                               private_link_ip_address=None,
                               private_link_subnet='PrivateLinkDefaultSubnet',
                               private_link_subnet_prefix='10.0.1.0/24',
                               private_link_primary=None,
                               trusted_client_cert=None,
                               ssl_profile=None,
                               ssl_profile_id=None,
                               ssl_cert_name=None):
    from azure.cli.core.util import random_string
    from azure.cli.core.commands.arm import ArmTemplateBuilder
    from azure.cli.command_modules.network._template_builder import (
        build_application_gateway_resource, build_public_ip_resource, build_vnet_resource)

    DeploymentProperties = cmd.get_models('DeploymentProperties', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    IPAllocationMethod = cmd.get_models('IPAllocationMethod')

    tags = tags or {}
    sku_tier = sku.split('_', 1)[0] if not _is_v2_sku(sku) else sku
    http_listener_protocol = 'https' if (cert_data or key_vault_secret_id) else 'http'
    private_ip_allocation = 'Static' if private_ip_address else 'Dynamic'
    virtual_network_name = virtual_network_name or '{}Vnet'.format(application_gateway_name)

    # Build up the ARM template
    master_template = ArmTemplateBuilder()
    ag_dependencies = []

    public_ip_id = public_ip_address if is_valid_resource_id(public_ip_address) else None
    subnet_id = subnet if is_valid_resource_id(subnet) else None
    private_ip_allocation = IPAllocationMethod.static.value if private_ip_address \
        else IPAllocationMethod.dynamic.value

    network_id_template = resource_id(
        subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name,
        namespace='Microsoft.Network')

    if subnet_type == 'new':
        ag_dependencies.append('Microsoft.Network/virtualNetworks/{}'.format(virtual_network_name))
        vnet = build_vnet_resource(
            cmd, virtual_network_name, location, tags, vnet_address_prefix, subnet,
            subnet_address_prefix,
            enable_private_link=enable_private_link,
            private_link_subnet=private_link_subnet,
            private_link_subnet_prefix=private_link_subnet_prefix)
        master_template.add_resource(vnet)
        subnet_id = '{}/virtualNetworks/{}/subnets/{}'.format(network_id_template,
                                                              virtual_network_name, subnet)

    if public_ip_address_type == 'new':
        ag_dependencies.append('Microsoft.Network/publicIpAddresses/{}'.format(public_ip_address))
        public_ip_sku = None
        if _is_v2_sku(sku):
            public_ip_sku = 'Standard'
            public_ip_address_allocation = 'Static'
        master_template.add_resource(build_public_ip_resource(cmd, public_ip_address, location,
                                                              tags,
                                                              public_ip_address_allocation,
                                                              None, public_ip_sku, None))
        public_ip_id = '{}/publicIPAddresses/{}'.format(network_id_template,
                                                        public_ip_address)

    private_link_subnet_id = None
    private_link_name = 'PrivateLinkDefaultConfiguration'
    private_link_ip_allocation_method = 'Dynamic'
    if enable_private_link:
        private_link_subnet_id = '{}/virtualNetworks/{}/subnets/{}'.format(network_id_template,
                                                                           virtual_network_name,
                                                                           private_link_subnet)
        private_link_ip_allocation_method = IPAllocationMethod.static.value if private_link_ip_address \
            else IPAllocationMethod.dynamic.value

    app_gateway_resource = build_application_gateway_resource(
        cmd, application_gateway_name, location, tags, sku, sku_tier, capacity, servers, frontend_port,
        private_ip_address, private_ip_allocation, cert_data, cert_password, key_vault_secret_id,
        http_settings_cookie_based_affinity, http_settings_protocol, http_settings_port,
        http_listener_protocol, routing_rule_type, public_ip_id, subnet_id,
        connection_draining_timeout, enable_http2, min_capacity, zones, custom_error_pages,
        firewall_policy, max_capacity, user_assigned_identity,
        enable_private_link, private_link_name,
        private_link_ip_address, private_link_ip_allocation_method, private_link_primary,
        private_link_subnet_id, trusted_client_cert, ssl_profile, ssl_profile_id, ssl_cert_name)

    app_gateway_resource['dependsOn'] = ag_dependencies
    master_template.add_variable(
        'appGwID',
        "[resourceId('Microsoft.Network/applicationGateways', '{}')]".format(
            application_gateway_name))
    master_template.add_resource(app_gateway_resource)
    master_template.add_output('applicationGateway', application_gateway_name, output_type='object')
    if cert_password:
        master_template.add_secure_parameter('certPassword', cert_password)

    template = master_template.build()
    parameters = master_template.build_parameters()

    # deploy ARM template
    deployment_name = 'ag_deploy_' + random_string(32)
    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES).deployments
    properties = DeploymentProperties(template=template, parameters=parameters, mode='incremental')
    Deployment = cmd.get_models('Deployment', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    deployment = Deployment(properties=properties)

    if validate:
        _log_pprint_template(template)
        if cmd.supported_api_version(min_api='2019-10-01', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES):
            from azure.cli.core.commands import LongRunningOperation
            validation_poller = client.begin_validate(resource_group_name, deployment_name, deployment)
            return LongRunningOperation(cmd.cli_ctx)(validation_poller)

        return client.validate(resource_group_name, deployment_name, deployment)

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, deployment_name, deployment)


def update_application_gateway(cmd, instance, sku=None, capacity=None, tags=None, enable_http2=None, min_capacity=None,
                               custom_error_pages=None, max_capacity=None):
    if sku is not None:
        instance.sku.tier = sku.split('_', 1)[0] if not _is_v2_sku(sku) else sku

    try:
        if min_capacity is not None:
            instance.autoscale_configuration.min_capacity = min_capacity
        if max_capacity is not None:
            instance.autoscale_configuration.max_capacity = max_capacity
    except AttributeError:
        instance.autoscale_configuration = {
            'min_capacity': min_capacity,
            'max_capacity': max_capacity
        }

    with cmd.update_context(instance) as c:
        c.set_param('sku.name', sku)
        c.set_param('sku.capacity', capacity)
        c.set_param('tags', tags)
        c.set_param('enable_http2', enable_http2)
        c.set_param('custom_error_configurations', custom_error_pages)
    return instance


def create_ag_authentication_certificate(cmd, resource_group_name, application_gateway_name, item_name,
                                         cert_data, no_wait=False):
    AuthCert = cmd.get_models('ApplicationGatewayAuthenticationCertificate')
    ncf = network_client_factory(cmd.cli_ctx).application_gateways
    ag = ncf.get(resource_group_name, application_gateway_name)
    new_cert = AuthCert(data=cert_data, name=item_name)
    upsert_to_collection(ag, 'authentication_certificates', new_cert, 'name')
    return sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, application_gateway_name, ag)


def update_ag_authentication_certificate(instance, parent, item_name, cert_data):
    instance.data = cert_data
    return parent


def create_ag_backend_address_pool(cmd, resource_group_name, application_gateway_name, item_name,
                                   servers=None, no_wait=False):
    ApplicationGatewayBackendAddressPool = cmd.get_models('ApplicationGatewayBackendAddressPool')
    ncf = network_client_factory(cmd.cli_ctx)
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    new_pool = ApplicationGatewayBackendAddressPool(name=item_name, backend_addresses=servers)
    upsert_to_collection(ag, 'backend_address_pools', new_pool, 'name')
    return sdk_no_wait(no_wait, ncf.application_gateways.begin_create_or_update,
                       resource_group_name, application_gateway_name, ag)


def update_ag_backend_address_pool(instance, parent, item_name, servers=None):
    if servers is not None:
        instance.backend_addresses = servers
    return parent


def create_ag_frontend_ip_configuration(cmd, resource_group_name, application_gateway_name, item_name,
                                        public_ip_address=None, subnet=None,
                                        virtual_network_name=None, private_ip_address=None,
                                        private_ip_address_allocation=None, no_wait=False):
    ApplicationGatewayFrontendIPConfiguration, SubResource = cmd.get_models(
        'ApplicationGatewayFrontendIPConfiguration', 'SubResource')
    ncf = network_client_factory(cmd.cli_ctx)
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    if public_ip_address:
        new_config = ApplicationGatewayFrontendIPConfiguration(
            name=item_name,
            public_ip_address=SubResource(id=public_ip_address))
    else:
        new_config = ApplicationGatewayFrontendIPConfiguration(
            name=item_name,
            private_ip_address=private_ip_address if private_ip_address else None,
            private_ip_allocation_method='Static' if private_ip_address else 'Dynamic',
            subnet=SubResource(id=subnet))
    upsert_to_collection(ag, 'frontend_ip_configurations', new_config, 'name')
    return sdk_no_wait(no_wait, ncf.application_gateways.begin_create_or_update,
                       resource_group_name, application_gateway_name, ag)


def update_ag_frontend_ip_configuration(cmd, instance, parent, item_name, public_ip_address=None,
                                        subnet=None, virtual_network_name=None,
                                        private_ip_address=None):
    SubResource = cmd.get_models('SubResource')
    if public_ip_address is not None:
        instance.public_ip_address = SubResource(id=public_ip_address)
    if subnet is not None:
        instance.subnet = SubResource(id=subnet)
    if private_ip_address is not None:
        instance.private_ip_address = private_ip_address
        instance.private_ip_allocation_method = 'Static'
    return parent


def create_ag_frontend_port(cmd, resource_group_name, application_gateway_name, item_name, port,
                            no_wait=False):
    ApplicationGatewayFrontendPort = cmd.get_models('ApplicationGatewayFrontendPort')
    ncf = network_client_factory(cmd.cli_ctx)
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    new_port = ApplicationGatewayFrontendPort(name=item_name, port=port)
    upsert_to_collection(ag, 'frontend_ports', new_port, 'name')
    return sdk_no_wait(no_wait, ncf.application_gateways.begin_create_or_update,
                       resource_group_name, application_gateway_name, ag)


def update_ag_frontend_port(instance, parent, item_name, port=None):
    if port is not None:
        instance.port = port
    return parent


def create_ag_http_listener(cmd, resource_group_name, application_gateway_name, item_name,
                            frontend_port, frontend_ip=None, host_name=None, ssl_cert=None,
                            ssl_profile_id=None, firewall_policy=None, no_wait=False, host_names=None):
    ApplicationGatewayHttpListener, SubResource = cmd.get_models('ApplicationGatewayHttpListener', 'SubResource')
    ncf = network_client_factory(cmd.cli_ctx)
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    if not frontend_ip:
        frontend_ip = _get_default_id(ag, 'frontend_ip_configurations', '--frontend-ip')
    new_listener = ApplicationGatewayHttpListener(
        name=item_name,
        frontend_ip_configuration=SubResource(id=frontend_ip),
        frontend_port=SubResource(id=frontend_port),
        host_name=host_name,
        require_server_name_indication=True if ssl_cert and host_name else None,
        protocol='https' if ssl_cert else 'http',
        ssl_certificate=SubResource(id=ssl_cert) if ssl_cert else None,
        host_names=host_names
    )

    if cmd.supported_api_version(min_api='2019-09-01'):
        new_listener.firewall_policy = SubResource(id=firewall_policy) if firewall_policy else None

    if cmd.supported_api_version(min_api='2020-06-01'):
        new_listener.ssl_profile = SubResource(id=ssl_profile_id) if ssl_profile_id else None

    upsert_to_collection(ag, 'http_listeners', new_listener, 'name')
    return sdk_no_wait(no_wait, ncf.application_gateways.begin_create_or_update,
                       resource_group_name, application_gateway_name, ag)


def update_ag_http_listener(cmd, instance, parent, item_name, frontend_ip=None, frontend_port=None,
                            host_name=None, ssl_cert=None, ssl_profile_id=None, firewall_policy=None, host_names=None):
    SubResource = cmd.get_models('SubResource')
    if frontend_ip is not None:
        instance.frontend_ip_configuration = SubResource(id=frontend_ip)
    if frontend_port is not None:
        instance.frontend_port = SubResource(id=frontend_port)
    if ssl_cert is not None:
        if ssl_cert:
            instance.ssl_certificate = SubResource(id=ssl_cert)
            instance.protocol = 'Https'
        else:
            instance.ssl_certificate = None
            instance.protocol = 'Http'
    if host_name is not None:
        instance.host_name = host_name or None

    if cmd.supported_api_version(min_api='2019-09-01'):
        if firewall_policy is not None:
            instance.firewall_policy = SubResource(id=firewall_policy)

    if cmd.supported_api_version(min_api='2020-06-01'):
        if ssl_profile_id is not None:
            instance.ssl_profile = SubResource(id=ssl_profile_id)

    if host_names is not None:
        instance.host_names = host_names or None

    instance.require_server_name_indication = instance.host_name and instance.protocol.lower() == 'https'
    return parent


def assign_ag_identity(cmd, resource_group_name, application_gateway_name,
                       user_assigned_identity, no_wait=False):
    ncf = network_client_factory(cmd.cli_ctx).application_gateways
    ag = ncf.get(resource_group_name, application_gateway_name)
    ManagedServiceIdentity, ManagedServiceIdentityUserAssignedIdentitiesValue = \
        cmd.get_models('ManagedServiceIdentity',
                       'Components1Jq1T4ISchemasManagedserviceidentityPropertiesUserassignedidentitiesAdditionalproperties')  # pylint: disable=line-too-long
    user_assigned_indentity_instance = ManagedServiceIdentityUserAssignedIdentitiesValue()

    user_assigned_identities_instance = dict()

    user_assigned_identities_instance[user_assigned_identity] = user_assigned_indentity_instance

    identity_instance = ManagedServiceIdentity(
        type="UserAssigned",
        user_assigned_identities=user_assigned_identities_instance
    )
    ag.identity = identity_instance

    return sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, application_gateway_name, ag)


def remove_ag_identity(cmd, resource_group_name, application_gateway_name, no_wait=False):
    ncf = network_client_factory(cmd.cli_ctx).application_gateways
    ag = ncf.get(resource_group_name, application_gateway_name)
    if ag.identity is None:
        logger.warning("This command will be ignored. The identity doesn't exist.")
    ag.identity = None

    return sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, application_gateway_name, ag)


def show_ag_identity(cmd, resource_group_name, application_gateway_name):
    ncf = network_client_factory(cmd.cli_ctx).application_gateways
    ag = ncf.get(resource_group_name, application_gateway_name)
    if ag.identity is None:
        raise CLIError("Please first use 'az network application-gateway identity assign` to init the identity.")
    return ag.identity


def add_ag_private_link(cmd,
                        resource_group_name,
                        application_gateway_name,
                        frontend_ip,
                        private_link_name,
                        private_link_subnet_name_or_id,
                        private_link_subnet_prefix=None,
                        private_link_primary=None,
                        private_link_ip_address=None,
                        no_wait=False):
    (SubResource, IPAllocationMethod, Subnet,
     ApplicationGatewayPrivateLinkConfiguration,
     ApplicationGatewayPrivateLinkIpConfiguration) = cmd.get_models(
         'SubResource', 'IPAllocationMethod', 'Subnet',
         'ApplicationGatewayPrivateLinkConfiguration', 'ApplicationGatewayPrivateLinkIpConfiguration')

    ncf = network_client_factory(cmd.cli_ctx)

    appgw = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    private_link_config_id = resource_id(
        subscription=get_subscription_id(cmd.cli_ctx),
        resource_group=resource_group_name,
        namespace='Microsoft.Network',
        type='applicationGateways',
        name=appgw.name,
        child_type_1='privateLinkConfigurations',
        child_name_1=private_link_name
    )

    if not any(fic for fic in appgw.frontend_ip_configurations if fic.name == frontend_ip):
        raise CLIError("Frontend IP doesn't exist")

    for fic in appgw.frontend_ip_configurations:
        if fic.private_link_configuration and fic.private_link_configuration.id == private_link_config_id:
            raise CLIError('Frontend IP already reference an existing Private Link')
        if fic.name == frontend_ip:
            break
    else:
        raise CLIError("Frontend IP doesn't exist")

    if appgw.private_link_configurations is not None:
        for pl in appgw.private_link_configurations:
            if pl.name == private_link_name:
                raise CLIError('Private Link name duplicates')

    # get the virtual network of this application gateway
    vnet_name = parse_resource_id(appgw.gateway_ip_configurations[0].subnet.id)['name']
    vnet = ncf.virtual_networks.get(resource_group_name, vnet_name)

    # prepare the subnet for new private link
    for subnet in vnet.subnets:
        if subnet.name == private_link_subnet_name_or_id:
            raise CLIError('Subnet duplicates')
        if subnet.address_prefix == private_link_subnet_prefix:
            raise CLIError('Subnet prefix duplicates')
        if subnet.address_prefixes and private_link_subnet_prefix in subnet.address_prefixes:
            raise CLIError('Subnet prefix duplicates')

    if is_valid_resource_id(private_link_subnet_name_or_id):
        private_link_subnet_id = private_link_subnet_name_or_id
    else:
        private_link_subnet = Subnet(name=private_link_subnet_name_or_id,
                                     address_prefix=private_link_subnet_prefix,
                                     private_link_service_network_policies='Disabled')
        private_link_subnet_id = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=vnet_name,
            child_type_1='subnets',
            child_name_1=private_link_subnet_name_or_id
        )
        vnet.subnets.append(private_link_subnet)
        ncf.virtual_networks.begin_create_or_update(resource_group_name, vnet_name, vnet)

    private_link_ip_allocation_method = IPAllocationMethod.static.value if private_link_ip_address \
        else IPAllocationMethod.dynamic.value
    private_link_ip_config = ApplicationGatewayPrivateLinkIpConfiguration(
        name='PrivateLinkDefaultIPConfiguration',
        private_ip_address=private_link_ip_address,
        private_ip_allocation_method=private_link_ip_allocation_method,
        subnet=SubResource(id=private_link_subnet_id),
        primary=private_link_primary
    )
    private_link_config = ApplicationGatewayPrivateLinkConfiguration(
        name=private_link_name,
        ip_configurations=[private_link_ip_config]
    )

    # associate the private link with the frontend IP configuration
    for fic in appgw.frontend_ip_configurations:
        if fic.name == frontend_ip:
            fic.private_link_configuration = SubResource(id=private_link_config_id)

    if appgw.private_link_configurations is None:
        appgw.private_link_configurations = []
    appgw.private_link_configurations.append(private_link_config)

    return sdk_no_wait(no_wait,
                       ncf.application_gateways.begin_create_or_update,
                       resource_group_name,
                       application_gateway_name, appgw)


def show_ag_private_link(cmd,
                         resource_group_name,
                         application_gateway_name,
                         private_link_name):
    ncf = network_client_factory(cmd.cli_ctx)

    appgw = ncf.application_gateways.get(resource_group_name, application_gateway_name)

    target_private_link = None
    for pl in appgw.private_link_configurations:
        if pl.name == private_link_name:
            target_private_link = pl
            break
    else:
        raise CLIError("Priavte Link doesn't exist")

    return target_private_link


def list_ag_private_link(cmd,
                         resource_group_name,
                         application_gateway_name):
    ncf = network_client_factory(cmd.cli_ctx)

    appgw = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    return appgw.private_link_configurations


def remove_ag_private_link(cmd,
                           resource_group_name,
                           application_gateway_name,
                           private_link_name,
                           no_wait=False):
    ncf = network_client_factory(cmd.cli_ctx)

    appgw = ncf.application_gateways.get(resource_group_name, application_gateway_name)

    removed_private_link = None

    for pl in appgw.private_link_configurations:
        if pl.name == private_link_name:
            removed_private_link = pl
            break
    else:
        raise CLIError("Priavte Link doesn't exist")

    for fic in appgw.frontend_ip_configurations:
        if fic.private_link_configuration and fic.private_link_configuration.id == removed_private_link.id:
            fic.private_link_configuration = None

    # the left vnet have to delete manually
    # rs = parse_resource_id(removed_private_link.ip_configurations[0].subnet.id)
    # vnet_resource_group, vnet_name, subnet = rs['resource_group'], rs['name'], rs['child_name_1']
    # ncf.subnets.delete(vnet_resource_group, vnet_name, subnet)

    appgw.private_link_configurations.remove(removed_private_link)
    return sdk_no_wait(no_wait,
                       ncf.application_gateways.begin_create_or_update,
                       resource_group_name,
                       application_gateway_name,
                       appgw)


# region application-gateway trusted-client-certificates
def add_trusted_client_certificate(cmd, resource_group_name, application_gateway_name, client_cert_name,
                                   client_cert_data, no_wait=False):
    ncf = network_client_factory(cmd.cli_ctx)
    appgw = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    ApplicationGatewayTrustedClientCertificate = cmd.get_models('ApplicationGatewayTrustedClientCertificate')
    cert = ApplicationGatewayTrustedClientCertificate(name=client_cert_name, data=client_cert_data)
    appgw.trusted_client_certificates.append(cert)

    return sdk_no_wait(no_wait, ncf.application_gateways.begin_create_or_update, resource_group_name,
                       application_gateway_name, appgw)


def update_trusted_client_certificate(cmd, resource_group_name, application_gateway_name, client_cert_name,
                                      client_cert_data, no_wait=False):
    ncf = network_client_factory(cmd.cli_ctx)
    appgw = ncf.application_gateways.get(resource_group_name, application_gateway_name)

    for cert in appgw.trusted_client_certificates:
        if cert.name == client_cert_name:
            cert.data = client_cert_data
            break
    else:
        raise ResourceNotFoundError(f"Trusted client certificate {client_cert_name} doesn't exist")

    return sdk_no_wait(no_wait, ncf.application_gateways.begin_create_or_update, resource_group_name,
                       application_gateway_name, appgw)


def list_trusted_client_certificate(cmd, resource_group_name, application_gateway_name):
    ncf = network_client_factory(cmd.cli_ctx)
    appgw = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    return appgw.trusted_client_certificates


def remove_trusted_client_certificate(cmd, resource_group_name, application_gateway_name, client_cert_name,
                                      no_wait=False):
    ncf = network_client_factory(cmd.cli_ctx)
    appgw = ncf.application_gateways.get(resource_group_name, application_gateway_name)

    for cert in appgw.trusted_client_certificates:
        if cert.name == client_cert_name:
            appgw.trusted_client_certificates.remove(cert)
            break
    else:
        raise ResourceNotFoundError(f"Trusted client certificate {client_cert_name} doesn't exist")

    return sdk_no_wait(no_wait, ncf.application_gateways.begin_create_or_update, resource_group_name,
                       application_gateway_name, appgw)


def show_trusted_client_certificate(cmd, resource_group_name, application_gateway_name, client_cert_name):
    ncf = network_client_factory(cmd.cli_ctx)
    appgw = ncf.application_gateways.get(resource_group_name, application_gateway_name)

    instance = None
    for cert in appgw.trusted_client_certificates:
        if cert.name == client_cert_name:
            instance = cert
            break
    else:
        raise ResourceNotFoundError(f"Trusted client certificate {client_cert_name} doesn't exist")

    return instance


def show_ag_backend_health(cmd, client, resource_group_name, application_gateway_name, expand=None,
                           protocol=None, host=None, path=None, timeout=None, host_name_from_http_settings=None,
                           match_body=None, match_status_codes=None, address_pool=None, http_settings=None):
    from azure.cli.core.commands import LongRunningOperation
    on_demand_arguments = {protocol, host, path, timeout, host_name_from_http_settings, match_body, match_status_codes,
                           address_pool, http_settings}
    if on_demand_arguments.difference({None}) and cmd.supported_api_version(min_api='2019-04-01'):
        SubResource, ApplicationGatewayOnDemandProbe, ApplicationGatewayProbeHealthResponseMatch = cmd.get_models(
            "SubResource", "ApplicationGatewayOnDemandProbe", "ApplicationGatewayProbeHealthResponseMatch")
        probe_request = ApplicationGatewayOnDemandProbe(
            protocol=protocol,
            host=host,
            path=path,
            timeout=timeout,
            pick_host_name_from_backend_http_settings=host_name_from_http_settings
        )
        if match_body is not None or match_status_codes is not None:
            probe_request.match = ApplicationGatewayProbeHealthResponseMatch(
                body=match_body,
                status_codes=match_status_codes,
            )
        if address_pool is not None:
            if not is_valid_resource_id(address_pool):
                address_pool = resource_id(
                    subscription=get_subscription_id(cmd.cli_ctx),
                    resource_group=resource_group_name,
                    namespace='Microsoft.Network',
                    type='applicationGateways',
                    name=application_gateway_name,
                    child_type_1='backendAddressPools',
                    child_name_1=address_pool
                )
            probe_request.backend_address_pool = SubResource(id=address_pool)
        if http_settings is not None:
            if not is_valid_resource_id(http_settings):
                http_settings = resource_id(
                    subscription=get_subscription_id(cmd.cli_ctx),
                    resource_group=resource_group_name,
                    namespace='Microsoft.Network',
                    type='applicationGateways',
                    name=application_gateway_name,
                    child_type_1='backendHttpSettingsCollection',
                    child_name_1=http_settings
                )
            probe_request.backend_http_settings = SubResource(id=http_settings)
        return LongRunningOperation(cmd.cli_ctx)(client.begin_backend_health_on_demand(
            resource_group_name, application_gateway_name, probe_request, expand))

    return LongRunningOperation(cmd.cli_ctx)(client.begin_backend_health(
        resource_group_name, application_gateway_name, expand))

# endregion


# region application-gateway ssl-profile
def add_ssl_profile(cmd, resource_group_name, application_gateway_name, ssl_profile_name, policy_name=None,
                    policy_type=None, min_protocol_version=None, cipher_suites=None, disabled_ssl_protocols=None,
                    trusted_client_certificates=None, client_auth_configuration=None, no_wait=False):
    ncf = network_client_factory(cmd.cli_ctx)
    appgw = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    (SubResource,
     ApplicationGatewaySslPolicy,
     ApplicationGatewayClientAuthConfiguration,
     ApplicationGatewaySslProfile) = cmd.get_models('SubResource',
                                                    'ApplicationGatewaySslPolicy',
                                                    'ApplicationGatewayClientAuthConfiguration',
                                                    'ApplicationGatewaySslProfile')
    sr_trusted_client_certificates = [SubResource(id=item) for item in
                                      trusted_client_certificates] if trusted_client_certificates else None
    ssl_policy = ApplicationGatewaySslPolicy(policy_name=policy_name, policy_type=policy_type,
                                             min_protocol_version=min_protocol_version,
                                             cipher_suites=cipher_suites, disabled_ssl_protocols=disabled_ssl_protocols)
    client_auth = ApplicationGatewayClientAuthConfiguration(
        verify_client_cert_issuer_dn=client_auth_configuration) if client_auth_configuration else None
    ssl_profile = ApplicationGatewaySslProfile(trusted_client_certificates=sr_trusted_client_certificates,
                                               ssl_policy=ssl_policy, client_auth_configuration=client_auth,
                                               name=ssl_profile_name)
    appgw.ssl_profiles.append(ssl_profile)
    return sdk_no_wait(no_wait, ncf.application_gateways.begin_create_or_update, resource_group_name,
                       application_gateway_name, appgw)


def update_ssl_profile(cmd, resource_group_name, application_gateway_name, ssl_profile_name, policy_name=None,
                       policy_type=None, min_protocol_version=None, cipher_suites=None, disabled_ssl_protocols=None,
                       trusted_client_certificates=None, client_auth_configuration=None, no_wait=False):
    ncf = network_client_factory(cmd.cli_ctx)
    appgw = ncf.application_gateways.get(resource_group_name, application_gateway_name)

    instance = None
    for profile in appgw.ssl_profiles:
        if profile.name == ssl_profile_name:
            instance = profile
            break
    else:
        raise ResourceNotFoundError(f"Ssl profiles {ssl_profile_name} doesn't exist")

    if policy_name is not None:
        instance.ssl_policy.policy_name = policy_name
    if policy_type is not None:
        instance.ssl_policy.policy_type = policy_type
    if min_protocol_version is not None:
        instance.ssl_policy.min_protocol_version = min_protocol_version
    if cipher_suites is not None:
        instance.ssl_policy.cipher_suites = cipher_suites
    if disabled_ssl_protocols is not None:
        instance.ssl_policy.disabled_ssl_protocols = disabled_ssl_protocols
    if trusted_client_certificates is not None:
        SubResource = cmd.get_models('SubResource')
        instance.trusted_client_certificates = [SubResource(id=item) for item in trusted_client_certificates]
    if client_auth_configuration is not None:
        ApplicationGatewayClientAuthConfiguration = cmd.get_models('ApplicationGatewayClientAuthConfiguration')
        instance.client_auth_configuration = ApplicationGatewayClientAuthConfiguration(
            verify_client_cert_issuer_dn=(client_auth_configuration == 'True')
        )

    return sdk_no_wait(no_wait, ncf.application_gateways.begin_create_or_update, resource_group_name,
                       application_gateway_name, appgw)


def list_ssl_profile(cmd, resource_group_name, application_gateway_name):
    ncf = network_client_factory(cmd.cli_ctx)
    appgw = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    return appgw.ssl_profiles


def remove_ssl_profile(cmd, resource_group_name, application_gateway_name, ssl_profile_name, no_wait=False):
    ncf = network_client_factory(cmd.cli_ctx)
    appgw = ncf.application_gateways.get(resource_group_name, application_gateway_name)

    for profile in appgw.ssl_profiles:
        if profile.name == ssl_profile_name:
            appgw.ssl_profiles.remove(profile)
            break
    else:
        raise ResourceNotFoundError(f"Ssl profiles {ssl_profile_name} doesn't exist")

    return sdk_no_wait(no_wait, ncf.application_gateways.begin_create_or_update, resource_group_name,
                       application_gateway_name, appgw)


def show_ssl_profile(cmd, resource_group_name, application_gateway_name, ssl_profile_name):
    ncf = network_client_factory(cmd.cli_ctx)
    appgw = ncf.application_gateways.get(resource_group_name, application_gateway_name)

    instance = None
    for profile in appgw.ssl_profiles:
        if profile.name == ssl_profile_name:
            instance = profile
            break
    else:
        raise ResourceNotFoundError(f"Ssl profiles {ssl_profile_name} doesn't exist")
    return instance

# endregion


def add_ag_private_link_ip(cmd,
                           resource_group_name,
                           application_gateway_name,
                           private_link_name,
                           private_link_ip_name,
                           private_link_primary=False,
                           private_link_ip_address=None,
                           no_wait=False):
    ncf = network_client_factory(cmd.cli_ctx)

    appgw = ncf.application_gateways.get(resource_group_name, application_gateway_name)

    target_private_link = None
    for pl in appgw.private_link_configurations:
        if pl.name == private_link_name:
            target_private_link = pl
            break
    else:
        raise CLIError("Priavte Link doesn't exist")

    (SubResource, IPAllocationMethod,
     ApplicationGatewayPrivateLinkIpConfiguration) = \
        cmd.get_models('SubResource', 'IPAllocationMethod',
                       'ApplicationGatewayPrivateLinkIpConfiguration')

    private_link_subnet_id = target_private_link.ip_configurations[0].subnet.id

    private_link_ip_allocation_method = IPAllocationMethod.static.value if private_link_ip_address \
        else IPAllocationMethod.dynamic.value
    private_link_ip_config = ApplicationGatewayPrivateLinkIpConfiguration(
        name=private_link_ip_name,
        private_ip_address=private_link_ip_address,
        private_ip_allocation_method=private_link_ip_allocation_method,
        subnet=SubResource(id=private_link_subnet_id),
        primary=private_link_primary
    )

    target_private_link.ip_configurations.append(private_link_ip_config)

    return sdk_no_wait(no_wait,
                       ncf.application_gateways.begin_create_or_update,
                       resource_group_name,
                       application_gateway_name,
                       appgw)


def show_ag_private_link_ip(cmd,
                            resource_group_name,
                            application_gateway_name,
                            private_link_name,
                            private_link_ip_name):
    ncf = network_client_factory(cmd.cli_ctx)

    appgw = ncf.application_gateways.get(resource_group_name, application_gateway_name)

    target_private_link = None
    for pl in appgw.private_link_configurations:
        if pl.name == private_link_name:
            target_private_link = pl
            break
    else:
        raise CLIError("Priavte Link doesn't exist")

    target_private_link_ip_config = None
    for pic in target_private_link.ip_configurations:
        if pic.name == private_link_ip_name:
            target_private_link_ip_config = pic
            break
    else:
        raise CLIError("IP Configuration doesn't exist")

    return target_private_link_ip_config


def list_ag_private_link_ip(cmd,
                            resource_group_name,
                            application_gateway_name,
                            private_link_name):
    ncf = network_client_factory(cmd.cli_ctx)

    appgw = ncf.application_gateways.get(resource_group_name, application_gateway_name)

    target_private_link = None
    for pl in appgw.private_link_configurations:
        if pl.name == private_link_name:
            target_private_link = pl
            break
    else:
        raise CLIError("Priavte Link doesn't exist")

    return target_private_link.ip_configurations


def remove_ag_private_link_ip(cmd,
                              resource_group_name,
                              application_gateway_name,
                              private_link_name,
                              private_link_ip_name,
                              no_wait=False):
    ncf = network_client_factory(cmd.cli_ctx)

    appgw = ncf.application_gateways.get(resource_group_name, application_gateway_name)

    target_private_link = None
    for pl in appgw.private_link_configurations:
        if pl.name == private_link_name:
            target_private_link = pl
            break
    else:
        raise CLIError("Priavte Link doesn't exist")

    updated_ip_configurations = target_private_link.ip_configurations
    for pic in target_private_link.ip_configurations:
        if pic.name == private_link_ip_name:
            updated_ip_configurations.remove(pic)
            break
    else:
        raise CLIError("IP Configuration doesn't exist")

    return sdk_no_wait(no_wait,
                       ncf.application_gateways.begin_create_or_update,
                       resource_group_name,
                       application_gateway_name,
                       appgw)


def create_ag_backend_http_settings_collection(cmd, resource_group_name, application_gateway_name, item_name, port,
                                               probe=None, protocol='http', cookie_based_affinity=None, timeout=None,
                                               no_wait=False, connection_draining_timeout=0,
                                               host_name=None, host_name_from_backend_pool=None,
                                               affinity_cookie_name=None, enable_probe=None, path=None,
                                               auth_certs=None, root_certs=None):
    ApplicationGatewayBackendHttpSettings, ApplicationGatewayConnectionDraining, SubResource = cmd.get_models(
        'ApplicationGatewayBackendHttpSettings', 'ApplicationGatewayConnectionDraining', 'SubResource')
    ncf = network_client_factory(cmd.cli_ctx)
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    new_settings = ApplicationGatewayBackendHttpSettings(
        port=port,
        protocol=protocol,
        cookie_based_affinity=cookie_based_affinity or 'Disabled',
        request_timeout=timeout,
        probe=SubResource(id=probe) if probe else None,
        name=item_name)
    if cmd.supported_api_version(min_api='2016-09-01'):
        new_settings.authentication_certificates = [SubResource(id=x) for x in auth_certs or []]
    if cmd.supported_api_version(min_api='2016-12-01'):
        new_settings.connection_draining = \
            ApplicationGatewayConnectionDraining(
                enabled=bool(connection_draining_timeout), drain_timeout_in_sec=connection_draining_timeout or 1)
    if cmd.supported_api_version(min_api='2017-06-01'):
        new_settings.host_name = host_name
        new_settings.pick_host_name_from_backend_address = host_name_from_backend_pool
        new_settings.affinity_cookie_name = affinity_cookie_name
        new_settings.probe_enabled = enable_probe
        new_settings.path = path
    if cmd.supported_api_version(min_api='2019-04-01'):
        new_settings.trusted_root_certificates = [SubResource(id=x) for x in root_certs or []]
    upsert_to_collection(ag, 'backend_http_settings_collection', new_settings, 'name')
    return sdk_no_wait(no_wait, ncf.application_gateways.begin_create_or_update,
                       resource_group_name, application_gateway_name, ag)


def update_ag_backend_http_settings_collection(cmd, instance, parent, item_name, port=None, probe=None, protocol=None,
                                               cookie_based_affinity=None, timeout=None,
                                               connection_draining_timeout=None,
                                               host_name=None, host_name_from_backend_pool=None,
                                               affinity_cookie_name=None, enable_probe=None, path=None,
                                               auth_certs=None, root_certs=None):
    SubResource = cmd.get_models('SubResource')
    if auth_certs == "":
        instance.authentication_certificates = None
    elif auth_certs is not None:
        instance.authentication_certificates = [SubResource(id=x) for x in auth_certs]
    if root_certs == "":
        instance.trusted_root_certificates = None
    elif root_certs is not None:
        instance.trusted_root_certificates = [SubResource(id=x) for x in root_certs]
    if port is not None:
        instance.port = port
    if probe is not None:
        instance.probe = SubResource(id=probe)
    if protocol is not None:
        instance.protocol = protocol
    if cookie_based_affinity is not None:
        instance.cookie_based_affinity = cookie_based_affinity
    if timeout is not None:
        instance.request_timeout = timeout
    if connection_draining_timeout is not None:
        instance.connection_draining = {
            'enabled': bool(connection_draining_timeout),
            'drain_timeout_in_sec': connection_draining_timeout or 1
        }
    if host_name is not None:
        instance.host_name = host_name
    if host_name_from_backend_pool is not None:
        instance.pick_host_name_from_backend_address = host_name_from_backend_pool
    if affinity_cookie_name is not None:
        instance.affinity_cookie_name = affinity_cookie_name
    if enable_probe is not None:
        instance.probe_enabled = enable_probe
    if path is not None:
        instance.path = path
    return parent


def create_ag_redirect_configuration(cmd, resource_group_name, application_gateway_name, item_name, redirect_type,
                                     target_listener=None, target_url=None, include_path=None,
                                     include_query_string=None, no_wait=False):
    ApplicationGatewayRedirectConfiguration, SubResource = cmd.get_models(
        'ApplicationGatewayRedirectConfiguration', 'SubResource')
    ncf = network_client_factory(cmd.cli_ctx).application_gateways
    ag = ncf.get(resource_group_name, application_gateway_name)
    new_config = ApplicationGatewayRedirectConfiguration(
        name=item_name,
        redirect_type=redirect_type,
        target_listener=SubResource(id=target_listener) if target_listener else None,
        target_url=target_url,
        include_path=include_path,
        include_query_string=include_query_string)
    upsert_to_collection(ag, 'redirect_configurations', new_config, 'name')
    return sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, application_gateway_name, ag)


def update_ag_redirect_configuration(cmd, instance, parent, item_name, redirect_type=None,
                                     target_listener=None, target_url=None, include_path=None,
                                     include_query_string=None, raw=False):
    SubResource = cmd.get_models('SubResource')
    if redirect_type:
        instance.redirect_type = redirect_type
    if target_listener:
        instance.target_listener = SubResource(id=target_listener)
        instance.target_url = None
    if target_url:
        instance.target_listener = None
        instance.target_url = target_url
    if include_path is not None:
        instance.include_path = include_path
    if include_query_string is not None:
        instance.include_query_string = include_query_string
    return parent


def create_ag_rewrite_rule_set(cmd, resource_group_name, application_gateway_name, item_name, no_wait=False):
    ApplicationGatewayRewriteRuleSet = cmd.get_models(
        'ApplicationGatewayRewriteRuleSet')
    ncf = network_client_factory(cmd.cli_ctx).application_gateways
    ag = ncf.get(resource_group_name, application_gateway_name)
    new_set = ApplicationGatewayRewriteRuleSet(name=item_name)
    upsert_to_collection(ag, 'rewrite_rule_sets', new_set, 'name')
    if no_wait:
        return sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, application_gateway_name, ag)
    parent = sdk_no_wait(no_wait, ncf.begin_create_or_update,
                         resource_group_name, application_gateway_name, ag).result()
    return find_child_item(parent, item_name,
                           path='rewrite_rule_sets', key_path='name')


def update_ag_rewrite_rule_set(instance, parent, item_name):
    return parent


def create_ag_rewrite_rule(cmd, resource_group_name, application_gateway_name, rule_set_name, rule_name,
                           sequence=None, request_headers=None, response_headers=None, no_wait=False,
                           modified_path=None, modified_query_string=None, enable_reroute=None):
    (ApplicationGatewayRewriteRule,
     ApplicationGatewayRewriteRuleActionSet,
     ApplicationGatewayUrlConfiguration) = cmd.get_models('ApplicationGatewayRewriteRule',
                                                          'ApplicationGatewayRewriteRuleActionSet',
                                                          'ApplicationGatewayUrlConfiguration')
    ncf = network_client_factory(cmd.cli_ctx).application_gateways
    ag = ncf.get(resource_group_name, application_gateway_name)
    rule_set = find_child_item(ag, rule_set_name,
                               path='rewrite_rule_sets', key_path='name')
    url_configuration = None
    if any([modified_path, modified_query_string, enable_reroute]):
        url_configuration = ApplicationGatewayUrlConfiguration(modified_path=modified_path,
                                                               modified_query_string=modified_query_string,
                                                               reroute=enable_reroute)
    new_rule = ApplicationGatewayRewriteRule(
        name=rule_name,
        rule_sequence=sequence,
        action_set=ApplicationGatewayRewriteRuleActionSet(
            request_header_configurations=request_headers,
            response_header_configurations=response_headers,
            url_configuration=url_configuration
        )
    )
    upsert_to_collection(rule_set, 'rewrite_rules', new_rule, 'name')
    if no_wait:
        return sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, application_gateway_name, ag)
    parent = sdk_no_wait(no_wait, ncf.begin_create_or_update,
                         resource_group_name, application_gateway_name, ag).result()
    return find_child_item(parent, rule_set_name, rule_name,
                           path='rewrite_rule_sets.rewrite_rules', key_path='name.name')


def update_ag_rewrite_rule(instance, parent, cmd, rule_set_name, rule_name, sequence=None,
                           request_headers=None, response_headers=None,
                           modified_path=None, modified_query_string=None, enable_reroute=None):
    with cmd.update_context(instance) as c:
        c.set_param('rule_sequence', sequence)
        c.set_param('action_set.request_header_configurations', request_headers)
        c.set_param('action_set.response_header_configurations', response_headers)
        ApplicationGatewayUrlConfiguration = cmd.get_models('ApplicationGatewayUrlConfiguration')
        url_configuration = None
        if any([modified_path, modified_query_string, enable_reroute]):
            url_configuration = ApplicationGatewayUrlConfiguration(modified_path=modified_path,
                                                                   modified_query_string=modified_query_string,
                                                                   reroute=enable_reroute)
        c.set_param('action_set.url_configuration', url_configuration)
    return parent


def show_ag_rewrite_rule(cmd, resource_group_name, application_gateway_name, rule_set_name, rule_name):
    client = network_client_factory(cmd.cli_ctx).application_gateways
    gateway = client.get(resource_group_name, application_gateway_name)
    return find_child_item(gateway, rule_set_name, rule_name,
                           path='rewrite_rule_sets.rewrite_rules', key_path='name.name')


def list_ag_rewrite_rules(cmd, resource_group_name, application_gateway_name, rule_set_name):
    client = network_client_factory(cmd.cli_ctx).application_gateways
    gateway = client.get(resource_group_name, application_gateway_name)
    return find_child_collection(gateway, rule_set_name, path='rewrite_rule_sets.rewrite_rules', key_path='name')


def delete_ag_rewrite_rule(cmd, resource_group_name, application_gateway_name, rule_set_name, rule_name, no_wait=None):
    client = network_client_factory(cmd.cli_ctx).application_gateways
    gateway = client.get(resource_group_name, application_gateway_name)
    rule_set = find_child_item(gateway, rule_set_name, path='rewrite_rule_sets', key_path='name')
    rule = find_child_item(rule_set, rule_name, path='rewrite_rules', key_path='name')
    rule_set.rewrite_rules.remove(rule)
    sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, application_gateway_name, gateway)


def create_ag_rewrite_rule_condition(cmd, resource_group_name, application_gateway_name, rule_set_name, rule_name,
                                     variable, no_wait=False, pattern=None, ignore_case=None, negate=None):
    ApplicationGatewayRewriteRuleCondition = cmd.get_models(
        'ApplicationGatewayRewriteRuleCondition')
    ncf = network_client_factory(cmd.cli_ctx).application_gateways
    ag = ncf.get(resource_group_name, application_gateway_name)
    rule = find_child_item(ag, rule_set_name, rule_name,
                           path='rewrite_rule_sets.rewrite_rules', key_path='name.name')
    new_condition = ApplicationGatewayRewriteRuleCondition(
        variable=variable,
        pattern=pattern,
        ignore_case=ignore_case,
        negate=negate
    )
    upsert_to_collection(rule, 'conditions', new_condition, 'variable')
    if no_wait:
        return sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, application_gateway_name, ag)
    parent = sdk_no_wait(no_wait, ncf.begin_create_or_update,
                         resource_group_name, application_gateway_name, ag).result()
    return find_child_item(parent, rule_set_name, rule_name, variable,
                           path='rewrite_rule_sets.rewrite_rules.conditions', key_path='name.name.variable')


def update_ag_rewrite_rule_condition(instance, parent, cmd, rule_set_name, rule_name, variable, pattern=None,
                                     ignore_case=None, negate=None):
    with cmd.update_context(instance) as c:
        c.set_param('pattern', pattern)
        c.set_param('ignore_case', ignore_case)
        c.set_param('negate', negate)
    return parent


def show_ag_rewrite_rule_condition(cmd, resource_group_name, application_gateway_name, rule_set_name,
                                   rule_name, variable):
    client = network_client_factory(cmd.cli_ctx).application_gateways
    gateway = client.get(resource_group_name, application_gateway_name)
    return find_child_item(gateway, rule_set_name, rule_name, variable,
                           path='rewrite_rule_sets.rewrite_rules.conditions', key_path='name.name.variable')


def list_ag_rewrite_rule_conditions(cmd, resource_group_name, application_gateway_name, rule_set_name, rule_name):
    client = network_client_factory(cmd.cli_ctx).application_gateways
    gateway = client.get(resource_group_name, application_gateway_name)
    return find_child_collection(gateway, rule_set_name, rule_name,
                                 path='rewrite_rule_sets.rewrite_rules.conditions', key_path='name.name')


def delete_ag_rewrite_rule_condition(cmd, resource_group_name, application_gateway_name, rule_set_name,
                                     rule_name, variable, no_wait=None):
    client = network_client_factory(cmd.cli_ctx).application_gateways
    gateway = client.get(resource_group_name, application_gateway_name)
    rule = find_child_item(gateway, rule_set_name, rule_name,
                           path='rewrite_rule_sets.rewrite_rules', key_path='name.name')
    condition = find_child_item(rule, variable, path='conditions', key_path='variable')
    rule.conditions.remove(condition)
    sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, application_gateway_name, gateway)


def create_ag_probe(cmd, resource_group_name, application_gateway_name, item_name, protocol, host,
                    path, interval=30, timeout=120, threshold=8, no_wait=False, host_name_from_http_settings=None,
                    min_servers=None, match_body=None, match_status_codes=None, port=None):
    ApplicationGatewayProbe, ProbeMatchCriteria = cmd.get_models(
        'ApplicationGatewayProbe', 'ApplicationGatewayProbeHealthResponseMatch')
    ncf = network_client_factory(cmd.cli_ctx)
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    new_probe = ApplicationGatewayProbe(
        name=item_name,
        protocol=protocol,
        host=host,
        path=path,
        interval=interval,
        timeout=timeout,
        unhealthy_threshold=threshold)
    if cmd.supported_api_version(min_api='2017-06-01'):
        new_probe.pick_host_name_from_backend_http_settings = host_name_from_http_settings
        new_probe.min_servers = min_servers
        new_probe.match = ProbeMatchCriteria(body=match_body, status_codes=match_status_codes)
    if cmd.supported_api_version(min_api='2019-04-01'):
        new_probe.port = port

    upsert_to_collection(ag, 'probes', new_probe, 'name')
    return sdk_no_wait(no_wait, ncf.application_gateways.begin_create_or_update,
                       resource_group_name, application_gateway_name, ag)


def update_ag_probe(cmd, instance, parent, item_name, protocol=None, host=None, path=None,
                    interval=None, timeout=None, threshold=None, host_name_from_http_settings=None,
                    min_servers=None, match_body=None, match_status_codes=None, port=None):
    if protocol is not None:
        instance.protocol = protocol
    if host is not None:
        instance.host = host
    if path is not None:
        instance.path = path
    if interval is not None:
        instance.interval = interval
    if timeout is not None:
        instance.timeout = timeout
    if threshold is not None:
        instance.unhealthy_threshold = threshold
    if host_name_from_http_settings is not None:
        instance.pick_host_name_from_backend_http_settings = host_name_from_http_settings
    if min_servers is not None:
        instance.min_servers = min_servers
    if match_body is not None or match_status_codes is not None:
        ProbeMatchCriteria = \
            cmd.get_models('ApplicationGatewayProbeHealthResponseMatch')
        instance.match = instance.match or ProbeMatchCriteria()
        if match_body is not None:
            instance.match.body = match_body
        if match_status_codes is not None:
            instance.match.status_codes = match_status_codes
    if port is not None:
        instance.port = port
    return parent


def create_ag_request_routing_rule(cmd, resource_group_name, application_gateway_name, item_name,
                                   address_pool=None, http_settings=None, http_listener=None, redirect_config=None,
                                   url_path_map=None, rule_type='Basic', no_wait=False, rewrite_rule_set=None,
                                   priority=None):
    ApplicationGatewayRequestRoutingRule, SubResource = cmd.get_models(
        'ApplicationGatewayRequestRoutingRule', 'SubResource')
    ncf = network_client_factory(cmd.cli_ctx)
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    if not address_pool and not redirect_config:
        address_pool = _get_default_id(ag, 'backend_address_pools', '--address-pool')
    if not http_settings and not redirect_config:
        http_settings = _get_default_id(ag, 'backend_http_settings_collection', '--http-settings')
    if not http_listener:
        http_listener = _get_default_id(ag, 'http_listeners', '--http-listener')
    new_rule = ApplicationGatewayRequestRoutingRule(
        name=item_name,
        rule_type=rule_type,
        priority=priority,
        backend_address_pool=SubResource(id=address_pool) if address_pool else None,
        backend_http_settings=SubResource(id=http_settings) if http_settings else None,
        http_listener=SubResource(id=http_listener),
        url_path_map=SubResource(id=url_path_map) if url_path_map else None)
    if cmd.supported_api_version(min_api='2017-06-01'):
        new_rule.redirect_configuration = SubResource(id=redirect_config) if redirect_config else None

    rewrite_rule_set_name = next(key for key, value in locals().items() if id(value) == id(rewrite_rule_set))
    if cmd.supported_api_version(parameter_name=rewrite_rule_set_name):
        new_rule.rewrite_rule_set = SubResource(id=rewrite_rule_set) if rewrite_rule_set else None
    upsert_to_collection(ag, 'request_routing_rules', new_rule, 'name')
    return sdk_no_wait(no_wait, ncf.application_gateways.begin_create_or_update,
                       resource_group_name, application_gateway_name, ag)


def update_ag_request_routing_rule(cmd, instance, parent, item_name, address_pool=None,
                                   http_settings=None, http_listener=None, redirect_config=None, url_path_map=None,
                                   rule_type=None, rewrite_rule_set=None, priority=None):
    SubResource = cmd.get_models('SubResource')
    if address_pool is not None:
        instance.backend_address_pool = SubResource(id=address_pool)
    if http_settings is not None:
        instance.backend_http_settings = SubResource(id=http_settings)
    if redirect_config is not None:
        instance.redirect_configuration = SubResource(id=redirect_config)
    if http_listener is not None:
        instance.http_listener = SubResource(id=http_listener)
    if url_path_map is not None:
        instance.url_path_map = SubResource(id=url_path_map)
    if rule_type is not None:
        instance.rule_type = rule_type
    if rewrite_rule_set is not None:
        instance.rewrite_rule_set = SubResource(id=rewrite_rule_set)
    with cmd.update_context(instance) as c:
        c.set_param('priority', priority)
    return parent


def create_ag_ssl_certificate(cmd, resource_group_name, application_gateway_name, item_name, cert_data=None,
                              cert_password=None, key_vault_secret_id=None, no_wait=False):
    ApplicationGatewaySslCertificate = cmd.get_models('ApplicationGatewaySslCertificate')
    ncf = network_client_factory(cmd.cli_ctx)
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    new_cert = ApplicationGatewaySslCertificate(
        name=item_name, data=cert_data, password=cert_password, key_vault_secret_id=key_vault_secret_id)
    upsert_to_collection(ag, 'ssl_certificates', new_cert, 'name')
    return sdk_no_wait(no_wait, ncf.application_gateways.begin_create_or_update,
                       resource_group_name, application_gateway_name, ag)


def update_ag_ssl_certificate(instance, parent, item_name,
                              cert_data=None, cert_password=None, key_vault_secret_id=None):
    if cert_data is not None:
        instance.data = cert_data
    if cert_password is not None:
        instance.password = cert_password
    if key_vault_secret_id is not None:
        instance.key_vault_secret_id = key_vault_secret_id
    return parent


def set_ag_ssl_policy_2017_03_01(cmd, resource_group_name, application_gateway_name, disabled_ssl_protocols=None,
                                 clear=False, no_wait=False):
    ApplicationGatewaySslPolicy = cmd.get_models('ApplicationGatewaySslPolicy')
    ncf = network_client_factory(cmd.cli_ctx).application_gateways
    ag = ncf.get(resource_group_name, application_gateway_name)
    ag.ssl_policy = None if clear else ApplicationGatewaySslPolicy(
        disabled_ssl_protocols=disabled_ssl_protocols)
    return sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, application_gateway_name, ag)


def set_ag_ssl_policy_2017_06_01(cmd, resource_group_name, application_gateway_name, policy_name=None, policy_type=None,
                                 disabled_ssl_protocols=None, cipher_suites=None, min_protocol_version=None,
                                 no_wait=False):
    ApplicationGatewaySslPolicy, ApplicationGatewaySslPolicyType = cmd.get_models(
        'ApplicationGatewaySslPolicy', 'ApplicationGatewaySslPolicyType')
    ncf = network_client_factory(cmd.cli_ctx).application_gateways
    ag = ncf.get(resource_group_name, application_gateway_name)
    policy_type = None
    if policy_name:
        policy_type = ApplicationGatewaySslPolicyType.predefined.value
    elif cipher_suites or min_protocol_version:
        policy_type = ApplicationGatewaySslPolicyType.custom.value
    ag.ssl_policy = ApplicationGatewaySslPolicy(
        policy_name=policy_name,
        policy_type=policy_type,
        disabled_ssl_protocols=disabled_ssl_protocols,
        cipher_suites=cipher_suites,
        min_protocol_version=min_protocol_version)
    return sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, application_gateway_name, ag)


def show_ag_ssl_policy(cmd, resource_group_name, application_gateway_name):
    return network_client_factory(cmd.cli_ctx).application_gateways.get(
        resource_group_name, application_gateway_name).ssl_policy


def create_ag_trusted_root_certificate(cmd, resource_group_name, application_gateway_name, item_name, no_wait=False,
                                       cert_data=None, keyvault_secret=None):
    ApplicationGatewayTrustedRootCertificate = cmd.get_models('ApplicationGatewayTrustedRootCertificate')
    ncf = network_client_factory(cmd.cli_ctx).application_gateways
    ag = ncf.get(resource_group_name, application_gateway_name)
    root_cert = ApplicationGatewayTrustedRootCertificate(name=item_name, data=cert_data,
                                                         key_vault_secret_id=keyvault_secret)
    upsert_to_collection(ag, 'trusted_root_certificates', root_cert, 'name')
    return sdk_no_wait(no_wait, ncf.begin_create_or_update,
                       resource_group_name, application_gateway_name, ag)


def update_ag_trusted_root_certificate(instance, parent, item_name, cert_data=None, keyvault_secret=None):
    if cert_data is not None:
        instance.data = cert_data
    if keyvault_secret is not None:
        instance.key_vault_secret_id = keyvault_secret
    return parent


def create_ag_url_path_map(cmd, resource_group_name, application_gateway_name, item_name, paths,
                           address_pool=None, http_settings=None, redirect_config=None, rewrite_rule_set=None,
                           default_address_pool=None, default_http_settings=None, default_redirect_config=None,
                           no_wait=False, rule_name='default', default_rewrite_rule_set=None, firewall_policy=None):
    ApplicationGatewayUrlPathMap, ApplicationGatewayPathRule, SubResource = cmd.get_models(
        'ApplicationGatewayUrlPathMap', 'ApplicationGatewayPathRule', 'SubResource')
    ncf = network_client_factory(cmd.cli_ctx)
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)

    new_rule = ApplicationGatewayPathRule(
        name=rule_name,
        backend_address_pool=SubResource(id=address_pool) if address_pool else None,
        backend_http_settings=SubResource(id=http_settings) if http_settings else None,
        paths=paths
    )
    new_map = ApplicationGatewayUrlPathMap(
        name=item_name,
        default_backend_address_pool=SubResource(id=default_address_pool) if default_address_pool else None,
        default_backend_http_settings=SubResource(id=default_http_settings) if default_http_settings else None,
        path_rules=[])
    if cmd.supported_api_version(min_api='2017-06-01'):
        new_rule.redirect_configuration = SubResource(id=redirect_config) if redirect_config else None
        new_map.default_redirect_configuration = \
            SubResource(id=default_redirect_config) if default_redirect_config else None

    rewrite_rule_set_name = next(key for key, value in locals().items() if id(value) == id(rewrite_rule_set))
    if cmd.supported_api_version(parameter_name=rewrite_rule_set_name):
        new_rule.rewrite_rule_set = SubResource(id=rewrite_rule_set) if rewrite_rule_set else None
        new_map.default_rewrite_rule_set = \
            SubResource(id=default_rewrite_rule_set) if default_rewrite_rule_set else None

    if cmd.supported_api_version(min_api='2019-09-01'):
        new_rule.firewall_policy = SubResource(id=firewall_policy) if firewall_policy else None

    # pull defaults from the rule specific properties if the default-* option isn't specified
    if new_rule.backend_address_pool and not new_map.default_backend_address_pool:
        new_map.default_backend_address_pool = new_rule.backend_address_pool

    if new_rule.backend_http_settings and not new_map.default_backend_http_settings:
        new_map.default_backend_http_settings = new_rule.backend_http_settings

    if new_rule.redirect_configuration and not new_map.default_redirect_configuration:
        new_map.default_redirect_configuration = new_rule.redirect_configuration

    new_map.path_rules.append(new_rule)
    upsert_to_collection(ag, 'url_path_maps', new_map, 'name')
    return sdk_no_wait(no_wait, ncf.application_gateways.begin_create_or_update,
                       resource_group_name, application_gateway_name, ag)


def update_ag_url_path_map(cmd, instance, parent, item_name, default_address_pool=None,
                           default_http_settings=None, default_redirect_config=None, raw=False,
                           default_rewrite_rule_set=None):
    SubResource = cmd.get_models('SubResource')
    if default_address_pool == '':
        instance.default_backend_address_pool = None
    elif default_address_pool:
        instance.default_backend_address_pool = SubResource(id=default_address_pool)

    if default_http_settings == '':
        instance.default_backend_http_settings = None
    elif default_http_settings:
        instance.default_backend_http_settings = SubResource(id=default_http_settings)

    if default_redirect_config == '':
        instance.default_redirect_configuration = None
    elif default_redirect_config:
        instance.default_redirect_configuration = SubResource(id=default_redirect_config)

    if default_rewrite_rule_set == '':
        instance.default_rewrite_rule_set = None
    elif default_rewrite_rule_set:
        instance.default_rewrite_rule_set = SubResource(id=default_rewrite_rule_set)
    return parent


def create_ag_url_path_map_rule(cmd, resource_group_name, application_gateway_name, url_path_map_name,
                                item_name, paths, address_pool=None, http_settings=None, redirect_config=None,
                                firewall_policy=None, no_wait=False, rewrite_rule_set=None):
    ApplicationGatewayPathRule, SubResource = cmd.get_models('ApplicationGatewayPathRule', 'SubResource')
    if address_pool and redirect_config:
        raise CLIError("Cannot reference a BackendAddressPool when Redirect Configuration is specified.")
    ncf = network_client_factory(cmd.cli_ctx)
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    url_map = next((x for x in ag.url_path_maps if x.name == url_path_map_name), None)
    if not url_map:
        raise CLIError('URL path map "{}" not found.'.format(url_path_map_name))
    default_backend_pool = SubResource(id=url_map.default_backend_address_pool.id) \
        if (url_map.default_backend_address_pool and not redirect_config) else None
    default_http_settings = SubResource(id=url_map.default_backend_http_settings.id) \
        if url_map.default_backend_http_settings else None
    new_rule = ApplicationGatewayPathRule(
        name=item_name,
        paths=paths,
        backend_address_pool=SubResource(id=address_pool) if address_pool else default_backend_pool,
        backend_http_settings=SubResource(id=http_settings) if http_settings else default_http_settings)
    if cmd.supported_api_version(min_api='2017-06-01'):
        default_redirect = SubResource(id=url_map.default_redirect_configuration.id) \
            if (url_map.default_redirect_configuration and not address_pool) else None
        new_rule.redirect_configuration = SubResource(id=redirect_config) if redirect_config else default_redirect

    rewrite_rule_set_name = next(key for key, value in locals().items() if id(value) == id(rewrite_rule_set))
    if cmd.supported_api_version(parameter_name=rewrite_rule_set_name):
        new_rule.rewrite_rule_set = SubResource(id=rewrite_rule_set) if rewrite_rule_set else None

    if cmd.supported_api_version(min_api='2019-09-01'):
        new_rule.firewall_policy = SubResource(id=firewall_policy) if firewall_policy else None

    upsert_to_collection(url_map, 'path_rules', new_rule, 'name')
    return sdk_no_wait(no_wait, ncf.application_gateways.begin_create_or_update,
                       resource_group_name, application_gateway_name, ag)


def delete_ag_url_path_map_rule(cmd, resource_group_name, application_gateway_name, url_path_map_name,
                                item_name, no_wait=False):
    ncf = network_client_factory(cmd.cli_ctx)
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    url_map = next((x for x in ag.url_path_maps if x.name == url_path_map_name), None)
    if not url_map:
        raise CLIError('URL path map "{}" not found.'.format(url_path_map_name))
    url_map.path_rules = \
        [x for x in url_map.path_rules if x.name.lower() != item_name.lower()]
    return sdk_no_wait(no_wait, ncf.application_gateways.begin_create_or_update,
                       resource_group_name, application_gateway_name, ag)


def set_ag_waf_config_2016_09_01(cmd, resource_group_name, application_gateway_name, enabled,
                                 firewall_mode=None,
                                 no_wait=False):
    ApplicationGatewayWebApplicationFirewallConfiguration = cmd.get_models(
        'ApplicationGatewayWebApplicationFirewallConfiguration')
    ncf = network_client_factory(cmd.cli_ctx).application_gateways
    ag = ncf.get(resource_group_name, application_gateway_name)
    ag.web_application_firewall_configuration = \
        ApplicationGatewayWebApplicationFirewallConfiguration(
            enabled=(enabled == 'true'), firewall_mode=firewall_mode)

    return sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, application_gateway_name, ag)


def set_ag_waf_config_2017_03_01(cmd, resource_group_name, application_gateway_name, enabled,
                                 firewall_mode=None,
                                 rule_set_type='OWASP', rule_set_version=None,
                                 disabled_rule_groups=None,
                                 disabled_rules=None, no_wait=False,
                                 request_body_check=None, max_request_body_size=None, file_upload_limit=None,
                                 exclusions=None):
    ApplicationGatewayWebApplicationFirewallConfiguration = cmd.get_models(
        'ApplicationGatewayWebApplicationFirewallConfiguration')
    ncf = network_client_factory(cmd.cli_ctx).application_gateways
    ag = ncf.get(resource_group_name, application_gateway_name)
    ag.web_application_firewall_configuration = \
        ApplicationGatewayWebApplicationFirewallConfiguration(
            enabled=(enabled == 'true'), firewall_mode=firewall_mode, rule_set_type=rule_set_type,
            rule_set_version=rule_set_version)
    if disabled_rule_groups or disabled_rules:
        ApplicationGatewayFirewallDisabledRuleGroup = cmd.get_models('ApplicationGatewayFirewallDisabledRuleGroup')

        disabled_groups = []

        # disabled groups can be added directly
        for group in disabled_rule_groups or []:
            disabled_groups.append(ApplicationGatewayFirewallDisabledRuleGroup(rule_group_name=group))

        def _flatten(collection, expand_property_fn):
            for each in collection:
                for value in expand_property_fn(each):
                    yield value

        # for disabled rules, we have to look up the IDs
        if disabled_rules:
            results = list_ag_waf_rule_sets(ncf, _type=rule_set_type, version=rule_set_version, group='*')
            for group in _flatten(results, lambda r: r.rule_groups):
                disabled_group = ApplicationGatewayFirewallDisabledRuleGroup(
                    rule_group_name=group.rule_group_name, rules=[])

                for rule in group.rules:
                    if str(rule.rule_id) in disabled_rules:
                        disabled_group.rules.append(rule.rule_id)
                if disabled_group.rules:
                    disabled_groups.append(disabled_group)
        ag.web_application_firewall_configuration.disabled_rule_groups = disabled_groups

    if cmd.supported_api_version(min_api='2018-08-01'):
        ag.web_application_firewall_configuration.request_body_check = request_body_check
        ag.web_application_firewall_configuration.max_request_body_size_in_kb = max_request_body_size
        ag.web_application_firewall_configuration.file_upload_limit_in_mb = file_upload_limit
        ag.web_application_firewall_configuration.exclusions = exclusions

    return sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, application_gateway_name, ag)


def show_ag_waf_config(cmd, resource_group_name, application_gateway_name):
    return network_client_factory(cmd.cli_ctx).application_gateways.get(
        resource_group_name, application_gateway_name).web_application_firewall_configuration


def list_ag_waf_rule_sets(client, _type=None, version=None, group=None):
    results = client.list_available_waf_rule_sets().value
    filtered_results = []
    # filter by rule set name or version
    for rule_set in results:
        if _type and _type.lower() != rule_set.rule_set_type.lower():
            continue
        if version and version.lower() != rule_set.rule_set_version.lower():
            continue

        filtered_groups = []
        for rule_group in rule_set.rule_groups:
            if not group:
                rule_group.rules = None
                filtered_groups.append(rule_group)
            elif group.lower() == rule_group.rule_group_name.lower() or group == '*':
                filtered_groups.append(rule_group)

        if filtered_groups:
            rule_set.rule_groups = filtered_groups
            filtered_results.append(rule_set)

    return filtered_results


# endregion


# region ApplicationGatewayWAFPolicy
def create_ag_waf_policy(cmd, client, resource_group_name, policy_name,
                         location=None, tags=None, rule_set_type='OWASP',
                         rule_set_version='3.0'):
    WebApplicationFirewallPolicy, ManagedRulesDefinition, \
        ManagedRuleSet = cmd.get_models('WebApplicationFirewallPolicy',
                                        'ManagedRulesDefinition',
                                        'ManagedRuleSet')
    #  https://docs.microsoft.com/en-us/azure/application-gateway/waf-overview

    # mandatory default rule with empty rule sets
    managed_rule_set = ManagedRuleSet(rule_set_type=rule_set_type, rule_set_version=rule_set_version)
    managed_rule_definition = ManagedRulesDefinition(managed_rule_sets=[managed_rule_set])
    waf_policy = WebApplicationFirewallPolicy(location=location, tags=tags, managed_rules=managed_rule_definition)
    return client.create_or_update(resource_group_name, policy_name, waf_policy)


def update_ag_waf_policy(cmd, instance, tags=None):
    with cmd.update_context(instance) as c:
        c.set_param('tags', tags)
    return instance


def list_ag_waf_policies(cmd, resource_group_name=None):
    return _generic_list(cmd.cli_ctx, 'web_application_firewall_policies', resource_group_name)
# endregion


# region ApplicationGatewayWAFPolicyRules PolicySettings
def update_waf_policy_setting(cmd, instance,
                              state=None, mode=None,
                              max_request_body_size_in_kb=None, file_upload_limit_in_mb=None,
                              request_body_check=False):
    if state is not None:
        instance.policy_settings.state = state

    if mode is not None:
        instance.policy_settings.mode = mode

    if max_request_body_size_in_kb is not None:
        instance.policy_settings.max_request_body_size_in_kb = max_request_body_size_in_kb

    if file_upload_limit_in_mb is not None:
        instance.policy_settings.file_upload_limit_in_mb = file_upload_limit_in_mb

    if request_body_check is not None:
        instance.policy_settings.request_body_check = request_body_check

    return instance


def list_waf_policy_setting(cmd, client, resource_group_name, policy_name):
    return client.get(resource_group_name, policy_name).policy_settings
# endregion


# region ApplicationGatewayWAFPolicyRules
def create_waf_custom_rule(cmd, client, resource_group_name, policy_name, rule_name, priority, rule_type, action):
    """
    Initialize custom rule for WAF policy
    """
    WebApplicationFirewallCustomRule = cmd.get_models('WebApplicationFirewallCustomRule')
    waf_policy = client.get(resource_group_name, policy_name)
    new_custom_rule = WebApplicationFirewallCustomRule(
        name=rule_name,
        action=action,
        match_conditions=[],
        priority=priority,
        rule_type=rule_type
    )
    upsert_to_collection(waf_policy, 'custom_rules', new_custom_rule, 'name')
    parent = client.create_or_update(resource_group_name, policy_name, waf_policy)
    return find_child_item(parent, rule_name, path='custom_rules', key_path='name')


# pylint: disable=unused-argument
def update_waf_custom_rule(instance, parent, cmd, rule_name, priority=None, rule_type=None, action=None):
    with cmd.update_context(instance) as c:
        c.set_param('priority', priority)
        c.set_param('rule_type', rule_type)
        c.set_param('action', action)
    return parent


def show_waf_custom_rule(cmd, client, resource_group_name, policy_name, rule_name):
    waf_policy = client.get(resource_group_name, policy_name)
    return find_child_item(waf_policy, rule_name, path='custom_rules', key_path='name')


def list_waf_custom_rules(cmd, client, resource_group_name, policy_name):
    return client.get(resource_group_name, policy_name).custom_rules


def delete_waf_custom_rule(cmd, client, resource_group_name, policy_name, rule_name, no_wait=None):
    waf_policy = client.get(resource_group_name, policy_name)
    rule = find_child_item(waf_policy, rule_name, path='custom_rules', key_path='name')
    waf_policy.custom_rules.remove(rule)
    sdk_no_wait(no_wait, client.create_or_update, resource_group_name, policy_name, waf_policy)
# endregion


# region ApplicationGatewayWAFPolicyRuleMatchConditions
def add_waf_custom_rule_match_cond(cmd, client, resource_group_name, policy_name, rule_name,
                                   match_variables, operator, match_values, negation_condition=None, transforms=None):
    MatchCondition = cmd.get_models('MatchCondition')
    waf_policy = client.get(resource_group_name, policy_name)
    custom_rule = find_child_item(waf_policy, rule_name, path='custom_rules', key_path='name')
    new_cond = MatchCondition(
        match_variables=match_variables,
        operator=operator,
        match_values=match_values,
        negation_conditon=negation_condition,
        transforms=transforms
    )
    custom_rule.match_conditions.append(new_cond)
    upsert_to_collection(waf_policy, 'custom_rules', custom_rule, 'name', warn=False)
    client.create_or_update(resource_group_name, policy_name, waf_policy)
    return new_cond


def list_waf_custom_rule_match_cond(cmd, client, resource_group_name, policy_name, rule_name):
    waf_policy = client.get(resource_group_name, policy_name)
    return find_child_item(waf_policy, rule_name, path='custom_rules', key_path='name').match_conditions


def remove_waf_custom_rule_match_cond(cmd, client, resource_group_name, policy_name, rule_name, index):
    waf_policy = client.get(resource_group_name, policy_name)
    rule = find_child_item(waf_policy, rule_name, path='custom_rules', key_path='name')
    rule.match_conditions.pop(index)
    client.create_or_update(resource_group_name, policy_name, waf_policy)
# endregion


# region ApplicationGatewayWAFPolicy ManagedRule ManagedRuleSet
def add_waf_managed_rule_set(cmd, client, resource_group_name, policy_name,
                             rule_set_type, rule_set_version,
                             rule_group_name=None, rules=None):
    """
    Add managed rule set to the WAF policy managed rules.
    Visit: https://docs.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-crs-rulegroups-rules
    """
    ManagedRuleSet, ManagedRuleGroupOverride, ManagedRuleOverride = \
        cmd.get_models('ManagedRuleSet', 'ManagedRuleGroupOverride', 'ManagedRuleOverride')

    waf_policy = client.get(resource_group_name, policy_name)

    managed_rule_overrides = [ManagedRuleOverride(rule_id=r) for r in rules] if rules is not None else []

    rule_group_override = None
    if rule_group_name is not None:
        rule_group_override = ManagedRuleGroupOverride(rule_group_name=rule_group_name,
                                                       rules=managed_rule_overrides)
    new_managed_rule_set = ManagedRuleSet(rule_set_type=rule_set_type,
                                          rule_set_version=rule_set_version,
                                          rule_group_overrides=[rule_group_override] if rule_group_override is not None else [])  # pylint: disable=line-too-long

    for rule_set in waf_policy.managed_rules.managed_rule_sets:
        if rule_set.rule_set_type == rule_set_type and rule_set.rule_set_version == rule_set_version:
            for rule_override in rule_set.rule_group_overrides:
                if rule_override.rule_group_name == rule_group_name:
                    # Add one rule
                    rule_override.rules.extend(managed_rule_overrides)
                    break
            else:
                # Add one rule group
                if rule_group_override is not None:
                    rule_set.rule_group_overrides.append(rule_group_override)
            break
    else:
        # Add new rule set
        waf_policy.managed_rules.managed_rule_sets.append(new_managed_rule_set)

    return client.create_or_update(resource_group_name, policy_name, waf_policy)


def update_waf_managed_rule_set(cmd, instance, rule_set_type, rule_set_version, rule_group_name=None, rules=None):
    """
    Update(Override) existing rule set of a WAF policy managed rules.
    """
    ManagedRuleSet, ManagedRuleGroupOverride, ManagedRuleOverride = \
        cmd.get_models('ManagedRuleSet', 'ManagedRuleGroupOverride', 'ManagedRuleOverride')

    managed_rule_overrides = [ManagedRuleOverride(rule_id=r) for r in rules] if rules else None

    rule_group_override = ManagedRuleGroupOverride(rule_group_name=rule_group_name,
                                                   rules=managed_rule_overrides) if managed_rule_overrides else None

    new_managed_rule_set = ManagedRuleSet(rule_set_type=rule_set_type,
                                          rule_set_version=rule_set_version,
                                          rule_group_overrides=[rule_group_override] if rule_group_override is not None else [])  # pylint: disable=line-too-long

    updated_rule_set = None

    for rule_set in instance.managed_rules.managed_rule_sets:
        if rule_set.rule_set_type == rule_set_type and rule_set.rule_set_version != rule_set_version:
            updated_rule_set = rule_set
            break

        if rule_set.rule_set_type == rule_set_type and rule_set.rule_set_version == rule_set_version:
            if rule_group_name is None:
                updated_rule_set = rule_set
                break

            rg = next((rg for rg in rule_set.rule_group_overrides if rg.rule_group_name == rule_group_name), None)
            if rg:
                rg.rules = managed_rule_overrides   # differentiate with add_waf_managed_rule_set()
            else:
                rule_set.rule_group_overrides.append(rule_group_override)

    if updated_rule_set:
        instance.managed_rules.managed_rule_sets.remove(updated_rule_set)
        instance.managed_rules.managed_rule_sets.append(new_managed_rule_set)

    return instance


def remove_waf_managed_rule_set(cmd, client, resource_group_name, policy_name,
                                rule_set_type, rule_set_version, rule_group_name=None):
    """
    Remove a managed rule set by rule set group name if rule_group_name is specified. Otherwise, remove all rule set.
    """
    waf_policy = client.get(resource_group_name, policy_name)

    delete_rule_set = None

    for rule_set in waf_policy.managed_rules.managed_rule_sets:
        if rule_set.rule_set_type == rule_set_type or rule_set.rule_set_version == rule_set_version:
            if rule_group_name is None:
                delete_rule_set = rule_set
                break

            # Remove one rule from rule group
            rg = next((rg for rg in rule_set.rule_group_overrides if rg.rule_group_name == rule_group_name), None)
            if rg is None:
                raise CLIError('Rule set group [ {} ] not found.'.format(rule_group_name))
            rule_set.rule_group_overrides.remove(rg)

    if delete_rule_set:
        waf_policy.managed_rules.managed_rule_sets.remove(delete_rule_set)

    return client.create_or_update(resource_group_name, policy_name, waf_policy)


def list_waf_managed_rule_set(cmd, client, resource_group_name, policy_name):
    waf_policy = client.get(resource_group_name, policy_name)
    return waf_policy.managed_rules
# endregion


# region ApplicationGatewayWAFPolicy ManagedRule OwaspCrsExclusionEntry
def add_waf_managed_rule_exclusion(cmd, client, resource_group_name, policy_name,
                                   match_variable, selector_match_operator, selector):
    OwaspCrsExclusionEntry = cmd.get_models('OwaspCrsExclusionEntry')

    exclusion_entry = OwaspCrsExclusionEntry(match_variable=match_variable,
                                             selector_match_operator=selector_match_operator,
                                             selector=selector)

    waf_policy = client.get(resource_group_name, policy_name)

    waf_policy.managed_rules.exclusions.append(exclusion_entry)

    return client.create_or_update(resource_group_name, policy_name, waf_policy)


def remove_waf_managed_rule_exclusion(cmd, client, resource_group_name, policy_name):
    waf_policy = client.get(resource_group_name, policy_name)
    waf_policy.managed_rules.exclusions = []
    return client.create_or_update(resource_group_name, policy_name, waf_policy)


def list_waf_managed_rule_exclusion(cmd, client, resource_group_name, policy_name):
    waf_policy = client.get(resource_group_name, policy_name)
    return waf_policy.managed_rules


# pylint: disable=too-many-nested-blocks
def add_waf_exclusion_rule_set(cmd, client, resource_group_name, policy_name,
                               rule_set_type, rule_set_version,
                               match_variable, selector_match_operator, selector,
                               rule_group_name=None, rule_ids=None):
    def _has_exclusion():
        policy = client.get(resource_group_name, policy_name)
        for e in policy.managed_rules.exclusions:
            if e.match_variable == match_variable \
                    and e.selector_match_operator == selector_match_operator \
                    and e.selector == selector:
                return True
        return False

    ExclusionManagedRuleSet, ExclusionManagedRuleGroup, ExclusionManagedRule = cmd.get_models(
        'ExclusionManagedRuleSet', 'ExclusionManagedRuleGroup', 'ExclusionManagedRule'
    )
    # build current rules from ids
    rules = [ExclusionManagedRule(rule_id=rule_id) for rule_id in rule_ids] if rule_ids is not None else []
    # build current rule group from rules
    curr_rule_group = None
    if rule_group_name is not None:
        curr_rule_group = ExclusionManagedRuleGroup(rule_group_name=rule_group_name, rules=rules)
    # build current rule set from rule group
    curr_rule_set = ExclusionManagedRuleSet(rule_set_type=rule_set_type,
                                            rule_set_version=rule_set_version,
                                            rule_groups=[curr_rule_group] if curr_rule_group is not None else [])

    if not _has_exclusion():
        OwaspCrsExclusionEntry = cmd.get_models('OwaspCrsExclusionEntry')
        exclusion = OwaspCrsExclusionEntry(match_variable=match_variable,
                                           selector_match_operator=selector_match_operator,
                                           selector=selector,
                                           exclusion_managed_rule_sets=[curr_rule_set])
        waf_policy = client.get(resource_group_name, policy_name)
        waf_policy.managed_rules.exclusions.append(exclusion)
    else:
        waf_policy = client.get(resource_group_name, policy_name)
        for exclusion in waf_policy.managed_rules.exclusions:
            if exclusion.match_variable == match_variable \
                    and exclusion.selector_match_operator == selector_match_operator \
                    and exclusion.selector == selector:
                for rule_set in exclusion.exclusion_managed_rule_sets:
                    if rule_set.rule_set_type == rule_set_type and rule_set.rule_set_version == rule_set_version:
                        for rule_group in rule_set.rule_groups:
                            # add rules when rule group exists
                            if rule_group.rule_group_name == rule_group_name:
                                rule_group.rules.extend(rules)
                                break
                        else:
                            # add a new rule group
                            if curr_rule_group is not None:
                                rule_set.rule_groups.append(curr_rule_group)
                        break
                else:
                    # add a new rule set
                    exclusion.exclusion_managed_rule_sets.append(curr_rule_set)

    return client.create_or_update(resource_group_name, policy_name, waf_policy)


# pylint: disable=line-too-long
def remove_waf_exclusion_rule_set(client, resource_group_name, policy_name,
                                  rule_set_type, rule_set_version,
                                  match_variable, selector_match_operator, selector,
                                  rule_group_name=None):
    waf_policy = client.get(resource_group_name, policy_name)
    to_be_deleted = None
    for exclusion in waf_policy.managed_rules.exclusions:
        if exclusion.match_variable == match_variable \
                and exclusion.selector_match_operator == selector_match_operator \
                and exclusion.selector == selector:
            for rule_set in exclusion.exclusion_managed_rule_sets:
                if rule_set.rule_set_type == rule_set_type or rule_set.rule_set_version == rule_set_version:
                    if rule_group_name is None:
                        to_be_deleted = rule_set
                        break
                    rule_group = next((rule_group for rule_group in rule_set.rule_groups if rule_group.rule_group_name == rule_group_name), None)
                    if rule_group is None:
                        err_msg = f"Rule set group [{rule_group_name}] is not found."
                        raise ResourceNotFoundError(err_msg)
                    rule_set.rule_groups.remove(rule_group)
            if to_be_deleted:
                exclusion.exclusion_managed_rule_sets.remove(to_be_deleted)
    return client.create_or_update(resource_group_name, policy_name, waf_policy)


def list_waf_exclusion_rule_set(cmd, client, resource_group_name, policy_name):
    waf_policy = client.get(resource_group_name, policy_name)
    return waf_policy.managed_rules
# endregion


# region ApplicationSecurityGroups
def create_asg(cmd, client, resource_group_name, application_security_group_name, location=None, tags=None):
    ApplicationSecurityGroup = cmd.get_models('ApplicationSecurityGroup')
    asg = ApplicationSecurityGroup(location=location, tags=tags)
    return client.begin_create_or_update(resource_group_name, application_security_group_name, asg)


def update_asg(instance, tags=None):
    if tags is not None:
        instance.tags = tags
    return instance
# endregion


# region DdosProtectionPlans
def create_ddos_plan(cmd, resource_group_name, ddos_plan_name, location=None, tags=None, vnets=None):
    from azure.cli.core.commands import LongRunningOperation

    ddos_client = network_client_factory(cmd.cli_ctx).ddos_protection_plans
    ddos_protection_plan = cmd.get_models('DdosProtectionPlan')()
    if location:
        ddos_protection_plan.location = location
    if tags:
        ddos_protection_plan.tags = tags
    if not vnets:
        # if no VNETs can do a simple PUT
        return ddos_client.begin_create_or_update(resource_group_name, ddos_plan_name, parameters=ddos_protection_plan)

    # if VNETs specified, have to create the protection plan and then add the VNETs
    plan_id = LongRunningOperation(cmd.cli_ctx)(
        ddos_client.begin_create_or_update(resource_group_name, ddos_plan_name, parameters=ddos_protection_plan)).id

    SubResource = cmd.get_models('SubResource')
    logger.info('Attempting to attach VNets to newly created DDoS protection plan.')
    for vnet_subresource in vnets:
        vnet_client = network_client_factory(cmd.cli_ctx).virtual_networks
        id_parts = parse_resource_id(vnet_subresource.id)
        vnet = vnet_client.get(id_parts['resource_group'], id_parts['name'])
        vnet.ddos_protection_plan = SubResource(id=plan_id)
        vnet_client.begin_create_or_update(id_parts['resource_group'], id_parts['name'], vnet)
    return ddos_client.get(resource_group_name, ddos_plan_name)


def update_ddos_plan(cmd, instance, tags=None, vnets=None):
    SubResource = cmd.get_models('SubResource')

    if tags is not None:
        instance.tags = tags
    if vnets is not None:
        logger.info('Attempting to update the VNets attached to the DDoS protection plan.')
        vnet_ids = set([])
        if len(vnets) == 1 and not vnets[0]:
            pass
        else:
            vnet_ids = {x.id for x in vnets}
        existing_vnet_ids = {x.id for x in instance.virtual_networks} if instance.virtual_networks else set([])
        client = network_client_factory(cmd.cli_ctx).virtual_networks
        for vnet_id in vnet_ids.difference(existing_vnet_ids):
            logger.info("Adding VNet '%s' to plan.", vnet_id)
            id_parts = parse_resource_id(vnet_id)
            vnet = client.get(id_parts['resource_group'], id_parts['name'])
            vnet.ddos_protection_plan = SubResource(id=instance.id)
            client.begin_create_or_update(id_parts['resource_group'], id_parts['name'], vnet)
        for vnet_id in existing_vnet_ids.difference(vnet_ids):
            logger.info("Removing VNet '%s' from plan.", vnet_id)
            id_parts = parse_resource_id(vnet_id)
            vnet = client.get(id_parts['resource_group'], id_parts['name'])
            vnet.ddos_protection_plan = None
            client.begin_create_or_update(id_parts['resource_group'], id_parts['name'], vnet)
    return instance


def list_ddos_plans(cmd, resource_group_name=None):
    client = network_client_factory(cmd.cli_ctx).ddos_protection_plans
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()
# endregion


# region DNS Commands
# add delegation name server record for the created child zone in it's parent zone.
def add_dns_delegation(cmd, child_zone, parent_zone, child_rg, child_zone_name):
    """
     :param child_zone: the zone object corresponding to the child that is created.
     :param parent_zone: the parent zone name / FQDN of the parent zone.
                         if parent zone name is mentioned, assume current subscription and resource group.
     :param child_rg: resource group of the child zone
     :param child_zone_name: name of the child zone
    """
    import sys
    from azure.core.exceptions import HttpResponseError
    parent_rg = child_rg
    parent_subscription_id = None
    parent_zone_name = parent_zone

    if is_valid_resource_id(parent_zone):
        id_parts = parse_resource_id(parent_zone)
        parent_rg = id_parts['resource_group']
        parent_subscription_id = id_parts['subscription']
        parent_zone_name = id_parts['name']

    if all([parent_zone_name, parent_rg, child_zone_name, child_zone]) and child_zone_name.endswith(parent_zone_name):
        record_set_name = child_zone_name.replace('.' + parent_zone_name, '')
        try:
            for dname in child_zone.name_servers:
                add_dns_ns_record(cmd, parent_rg, parent_zone_name, record_set_name, dname, parent_subscription_id)
            print('Delegation added succesfully in \'{}\'\n'.format(parent_zone_name), file=sys.stderr)
        except HttpResponseError as ex:
            logger.error(ex)
            print('Could not add delegation in \'{}\'\n'.format(parent_zone_name), file=sys.stderr)


def create_dns_zone(cmd, client, resource_group_name, zone_name, parent_zone_name=None, tags=None,
                    if_none_match=False, zone_type='Public', resolution_vnets=None, registration_vnets=None):
    Zone = cmd.get_models('Zone', resource_type=ResourceType.MGMT_NETWORK_DNS)
    zone = Zone(location='global', tags=tags)

    if hasattr(zone, 'zone_type'):
        zone.zone_type = zone_type
        zone.registration_virtual_networks = registration_vnets
        zone.resolution_virtual_networks = resolution_vnets

    created_zone = client.create_or_update(resource_group_name, zone_name, zone,
                                           if_none_match='*' if if_none_match else None)

    if cmd.supported_api_version(min_api='2016-04-01') and parent_zone_name is not None:
        logger.info('Attempting to add delegation in the parent zone')
        add_dns_delegation(cmd, created_zone, parent_zone_name, resource_group_name, zone_name)
    return created_zone


def update_dns_zone(instance, tags=None, zone_type=None, resolution_vnets=None, registration_vnets=None):

    if tags is not None:
        instance.tags = tags

    if zone_type:
        instance.zone_type = zone_type

    if resolution_vnets == ['']:
        instance.resolution_virtual_networks = None
    elif resolution_vnets:
        instance.resolution_virtual_networks = resolution_vnets

    if registration_vnets == ['']:
        instance.registration_virtual_networks = None
    elif registration_vnets:
        instance.registration_virtual_networks = registration_vnets
    return instance


def list_dns_zones(cmd, resource_group_name=None):
    ncf = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_NETWORK_DNS).zones
    if resource_group_name:
        return ncf.list_by_resource_group(resource_group_name)
    return ncf.list()


def create_dns_record_set(cmd, resource_group_name, zone_name, record_set_name, record_set_type,
                          metadata=None, if_match=None, if_none_match=None, ttl=3600, target_resource=None):

    RecordSet = cmd.get_models('RecordSet', resource_type=ResourceType.MGMT_NETWORK_DNS)
    SubResource = cmd.get_models('SubResource', resource_type=ResourceType.MGMT_NETWORK)
    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_NETWORK_DNS).record_sets
    record_set = RecordSet(
        ttl=ttl,
        metadata=metadata,
        target_resource=SubResource(id=target_resource) if target_resource else None
    )
    return client.create_or_update(resource_group_name, zone_name, record_set_name,
                                   record_set_type, record_set, if_match=if_match,
                                   if_none_match='*' if if_none_match else None)


def list_dns_record_set(client, resource_group_name, zone_name, record_type=None):
    if record_type:
        return client.list_by_type(resource_group_name, zone_name, record_type)

    return client.list_by_dns_zone(resource_group_name, zone_name)


def update_dns_record_set(instance, cmd, metadata=None, target_resource=None):
    if metadata is not None:
        instance.metadata = metadata
    if target_resource == '':
        instance.target_resource = None
    elif target_resource is not None:
        SubResource = cmd.get_models('SubResource')
        instance.target_resource = SubResource(id=target_resource)
    return instance


def _type_to_property_name(key):
    type_dict = {
        'a': 'a_records',
        'aaaa': 'aaaa_records',
        'caa': 'caa_records',
        'cname': 'cname_record',
        'mx': 'mx_records',
        'ns': 'ns_records',
        'ptr': 'ptr_records',
        'soa': 'soa_record',
        'spf': 'txt_records',
        'srv': 'srv_records',
        'txt': 'txt_records',
    }
    return type_dict[key.lower()]


def export_zone(cmd, resource_group_name, zone_name, file_name=None):
    from time import localtime, strftime

    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_NETWORK_DNS)
    record_sets = client.record_sets.list_by_dns_zone(resource_group_name, zone_name)

    zone_obj = OrderedDict({
        '$origin': zone_name.rstrip('.') + '.',
        'resource-group': resource_group_name,
        'zone-name': zone_name.rstrip('.'),
        'datetime': strftime('%a, %d %b %Y %X %z', localtime())
    })

    for record_set in record_sets:
        record_type = record_set.type.rsplit('/', 1)[1].lower()
        record_set_name = record_set.name
        record_data = getattr(record_set, _type_to_property_name(record_type), None)

        # ignore empty record sets
        if not record_data:
            continue

        if not isinstance(record_data, list):
            record_data = [record_data]

        if record_set_name not in zone_obj:
            zone_obj[record_set_name] = OrderedDict()

        for record in record_data:

            record_obj = {'ttl': record_set.ttl}

            if record_type not in zone_obj[record_set_name]:
                zone_obj[record_set_name][record_type] = []

            if record_type == 'aaaa':
                record_obj.update({'ip': record.ipv6_address})
            elif record_type == 'a':
                record_obj.update({'ip': record.ipv4_address})
            elif record_type == 'caa':
                record_obj.update({'val': record.value, 'tag': record.tag, 'flags': record.flags})
            elif record_type == 'cname':
                record_obj.update({'alias': record.cname.rstrip('.') + '.'})
            elif record_type == 'mx':
                record_obj.update({'preference': record.preference, 'host': record.exchange.rstrip('.') + '.'})
            elif record_type == 'ns':
                record_obj.update({'host': record.nsdname.rstrip('.') + '.'})
            elif record_type == 'ptr':
                record_obj.update({'host': record.ptrdname.rstrip('.') + '.'})
            elif record_type == 'soa':
                record_obj.update({
                    'mname': record.host.rstrip('.') + '.',
                    'rname': record.email.rstrip('.') + '.',
                    'serial': int(record.serial_number), 'refresh': record.refresh_time,
                    'retry': record.retry_time, 'expire': record.expire_time,
                    'minimum': record.minimum_ttl
                })
                zone_obj['$ttl'] = record.minimum_ttl
            elif record_type == 'srv':
                record_obj.update({'priority': record.priority, 'weight': record.weight,
                                   'port': record.port, 'target': record.target.rstrip('.') + '.'})
            elif record_type == 'txt':
                record_obj.update({'txt': ''.join(record.value)})

            zone_obj[record_set_name][record_type].append(record_obj)

    zone_file_content = make_zone_file(zone_obj)
    print(zone_file_content)
    if file_name:
        try:
            with open(file_name, 'w') as f:
                f.write(zone_file_content)
        except IOError:
            raise CLIError('Unable to export to file: {}'.format(file_name))


# pylint: disable=too-many-return-statements, inconsistent-return-statements
def _build_record(cmd, data):
    AaaaRecord, ARecord, CaaRecord, CnameRecord, MxRecord, NsRecord, PtrRecord, SoaRecord, SrvRecord, TxtRecord = \
        cmd.get_models('AaaaRecord', 'ARecord', 'CaaRecord', 'CnameRecord', 'MxRecord', 'NsRecord',
                       'PtrRecord', 'SoaRecord', 'SrvRecord', 'TxtRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record_type = data['delim'].lower()
    try:
        if record_type == 'aaaa':
            return AaaaRecord(ipv6_address=data['ip'])
        if record_type == 'a':
            return ARecord(ipv4_address=data['ip'])
        if (record_type == 'caa' and
                supported_api_version(cmd.cli_ctx, ResourceType.MGMT_NETWORK_DNS, min_api='2018-03-01-preview')):
            return CaaRecord(value=data['val'], flags=int(data['flags']), tag=data['tag'])
        if record_type == 'cname':
            return CnameRecord(cname=data['alias'])
        if record_type == 'mx':
            return MxRecord(preference=data['preference'], exchange=data['host'])
        if record_type == 'ns':
            return NsRecord(nsdname=data['host'])
        if record_type == 'ptr':
            return PtrRecord(ptrdname=data['host'])
        if record_type == 'soa':
            return SoaRecord(host=data['host'], email=data['email'], serial_number=data['serial'],
                             refresh_time=data['refresh'], retry_time=data['retry'], expire_time=data['expire'],
                             minimum_ttl=data['minimum'])
        if record_type == 'srv':
            return SrvRecord(
                priority=int(data['priority']), weight=int(data['weight']), port=int(data['port']),
                target=data['target'])
        if record_type in ['txt', 'spf']:
            text_data = data['txt']
            return TxtRecord(value=text_data) if isinstance(text_data, list) else TxtRecord(value=[text_data])
    except KeyError as ke:
        raise CLIError("The {} record '{}' is missing a property.  {}"
                       .format(record_type, data['name'], ke))


# pylint: disable=too-many-statements
def import_zone(cmd, resource_group_name, zone_name, file_name):
    from azure.cli.core.util import read_file_content
    from azure.core.exceptions import HttpResponseError
    import sys
    logger.warning("In the future, zone name will be case insensitive.")
    RecordSet = cmd.get_models('RecordSet', resource_type=ResourceType.MGMT_NETWORK_DNS)

    from azure.cli.core.azclierror import FileOperationError, UnclassifiedUserFault
    try:
        file_text = read_file_content(file_name)
    except FileNotFoundError:
        raise FileOperationError("No such file: " + str(file_name))
    except IsADirectoryError:
        raise FileOperationError("Is a directory: " + str(file_name))
    except PermissionError:
        raise FileOperationError("Permission denied: " + str(file_name))
    except OSError as e:
        raise UnclassifiedUserFault(e)

    zone_obj = parse_zone_file(file_text, zone_name)

    origin = zone_name
    record_sets = {}
    for record_set_name in zone_obj:
        for record_set_type in zone_obj[record_set_name]:
            record_set_obj = zone_obj[record_set_name][record_set_type]

            if record_set_type == 'soa':
                origin = record_set_name.rstrip('.')

            if not isinstance(record_set_obj, list):
                record_set_obj = [record_set_obj]

            for entry in record_set_obj:

                record_set_ttl = entry['ttl']
                record_set_key = '{}{}'.format(record_set_name.lower(), record_set_type)

                record = _build_record(cmd, entry)
                if not record:
                    logger.warning('Cannot import %s. RecordType is not found. Skipping...', entry['delim'].lower())
                    continue

                record_set = record_sets.get(record_set_key, None)
                if not record_set:

                    # Workaround for issue #2824
                    relative_record_set_name = record_set_name.rstrip('.')
                    if not relative_record_set_name.endswith(origin):
                        logger.warning(
                            'Cannot import %s. Only records relative to origin may be '
                            'imported at this time. Skipping...', relative_record_set_name)
                        continue

                    record_set = RecordSet(ttl=record_set_ttl)
                    record_sets[record_set_key] = record_set
                _add_record(record_set, record, record_set_type,
                            is_list=record_set_type.lower() not in ['soa', 'cname'])

    total_records = 0
    for key, rs in record_sets.items():
        rs_name, rs_type = key.lower().rsplit('.', 1)
        rs_name = rs_name[:-(len(origin) + 1)] if rs_name != origin else '@'
        try:
            record_count = len(getattr(rs, _type_to_property_name(rs_type)))
        except TypeError:
            record_count = 1
        total_records += record_count
    cum_records = 0

    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_NETWORK_DNS)
    print('== BEGINNING ZONE IMPORT: {} ==\n'.format(zone_name), file=sys.stderr)

    Zone = cmd.get_models('Zone', resource_type=ResourceType.MGMT_NETWORK_DNS)
    client.zones.create_or_update(resource_group_name, zone_name, Zone(location='global'))
    for key, rs in record_sets.items():

        rs_name, rs_type = key.lower().rsplit('.', 1)
        rs_name = '@' if rs_name == origin else rs_name
        if rs_name.endswith(origin):
            rs_name = rs_name[:-(len(origin) + 1)]

        try:
            record_count = len(getattr(rs, _type_to_property_name(rs_type)))
        except TypeError:
            record_count = 1
        if rs_name == '@' and rs_type == 'soa':
            root_soa = client.record_sets.get(resource_group_name, zone_name, '@', 'SOA')
            rs.soa_record.host = root_soa.soa_record.host
            rs_name = '@'
        elif rs_name == '@' and rs_type == 'ns':
            root_ns = client.record_sets.get(resource_group_name, zone_name, '@', 'NS')
            root_ns.ttl = rs.ttl
            rs = root_ns
            rs_type = rs.type.rsplit('/', 1)[1]
        try:
            client.record_sets.create_or_update(
                resource_group_name, zone_name, rs_name, rs_type, rs)
            cum_records += record_count
            print("({}/{}) Imported {} records of type '{}' and name '{}'"
                  .format(cum_records, total_records, record_count, rs_type, rs_name), file=sys.stderr)
        except HttpResponseError as ex:
            logger.error(ex)
    print("\n== {}/{} RECORDS IMPORTED SUCCESSFULLY: '{}' =="
          .format(cum_records, total_records, zone_name), file=sys.stderr)


def add_dns_aaaa_record(cmd, resource_group_name, zone_name, record_set_name, ipv6_address,
                        ttl=3600, if_none_match=None):
    AaaaRecord = cmd.get_models('AaaaRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = AaaaRecord(ipv6_address=ipv6_address)
    record_type = 'aaaa'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            ttl=ttl, if_none_match=if_none_match)


def add_dns_a_record(cmd, resource_group_name, zone_name, record_set_name, ipv4_address,
                     ttl=3600, if_none_match=None):
    ARecord = cmd.get_models('ARecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = ARecord(ipv4_address=ipv4_address)
    record_type = 'a'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name, 'arecords',
                            ttl=ttl, if_none_match=if_none_match)


def add_dns_caa_record(cmd, resource_group_name, zone_name, record_set_name, value, flags, tag,
                       ttl=3600, if_none_match=None):
    CaaRecord = cmd.get_models('CaaRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = CaaRecord(flags=flags, tag=tag, value=value)
    record_type = 'caa'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            ttl=ttl, if_none_match=if_none_match)


def add_dns_cname_record(cmd, resource_group_name, zone_name, record_set_name, cname, ttl=3600, if_none_match=None):
    CnameRecord = cmd.get_models('CnameRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = CnameRecord(cname=cname)
    record_type = 'cname'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            is_list=False, ttl=ttl, if_none_match=if_none_match)


def add_dns_mx_record(cmd, resource_group_name, zone_name, record_set_name, preference, exchange,
                      ttl=3600, if_none_match=None):
    MxRecord = cmd.get_models('MxRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = MxRecord(preference=int(preference), exchange=exchange)
    record_type = 'mx'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            ttl=ttl, if_none_match=if_none_match)


def add_dns_ns_record(cmd, resource_group_name, zone_name, record_set_name, dname,
                      subscription_id=None, ttl=3600, if_none_match=None):
    NsRecord = cmd.get_models('NsRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = NsRecord(nsdname=dname)
    record_type = 'ns'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            subscription_id=subscription_id, ttl=ttl, if_none_match=if_none_match)


def add_dns_ptr_record(cmd, resource_group_name, zone_name, record_set_name, dname, ttl=3600, if_none_match=None):
    PtrRecord = cmd.get_models('PtrRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = PtrRecord(ptrdname=dname)
    record_type = 'ptr'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            ttl=ttl, if_none_match=if_none_match)


def update_dns_soa_record(cmd, resource_group_name, zone_name, host=None, email=None,
                          serial_number=None, refresh_time=None, retry_time=None, expire_time=None,
                          minimum_ttl=3600, if_none_match=None):
    record_set_name = '@'
    record_type = 'soa'

    ncf = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_NETWORK_DNS).record_sets
    record_set = ncf.get(resource_group_name, zone_name, record_set_name, record_type)
    record = record_set.soa_record

    record.host = host or record.host
    record.email = email or record.email
    record.serial_number = serial_number or record.serial_number
    record.refresh_time = refresh_time or record.refresh_time
    record.retry_time = retry_time or record.retry_time
    record.expire_time = expire_time or record.expire_time
    record.minimum_ttl = minimum_ttl or record.minimum_ttl

    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            is_list=False, if_none_match=if_none_match)


def add_dns_srv_record(cmd, resource_group_name, zone_name, record_set_name, priority, weight,
                       port, target, if_none_match=None):
    SrvRecord = cmd.get_models('SrvRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = SrvRecord(priority=priority, weight=weight, port=port, target=target)
    record_type = 'srv'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            if_none_match=if_none_match)


def add_dns_txt_record(cmd, resource_group_name, zone_name, record_set_name, value, if_none_match=None):
    TxtRecord = cmd.get_models('TxtRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = TxtRecord(value=value)
    record_type = 'txt'
    long_text = ''.join(x for x in record.value)
    original_len = len(long_text)
    record.value = []
    while len(long_text) > 255:
        record.value.append(long_text[:255])
        long_text = long_text[255:]
    record.value.append(long_text)
    final_str = ''.join(record.value)
    final_len = len(final_str)
    assert original_len == final_len
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            if_none_match=if_none_match)


def remove_dns_aaaa_record(cmd, resource_group_name, zone_name, record_set_name, ipv6_address,
                           keep_empty_record_set=False):
    AaaaRecord = cmd.get_models('AaaaRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = AaaaRecord(ipv6_address=ipv6_address)
    record_type = 'aaaa'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_a_record(cmd, resource_group_name, zone_name, record_set_name, ipv4_address,
                        keep_empty_record_set=False):
    ARecord = cmd.get_models('ARecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = ARecord(ipv4_address=ipv4_address)
    record_type = 'a'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_caa_record(cmd, resource_group_name, zone_name, record_set_name, value,
                          flags, tag, keep_empty_record_set=False):
    CaaRecord = cmd.get_models('CaaRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = CaaRecord(flags=flags, tag=tag, value=value)
    record_type = 'caa'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_cname_record(cmd, resource_group_name, zone_name, record_set_name, cname,
                            keep_empty_record_set=False):
    CnameRecord = cmd.get_models('CnameRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = CnameRecord(cname=cname)
    record_type = 'cname'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          is_list=False, keep_empty_record_set=keep_empty_record_set)


def remove_dns_mx_record(cmd, resource_group_name, zone_name, record_set_name, preference, exchange,
                         keep_empty_record_set=False):
    MxRecord = cmd.get_models('MxRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = MxRecord(preference=int(preference), exchange=exchange)
    record_type = 'mx'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_ns_record(cmd, resource_group_name, zone_name, record_set_name, dname,
                         keep_empty_record_set=False):
    NsRecord = cmd.get_models('NsRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = NsRecord(nsdname=dname)
    record_type = 'ns'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_ptr_record(cmd, resource_group_name, zone_name, record_set_name, dname,
                          keep_empty_record_set=False):
    PtrRecord = cmd.get_models('PtrRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = PtrRecord(ptrdname=dname)
    record_type = 'ptr'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_srv_record(cmd, resource_group_name, zone_name, record_set_name, priority, weight,
                          port, target, keep_empty_record_set=False):
    SrvRecord = cmd.get_models('SrvRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = SrvRecord(priority=priority, weight=weight, port=port, target=target)
    record_type = 'srv'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_txt_record(cmd, resource_group_name, zone_name, record_set_name, value,
                          keep_empty_record_set=False):
    TxtRecord = cmd.get_models('TxtRecord', resource_type=ResourceType.MGMT_NETWORK_DNS)
    record = TxtRecord(value=value)
    record_type = 'txt'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def _check_a_record_exist(record, exist_list):
    for r in exist_list:
        if r.ipv4_address == record.ipv4_address:
            return True
    return False


def _check_aaaa_record_exist(record, exist_list):
    for r in exist_list:
        if r.ipv6_address == record.ipv6_address:
            return True
    return False


def _check_caa_record_exist(record, exist_list):
    for r in exist_list:
        if (r.flags == record.flags and
                r.tag == record.tag and
                r.value == record.value):
            return True
    return False


def _check_cname_record_exist(record, exist_list):
    for r in exist_list:
        if r.cname == record.cname:
            return True
    return False


def _check_mx_record_exist(record, exist_list):
    for r in exist_list:
        if (r.preference == record.preference and
                r.exchange == record.exchange):
            return True
    return False


def _check_ns_record_exist(record, exist_list):
    for r in exist_list:
        if r.nsdname == record.nsdname:
            return True
    return False


def _check_ptr_record_exist(record, exist_list):
    for r in exist_list:
        if r.ptrdname == record.ptrdname:
            return True
    return False


def _check_srv_record_exist(record, exist_list):
    for r in exist_list:
        if (r.priority == record.priority and
                r.weight == record.weight and
                r.port == record.port and
                r.target == record.target):
            return True
    return False


def _check_txt_record_exist(record, exist_list):
    for r in exist_list:
        if r.value == record.value:
            return True
    return False


def _record_exist_func(record_type):
    return globals()["_check_{}_record_exist".format(record_type)]


def _add_record(record_set, record, record_type, is_list=False):
    record_property = _type_to_property_name(record_type)

    if is_list:
        record_list = getattr(record_set, record_property)
        if record_list is None:
            setattr(record_set, record_property, [])
            record_list = getattr(record_set, record_property)

        _record_exist = _record_exist_func(record_type)
        if not _record_exist(record, record_list):
            record_list.append(record)
    else:
        setattr(record_set, record_property, record)


def _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                     is_list=True, subscription_id=None, ttl=None, if_none_match=None):
    from azure.core.exceptions import HttpResponseError
    ncf = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_NETWORK_DNS,
                                  subscription_id=subscription_id).record_sets

    try:
        record_set = ncf.get(resource_group_name, zone_name, record_set_name, record_type)
    except HttpResponseError:
        RecordSet = cmd.get_models('RecordSet', resource_type=ResourceType.MGMT_NETWORK_DNS)
        record_set = RecordSet(ttl=3600)

    if ttl is not None:
        record_set.ttl = ttl

    _add_record(record_set, record, record_type, is_list)

    return ncf.create_or_update(resource_group_name, zone_name, record_set_name,
                                record_type, record_set,
                                if_none_match='*' if if_none_match else None)


def _remove_record(cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                   keep_empty_record_set, is_list=True):
    ncf = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_NETWORK_DNS).record_sets
    record_set = ncf.get(resource_group_name, zone_name, record_set_name, record_type)
    record_property = _type_to_property_name(record_type)

    if is_list:
        record_list = getattr(record_set, record_property)
        if record_list is not None:
            keep_list = [r for r in record_list
                         if not dict_matches_filter(r.__dict__, record.__dict__)]
            if len(keep_list) == len(record_list):
                raise CLIError('Record {} not found.'.format(str(record)))
            setattr(record_set, record_property, keep_list)
    else:
        setattr(record_set, record_property, None)

    if is_list:
        records_remaining = len(getattr(record_set, record_property))
    else:
        records_remaining = 1 if getattr(record_set, record_property) is not None else 0

    if not records_remaining and not keep_empty_record_set:
        logger.info('Removing empty %s record set: %s', record_type, record_set_name)
        return ncf.delete(resource_group_name, zone_name, record_set_name, record_type)

    return ncf.create_or_update(resource_group_name, zone_name, record_set_name, record_type, record_set)


def dict_matches_filter(d, filter_dict):
    sentinel = object()
    return all(not filter_dict.get(key, None) or
               str(filter_dict[key]) == str(d.get(key, sentinel)) or
               lists_match(filter_dict[key], d.get(key, []))
               for key in filter_dict)


def lists_match(l1, l2):
    try:
        return Counter(l1) == Counter(l2)  # pylint: disable=too-many-function-args
    except TypeError:
        return False
# endregion


# region ExpressRoutes
def create_express_route(cmd, circuit_name, resource_group_name, bandwidth_in_mbps, peering_location,
                         service_provider_name, location=None, tags=None, no_wait=False,
                         sku_family=None, sku_tier=None, allow_global_reach=None, express_route_port=None,
                         allow_classic_operations=None):
    ExpressRouteCircuit, ExpressRouteCircuitSku, ExpressRouteCircuitServiceProviderProperties, SubResource = \
        cmd.get_models(
            'ExpressRouteCircuit', 'ExpressRouteCircuitSku', 'ExpressRouteCircuitServiceProviderProperties',
            'SubResource')
    client = network_client_factory(cmd.cli_ctx).express_route_circuits
    sku_name = '{}_{}'.format(sku_tier, sku_family)
    circuit = ExpressRouteCircuit(
        location=location, tags=tags,
        service_provider_properties=ExpressRouteCircuitServiceProviderProperties(
            service_provider_name=service_provider_name,
            peering_location=peering_location,
            bandwidth_in_mbps=bandwidth_in_mbps if not express_route_port else None),
        sku=ExpressRouteCircuitSku(name=sku_name, tier=sku_tier, family=sku_family),
        allow_global_reach=allow_global_reach,
        bandwidth_in_gbps=(int(bandwidth_in_mbps) / 1000) if express_route_port else None
    )
    if cmd.supported_api_version(min_api='2010-07-01') and allow_classic_operations is not None:
        circuit.allow_classic_operations = allow_classic_operations
    if cmd.supported_api_version(min_api='2018-08-01') and express_route_port:
        circuit.express_route_port = SubResource(id=express_route_port)
        circuit.service_provider_properties = None
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, circuit_name, circuit)


def update_express_route(instance, cmd, bandwidth_in_mbps=None, peering_location=None,
                         service_provider_name=None, sku_family=None, sku_tier=None, tags=None,
                         allow_global_reach=None, express_route_port=None,
                         allow_classic_operations=None):

    with cmd.update_context(instance) as c:
        c.set_param('allow_classic_operations', allow_classic_operations)
        c.set_param('tags', tags)
        c.set_param('allow_global_reach', allow_global_reach)

    with cmd.update_context(instance.sku) as c:
        c.set_param('family', sku_family)
        c.set_param('tier', sku_tier)

    with cmd.update_context(instance.service_provider_properties) as c:
        c.set_param('peering_location', peering_location)
        c.set_param('service_provider_name', service_provider_name)

    if express_route_port is not None:
        SubResource = cmd.get_models('SubResource')
        instance.express_route_port = SubResource(id=express_route_port)
        instance.service_provider_properties = None

    if bandwidth_in_mbps is not None:
        if not instance.express_route_port:
            instance.service_provider_properties.bandwith_in_mbps = float(bandwidth_in_mbps)
        else:
            instance.bandwidth_in_gbps = (float(bandwidth_in_mbps) / 1000)

    return instance


def create_express_route_peering_connection(cmd, resource_group_name, circuit_name, peering_name, connection_name,
                                            peer_circuit, address_prefix, authorization_key=None):
    client = network_client_factory(cmd.cli_ctx).express_route_circuit_connections
    ExpressRouteCircuitConnection, SubResource = cmd.get_models('ExpressRouteCircuitConnection', 'SubResource')
    source_circuit = resource_id(
        subscription=get_subscription_id(cmd.cli_ctx),
        resource_group=resource_group_name,
        namespace='Microsoft.Network',
        type='expressRouteCircuits',
        name=circuit_name,
        child_type_1='peerings',
        child_name_1=peering_name
    )
    conn = ExpressRouteCircuitConnection(
        express_route_circuit_peering=SubResource(id=source_circuit),
        peer_express_route_circuit_peering=SubResource(id=peer_circuit),
        address_prefix=address_prefix,
        authorization_key=authorization_key
    )
    return client.begin_create_or_update(resource_group_name, circuit_name, peering_name, connection_name, conn)


def set_express_route_peering_connection_config(cmd, resource_group_name, circuit_name, peering_name, connection_name,
                                                address_prefix):
    client = network_client_factory(cmd.cli_ctx).express_route_circuit_connections

    # Get Conn
    try:
        conn = client.get(resource_group_name, circuit_name, peering_name, connection_name)
    except ResourceNotFoundError:
        raise ResourceNotFoundError("Peering Connection {} doesn't exist".format(connection_name))

    Ipv6CircuitConnectionConfig = cmd.get_models('Ipv6CircuitConnectionConfig')

    ipv6_config = Ipv6CircuitConnectionConfig(
        address_prefix=address_prefix
    )
    conn.ipv6_circuit_connection_config = ipv6_config

    return client.begin_create_or_update(resource_group_name, circuit_name, peering_name, connection_name, conn)


def remove_express_route_peering_connection_config(cmd, resource_group_name, circuit_name, peering_name,
                                                   connection_name):
    client = network_client_factory(cmd.cli_ctx).express_route_circuit_connections

    # Get Conn
    try:
        conn = client.get(resource_group_name, circuit_name, peering_name, connection_name)
    except ResourceNotFoundError:
        raise ResourceNotFoundError("Peering Connection {} doesn't exist".format(connection_name))

    conn.ipv6_circuit_connection_config = None

    return client.begin_create_or_update(resource_group_name, circuit_name, peering_name, connection_name, conn)


def _validate_ipv6_address_prefixes(prefixes):
    from ipaddress import ip_network, IPv6Network
    prefixes = prefixes if isinstance(prefixes, list) else [prefixes]
    version = None
    for prefix in prefixes:
        try:
            network = ip_network(prefix)
            if version is None:
                version = type(network)
            else:
                if not isinstance(network, version):  # pylint: disable=isinstance-second-argument-not-valid-type
                    raise CLIError("usage error: '{}' incompatible mix of IPv4 and IPv6 address prefixes."
                                   .format(prefixes))
        except ValueError:
            raise CLIError("usage error: prefix '{}' is not recognized as an IPv4 or IPv6 address prefix."
                           .format(prefix))
    return version == IPv6Network


def create_express_route_peering(
        cmd, client, resource_group_name, circuit_name, peering_type, peer_asn, vlan_id,
        primary_peer_address_prefix, secondary_peer_address_prefix, shared_key=None,
        advertised_public_prefixes=None, customer_asn=None, routing_registry_name=None,
        route_filter=None, legacy_mode=None, ip_version='IPv4'):
    (ExpressRouteCircuitPeering, ExpressRouteCircuitPeeringConfig, RouteFilter) = \
        cmd.get_models('ExpressRouteCircuitPeering', 'ExpressRouteCircuitPeeringConfig', 'RouteFilter')

    if cmd.supported_api_version(min_api='2018-02-01'):
        ExpressRoutePeeringType = cmd.get_models('ExpressRoutePeeringType')
    else:
        ExpressRoutePeeringType = cmd.get_models('ExpressRouteCircuitPeeringType')

    if ip_version == 'IPv6' and cmd.supported_api_version(min_api='2020-08-01'):
        Ipv6ExpressRouteCircuitPeeringConfig = cmd.get_models('Ipv6ExpressRouteCircuitPeeringConfig')
        if peering_type == ExpressRoutePeeringType.microsoft_peering.value:
            microsoft_config = ExpressRouteCircuitPeeringConfig(advertised_public_prefixes=advertised_public_prefixes,
                                                                customer_asn=customer_asn,
                                                                routing_registry_name=routing_registry_name)
        else:
            microsoft_config = None
        ipv6 = Ipv6ExpressRouteCircuitPeeringConfig(primary_peer_address_prefix=primary_peer_address_prefix,
                                                    secondary_peer_address_prefix=secondary_peer_address_prefix,
                                                    microsoft_peering_config=microsoft_config,
                                                    route_filter=route_filter)
        peering = ExpressRouteCircuitPeering(peering_type=peering_type, ipv6_peering_config=ipv6, peer_asn=peer_asn,
                                             vlan_id=vlan_id)

    else:
        peering = ExpressRouteCircuitPeering(
            peering_type=peering_type, peer_asn=peer_asn, vlan_id=vlan_id,
            primary_peer_address_prefix=primary_peer_address_prefix,
            secondary_peer_address_prefix=secondary_peer_address_prefix,
            shared_key=shared_key)

        if peering_type == ExpressRoutePeeringType.microsoft_peering.value:
            peering.microsoft_peering_config = ExpressRouteCircuitPeeringConfig(
                advertised_public_prefixes=advertised_public_prefixes,
                customer_asn=customer_asn,
                routing_registry_name=routing_registry_name)
        if cmd.supported_api_version(min_api='2016-12-01') and route_filter:
            peering.route_filter = RouteFilter(id=route_filter)
        if cmd.supported_api_version(min_api='2017-10-01') and legacy_mode is not None:
            peering.microsoft_peering_config.legacy_mode = legacy_mode

    return client.begin_create_or_update(resource_group_name, circuit_name, peering_type, peering)


def _create_or_update_ipv6_peering(cmd, config, primary_peer_address_prefix, secondary_peer_address_prefix,
                                   route_filter, advertised_public_prefixes, customer_asn, routing_registry_name):
    if config:
        # update scenario
        with cmd.update_context(config) as c:
            c.set_param('primary_peer_address_prefix', primary_peer_address_prefix)
            c.set_param('secondary_peer_address_prefix', secondary_peer_address_prefix)
            c.set_param('advertised_public_prefixes', advertised_public_prefixes)
            c.set_param('customer_asn', customer_asn)
            c.set_param('routing_registry_name', routing_registry_name)

        if route_filter:
            RouteFilter = cmd.get_models('RouteFilter')
            config.route_filter = RouteFilter(id=route_filter)
    else:
        # create scenario

        IPv6Config, MicrosoftPeeringConfig = cmd.get_models(
            'Ipv6ExpressRouteCircuitPeeringConfig', 'ExpressRouteCircuitPeeringConfig')
        microsoft_config = MicrosoftPeeringConfig(advertised_public_prefixes=advertised_public_prefixes,
                                                  customer_asn=customer_asn,
                                                  routing_registry_name=routing_registry_name)
        config = IPv6Config(primary_peer_address_prefix=primary_peer_address_prefix,
                            secondary_peer_address_prefix=secondary_peer_address_prefix,
                            microsoft_peering_config=microsoft_config,
                            route_filter=route_filter)

    return config


def update_express_route_peering(cmd, instance, peer_asn=None, primary_peer_address_prefix=None,
                                 secondary_peer_address_prefix=None, vlan_id=None, shared_key=None,
                                 advertised_public_prefixes=None, customer_asn=None,
                                 routing_registry_name=None, route_filter=None, ip_version='IPv4',
                                 legacy_mode=None):

    # update settings common to all peering types
    with cmd.update_context(instance) as c:
        c.set_param('peer_asn', peer_asn)
        c.set_param('vlan_id', vlan_id)
        c.set_param('shared_key', shared_key)

    if ip_version == 'IPv6':
        # update is the only way to add IPv6 peering options
        instance.ipv6_peering_config = _create_or_update_ipv6_peering(cmd, instance.ipv6_peering_config,
                                                                      primary_peer_address_prefix,
                                                                      secondary_peer_address_prefix, route_filter,
                                                                      advertised_public_prefixes, customer_asn,
                                                                      routing_registry_name)
    else:
        # IPv4 Microsoft Peering (or non-Microsoft Peering)
        with cmd.update_context(instance) as c:
            c.set_param('primary_peer_address_prefix', primary_peer_address_prefix)
            c.set_param('secondary_peer_address_prefix', secondary_peer_address_prefix)

        if route_filter is not None:
            RouteFilter = cmd.get_models('RouteFilter')
            instance.route_filter = RouteFilter(id=route_filter)

        try:
            with cmd.update_context(instance.microsoft_peering_config) as c:
                c.set_param('advertised_public_prefixes', advertised_public_prefixes)
                c.set_param('customer_asn', customer_asn)
                c.set_param('routing_registry_name', routing_registry_name)
                c.set_param('legacy_mode', legacy_mode)
        except AttributeError:
            raise CLIError('--advertised-public-prefixes, --customer-asn, --routing-registry-name and '
                           '--legacy-mode are only applicable for Microsoft Peering.')
    return instance
# endregion


# region ExpressRoute Connection
# pylint: disable=unused-argument
def create_express_route_connection(cmd, resource_group_name, express_route_gateway_name, connection_name,
                                    peering, circuit_name=None, authorization_key=None, routing_weight=None,
                                    enable_internet_security=None, associated_route_table=None,
                                    propagated_route_tables=None, labels=None):
    ExpressRouteConnection, SubResource, RoutingConfiguration, PropagatedRouteTable\
        = cmd.get_models('ExpressRouteConnection', 'SubResource', 'RoutingConfiguration', 'PropagatedRouteTable')
    client = network_client_factory(cmd.cli_ctx).express_route_connections

    propagated_route_tables = PropagatedRouteTable(
        labels=labels,
        ids=[SubResource(id=propagated_route_table) for propagated_route_table in
             propagated_route_tables] if propagated_route_tables else None
    )
    routing_configuration = RoutingConfiguration(
        associated_route_table=SubResource(id=associated_route_table),
        propagated_route_tables=propagated_route_tables
    )
    connection = ExpressRouteConnection(
        name=connection_name,
        express_route_circuit_peering=SubResource(id=peering) if peering else None,
        authorization_key=authorization_key,
        routing_weight=routing_weight,
        routing_configuration=routing_configuration
    )

    if enable_internet_security and cmd.supported_api_version(min_api='2019-09-01'):
        connection.enable_internet_security = enable_internet_security

    return client.begin_create_or_update(resource_group_name, express_route_gateway_name, connection_name, connection)


# pylint: disable=unused-argument
def update_express_route_connection(instance, cmd, circuit_name=None, peering=None, authorization_key=None,
                                    routing_weight=None, enable_internet_security=None, associated_route_table=None,
                                    propagated_route_tables=None, labels=None):
    SubResource = cmd.get_models('SubResource')
    if peering is not None:
        instance.express_route_connection_id = SubResource(id=peering)
    if authorization_key is not None:
        instance.authorization_key = authorization_key
    if routing_weight is not None:
        instance.routing_weight = routing_weight
    if enable_internet_security is not None and cmd.supported_api_version(min_api='2019-09-01'):
        instance.enable_internet_security = enable_internet_security
    if associated_route_table is not None or propagated_route_tables is not None or labels is not None:
        if instance.routing_configuration is None:
            RoutingConfiguration = cmd.get_models('RoutingConfiguration')
            instance.routing_configuration = RoutingConfiguration()
        if associated_route_table is not None:
            instance.routing_configuration.associated_route_table = SubResource(id=associated_route_table)
        if propagated_route_tables is not None or labels is not None:
            if instance.routing_configuration.propagated_route_tables is None:
                PropagatedRouteTable = cmd.get_models('PropagatedRouteTable')
                instance.routing_configuration.propagated_route_tables = PropagatedRouteTable()
            if propagated_route_tables is not None:
                instance.routing_configuration.propagated_route_tables.ids = [SubResource(id=propagated_route_table) for propagated_route_table in propagated_route_tables]  # pylint: disable=line-too-long
            if labels is not None:
                instance.routing_configuration.propagated_route_tables.labels = labels

    return instance
# endregion


# region ExpressRoute Gateways
def create_express_route_gateway(cmd, resource_group_name, express_route_gateway_name, location=None, tags=None,
                                 min_val=2, max_val=None, virtual_hub=None):
    ExpressRouteGateway, SubResource = cmd.get_models('ExpressRouteGateway', 'SubResource')
    client = network_client_factory(cmd.cli_ctx).express_route_gateways
    gateway = ExpressRouteGateway(
        location=location,
        tags=tags,
        virtual_hub=SubResource(id=virtual_hub) if virtual_hub else None
    )
    if min or max:
        gateway.auto_scale_configuration = {'bounds': {'min': min_val, 'max': max_val}}
    return client.begin_create_or_update(resource_group_name, express_route_gateway_name, gateway)


def update_express_route_gateway(instance, cmd, tags=None, min_val=None, max_val=None):

    def _ensure_autoscale():
        if not instance.auto_scale_configuration:
            ExpressRouteGatewayPropertiesAutoScaleConfiguration, \
                ExpressRouteGatewayPropertiesAutoScaleConfigurationBounds = cmd.get_models(
                    'ExpressRouteGatewayPropertiesAutoScaleConfiguration',
                    'ExpressRouteGatewayPropertiesAutoScaleConfigurationBounds')
            instance.auto_scale_configuration = ExpressRouteGatewayPropertiesAutoScaleConfiguration(
                bounds=ExpressRouteGatewayPropertiesAutoScaleConfigurationBounds(min=min, max=max))

    if tags is not None:
        instance.tags = tags
    if min is not None:
        _ensure_autoscale()
        instance.auto_scale_configuration.bounds.min = min_val
    if max is not None:
        _ensure_autoscale()
        instance.auto_scale_configuration.bounds.max = max_val
    return instance


def list_express_route_gateways(cmd, resource_group_name=None):
    client = network_client_factory(cmd.cli_ctx).express_route_gateways
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list_by_subscription()
# endregion


# region ExpressRoute ports
def create_express_route_port(cmd, resource_group_name, express_route_port_name, location=None, tags=None,
                              peering_location=None, bandwidth_in_gbps=None, encapsulation=None):
    client = network_client_factory(cmd.cli_ctx).express_route_ports
    ExpressRoutePort = cmd.get_models('ExpressRoutePort')
    if bandwidth_in_gbps is not None:
        bandwidth_in_gbps = int(bandwidth_in_gbps)
    port = ExpressRoutePort(
        location=location,
        tags=tags,
        peering_location=peering_location,
        bandwidth_in_gbps=bandwidth_in_gbps,
        encapsulation=encapsulation
    )
    return client.begin_create_or_update(resource_group_name, express_route_port_name, port)


def update_express_route_port(cmd, instance, tags=None):
    with cmd.update_context(instance) as c:
        c.set_param('tags', tags, True)
    return instance


def download_generated_loa_as_pdf(cmd,
                                  resource_group_name,
                                  express_route_port_name,
                                  customer_name,
                                  file_path='loa.pdf'):
    import os
    import base64

    dirname, basename = os.path.dirname(file_path), os.path.basename(file_path)

    if basename == '':
        basename = 'loa.pdf'
    elif basename.endswith('.pdf') is False:
        basename = basename + '.pdf'

    file_path = os.path.join(dirname, basename)
    generate_express_route_ports_loa_request =\
        cmd.get_models('GenerateExpressRoutePortsLOARequest')(customer_name=customer_name)
    client = network_client_factory(cmd.cli_ctx).express_route_ports
    response = client.generate_loa(resource_group_name, express_route_port_name,
                                   generate_express_route_ports_loa_request)

    encoded_content = base64.b64decode(response.encoded_content)

    from azure.cli.core.azclierror import FileOperationError
    try:
        with open(file_path, 'wb') as f:
            f.write(encoded_content)
    except OSError as ex:
        raise FileOperationError(ex)

    logger.warning("The generated letter of authorization is saved at %s", file_path)


def list_express_route_ports(cmd, resource_group_name=None):
    client = network_client_factory(cmd.cli_ctx).express_route_ports
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()


def assign_express_route_port_identity(cmd, resource_group_name, express_route_port_name,
                                       user_assigned_identity, no_wait=False):
    client = network_client_factory(cmd.cli_ctx).express_route_ports
    ports = client.get(resource_group_name, express_route_port_name)

    ManagedServiceIdentity, ManagedServiceIdentityUserAssignedIdentitiesValue = \
        cmd.get_models('ManagedServiceIdentity', 'Components1Jq1T4ISchemasManagedserviceidentityPropertiesUserassignedidentitiesAdditionalproperties')  # pylint: disable=line-too-long

    user_assigned_identity_instance = ManagedServiceIdentityUserAssignedIdentitiesValue()
    user_assigned_identities_instance = dict()
    user_assigned_identities_instance[user_assigned_identity] = user_assigned_identity_instance

    identity_instance = ManagedServiceIdentity(type="UserAssigned",
                                               user_assigned_identities=user_assigned_identities_instance)
    ports.identity = identity_instance

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, express_route_port_name, ports)


def remove_express_route_port_identity(cmd, resource_group_name, express_route_port_name, no_wait=False):
    client = network_client_factory(cmd.cli_ctx).express_route_ports
    ports = client.get(resource_group_name, express_route_port_name)

    if ports.identity is None:
        logger.warning("The identity of the ExpressRoute Port doesn't exist.")
        return ports

    ports.identity = None

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, express_route_port_name, ports)


def show_express_route_port_identity(cmd, resource_group_name, express_route_port_name):
    client = network_client_factory(cmd.cli_ctx).express_route_ports
    ports = client.get(resource_group_name, express_route_port_name)
    return ports.identity


def update_express_route_port_link(cmd, instance, parent, express_route_port_name, link_name,
                                   macsec_cak_secret_identifier=None, macsec_ckn_secret_identifier=None,
                                   macsec_sci_state=None, macsec_cipher=None, admin_state=None):
    """
    :param cmd:
    :param instance: an instance of ExpressRoutePort
    :param express_route_port_name:
    :param link_name:
    :param macsec_cak_secret_identifier:
    :param macsec_ckn_secret_identifier:
    :param macsec_cipher:
    :param admin_state:
    :return:
    """
    if any([macsec_cak_secret_identifier, macsec_ckn_secret_identifier, macsec_cipher, macsec_sci_state]):
        instance.mac_sec_config.cak_secret_identifier = macsec_cak_secret_identifier
        instance.mac_sec_config.ckn_secret_identifier = macsec_ckn_secret_identifier

        # TODO https://github.com/Azure/azure-rest-api-specs/issues/7569
        # need to remove this conversion when the issue is fixed.
        if macsec_cipher is not None:
            macsec_ciphers_tmp = {'gcm-aes-128': 'GcmAes128', 'gcm-aes-256': 'GcmAes256'}
            macsec_cipher = macsec_ciphers_tmp.get(macsec_cipher, macsec_cipher)
        instance.mac_sec_config.cipher = macsec_cipher
        instance.mac_sec_config.sci_state = macsec_sci_state

    if admin_state is not None:
        instance.admin_state = admin_state

    return parent
# endregion


# region PrivateEndpoint
def create_private_endpoint(cmd, resource_group_name, private_endpoint_name, subnet,
                            private_connection_resource_id, connection_name, group_ids=None,
                            virtual_network_name=None, tags=None, location=None,
                            request_message=None, manual_request=None, edge_zone=None,
                            ip_configurations=None, application_security_groups=None, custom_interface_name=None):
    client = network_client_factory(cmd.cli_ctx).private_endpoints
    PrivateEndpoint, Subnet, PrivateLinkServiceConnection = cmd.get_models('PrivateEndpoint',
                                                                           'Subnet',
                                                                           'PrivateLinkServiceConnection')
    pls_connection = PrivateLinkServiceConnection(private_link_service_id=private_connection_resource_id,
                                                  group_ids=group_ids,
                                                  request_message=request_message,
                                                  name=connection_name)
    private_endpoint = PrivateEndpoint(
        location=location,
        tags=tags,
        subnet=Subnet(id=subnet)
    )

    if manual_request:
        private_endpoint.manual_private_link_service_connections = [pls_connection]
    else:
        private_endpoint.private_link_service_connections = [pls_connection]

    if edge_zone:
        private_endpoint.extended_location = _edge_zone_model(cmd, edge_zone)

    if cmd.supported_api_version(min_api='2021-05-01'):
        if ip_configurations:
            PrivateEndpointIPConfiguration = cmd.get_models("PrivateEndpointIPConfiguration")
            for prop in ip_configurations:
                ip_config = PrivateEndpointIPConfiguration(
                    name=prop['name'],
                    group_id=prop['group_id'],
                    member_name=prop['member_name'],
                    private_ip_address=prop['private_ip_address']
                )
                try:
                    private_endpoint.ip_configurations.append(ip_config)
                except AttributeError:
                    private_endpoint.ip_configurations = [ip_config]
        if application_security_groups:
            ApplicationSecurityGroup = cmd.get_models("ApplicationSecurityGroup")
            for prop in application_security_groups:
                asg = ApplicationSecurityGroup(id=prop["id"])
                try:
                    private_endpoint.application_security_groups.append(asg)
                except AttributeError:
                    private_endpoint.application_security_groups = [asg]
        if custom_interface_name:
            private_endpoint.custom_network_interface_name = custom_interface_name

    return client.begin_create_or_update(resource_group_name, private_endpoint_name, private_endpoint)


def update_private_endpoint(instance, cmd, tags=None, request_message=None):
    with cmd.update_context(instance) as c:
        c.set_param('tags', tags)

    if request_message is not None:
        if instance.private_link_service_connections:
            instance.private_link_service_connections[0].request_message = request_message
        else:
            instance.manual_private_link_service_connections[0].request_message = request_message

    return instance


def list_private_endpoints(cmd, resource_group_name=None):
    client = network_client_factory(cmd.cli_ctx).private_endpoints
    if resource_group_name:
        return client.list(resource_group_name)
    return client.list_by_subscription()


def create_private_endpoint_private_dns_zone_group(cmd, resource_group_name, private_endpoint_name,
                                                   private_dns_zone_group_name,
                                                   private_dns_zone_name, private_dns_zone):
    client = network_client_factory(cmd.cli_ctx).private_dns_zone_groups
    PrivateDnsZoneGroup, PrivateDnsZoneConfig = cmd.get_models('PrivateDnsZoneGroup', 'PrivateDnsZoneConfig')
    private_dns_zone_group = PrivateDnsZoneGroup(name=private_dns_zone_group_name,
                                                 private_dns_zone_configs=[PrivateDnsZoneConfig(private_dns_zone_id=private_dns_zone,  # pylint: disable=line-too-long
                                                                                                name=private_dns_zone_name)])  # pylint: disable=line-too-long
    return client.begin_create_or_update(resource_group_name=resource_group_name,
                                         private_endpoint_name=private_endpoint_name,
                                         private_dns_zone_group_name=private_dns_zone_group_name,
                                         parameters=private_dns_zone_group)


def add_private_endpoint_private_dns_zone(cmd, resource_group_name, private_endpoint_name,
                                          private_dns_zone_group_name,
                                          private_dns_zone_name, private_dns_zone):
    client = network_client_factory(cmd.cli_ctx).private_dns_zone_groups
    PrivateDnsZoneConfig = cmd.get_models('PrivateDnsZoneConfig')
    private_dns_zone_group = client.get(resource_group_name=resource_group_name,
                                        private_endpoint_name=private_endpoint_name,
                                        private_dns_zone_group_name=private_dns_zone_group_name)
    private_dns_zone = PrivateDnsZoneConfig(private_dns_zone_id=private_dns_zone, name=private_dns_zone_name)
    private_dns_zone_group.private_dns_zone_configs.append(private_dns_zone)
    return client.begin_create_or_update(resource_group_name=resource_group_name,
                                         private_endpoint_name=private_endpoint_name,
                                         private_dns_zone_group_name=private_dns_zone_group_name,
                                         parameters=private_dns_zone_group)


def remove_private_endpoint_private_dns_zone(cmd, resource_group_name, private_endpoint_name,
                                             private_dns_zone_group_name,
                                             private_dns_zone_name):
    client = network_client_factory(cmd.cli_ctx).private_dns_zone_groups
    private_dns_zone_group = client.get(resource_group_name=resource_group_name,
                                        private_endpoint_name=private_endpoint_name,
                                        private_dns_zone_group_name=private_dns_zone_group_name)
    private_dns_zone_configs = [item for item in private_dns_zone_group.private_dns_zone_configs if item.name != private_dns_zone_name]  # pylint: disable=line-too-long
    private_dns_zone_group.private_dns_zone_configs = private_dns_zone_configs
    return client.begin_create_or_update(resource_group_name=resource_group_name,
                                         private_endpoint_name=private_endpoint_name,
                                         private_dns_zone_group_name=private_dns_zone_group_name,
                                         parameters=private_dns_zone_group)


def add_private_endpoint_ip_config(cmd, resource_group_name, private_endpoint_name,
                                   ip_config_name=None, group_id=None, member_name=None, private_ip_address=None):
    client = network_client_factory(cmd.cli_ctx).private_endpoints
    private_endpoint = client.get(resource_group_name, private_endpoint_name)

    PrivateEndpointIPConfiguration = cmd.get_models("PrivateEndpointIPConfiguration")
    ip_config = PrivateEndpointIPConfiguration(
        name=ip_config_name,
        group_id=group_id,
        member_name=member_name,
        private_ip_address=private_ip_address
    )
    private_endpoint.ip_configurations.append(ip_config)
    return client.begin_create_or_update(resource_group_name, private_endpoint_name, private_endpoint)


def remove_private_endpoint_ip_config(cmd, resource_group_name, private_endpoint_name, ip_config_name):
    client = network_client_factory(cmd.cli_ctx).private_endpoints
    private_endpoint = client.get(resource_group_name, private_endpoint_name)

    ip_config = None
    for item in private_endpoint.ip_configurations:
        if item.name == ip_config_name:
            ip_config = item
            break
    if ip_config is None:
        logger.warning("IP Configuration %s doesn't exist.", ip_config_name)
        return private_endpoint
    private_endpoint.ip_configurations.remove(ip_config)
    return client.begin_create_or_update(resource_group_name, private_endpoint_name, private_endpoint)


def list_private_endpoint_ip_config(cmd, resource_group_name, private_endpoint_name):
    client = network_client_factory(cmd.cli_ctx).private_endpoints
    private_endpoint = client.get(resource_group_name, private_endpoint_name)
    return private_endpoint.ip_configurations


def add_private_endpoint_asg(cmd, resource_group_name, private_endpoint_name, application_security_group_id=None):
    client = network_client_factory(cmd.cli_ctx).private_endpoints
    private_endpoint = client.get(resource_group_name, private_endpoint_name)

    ApplicationSecurityGroup = cmd.get_models("ApplicationSecurityGroup")
    asg = ApplicationSecurityGroup(id=application_security_group_id)
    try:
        private_endpoint.application_security_groups.append(asg)
    except AttributeError:
        private_endpoint.application_security_groups = [asg]
    return client.begin_create_or_update(resource_group_name, private_endpoint_name, private_endpoint)


def remove_private_endpoint_asg(cmd, resource_group_name, private_endpoint_name, application_security_group_id):
    client = network_client_factory(cmd.cli_ctx).private_endpoints
    private_endpoint = client.get(resource_group_name, private_endpoint_name)

    asg = None
    for item in private_endpoint.application_security_groups:
        if item.id == application_security_group_id:
            asg = item
            break
    if asg is None:
        logger.warning("Application security group %s doesn't exist.", application_security_group_id)
        return private_endpoint
    private_endpoint.application_security_groups.remove(asg)
    return client.begin_create_or_update(resource_group_name, private_endpoint_name, private_endpoint)


def list_private_endpoint_asg(cmd, resource_group_name, private_endpoint_name):
    client = network_client_factory(cmd.cli_ctx).private_endpoints
    private_endpoint = client.get(resource_group_name, private_endpoint_name)
    return private_endpoint.application_security_groups
# endregion


# region PrivateLinkService
def create_private_link_service(cmd, resource_group_name, service_name, subnet, frontend_ip_configurations,
                                private_ip_address=None, private_ip_allocation_method=None,
                                private_ip_address_version=None,
                                virtual_network_name=None, public_ip_address=None,
                                location=None, tags=None, load_balancer_name=None,
                                visibility=None, auto_approval=None, fqdns=None,
                                enable_proxy_protocol=None, edge_zone=None):
    client = network_client_factory(cmd.cli_ctx).private_link_services
    FrontendIPConfiguration, PrivateLinkService, PrivateLinkServiceIpConfiguration, PublicIPAddress, Subnet = \
        cmd.get_models('FrontendIPConfiguration', 'PrivateLinkService', 'PrivateLinkServiceIpConfiguration',
                       'PublicIPAddress', 'Subnet')
    pls_ip_config = PrivateLinkServiceIpConfiguration(
        name='{}_ipconfig_0'.format(service_name),
        private_ip_address=private_ip_address,
        private_ip_allocation_method=private_ip_allocation_method,
        private_ip_address_version=private_ip_address_version,
        subnet=subnet and Subnet(id=subnet),
        public_ip_address=public_ip_address and PublicIPAddress(id=public_ip_address)
    )
    link_service = PrivateLinkService(
        location=location,
        load_balancer_frontend_ip_configurations=frontend_ip_configurations and [
            FrontendIPConfiguration(id=ip_config) for ip_config in frontend_ip_configurations
        ],
        ip_configurations=[pls_ip_config],
        visbility=visibility,
        auto_approval=auto_approval,
        fqdns=fqdns,
        tags=tags,
        enable_proxy_protocol=enable_proxy_protocol
    )
    if edge_zone:
        link_service.extended_location = _edge_zone_model(cmd, edge_zone)
    return client.begin_create_or_update(resource_group_name, service_name, link_service)


def update_private_link_service(instance, cmd, tags=None, frontend_ip_configurations=None, load_balancer_name=None,
                                visibility=None, auto_approval=None, fqdns=None, enable_proxy_protocol=None):
    FrontendIPConfiguration = cmd.get_models('FrontendIPConfiguration')
    with cmd.update_context(instance) as c:
        c.set_param('tags', tags)
        c.set_param('load_balancer_frontend_ip_configurations', frontend_ip_configurations and [
            FrontendIPConfiguration(id=ip_config) for ip_config in frontend_ip_configurations
        ])
        c.set_param('visibility', visibility)
        c.set_param('auto_approval', auto_approval)
        c.set_param('fqdns', fqdns)
        c.set_param('enable_proxy_protocol', enable_proxy_protocol)
    return instance


def list_private_link_services(cmd, resource_group_name=None):
    client = network_client_factory(cmd.cli_ctx).private_link_services
    if resource_group_name:
        return client.list(resource_group_name)
    return client.list_by_subscription()


def update_private_endpoint_connection(cmd, resource_group_name, service_name, pe_connection_name,
                                       connection_status, description=None, action_required=None):
    client = network_client_factory(cmd.cli_ctx).private_link_services
    PrivateEndpointConnection, PrivateLinkServiceConnectionState = cmd.get_models('PrivateEndpointConnection',
                                                                                  'PrivateLinkServiceConnectionState')
    connection_state = PrivateLinkServiceConnectionState(
        status=connection_status,
        description=description,
        actions_required=action_required
    )
    pe_connection = PrivateEndpointConnection(
        private_link_service_connection_state=connection_state
    )
    return client.update_private_endpoint_connection(resource_group_name, service_name, pe_connection_name, pe_connection)  # pylint: disable=line-too-long


def add_private_link_services_ipconfig(cmd, resource_group_name, service_name,
                                       private_ip_address=None, private_ip_allocation_method=None,
                                       private_ip_address_version=None,
                                       subnet=None, virtual_network_name=None, public_ip_address=None):
    client = network_client_factory(cmd.cli_ctx).private_link_services
    PrivateLinkServiceIpConfiguration, PublicIPAddress, Subnet = cmd.get_models('PrivateLinkServiceIpConfiguration',
                                                                                'PublicIPAddress',
                                                                                'Subnet')
    link_service = client.get(resource_group_name, service_name)
    if link_service is None:
        raise CLIError("Private link service should be existed. Please create it first.")
    ip_name_index = len(link_service.ip_configurations)
    ip_config = PrivateLinkServiceIpConfiguration(
        name='{0}_ipconfig_{1}'.format(service_name, ip_name_index),
        private_ip_address=private_ip_address,
        private_ip_allocation_method=private_ip_allocation_method,
        private_ip_address_version=private_ip_address_version,
        subnet=subnet and Subnet(id=subnet),
        public_ip_address=public_ip_address and PublicIPAddress(id=public_ip_address)
    )
    link_service.ip_configurations.append(ip_config)
    return client.begin_create_or_update(resource_group_name, service_name, link_service)


def remove_private_link_services_ipconfig(cmd, resource_group_name, service_name, ip_config_name):
    client = network_client_factory(cmd.cli_ctx).private_link_services
    link_service = client.get(resource_group_name, service_name)
    if link_service is None:
        raise CLIError("Private link service should be existed. Please create it first.")
    ip_config = None
    for item in link_service.ip_configurations:
        if item.name == ip_config_name:
            ip_config = item
            break
    if ip_config is None:  # pylint: disable=no-else-return
        logger.warning("%s ip configuration doesn't exist", ip_config_name)
        return link_service
    else:
        link_service.ip_configurations.remove(ip_config)
        return client.begin_create_or_update(resource_group_name, service_name, link_service)
# endregion


def _edge_zone_model(cmd, edge_zone):
    ExtendedLocation, ExtendedLocationTypes = cmd.get_models('ExtendedLocation', 'ExtendedLocationTypes')
    return ExtendedLocation(name=edge_zone, type=ExtendedLocationTypes.EDGE_ZONE)


# region LoadBalancers
def create_load_balancer(cmd, load_balancer_name, resource_group_name, location=None, tags=None,
                         backend_pool_name=None, frontend_ip_name='LoadBalancerFrontEnd',
                         private_ip_address=None, public_ip_address=None,
                         public_ip_address_allocation=None,
                         public_ip_dns_name=None, subnet=None, subnet_address_prefix='10.0.0.0/24',
                         virtual_network_name=None, vnet_address_prefix='10.0.0.0/16',
                         public_ip_address_type=None, subnet_type=None, validate=False,
                         no_wait=False, sku=None, frontend_ip_zone=None, public_ip_zone=None,
                         private_ip_address_version=None, edge_zone=None):
    from azure.cli.core.util import random_string
    from azure.cli.core.commands.arm import ArmTemplateBuilder
    from azure.cli.command_modules.network._template_builder import (
        build_load_balancer_resource, build_public_ip_resource, build_vnet_resource)

    DeploymentProperties = cmd.get_models('DeploymentProperties', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    IPAllocationMethod = cmd.get_models('IPAllocationMethod')

    tags = tags or {}
    public_ip_address = public_ip_address or 'PublicIP{}'.format(load_balancer_name)
    backend_pool_name = backend_pool_name or '{}bepool'.format(load_balancer_name)
    if not public_ip_address_allocation:
        public_ip_address_allocation = IPAllocationMethod.static.value if (sku and sku.lower() == 'standard') \
            else IPAllocationMethod.dynamic.value

    # Build up the ARM template
    master_template = ArmTemplateBuilder()
    lb_dependencies = []

    public_ip_id = public_ip_address if is_valid_resource_id(public_ip_address) else None
    subnet_id = subnet if is_valid_resource_id(subnet) else None
    private_ip_allocation = IPAllocationMethod.static.value if private_ip_address \
        else IPAllocationMethod.dynamic.value

    network_id_template = resource_id(
        subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name,
        namespace='Microsoft.Network')

    if edge_zone and cmd.supported_api_version(min_api='2020-08-01'):
        edge_zone_type = 'EdgeZone'
    else:
        edge_zone_type = None

    if subnet_type == 'new':
        lb_dependencies.append('Microsoft.Network/virtualNetworks/{}'.format(virtual_network_name))
        vnet = build_vnet_resource(
            cmd, virtual_network_name, location, tags, vnet_address_prefix, subnet,
            subnet_address_prefix)
        master_template.add_resource(vnet)
        subnet_id = '{}/virtualNetworks/{}/subnets/{}'.format(
            network_id_template, virtual_network_name, subnet)

    if public_ip_address_type == 'new':
        lb_dependencies.append('Microsoft.Network/publicIpAddresses/{}'.format(public_ip_address))
        master_template.add_resource(build_public_ip_resource(cmd, public_ip_address, location,
                                                              tags,
                                                              public_ip_address_allocation,
                                                              public_ip_dns_name,
                                                              sku, public_ip_zone, None, edge_zone, edge_zone_type))
        public_ip_id = '{}/publicIPAddresses/{}'.format(network_id_template,
                                                        public_ip_address)

    load_balancer_resource = build_load_balancer_resource(
        cmd, load_balancer_name, location, tags, backend_pool_name, frontend_ip_name,
        public_ip_id, subnet_id, private_ip_address, private_ip_allocation, sku,
        frontend_ip_zone, private_ip_address_version, None, edge_zone, edge_zone_type)
    load_balancer_resource['dependsOn'] = lb_dependencies
    master_template.add_resource(load_balancer_resource)
    master_template.add_output('loadBalancer', load_balancer_name, output_type='object')

    template = master_template.build()

    # deploy ARM template
    deployment_name = 'lb_deploy_' + random_string(32)
    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES).deployments
    properties = DeploymentProperties(template=template, parameters={}, mode='incremental')
    Deployment = cmd.get_models('Deployment', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    deployment = Deployment(properties=properties)

    if validate:
        _log_pprint_template(template)
        if cmd.supported_api_version(min_api='2019-10-01', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES):
            from azure.cli.core.commands import LongRunningOperation
            validation_poller = client.begin_validate(resource_group_name, deployment_name, deployment)
            return LongRunningOperation(cmd.cli_ctx)(validation_poller)

        return client.validate(resource_group_name, deployment_name, deployment)

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, deployment_name, deployment)


def list_load_balancer_nic(cmd, resource_group_name, load_balancer_name):
    client = network_client_factory(cmd.cli_ctx).load_balancer_network_interfaces
    return client.list(resource_group_name, load_balancer_name)


def list_load_balancer_mapping(cmd, resource_group_name, load_balancer_name, backend_pool_name, request):
    client = network_client_factory(cmd.cli_ctx).load_balancers
    return client.begin_list_inbound_nat_rule_port_mappings(
        resource_group_name,
        load_balancer_name,
        backend_pool_name,
        request
    )


def create_lb_inbound_nat_rule(
        cmd, resource_group_name, load_balancer_name, item_name, protocol, backend_port, frontend_port=None,
        frontend_ip_name=None, floating_ip=None, idle_timeout=None, enable_tcp_reset=None,
        frontend_port_range_start=None, frontend_port_range_end=None, backend_pool_name=None):
    InboundNatRule, SubResource = cmd.get_models('InboundNatRule', 'SubResource')
    ncf = network_client_factory(cmd.cli_ctx)
    lb = lb_get(ncf.load_balancers, resource_group_name, load_balancer_name)
    if not frontend_ip_name:
        frontend_ip_name = _get_default_name(lb, 'frontend_ip_configurations', '--frontend-ip-name')
    frontend_ip = get_property(lb.frontend_ip_configurations, frontend_ip_name)  # pylint: disable=no-member
    new_rule = InboundNatRule(
        name=item_name, protocol=protocol,
        frontend_port=frontend_port, backend_port=backend_port,
        frontend_ip_configuration=frontend_ip,
        enable_floating_ip=floating_ip,
        idle_timeout_in_minutes=idle_timeout,
        enable_tcp_reset=enable_tcp_reset)
    if frontend_port_range_end and cmd.supported_api_version('2021-03-01'):
        new_rule.frontend_port_range_end = frontend_port_range_end
    if frontend_port_range_start and cmd.supported_api_version('2021-03-01'):
        new_rule.frontend_port_range_start = frontend_port_range_start
    if backend_pool_name and cmd.supported_api_version('2021-03-01'):
        backend_pool_id = get_property(lb.backend_address_pools, backend_pool_name).id
        new_rule.backend_address_pool = SubResource(id=backend_pool_id)
    upsert_to_collection(lb, 'inbound_nat_rules', new_rule, 'name')
    poller = ncf.load_balancers.begin_create_or_update(resource_group_name, load_balancer_name, lb)
    return get_property(poller.result().inbound_nat_rules, item_name)


# workaround for : https://github.com/Azure/azure-cli/issues/17071
def lb_get(client, resource_group_name, load_balancer_name):
    lb = client.get(resource_group_name, load_balancer_name)
    return lb_get_operation(lb)


# workaround for : https://github.com/Azure/azure-cli/issues/17071
def lb_get_operation(lb):
    for item in lb.frontend_ip_configurations:
        if item.zones is not None and len(item.zones) >= 3 and item.subnet is None:
            item.zones = None

    return lb


def set_lb_inbound_nat_rule(
        cmd, instance, parent, item_name, protocol=None, frontend_port=None,
        frontend_ip_name=None, backend_port=None, floating_ip=None, idle_timeout=None, enable_tcp_reset=None,
        frontend_port_range_start=None, frontend_port_range_end=None):
    if frontend_ip_name:
        instance.frontend_ip_configuration = \
            get_property(parent.frontend_ip_configurations, frontend_ip_name)

    if enable_tcp_reset is not None:
        instance.enable_tcp_reset = enable_tcp_reset
    if frontend_port_range_start is not None and cmd.supported_api_version('2021-03-01'):
        instance.frontend_port_range_start = frontend_port_range_start
    if frontend_port_range_end is not None and cmd.supported_api_version('2021-03-01'):
        instance.frontend_port_range_end = frontend_port_range_end

    with cmd.update_context(instance) as c:
        c.set_param('protocol', protocol)
        c.set_param('frontend_port', frontend_port)
        c.set_param('backend_port', backend_port)
        c.set_param('idle_timeout_in_minutes', idle_timeout)
        c.set_param('enable_floating_ip', floating_ip)

    return parent


def create_lb_inbound_nat_pool(
        cmd, resource_group_name, load_balancer_name, item_name, protocol, frontend_port_range_start,
        frontend_port_range_end, backend_port, frontend_ip_name=None, enable_tcp_reset=None,
        floating_ip=None, idle_timeout=None):
    InboundNatPool = cmd.get_models('InboundNatPool')
    ncf = network_client_factory(cmd.cli_ctx)
    lb = lb_get(ncf.load_balancers, resource_group_name, load_balancer_name)
    if not frontend_ip_name:
        frontend_ip_name = _get_default_name(lb, 'frontend_ip_configurations', '--frontend-ip-name')
    frontend_ip = get_property(lb.frontend_ip_configurations, frontend_ip_name) \
        if frontend_ip_name else None
    new_pool = InboundNatPool(
        name=item_name,
        protocol=protocol,
        frontend_ip_configuration=frontend_ip,
        frontend_port_range_start=frontend_port_range_start,
        frontend_port_range_end=frontend_port_range_end,
        backend_port=backend_port,
        enable_tcp_reset=enable_tcp_reset,
        enable_floating_ip=floating_ip,
        idle_timeout_in_minutes=idle_timeout)
    upsert_to_collection(lb, 'inbound_nat_pools', new_pool, 'name')
    poller = ncf.load_balancers.begin_create_or_update(resource_group_name, load_balancer_name, lb)
    return get_property(poller.result().inbound_nat_pools, item_name)


def set_lb_inbound_nat_pool(
        cmd, instance, parent, item_name, protocol=None,
        frontend_port_range_start=None, frontend_port_range_end=None, backend_port=None,
        frontend_ip_name=None, enable_tcp_reset=None, floating_ip=None, idle_timeout=None):
    with cmd.update_context(instance) as c:
        c.set_param('protocol', protocol)
        c.set_param('frontend_port_range_start', frontend_port_range_start)
        c.set_param('frontend_port_range_end', frontend_port_range_end)
        c.set_param('backend_port', backend_port)
        c.set_param('enable_floating_ip', floating_ip)
        c.set_param('idle_timeout_in_minutes', idle_timeout)

    if enable_tcp_reset is not None:
        instance.enable_tcp_reset = enable_tcp_reset

    if frontend_ip_name == '':
        instance.frontend_ip_configuration = None
    elif frontend_ip_name is not None:
        instance.frontend_ip_configuration = \
            get_property(parent.frontend_ip_configurations, frontend_ip_name)

    return parent


def create_lb_frontend_ip_configuration(
        cmd, resource_group_name, load_balancer_name, item_name, public_ip_address=None,
        public_ip_prefix=None, subnet=None, virtual_network_name=None, private_ip_address=None,
        private_ip_address_version=None, private_ip_address_allocation=None, zone=None):
    FrontendIPConfiguration, SubResource, Subnet = cmd.get_models(
        'FrontendIPConfiguration', 'SubResource', 'Subnet')
    ncf = network_client_factory(cmd.cli_ctx)
    lb = lb_get(ncf.load_balancers, resource_group_name, load_balancer_name)

    if private_ip_address_allocation is None:
        private_ip_address_allocation = 'static' if private_ip_address else 'dynamic'

    new_config = FrontendIPConfiguration(
        name=item_name,
        private_ip_address=private_ip_address,
        private_ip_address_version=private_ip_address_version,
        private_ip_allocation_method=private_ip_address_allocation,
        public_ip_address=SubResource(id=public_ip_address) if public_ip_address else None,
        public_ip_prefix=SubResource(id=public_ip_prefix) if public_ip_prefix else None,
        subnet=Subnet(id=subnet) if subnet else None)

    if zone and cmd.supported_api_version(min_api='2017-06-01'):
        new_config.zones = zone

    upsert_to_collection(lb, 'frontend_ip_configurations', new_config, 'name')
    poller = ncf.load_balancers.begin_create_or_update(resource_group_name, load_balancer_name, lb)
    return get_property(poller.result().frontend_ip_configurations, item_name)


def update_lb_frontend_ip_configuration_setter(cmd, resource_group_name, load_balancer_name, parameters, gateway_lb):
    aux_subscriptions = []
    if is_valid_resource_id(gateway_lb):
        aux_subscriptions.append(parse_resource_id(gateway_lb)['subscription'])
    client = network_client_factory(cmd.cli_ctx, aux_subscriptions=aux_subscriptions).load_balancers
    return client.begin_create_or_update(resource_group_name, load_balancer_name, parameters)


def set_lb_frontend_ip_configuration(
        cmd, instance, parent, item_name, private_ip_address=None,
        private_ip_address_allocation=None, public_ip_address=None,
        subnet=None, virtual_network_name=None, public_ip_prefix=None, gateway_lb=None):
    PublicIPAddress, Subnet, SubResource = cmd.get_models('PublicIPAddress', 'Subnet', 'SubResource')
    if not private_ip_address:
        instance.private_ip_allocation_method = 'dynamic'
        instance.private_ip_address = None
    elif private_ip_address is not None:
        instance.private_ip_allocation_method = 'static'
        instance.private_ip_address = private_ip_address

    # Doesn't support update operation for now
    # if cmd.supported_api_version(min_api='2019-04-01'):
    #    instance.private_ip_address_version = private_ip_address_version

    if subnet == '':
        instance.subnet = None
    elif subnet is not None:
        instance.subnet = Subnet(id=subnet)

    if public_ip_address == '':
        instance.public_ip_address = None
    elif public_ip_address is not None:
        instance.public_ip_address = PublicIPAddress(id=public_ip_address)

    if public_ip_prefix:
        instance.public_ip_prefix = SubResource(id=public_ip_prefix)
    if gateway_lb is not None:
        instance.gateway_load_balancer = None if gateway_lb == '' else SubResource(id=gateway_lb)

    return parent


def _process_vnet_name_and_id(vnet, cmd, resource_group_name):
    if vnet and not is_valid_resource_id(vnet):
        vnet = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=vnet)
    return vnet


def _process_subnet_name_and_id(subnet, vnet, cmd, resource_group_name):
    if subnet and not is_valid_resource_id(subnet):
        vnet = _process_vnet_name_and_id(vnet, cmd, resource_group_name)
        if vnet is None:
            raise UnrecognizedArgumentError('vnet should be provided when input subnet name instead of subnet id')

        subnet = vnet + f'/subnets/{subnet}'
    return subnet


# pylint: disable=too-many-branches
def create_lb_backend_address_pool(cmd, resource_group_name, load_balancer_name, backend_address_pool_name,
                                   vnet=None, backend_addresses=None, backend_addresses_config_file=None):
    if backend_addresses and backend_addresses_config_file:
        raise CLIError('usage error: Only one of --backend-address and --backend-addresses-config-file can be provided at the same time.')  # pylint: disable=line-too-long
    if backend_addresses_config_file:
        if not isinstance(backend_addresses_config_file, list):
            raise CLIError('Config file must be a list. Please see example as a reference.')
        for addr in backend_addresses_config_file:
            if not isinstance(addr, dict):
                raise CLIError('Each address in config file must be a dictionary. Please see example as a reference.')
    ncf = network_client_factory(cmd.cli_ctx)
    lb = lb_get(ncf.load_balancers, resource_group_name, load_balancer_name)
    (BackendAddressPool,
     LoadBalancerBackendAddress,
     Subnet,
     VirtualNetwork) = cmd.get_models('BackendAddressPool',
                                      'LoadBalancerBackendAddress',
                                      'Subnet',
                                      'VirtualNetwork')
    # Before 2020-03-01, service doesn't support the other rest method.
    # We have to use old one to keep backward compatibility.
    # Same for basic sku. service refuses that basic sku lb call the other rest method.
    if cmd.supported_api_version(max_api='2020-03-01') or lb.sku.name.lower() == 'basic':
        new_pool = BackendAddressPool(name=backend_address_pool_name)
        upsert_to_collection(lb, 'backend_address_pools', new_pool, 'name')
        poller = ncf.load_balancers.begin_create_or_update(resource_group_name, load_balancer_name, lb)
        return get_property(poller.result().backend_address_pools, backend_address_pool_name)

    addresses_pool = []
    if backend_addresses:
        addresses_pool.extend(backend_addresses)
    if backend_addresses_config_file:
        addresses_pool.extend(backend_addresses_config_file)
    for addr in addresses_pool:
        if 'virtual_network' not in addr and vnet:
            addr['virtual_network'] = vnet

    # pylint: disable=line-too-long
    if cmd.supported_api_version(min_api='2020-11-01'):  # pylint: disable=too-many-nested-blocks
        try:
            if addresses_pool:
                new_addresses = []
                for addr in addresses_pool:
                    # vnet      | subnet        |  status
                    # name/id   | name/id/null  |    ok
                    # null      | id            |    ok
                    if 'virtual_network' in addr:
                        address = LoadBalancerBackendAddress(name=addr['name'],
                                                             virtual_network=VirtualNetwork(id=_process_vnet_name_and_id(addr['virtual_network'], cmd, resource_group_name)),
                                                             subnet=Subnet(id=_process_subnet_name_and_id(addr['subnet'], addr['virtual_network'], cmd, resource_group_name)) if 'subnet' in addr else None,
                                                             ip_address=addr['ip_address'])
                    elif 'subnet' in addr and is_valid_resource_id(addr['subnet']):
                        address = LoadBalancerBackendAddress(name=addr['name'],
                                                             subnet=Subnet(id=addr['subnet']),
                                                             ip_address=addr['ip_address'])
                    else:
                        raise KeyError

                    new_addresses.append(address)
            else:
                new_addresses = None
        except KeyError:
            raise UnrecognizedArgumentError('Each backend address must have name, ip-address, (vnet name and subnet '
                                            'name | subnet id) information.')
    else:
        try:
            new_addresses = [LoadBalancerBackendAddress(name=addr['name'],
                                                        virtual_network=VirtualNetwork(id=_process_vnet_name_and_id(addr['virtual_network'], cmd, resource_group_name)),
                                                        ip_address=addr['ip_address']) for addr in addresses_pool] if addresses_pool else None
        except KeyError:
            raise UnrecognizedArgumentError('Each backend address must have name, vnet and ip-address information.')

    new_pool = BackendAddressPool(name=backend_address_pool_name,
                                  load_balancer_backend_addresses=new_addresses)

    # when sku is 'gateway', 'tunnelInterfaces' can't be None. Otherwise service will response error
    if cmd.supported_api_version(min_api='2021-02-01') and lb.sku.name.lower() == 'gateway':
        GatewayLoadBalancerTunnelInterface = cmd.get_models('GatewayLoadBalancerTunnelInterface')
        new_pool.tunnel_interfaces = [
            GatewayLoadBalancerTunnelInterface(type='Internal', protocol='VXLAN', identifier=900)]
    return ncf.load_balancer_backend_address_pools.begin_create_or_update(resource_group_name,
                                                                          load_balancer_name,
                                                                          backend_address_pool_name,
                                                                          new_pool)


def set_lb_backend_address_pool(cmd, instance, resource_group_name, vnet=None, backend_addresses=None,
                                backend_addresses_config_file=None):

    if backend_addresses and backend_addresses_config_file:
        raise CLIError('usage error: Only one of --backend-address and --backend-addresses-config-file can be provided at the same time.')  # pylint: disable=line-too-long
    if backend_addresses_config_file:
        if not isinstance(backend_addresses_config_file, list):
            raise CLIError('Config file must be a list. Please see example as a reference.')
        for addr in backend_addresses_config_file:
            if not isinstance(addr, dict):
                raise CLIError('Each address in config file must be a dictionary. Please see example as a reference.')

    (LoadBalancerBackendAddress,
     Subnet,
     VirtualNetwork) = cmd.get_models('LoadBalancerBackendAddress',
                                      'Subnet',
                                      'VirtualNetwork')

    addresses_pool = []
    if backend_addresses:
        addresses_pool.extend(backend_addresses)
    if backend_addresses_config_file:
        addresses_pool.extend(backend_addresses_config_file)
    for addr in addresses_pool:
        if 'virtual_network' not in addr and vnet:
            addr['virtual_network'] = vnet

    # pylint: disable=line-too-long
    if cmd.supported_api_version(min_api='2020-11-01'):  # pylint: disable=too-many-nested-blocks
        try:
            if addresses_pool:
                new_addresses = []
                for addr in addresses_pool:
                    # vnet      | subnet        |  status
                    # name/id   | name/id/null  |    ok
                    # null      | id            |    ok
                    if 'virtual_network' in addr:
                        address = LoadBalancerBackendAddress(name=addr['name'],
                                                             virtual_network=VirtualNetwork(id=_process_vnet_name_and_id(addr['virtual_network'], cmd, resource_group_name)),
                                                             subnet=Subnet(id=_process_subnet_name_and_id(addr['subnet'], addr['virtual_network'], cmd, resource_group_name)) if 'subnet' in addr else None,
                                                             ip_address=addr['ip_address'])
                    elif 'subnet' in addr and is_valid_resource_id(addr['subnet']):
                        address = LoadBalancerBackendAddress(name=addr['name'],
                                                             subnet=Subnet(id=addr['subnet']),
                                                             ip_address=addr['ip_address'])
                    else:
                        raise KeyError

                    new_addresses.append(address)
            else:
                new_addresses = None
        except KeyError:
            raise UnrecognizedArgumentError('Each backend address must have name, ip-address, (vnet name and subnet '
                                            'name | subnet id) information.')
    else:
        try:
            new_addresses = [LoadBalancerBackendAddress(name=addr['name'],
                                                        virtual_network=VirtualNetwork(id=_process_vnet_name_and_id(addr['virtual_network'], cmd, resource_group_name)),
                                                        ip_address=addr['ip_address']) for addr in addresses_pool] if addresses_pool else None
        except KeyError:
            raise UnrecognizedArgumentError('Each backend address must have name, vnet and ip-address information.')

    if new_addresses:
        instance.load_balancer_backend_addresses = new_addresses

    return instance


def delete_lb_backend_address_pool(cmd, resource_group_name, load_balancer_name, backend_address_pool_name):
    from azure.cli.core.commands import LongRunningOperation
    ncf = network_client_factory(cmd.cli_ctx)
    lb = lb_get(ncf.load_balancers, resource_group_name, load_balancer_name)

    def delete_basic_lb_backend_address_pool():
        new_be_pools = [pool for pool in lb.backend_address_pools
                        if pool.name.lower() != backend_address_pool_name.lower()]
        lb.backend_address_pools = new_be_pools
        poller = ncf.load_balancers.begin_create_or_update(resource_group_name, load_balancer_name, lb)
        result = LongRunningOperation(cmd.cli_ctx)(poller).backend_address_pools
        if next((x for x in result if x.name.lower() == backend_address_pool_name.lower()), None):
            raise CLIError("Failed to delete '{}' on '{}'".format(backend_address_pool_name, load_balancer_name))

    if lb.sku.name.lower() == 'basic':
        delete_basic_lb_backend_address_pool()
        return None

    return ncf.load_balancer_backend_address_pools.begin_delete(resource_group_name,
                                                                load_balancer_name,
                                                                backend_address_pool_name)


# region cross-region lb
def create_cross_region_load_balancer(cmd, load_balancer_name, resource_group_name, location=None, tags=None,
                                      backend_pool_name=None, frontend_ip_name='LoadBalancerFrontEnd',
                                      public_ip_address=None, public_ip_address_allocation=None,
                                      public_ip_dns_name=None, public_ip_address_type=None, validate=False,
                                      no_wait=False, frontend_ip_zone=None, public_ip_zone=None):
    from azure.cli.core.util import random_string
    from azure.cli.core.commands.arm import ArmTemplateBuilder
    from azure.cli.command_modules.network._template_builder import (
        build_load_balancer_resource, build_public_ip_resource)

    DeploymentProperties = cmd.get_models('DeploymentProperties', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    IPAllocationMethod = cmd.get_models('IPAllocationMethod')

    sku = 'standard'
    tier = 'Global'

    tags = tags or {}
    public_ip_address = public_ip_address or 'PublicIP{}'.format(load_balancer_name)
    backend_pool_name = backend_pool_name or '{}bepool'.format(load_balancer_name)
    if not public_ip_address_allocation:
        public_ip_address_allocation = IPAllocationMethod.static.value if (sku and sku.lower() == 'standard') \
            else IPAllocationMethod.dynamic.value

    # Build up the ARM template
    master_template = ArmTemplateBuilder()
    lb_dependencies = []

    public_ip_id = public_ip_address if is_valid_resource_id(public_ip_address) else None

    network_id_template = resource_id(
        subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name,
        namespace='Microsoft.Network')

    if public_ip_address_type == 'new':
        lb_dependencies.append('Microsoft.Network/publicIpAddresses/{}'.format(public_ip_address))
        master_template.add_resource(build_public_ip_resource(cmd, public_ip_address, location,
                                                              tags,
                                                              public_ip_address_allocation,
                                                              public_ip_dns_name,
                                                              sku, public_ip_zone, tier))
        public_ip_id = '{}/publicIPAddresses/{}'.format(network_id_template,
                                                        public_ip_address)

    load_balancer_resource = build_load_balancer_resource(
        cmd, load_balancer_name, location, tags, backend_pool_name, frontend_ip_name,
        public_ip_id, None, None, None, sku, frontend_ip_zone, None, tier)
    load_balancer_resource['dependsOn'] = lb_dependencies
    master_template.add_resource(load_balancer_resource)
    master_template.add_output('loadBalancer', load_balancer_name, output_type='object')

    template = master_template.build()

    # deploy ARM template
    deployment_name = 'lb_deploy_' + random_string(32)
    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES).deployments
    properties = DeploymentProperties(template=template, parameters={}, mode='incremental')
    Deployment = cmd.get_models('Deployment', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    deployment = Deployment(properties=properties)

    if validate:
        _log_pprint_template(template)
        if cmd.supported_api_version(min_api='2019-10-01', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES):
            from azure.cli.core.commands import LongRunningOperation
            validation_poller = client.begin_validate(resource_group_name, deployment_name, deployment)
            return LongRunningOperation(cmd.cli_ctx)(validation_poller)

        return client.validate(resource_group_name, deployment_name, deployment)

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, deployment_name, deployment)


def create_cross_region_lb_frontend_ip_configuration(
        cmd, resource_group_name, load_balancer_name, item_name, public_ip_address=None,
        public_ip_prefix=None, zone=None):
    FrontendIPConfiguration, SubResource = cmd.get_models(
        'FrontendIPConfiguration', 'SubResource')
    ncf = network_client_factory(cmd.cli_ctx)
    lb = lb_get(ncf.load_balancers, resource_group_name, load_balancer_name)

    new_config = FrontendIPConfiguration(
        name=item_name,
        public_ip_address=SubResource(id=public_ip_address) if public_ip_address else None,
        public_ip_prefix=SubResource(id=public_ip_prefix) if public_ip_prefix else None)

    if zone and cmd.supported_api_version(min_api='2017-06-01'):
        new_config.zones = zone

    upsert_to_collection(lb, 'frontend_ip_configurations', new_config, 'name')
    poller = ncf.load_balancers.begin_create_or_update(resource_group_name, load_balancer_name, lb)
    return get_property(poller.result().frontend_ip_configurations, item_name)


def set_cross_region_lb_frontend_ip_configuration(
        cmd, instance, parent, item_name, public_ip_address=None, public_ip_prefix=None):
    PublicIPAddress, SubResource = cmd.get_models('PublicIPAddress', 'SubResource')

    if public_ip_address == '':
        instance.public_ip_address = None
    elif public_ip_address is not None:
        instance.public_ip_address = PublicIPAddress(id=public_ip_address)

    if public_ip_prefix:
        instance.public_ip_prefix = SubResource(id=public_ip_prefix)

    return parent


def create_cross_region_lb_backend_address_pool(cmd, resource_group_name, load_balancer_name, backend_address_pool_name,
                                                backend_addresses=None, backend_addresses_config_file=None):
    if backend_addresses and backend_addresses_config_file:
        raise CLIError('usage error: Only one of --backend-address and --backend-addresses-config-file can be provided at the same time.')  # pylint: disable=line-too-long
    if backend_addresses_config_file:
        if not isinstance(backend_addresses_config_file, list):
            raise CLIError('Config file must be a list. Please see example as a reference.')
        for addr in backend_addresses_config_file:
            if not isinstance(addr, dict):
                raise CLIError('Each address in config file must be a dictionary. Please see example as a reference.')
    ncf = network_client_factory(cmd.cli_ctx)
    (BackendAddressPool,
     LoadBalancerBackendAddress,
     FrontendIPConfiguration) = cmd.get_models('BackendAddressPool',
                                               'LoadBalancerBackendAddress',
                                               'FrontendIPConfiguration')

    addresses_pool = []
    if backend_addresses:
        addresses_pool.extend(backend_addresses)
    if backend_addresses_config_file:
        addresses_pool.extend(backend_addresses_config_file)

    # pylint: disable=line-too-long
    try:
        new_addresses = [LoadBalancerBackendAddress(name=addr['name'],
                                                    load_balancer_frontend_ip_configuration=FrontendIPConfiguration(id=addr['frontend_ip_address'])) for addr in addresses_pool] if addresses_pool else None
    except KeyError:
        raise CLIError('Each backend address must have name and frontend_ip_configuration information.')
    new_pool = BackendAddressPool(name=backend_address_pool_name,
                                  load_balancer_backend_addresses=new_addresses)
    return ncf.load_balancer_backend_address_pools.begin_create_or_update(resource_group_name,
                                                                          load_balancer_name,
                                                                          backend_address_pool_name,
                                                                          new_pool)


def delete_cross_region_lb_backend_address_pool(cmd, resource_group_name, load_balancer_name, backend_address_pool_name):  # pylint: disable=line-too-long
    ncf = network_client_factory(cmd.cli_ctx)

    return ncf.load_balancer_backend_address_pools.begin_delete(resource_group_name,
                                                                load_balancer_name,
                                                                backend_address_pool_name)


def add_cross_region_lb_backend_address_pool_address(cmd, resource_group_name, load_balancer_name,
                                                     backend_address_pool_name, address_name, frontend_ip_address):
    client = network_client_factory(cmd.cli_ctx).load_balancer_backend_address_pools
    address_pool = client.get(resource_group_name, load_balancer_name, backend_address_pool_name)
    # pylint: disable=line-too-long
    (LoadBalancerBackendAddress, FrontendIPConfiguration) = cmd.get_models('LoadBalancerBackendAddress', 'FrontendIPConfiguration')
    new_address = LoadBalancerBackendAddress(name=address_name,
                                             load_balancer_frontend_ip_configuration=FrontendIPConfiguration(id=frontend_ip_address) if frontend_ip_address else None)
    if address_pool.load_balancer_backend_addresses is None:
        address_pool.load_balancer_backend_addresses = []
    address_pool.load_balancer_backend_addresses.append(new_address)
    return client.begin_create_or_update(resource_group_name, load_balancer_name,
                                         backend_address_pool_name, address_pool)


def create_cross_region_lb_rule(
        cmd, resource_group_name, load_balancer_name, item_name,
        protocol, frontend_port, backend_port, frontend_ip_name=None,
        backend_address_pool_name=None, probe_name=None, load_distribution='default',
        floating_ip=None, idle_timeout=None, enable_tcp_reset=None, backend_pools_name=None):
    LoadBalancingRule = cmd.get_models('LoadBalancingRule')
    ncf = network_client_factory(cmd.cli_ctx)
    lb = cached_get(cmd, ncf.load_balancers.get, resource_group_name, load_balancer_name)
    lb = lb_get_operation(lb)
    if not frontend_ip_name:
        frontend_ip_name = _get_default_name(lb, 'frontend_ip_configurations', '--frontend-ip-name')
    if not backend_address_pool_name:
        backend_address_pool_name = _get_default_name(lb, 'backend_address_pools', '--backend-pool-name')
    new_rule = LoadBalancingRule(
        name=item_name,
        protocol=protocol,
        frontend_port=frontend_port,
        backend_port=backend_port,
        frontend_ip_configuration=get_property(lb.frontend_ip_configurations,
                                               frontend_ip_name),
        backend_address_pool=get_property(lb.backend_address_pools,
                                          backend_address_pool_name),
        probe=get_property(lb.probes, probe_name) if probe_name else None,
        load_distribution=load_distribution,
        enable_floating_ip=floating_ip,
        idle_timeout_in_minutes=idle_timeout,
        enable_tcp_reset=enable_tcp_reset)
    if backend_pools_name:
        new_rule.backend_address_pools = [get_property(lb.backend_address_pools, i) for i in backend_pools_name]
    upsert_to_collection(lb, 'load_balancing_rules', new_rule, 'name')
    poller = cached_put(cmd, ncf.load_balancers.begin_create_or_update, lb, resource_group_name, load_balancer_name)
    return get_property(poller.result().load_balancing_rules, item_name)


def set_cross_region_lb_rule(
        cmd, instance, parent, item_name, protocol=None, frontend_port=None,
        frontend_ip_name=None, backend_port=None, backend_address_pool_name=None, probe_name=None,
        load_distribution=None, floating_ip=None, idle_timeout=None, enable_tcp_reset=None, backend_pools_name=None):
    with cmd.update_context(instance) as c:
        c.set_param('protocol', protocol)
        c.set_param('frontend_port', frontend_port)
        c.set_param('backend_port', backend_port)
        c.set_param('idle_timeout_in_minutes', idle_timeout)
        c.set_param('load_distribution', load_distribution)
        c.set_param('enable_tcp_reset', enable_tcp_reset)
        c.set_param('enable_floating_ip', floating_ip)

    if frontend_ip_name is not None:
        instance.frontend_ip_configuration = \
            get_property(parent.frontend_ip_configurations, frontend_ip_name)

    if backend_address_pool_name is not None:
        instance.backend_address_pool = \
            get_property(parent.backend_address_pools, backend_address_pool_name)
        # To keep compatible when bump version from '2020-11-01' to '2021-02-01'
        # https://github.com/Azure/azure-rest-api-specs/issues/14430
        if cmd.supported_api_version(min_api='2021-02-01') and not backend_pools_name:
            instance.backend_address_pools = [instance.backend_address_pool]
    if backend_pools_name is not None:
        instance.backend_address_pools = [get_property(parent.backend_address_pools, i) for i in backend_pools_name]

    if probe_name == '':
        instance.probe = None
    elif probe_name is not None:
        instance.probe = get_property(parent.probes, probe_name)

    return parent
# endregion


# pylint: disable=line-too-long
def add_lb_backend_address_pool_address(cmd, resource_group_name, load_balancer_name, backend_address_pool_name,
                                        address_name, ip_address, vnet=None, subnet=None):
    client = network_client_factory(cmd.cli_ctx).load_balancer_backend_address_pools
    address_pool = client.get(resource_group_name, load_balancer_name, backend_address_pool_name)
    (LoadBalancerBackendAddress,
     Subnet,
     VirtualNetwork) = cmd.get_models('LoadBalancerBackendAddress',
                                      'Subnet',
                                      'VirtualNetwork')
    if cmd.supported_api_version(min_api='2020-11-01'):
        if vnet:
            new_address = LoadBalancerBackendAddress(name=address_name,
                                                     subnet=Subnet(id=_process_subnet_name_and_id(subnet, vnet, cmd, resource_group_name)) if subnet else None,
                                                     virtual_network=VirtualNetwork(id=vnet),
                                                     ip_address=ip_address if ip_address else None)
        elif is_valid_resource_id(subnet):
            new_address = LoadBalancerBackendAddress(name=address_name,
                                                     subnet=Subnet(id=subnet),
                                                     ip_address=ip_address if ip_address else None)
        else:
            raise UnrecognizedArgumentError('Each backend address must have name, ip-address, (vnet name and subnet name | subnet id) information.')

    else:
        new_address = LoadBalancerBackendAddress(name=address_name,
                                                 virtual_network=VirtualNetwork(id=vnet) if vnet else None,
                                                 ip_address=ip_address if ip_address else None)
    if address_pool.load_balancer_backend_addresses is None:
        address_pool.load_balancer_backend_addresses = []
    address_pool.load_balancer_backend_addresses.append(new_address)
    return client.begin_create_or_update(resource_group_name, load_balancer_name,
                                         backend_address_pool_name, address_pool)


def remove_lb_backend_address_pool_address(cmd, resource_group_name, load_balancer_name,
                                           backend_address_pool_name, address_name):
    client = network_client_factory(cmd.cli_ctx).load_balancer_backend_address_pools
    address_pool = client.get(resource_group_name, load_balancer_name, backend_address_pool_name)
    if address_pool.load_balancer_backend_addresses is None:
        address_pool.load_balancer_backend_addresses = []
    lb_addresses = [addr for addr in address_pool.load_balancer_backend_addresses if addr.name != address_name]
    address_pool.load_balancer_backend_addresses = lb_addresses
    return client.begin_create_or_update(resource_group_name, load_balancer_name,
                                         backend_address_pool_name, address_pool)


def list_lb_backend_address_pool_address(cmd, resource_group_name, load_balancer_name,
                                         backend_address_pool_name):
    client = network_client_factory(cmd.cli_ctx).load_balancer_backend_address_pools
    address_pool = client.get(resource_group_name, load_balancer_name, backend_address_pool_name)
    return address_pool.load_balancer_backend_addresses


def create_lb_outbound_rule(cmd, resource_group_name, load_balancer_name, item_name,
                            backend_address_pool, frontend_ip_configurations, protocol,
                            outbound_ports=None, enable_tcp_reset=None, idle_timeout=None):
    OutboundRule, SubResource = cmd.get_models('OutboundRule', 'SubResource')
    client = network_client_factory(cmd.cli_ctx).load_balancers
    lb = lb_get(client, resource_group_name, load_balancer_name)
    rule = OutboundRule(
        protocol=protocol, enable_tcp_reset=enable_tcp_reset, idle_timeout_in_minutes=idle_timeout,
        backend_address_pool=SubResource(id=backend_address_pool),
        frontend_ip_configurations=[SubResource(id=x) for x in frontend_ip_configurations]
        if frontend_ip_configurations else None,
        allocated_outbound_ports=outbound_ports, name=item_name)
    upsert_to_collection(lb, 'outbound_rules', rule, 'name')
    poller = client.begin_create_or_update(resource_group_name, load_balancer_name, lb)
    return get_property(poller.result().outbound_rules, item_name)


def set_lb_outbound_rule(instance, cmd, parent, item_name, protocol=None, outbound_ports=None,
                         idle_timeout=None, frontend_ip_configurations=None, enable_tcp_reset=None,
                         backend_address_pool=None):
    SubResource = cmd.get_models('SubResource')
    with cmd.update_context(instance) as c:
        c.set_param('protocol', protocol)
        c.set_param('allocated_outbound_ports', outbound_ports)
        c.set_param('idle_timeout_in_minutes', idle_timeout)
        c.set_param('enable_tcp_reset', enable_tcp_reset)
        c.set_param('backend_address_pool', SubResource(id=backend_address_pool)
                    if backend_address_pool else None)
        c.set_param('frontend_ip_configurations',
                    [SubResource(id=x) for x in frontend_ip_configurations] if frontend_ip_configurations else None)
    return parent


def create_lb_probe(cmd, resource_group_name, load_balancer_name, item_name, protocol, port,
                    path=None, interval=None, threshold=None):
    Probe = cmd.get_models('Probe')
    ncf = network_client_factory(cmd.cli_ctx)
    lb = lb_get(ncf.load_balancers, resource_group_name, load_balancer_name)
    new_probe = Probe(
        protocol=protocol, port=port, interval_in_seconds=interval, number_of_probes=threshold,
        request_path=path, name=item_name)
    upsert_to_collection(lb, 'probes', new_probe, 'name')
    poller = ncf.load_balancers.begin_create_or_update(resource_group_name, load_balancer_name, lb)
    return get_property(poller.result().probes, item_name)


def set_lb_probe(cmd, instance, parent, item_name, protocol=None, port=None,
                 path=None, interval=None, threshold=None):
    with cmd.update_context(instance) as c:
        c.set_param('protocol', protocol)
        c.set_param('port', port)
        c.set_param('request_path', path)
        c.set_param('interval_in_seconds', interval)
        c.set_param('number_of_probes', threshold)
    return parent


def create_lb_rule(
        cmd, resource_group_name, load_balancer_name, item_name,
        protocol, frontend_port, backend_port, frontend_ip_name=None,
        backend_address_pool_name=None, probe_name=None, load_distribution='default',
        floating_ip=None, idle_timeout=None, enable_tcp_reset=None, disable_outbound_snat=None, backend_pools_name=None):
    LoadBalancingRule = cmd.get_models('LoadBalancingRule')
    ncf = network_client_factory(cmd.cli_ctx)
    lb = cached_get(cmd, ncf.load_balancers.get, resource_group_name, load_balancer_name)
    lb = lb_get_operation(lb)
    if not frontend_ip_name:
        frontend_ip_name = _get_default_name(lb, 'frontend_ip_configurations', '--frontend-ip-name')
    # avoid break when backend_address_pool_name is None and backend_pools_name is not None
    if not backend_address_pool_name and backend_pools_name:
        backend_address_pool_name = backend_pools_name[0]
    if not backend_address_pool_name:
        backend_address_pool_name = _get_default_name(lb, 'backend_address_pools', '--backend-pool-name')
    new_rule = LoadBalancingRule(
        name=item_name,
        protocol=protocol,
        frontend_port=frontend_port,
        backend_port=backend_port,
        frontend_ip_configuration=get_property(lb.frontend_ip_configurations,
                                               frontend_ip_name),
        backend_address_pool=get_property(lb.backend_address_pools,
                                          backend_address_pool_name),
        probe=get_property(lb.probes, probe_name) if probe_name else None,
        load_distribution=load_distribution,
        enable_floating_ip=floating_ip,
        idle_timeout_in_minutes=idle_timeout,
        enable_tcp_reset=enable_tcp_reset,
        disable_outbound_snat=disable_outbound_snat)

    if backend_pools_name:
        new_rule.backend_address_pools = [get_property(lb.backend_address_pools, name) for name in backend_pools_name]
        # Otherwiase service will response error : (LoadBalancingRuleBackendAdressPoolAndBackendAddressPoolsCannotBeSetAtTheSameTimeWithDifferentValue) BackendAddressPool and BackendAddressPools[] in LoadBalancingRule rule2 cannot be set at the same time with different value.
        new_rule.backend_address_pool = None

    upsert_to_collection(lb, 'load_balancing_rules', new_rule, 'name')
    poller = cached_put(cmd, ncf.load_balancers.begin_create_or_update, lb, resource_group_name, load_balancer_name)
    return get_property(poller.result().load_balancing_rules, item_name)


def set_lb_rule(
        cmd, instance, parent, item_name, protocol=None, frontend_port=None,
        frontend_ip_name=None, backend_port=None, backend_address_pool_name=None, probe_name=None,
        load_distribution='default', floating_ip=None, idle_timeout=None, enable_tcp_reset=None,
        disable_outbound_snat=None, backend_pools_name=None):
    with cmd.update_context(instance) as c:
        c.set_param('protocol', protocol)
        c.set_param('frontend_port', frontend_port)
        c.set_param('backend_port', backend_port)
        c.set_param('idle_timeout_in_minutes', idle_timeout)
        c.set_param('load_distribution', load_distribution)
        c.set_param('disable_outbound_snat', disable_outbound_snat)
        c.set_param('enable_tcp_reset', enable_tcp_reset)
        c.set_param('enable_floating_ip', floating_ip)

    if frontend_ip_name is not None:
        instance.frontend_ip_configuration = \
            get_property(parent.frontend_ip_configurations, frontend_ip_name)

    if backend_address_pool_name is not None:
        instance.backend_address_pool = \
            get_property(parent.backend_address_pools, backend_address_pool_name)
        # To keep compatible when bump version from '2020-11-01' to '2021-02-01'
        # https://github.com/Azure/azure-rest-api-specs/issues/14430
        if cmd.supported_api_version(min_api='2021-02-01') and not backend_pools_name:
            instance.backend_address_pools = [instance.backend_address_pool]
    if backend_pools_name is not None:
        instance.backend_address_pools = [get_property(parent.backend_address_pools, i) for i in backend_pools_name]
        # Otherwiase service will response error : (LoadBalancingRuleBackendAdressPoolAndBackendAddressPoolsCannotBeSetAtTheSameTimeWithDifferentValue) BackendAddressPool and BackendAddressPools[] in LoadBalancingRule rule2 cannot be set at the same time with different value.
        instance.backend_address_pool = None

    if probe_name == '':
        instance.probe = None
    elif probe_name is not None:
        instance.probe = get_property(parent.probes, probe_name)

    return parent


def add_lb_backend_address_pool_tunnel_interface(cmd, resource_group_name, load_balancer_name,
                                                 backend_address_pool_name, protocol, identifier, traffic_type, port=None):
    client = network_client_factory(cmd.cli_ctx).load_balancer_backend_address_pools
    address_pool = client.get(resource_group_name, load_balancer_name, backend_address_pool_name)
    GatewayLoadBalancerTunnelInterface = cmd.get_models('GatewayLoadBalancerTunnelInterface')
    tunnel_interface = GatewayLoadBalancerTunnelInterface(port=port, identifier=identifier, protocol=protocol, type=traffic_type)
    if not address_pool.tunnel_interfaces:
        address_pool.tunnel_interfaces = []
    address_pool.tunnel_interfaces.append(tunnel_interface)
    return client.begin_create_or_update(resource_group_name, load_balancer_name,
                                         backend_address_pool_name, address_pool)


def update_lb_backend_address_pool_tunnel_interface(cmd, resource_group_name, load_balancer_name,
                                                    backend_address_pool_name, index, protocol=None, identifier=None, traffic_type=None, port=None):
    client = network_client_factory(cmd.cli_ctx).load_balancer_backend_address_pools
    address_pool = client.get(resource_group_name, load_balancer_name, backend_address_pool_name)
    if index >= len(address_pool.tunnel_interfaces):
        raise UnrecognizedArgumentError(f'{index} is out of scope, please input proper index')

    item = address_pool.tunnel_interfaces[index]
    if protocol:
        item.protocol = protocol
    if identifier:
        item.identifier = identifier
    if port:
        item.port = port
    if traffic_type:
        item.type = traffic_type
    return client.begin_create_or_update(resource_group_name, load_balancer_name,
                                         backend_address_pool_name, address_pool)


def remove_lb_backend_address_pool_tunnel_interface(cmd, resource_group_name, load_balancer_name,
                                                    backend_address_pool_name, index):
    client = network_client_factory(cmd.cli_ctx).load_balancer_backend_address_pools
    address_pool = client.get(resource_group_name, load_balancer_name, backend_address_pool_name)
    if index >= len(address_pool.tunnel_interfaces):
        raise UnrecognizedArgumentError(f'{index} is out of scope, please input proper index')
    address_pool.tunnel_interfaces.pop(index)
    return client.begin_create_or_update(resource_group_name, load_balancer_name,
                                         backend_address_pool_name, address_pool)


def list_lb_backend_address_pool_tunnel_interface(cmd, resource_group_name, load_balancer_name,
                                                  backend_address_pool_name):
    client = network_client_factory(cmd.cli_ctx).load_balancer_backend_address_pools
    address_pool = client.get(resource_group_name, load_balancer_name, backend_address_pool_name)
    return address_pool.tunnel_interfaces
# endregion


# region LocalGateways
def _validate_bgp_peering(cmd, instance, asn, bgp_peering_address, peer_weight):
    if any([asn, bgp_peering_address, peer_weight]):
        if instance.bgp_settings is not None:
            # update existing parameters selectively
            if asn is not None:
                instance.bgp_settings.asn = asn
            if peer_weight is not None:
                instance.bgp_settings.peer_weight = peer_weight
            if bgp_peering_address is not None:
                instance.bgp_settings.bgp_peering_address = bgp_peering_address
        elif asn:
            BgpSettings = cmd.get_models('BgpSettings')
            instance.bgp_settings = BgpSettings(asn, bgp_peering_address, peer_weight)
        else:
            raise CLIError(
                'incorrect usage: --asn ASN [--peer-weight WEIGHT --bgp-peering-address IP]')


def create_local_gateway(cmd, resource_group_name, local_network_gateway_name, gateway_ip_address,
                         location=None, tags=None, local_address_prefix=None, asn=None,
                         bgp_peering_address=None, peer_weight=None, no_wait=False):
    AddressSpace, LocalNetworkGateway, BgpSettings = cmd.get_models(
        'AddressSpace', 'LocalNetworkGateway', 'BgpSettings')
    client = network_client_factory(cmd.cli_ctx).local_network_gateways
    local_gateway = LocalNetworkGateway(
        local_network_address_space=AddressSpace(address_prefixes=(local_address_prefix or [])),
        location=location, tags=tags, gateway_ip_address=gateway_ip_address)
    if bgp_peering_address or asn or peer_weight:
        local_gateway.bgp_settings = BgpSettings(asn=asn, bgp_peering_address=bgp_peering_address,
                                                 peer_weight=peer_weight)
    return sdk_no_wait(no_wait, client.begin_create_or_update,
                       resource_group_name, local_network_gateway_name, local_gateway)


def update_local_gateway(cmd, instance, gateway_ip_address=None, local_address_prefix=None, asn=None,
                         bgp_peering_address=None, peer_weight=None, tags=None):
    _validate_bgp_peering(cmd, instance, asn, bgp_peering_address, peer_weight)

    if gateway_ip_address is not None:
        instance.gateway_ip_address = gateway_ip_address
    if local_address_prefix is not None:
        instance.local_network_address_space.address_prefixes = local_address_prefix
    if tags is not None:
        instance.tags = tags
    return instance
# endregion


# region NetworkInterfaces (NIC)
def create_nic(cmd, resource_group_name, network_interface_name, subnet, location=None, tags=None,
               internal_dns_name_label=None, dns_servers=None, enable_ip_forwarding=False,
               load_balancer_backend_address_pool_ids=None,
               load_balancer_inbound_nat_rule_ids=None,
               load_balancer_name=None, network_security_group=None,
               private_ip_address=None, private_ip_address_version=None,
               public_ip_address=None, virtual_network_name=None, enable_accelerated_networking=None,
               application_security_groups=None, no_wait=False,
               app_gateway_backend_address_pools=None, edge_zone=None):
    client = network_client_factory(cmd.cli_ctx).network_interfaces
    (NetworkInterface, NetworkInterfaceDnsSettings, NetworkInterfaceIPConfiguration, NetworkSecurityGroup,
     PublicIPAddress, Subnet, SubResource) = cmd.get_models(
         'NetworkInterface', 'NetworkInterfaceDnsSettings', 'NetworkInterfaceIPConfiguration',
         'NetworkSecurityGroup', 'PublicIPAddress', 'Subnet', 'SubResource')

    dns_settings = NetworkInterfaceDnsSettings(internal_dns_name_label=internal_dns_name_label,
                                               dns_servers=dns_servers or [])

    nic = NetworkInterface(location=location, tags=tags, enable_ip_forwarding=enable_ip_forwarding,
                           dns_settings=dns_settings)

    if cmd.supported_api_version(min_api='2016-09-01'):
        nic.enable_accelerated_networking = enable_accelerated_networking

    if network_security_group:
        nic.network_security_group = NetworkSecurityGroup(id=network_security_group)
    ip_config_args = {
        'name': 'ipconfig1',
        'load_balancer_backend_address_pools': load_balancer_backend_address_pool_ids,
        'load_balancer_inbound_nat_rules': load_balancer_inbound_nat_rule_ids,
        'private_ip_allocation_method': 'Static' if private_ip_address else 'Dynamic',
        'private_ip_address': private_ip_address,
        'subnet': Subnet(id=subnet),
        'application_gateway_backend_address_pools':
            [SubResource(id=x) for x in app_gateway_backend_address_pools]
            if app_gateway_backend_address_pools else None
    }
    if cmd.supported_api_version(min_api='2016-09-01'):
        ip_config_args['private_ip_address_version'] = private_ip_address_version
    if cmd.supported_api_version(min_api='2017-09-01'):
        ip_config_args['application_security_groups'] = application_security_groups
    ip_config = NetworkInterfaceIPConfiguration(**ip_config_args)

    if public_ip_address:
        ip_config.public_ip_address = PublicIPAddress(id=public_ip_address)
    nic.ip_configurations = [ip_config]

    if edge_zone:
        nic.extended_location = _edge_zone_model(cmd, edge_zone)
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, network_interface_name, nic)


def update_nic(cmd, instance, network_security_group=None, enable_ip_forwarding=None,
               internal_dns_name_label=None, dns_servers=None, enable_accelerated_networking=None):
    if enable_ip_forwarding is not None:
        instance.enable_ip_forwarding = enable_ip_forwarding

    if network_security_group == '':
        instance.network_security_group = None
    elif network_security_group is not None:
        NetworkSecurityGroup = cmd.get_models('NetworkSecurityGroup')
        instance.network_security_group = NetworkSecurityGroup(id=network_security_group)

    if internal_dns_name_label == '':
        instance.dns_settings.internal_dns_name_label = None
    elif internal_dns_name_label is not None:
        instance.dns_settings.internal_dns_name_label = internal_dns_name_label
    if dns_servers == ['']:
        instance.dns_settings.dns_servers = None
    elif dns_servers:
        instance.dns_settings.dns_servers = dns_servers

    if enable_accelerated_networking is not None:
        instance.enable_accelerated_networking = enable_accelerated_networking

    return instance


def create_nic_ip_config(cmd, resource_group_name, network_interface_name, ip_config_name, subnet=None,
                         virtual_network_name=None, public_ip_address=None, load_balancer_name=None,
                         load_balancer_backend_address_pool_ids=None,
                         load_balancer_inbound_nat_rule_ids=None,
                         private_ip_address=None,
                         private_ip_address_version=None,
                         make_primary=False,
                         application_security_groups=None,
                         app_gateway_backend_address_pools=None):
    NetworkInterfaceIPConfiguration, PublicIPAddress, Subnet, SubResource = cmd.get_models(
        'NetworkInterfaceIPConfiguration', 'PublicIPAddress', 'Subnet', 'SubResource')
    ncf = network_client_factory(cmd.cli_ctx)
    nic = ncf.network_interfaces.get(resource_group_name, network_interface_name)

    if cmd.supported_api_version(min_api='2016-09-01'):
        IPVersion = cmd.get_models('IPVersion')
        private_ip_address_version = private_ip_address_version or IPVersion.I_PV4.value
        if private_ip_address_version == IPVersion.I_PV4.value and not subnet:
            primary_config = next(x for x in nic.ip_configurations if x.primary)
            subnet = primary_config.subnet.id
        if make_primary:
            for config in nic.ip_configurations:
                config.primary = False

    new_config_args = {
        'name': ip_config_name,
        'subnet': Subnet(id=subnet) if subnet else None,
        'public_ip_address': PublicIPAddress(id=public_ip_address) if public_ip_address else None,
        'load_balancer_backend_address_pools': load_balancer_backend_address_pool_ids,
        'load_balancer_inbound_nat_rules': load_balancer_inbound_nat_rule_ids,
        'private_ip_address': private_ip_address,
        'private_ip_allocation_method': 'Static' if private_ip_address else 'Dynamic'
    }
    if cmd.supported_api_version(min_api='2016-09-01'):
        new_config_args['private_ip_address_version'] = private_ip_address_version
        new_config_args['primary'] = make_primary
    if cmd.supported_api_version(min_api='2017-09-01'):
        new_config_args['application_security_groups'] = application_security_groups
    if cmd.supported_api_version(min_api='2018-08-01'):
        new_config_args['application_gateway_backend_address_pools'] = \
            [SubResource(id=x) for x in app_gateway_backend_address_pools] \
            if app_gateway_backend_address_pools else None

    new_config = NetworkInterfaceIPConfiguration(**new_config_args)

    upsert_to_collection(nic, 'ip_configurations', new_config, 'name')
    poller = ncf.network_interfaces.begin_create_or_update(
        resource_group_name, network_interface_name, nic)
    return get_property(poller.result().ip_configurations, ip_config_name)


def update_nic_ip_config_setter(cmd, resource_group_name, network_interface_name, parameters, gateway_lb):
    aux_subscriptions = []
    if is_valid_resource_id(gateway_lb):
        aux_subscriptions.append(parse_resource_id(gateway_lb)['subscription'])
    client = network_client_factory(cmd.cli_ctx, aux_subscriptions=aux_subscriptions).network_interfaces
    return client.begin_create_or_update(resource_group_name, network_interface_name, parameters)


def set_nic_ip_config(cmd, instance, parent, ip_config_name, subnet=None,
                      virtual_network_name=None, public_ip_address=None, load_balancer_name=None,
                      load_balancer_backend_address_pool_ids=None,
                      load_balancer_inbound_nat_rule_ids=None,
                      private_ip_address=None,
                      private_ip_address_version=None, make_primary=False,
                      application_security_groups=None,
                      app_gateway_backend_address_pools=None, gateway_lb=None):
    PublicIPAddress, Subnet, SubResource = cmd.get_models('PublicIPAddress', 'Subnet', 'SubResource')

    if make_primary:
        for config in parent.ip_configurations:
            config.primary = False
        instance.primary = True

    if private_ip_address == '':
        # switch private IP address allocation to Dynamic if empty string is used
        instance.private_ip_address = None
        instance.private_ip_allocation_method = 'dynamic'
        if cmd.supported_api_version(min_api='2016-09-01'):
            instance.private_ip_address_version = 'ipv4'
    elif private_ip_address is not None:
        # if specific address provided, allocation is static
        instance.private_ip_address = private_ip_address
        instance.private_ip_allocation_method = 'static'
        if private_ip_address_version is not None:
            instance.private_ip_address_version = private_ip_address_version

    if subnet == '':
        instance.subnet = None
    elif subnet is not None:
        instance.subnet = Subnet(id=subnet)

    if public_ip_address == '':
        instance.public_ip_address = None
    elif public_ip_address is not None:
        instance.public_ip_address = PublicIPAddress(id=public_ip_address)

    if load_balancer_backend_address_pool_ids == '':
        instance.load_balancer_backend_address_pools = None
    elif load_balancer_backend_address_pool_ids is not None:
        instance.load_balancer_backend_address_pools = load_balancer_backend_address_pool_ids

    if load_balancer_inbound_nat_rule_ids == '':
        instance.load_balancer_inbound_nat_rules = None
    elif load_balancer_inbound_nat_rule_ids is not None:
        instance.load_balancer_inbound_nat_rules = load_balancer_inbound_nat_rule_ids

    if application_security_groups == ['']:
        instance.application_security_groups = None
    elif application_security_groups:
        instance.application_security_groups = application_security_groups

    if app_gateway_backend_address_pools == ['']:
        instance.application_gateway_backend_address_pools = None
    elif app_gateway_backend_address_pools:
        instance.application_gateway_backend_address_pools = \
            [SubResource(id=x) for x in app_gateway_backend_address_pools]
    if gateway_lb is not None:
        instance.gateway_load_balancer = None if gateway_lb == '' else SubResource(id=gateway_lb)
    return parent


def _get_nic_ip_config(nic, name):
    if nic.ip_configurations:
        ip_config = next(
            (x for x in nic.ip_configurations if x.name.lower() == name.lower()), None)
    else:
        ip_config = None
    if not ip_config:
        raise CLIError('IP configuration {} not found.'.format(name))
    return ip_config


def add_nic_ip_config_address_pool(
        cmd, resource_group_name, network_interface_name, ip_config_name, backend_address_pool,
        load_balancer_name=None, application_gateway_name=None):
    BackendAddressPool = cmd.get_models('BackendAddressPool')
    client = network_client_factory(cmd.cli_ctx).network_interfaces
    nic = client.get(resource_group_name, network_interface_name)
    ip_config = _get_nic_ip_config(nic, ip_config_name)
    if load_balancer_name:
        upsert_to_collection(ip_config, 'load_balancer_backend_address_pools',
                             BackendAddressPool(id=backend_address_pool),
                             'id')
    elif application_gateway_name:
        upsert_to_collection(ip_config, 'application_gateway_backend_address_pools',
                             BackendAddressPool(id=backend_address_pool),
                             'id')
    poller = client.begin_create_or_update(resource_group_name, network_interface_name, nic)
    return get_property(poller.result().ip_configurations, ip_config_name)


def remove_nic_ip_config_address_pool(
        cmd, resource_group_name, network_interface_name, ip_config_name, backend_address_pool,
        load_balancer_name=None, application_gateway_name=None):
    client = network_client_factory(cmd.cli_ctx).network_interfaces
    nic = client.get(resource_group_name, network_interface_name)
    ip_config = _get_nic_ip_config(nic, ip_config_name)
    if load_balancer_name:
        keep_items = [x for x in ip_config.load_balancer_backend_address_pools or [] if x.id != backend_address_pool]
        ip_config.load_balancer_backend_address_pools = keep_items
    elif application_gateway_name:
        keep_items = [x for x in ip_config.application_gateway_backend_address_pools or [] if
                      x.id != backend_address_pool]
        ip_config.application_gateway_backend_address_pools = keep_items
    poller = client.begin_create_or_update(resource_group_name, network_interface_name, nic)
    return get_property(poller.result().ip_configurations, ip_config_name)


def add_nic_ip_config_inbound_nat_rule(
        cmd, resource_group_name, network_interface_name, ip_config_name, inbound_nat_rule,
        load_balancer_name=None):
    InboundNatRule = cmd.get_models('InboundNatRule')
    client = network_client_factory(cmd.cli_ctx).network_interfaces
    nic = client.get(resource_group_name, network_interface_name)
    ip_config = _get_nic_ip_config(nic, ip_config_name)
    upsert_to_collection(ip_config, 'load_balancer_inbound_nat_rules',
                         InboundNatRule(id=inbound_nat_rule),
                         'id')
    poller = client.begin_create_or_update(resource_group_name, network_interface_name, nic)
    return get_property(poller.result().ip_configurations, ip_config_name)


def remove_nic_ip_config_inbound_nat_rule(
        cmd, resource_group_name, network_interface_name, ip_config_name, inbound_nat_rule,
        load_balancer_name=None):
    client = network_client_factory(cmd.cli_ctx).network_interfaces
    nic = client.get(resource_group_name, network_interface_name)
    ip_config = _get_nic_ip_config(nic, ip_config_name)
    keep_items = \
        [x for x in ip_config.load_balancer_inbound_nat_rules or [] if x.id != inbound_nat_rule]
    ip_config.load_balancer_inbound_nat_rules = keep_items
    poller = client.begin_create_or_update(resource_group_name, network_interface_name, nic)
    return get_property(poller.result().ip_configurations, ip_config_name)
# endregion


# region NetworkSecurityGroups
def create_nsg(cmd, resource_group_name, network_security_group_name, location=None, tags=None):
    client = network_client_factory(cmd.cli_ctx).network_security_groups
    NetworkSecurityGroup = cmd.get_models('NetworkSecurityGroup')
    nsg = NetworkSecurityGroup(location=location, tags=tags)
    return client.begin_create_or_update(resource_group_name, network_security_group_name, nsg)


def _create_singular_or_plural_property(kwargs, val, singular_name, plural_name):

    if not val:
        return
    if not isinstance(val, list):
        val = [val]
    if len(val) > 1:
        kwargs[plural_name] = val
        kwargs[singular_name] = None
    else:
        kwargs[singular_name] = val[0]
        kwargs[plural_name] = None


def _handle_asg_property(kwargs, key, asgs):
    prefix = key.split('_', 1)[0] + '_'
    if asgs:
        kwargs[key] = asgs
        if kwargs[prefix + 'address_prefix']:
            kwargs[prefix + 'address_prefix'] = ''


def create_nsg_rule_2017_06_01(cmd, resource_group_name, network_security_group_name, security_rule_name,
                               priority, description=None, protocol=None, access=None, direction=None,
                               source_port_ranges='*', source_address_prefixes='*',
                               destination_port_ranges=80, destination_address_prefixes='*',
                               source_asgs=None, destination_asgs=None):
    kwargs = {
        'protocol': protocol,
        'direction': direction,
        'description': description,
        'priority': priority,
        'access': access,
        'name': security_rule_name
    }
    _create_singular_or_plural_property(kwargs, source_address_prefixes,
                                        'source_address_prefix', 'source_address_prefixes')
    _create_singular_or_plural_property(kwargs, destination_address_prefixes,
                                        'destination_address_prefix', 'destination_address_prefixes')
    _create_singular_or_plural_property(kwargs, source_port_ranges,
                                        'source_port_range', 'source_port_ranges')
    _create_singular_or_plural_property(kwargs, destination_port_ranges,
                                        'destination_port_range', 'destination_port_ranges')

    # workaround for issue https://github.com/Azure/azure-rest-api-specs/issues/1591
    kwargs['source_address_prefix'] = kwargs['source_address_prefix'] or ''
    kwargs['destination_address_prefix'] = kwargs['destination_address_prefix'] or ''

    if cmd.supported_api_version(min_api='2017-09-01'):
        _handle_asg_property(kwargs, 'source_application_security_groups', source_asgs)
        _handle_asg_property(kwargs, 'destination_application_security_groups', destination_asgs)

    SecurityRule = cmd.get_models('SecurityRule')
    settings = SecurityRule(**kwargs)
    ncf = network_client_factory(cmd.cli_ctx)
    return ncf.security_rules.begin_create_or_update(
        resource_group_name, network_security_group_name, security_rule_name, settings)


def create_nsg_rule_2017_03_01(cmd, resource_group_name, network_security_group_name, security_rule_name,
                               priority, description=None, protocol=None, access=None, direction=None,
                               source_port_range='*', source_address_prefix='*',
                               destination_port_range=80, destination_address_prefix='*'):
    SecurityRule = cmd.get_models('SecurityRule')
    settings = SecurityRule(protocol=protocol, source_address_prefix=source_address_prefix,
                            destination_address_prefix=destination_address_prefix, access=access,
                            direction=direction,
                            description=description, source_port_range=source_port_range,
                            destination_port_range=destination_port_range, priority=priority,
                            name=security_rule_name)

    ncf = network_client_factory(cmd.cli_ctx)
    return ncf.security_rules.begin_create_or_update(
        resource_group_name, network_security_group_name, security_rule_name, settings)


def _update_singular_or_plural_property(instance, val, singular_name, plural_name):

    if val is None:
        return
    if not isinstance(val, list):
        val = [val]
    if len(val) > 1:
        setattr(instance, plural_name, val)
        setattr(instance, singular_name, None)
    else:
        setattr(instance, plural_name, None)
        setattr(instance, singular_name, val[0])


def update_nsg_rule_2017_06_01(instance, protocol=None, source_address_prefixes=None,
                               destination_address_prefixes=None, access=None, direction=None, description=None,
                               source_port_ranges=None, destination_port_ranges=None, priority=None,
                               source_asgs=None, destination_asgs=None):
    # No client validation as server side returns pretty good errors
    instance.protocol = protocol if protocol is not None else instance.protocol
    instance.access = access if access is not None else instance.access
    instance.direction = direction if direction is not None else instance.direction
    instance.description = description if description is not None else instance.description
    instance.priority = priority if priority is not None else instance.priority

    _update_singular_or_plural_property(instance, source_address_prefixes,
                                        'source_address_prefix', 'source_address_prefixes')
    _update_singular_or_plural_property(instance, destination_address_prefixes,
                                        'destination_address_prefix', 'destination_address_prefixes')
    _update_singular_or_plural_property(instance, source_port_ranges,
                                        'source_port_range', 'source_port_ranges')
    _update_singular_or_plural_property(instance, destination_port_ranges,
                                        'destination_port_range', 'destination_port_ranges')

    # workaround for issue https://github.com/Azure/azure-rest-api-specs/issues/1591
    instance.source_address_prefix = instance.source_address_prefix or ''
    instance.destination_address_prefix = instance.destination_address_prefix or ''

    if source_asgs == ['']:
        instance.source_application_security_groups = None
    elif source_asgs:
        instance.source_application_security_groups = source_asgs

    if destination_asgs == ['']:
        instance.destination_application_security_groups = None
    elif destination_asgs:
        instance.destination_application_security_groups = destination_asgs

    return instance


def update_nsg_rule_2017_03_01(instance, protocol=None, source_address_prefix=None,
                               destination_address_prefix=None, access=None, direction=None, description=None,
                               source_port_range=None, destination_port_range=None, priority=None):
    # No client validation as server side returns pretty good errors
    instance.protocol = protocol if protocol is not None else instance.protocol
    instance.source_address_prefix = (source_address_prefix if source_address_prefix is not None
                                      else instance.source_address_prefix)
    instance.destination_address_prefix = destination_address_prefix \
        if destination_address_prefix is not None else instance.destination_address_prefix
    instance.access = access if access is not None else instance.access
    instance.direction = direction if direction is not None else instance.direction
    instance.description = description if description is not None else instance.description
    instance.source_port_range = source_port_range \
        if source_port_range is not None else instance.source_port_range
    instance.destination_port_range = destination_port_range \
        if destination_port_range is not None else instance.destination_port_range
    instance.priority = priority if priority is not None else instance.priority
    return instance
# endregion


# region NetworkProfiles
def list_network_profiles(cmd, resource_group_name=None):
    client = network_client_factory(cmd.cli_ctx).network_profiles
    if resource_group_name:
        return client.list(resource_group_name)
    return client.list_all()
# endregion


# region NetworkWatchers
def _create_network_watchers(cmd, client, resource_group_name, locations, tags):
    if resource_group_name is None:
        raise CLIError("usage error: '--resource-group' required when enabling new regions")

    NetworkWatcher = cmd.get_models('NetworkWatcher')
    for location in locations:
        client.create_or_update(
            resource_group_name, '{}-watcher'.format(location),
            NetworkWatcher(location=location, tags=tags))


def _update_network_watchers(cmd, client, watchers, tags):
    NetworkWatcher = cmd.get_models('NetworkWatcher')
    for watcher in watchers:
        id_parts = parse_resource_id(watcher.id)
        watcher_rg = id_parts['resource_group']
        watcher_name = id_parts['name']
        watcher_tags = watcher.tags if tags is None else tags
        client.create_or_update(
            watcher_rg, watcher_name,
            NetworkWatcher(location=watcher.location, tags=watcher_tags))


def _delete_network_watchers(cmd, client, watchers):
    for watcher in watchers:
        from azure.cli.core.commands import LongRunningOperation
        id_parts = parse_resource_id(watcher.id)
        watcher_rg = id_parts['resource_group']
        watcher_name = id_parts['name']
        logger.warning(
            "Disabling Network Watcher for region '%s' by deleting resource '%s'",
            watcher.location, watcher.id)
        LongRunningOperation(cmd.cli_ctx)(client.begin_delete(watcher_rg, watcher_name))


def configure_network_watcher(cmd, client, locations, resource_group_name=None, enabled=None, tags=None):
    watcher_list = list(client.list_all())
    locations_list = [location.lower() for location in locations]
    existing_watchers = [w for w in watcher_list if w.location in locations_list]
    nonenabled_regions = list(set(locations) - set(watcher.location for watcher in existing_watchers))

    if enabled is None:
        if resource_group_name is not None:
            logger.warning(
                "Resource group '%s' is only used when enabling new regions and will be ignored.",
                resource_group_name)
        for location in nonenabled_regions:
            logger.warning(
                "Region '%s' is not enabled for Network Watcher and will be ignored.", location)
        _update_network_watchers(cmd, client, existing_watchers, tags)

    elif enabled:
        _create_network_watchers(cmd, client, resource_group_name, nonenabled_regions, tags)
        _update_network_watchers(cmd, client, existing_watchers, tags)

    else:
        if tags is not None:
            raise CLIError("usage error: '--tags' cannot be used when disabling regions")
        _delete_network_watchers(cmd, client, existing_watchers)

    return client.list_all()


def create_nw_connection_monitor(cmd,
                                 client,
                                 connection_monitor_name,
                                 watcher_rg,
                                 watcher_name,
                                 resource_group_name=None,
                                 location=None,
                                 source_resource=None,
                                 source_port=None,
                                 dest_resource=None,
                                 dest_port=None,
                                 dest_address=None,
                                 tags=None,
                                 do_not_start=None,
                                 monitoring_interval=None,
                                 endpoint_source_name=None,
                                 endpoint_source_resource_id=None,
                                 endpoint_source_address=None,
                                 endpoint_source_type=None,
                                 endpoint_source_coverage_level=None,
                                 endpoint_dest_name=None,
                                 endpoint_dest_resource_id=None,
                                 endpoint_dest_address=None,
                                 endpoint_dest_type=None,
                                 endpoint_dest_coverage_level=None,
                                 test_config_name=None,
                                 test_config_frequency=None,
                                 test_config_protocol=None,
                                 test_config_preferred_ip_version=None,
                                 test_config_threshold_failed_percent=None,
                                 test_config_threshold_round_trip_time=None,
                                 test_config_tcp_disable_trace_route=None,
                                 test_config_tcp_port=None,
                                 test_config_tcp_port_behavior=None,
                                 test_config_icmp_disable_trace_route=None,
                                 test_config_http_port=None,
                                 test_config_http_method=None,
                                 test_config_http_path=None,
                                 test_config_http_valid_status_codes=None,
                                 test_config_http_prefer_https=None,
                                 test_group_name=None,
                                 test_group_disable=None,
                                 output_type=None,
                                 workspace_ids=None,
                                 notes=None):
    v1_required_parameter_set = [
        source_resource, source_port,
        dest_resource, dest_address, dest_port
    ]

    v2_required_parameter_set = [
        endpoint_source_name, endpoint_source_resource_id, endpoint_source_type, endpoint_source_coverage_level,
        endpoint_dest_name, endpoint_dest_address, endpoint_dest_type, endpoint_dest_coverage_level,
        test_config_name, test_config_protocol,
        output_type, workspace_ids,
    ]

    if any(v1_required_parameter_set):  # V1 creation
        connection_monitor = _create_nw_connection_monitor_v1(cmd,
                                                              connection_monitor_name,
                                                              watcher_rg,
                                                              watcher_name,
                                                              source_resource,
                                                              resource_group_name,
                                                              source_port,
                                                              location,
                                                              dest_resource,
                                                              dest_port,
                                                              dest_address,
                                                              tags,
                                                              do_not_start,
                                                              monitoring_interval)
        from azure.cli.core.profiles._shared import AD_HOC_API_VERSIONS
        client = get_mgmt_service_client(
            cmd.cli_ctx,
            ResourceType.MGMT_NETWORK,
            api_version=AD_HOC_API_VERSIONS[ResourceType.MGMT_NETWORK]['nw_connection_monitor']
        ).connection_monitors
    elif any(v2_required_parameter_set):  # V2 creation
        connection_monitor = _create_nw_connection_monitor_v2(cmd,
                                                              location,
                                                              tags,
                                                              endpoint_source_name,
                                                              endpoint_source_resource_id,
                                                              endpoint_source_address,
                                                              endpoint_source_type,
                                                              endpoint_source_coverage_level,
                                                              endpoint_dest_name,
                                                              endpoint_dest_resource_id,
                                                              endpoint_dest_address,
                                                              endpoint_dest_type,
                                                              endpoint_dest_coverage_level,
                                                              test_config_name,
                                                              test_config_frequency,
                                                              test_config_protocol,
                                                              test_config_preferred_ip_version,
                                                              test_config_threshold_failed_percent,
                                                              test_config_threshold_round_trip_time,
                                                              test_config_tcp_port,
                                                              test_config_tcp_port_behavior,
                                                              test_config_tcp_disable_trace_route,
                                                              test_config_icmp_disable_trace_route,
                                                              test_config_http_port,
                                                              test_config_http_method,
                                                              test_config_http_path,
                                                              test_config_http_valid_status_codes,
                                                              test_config_http_prefer_https,
                                                              test_group_name,
                                                              test_group_disable,
                                                              output_type,
                                                              workspace_ids,
                                                              notes)
    else:
        raise CLIError('Unknown operation')

    return client.begin_create_or_update(watcher_rg, watcher_name, connection_monitor_name, connection_monitor)


def _create_nw_connection_monitor_v1(cmd,
                                     connection_monitor_name,
                                     watcher_rg,
                                     watcher_name,
                                     source_resource,
                                     resource_group_name=None,
                                     source_port=None,
                                     location=None,
                                     dest_resource=None,
                                     dest_port=None,
                                     dest_address=None,
                                     tags=None,
                                     do_not_start=None,
                                     monitoring_interval=60):
    ConnectionMonitor, ConnectionMonitorSource, ConnectionMonitorDestination = cmd.get_models(
        'ConnectionMonitor', 'ConnectionMonitorSource', 'ConnectionMonitorDestination')

    cmv1 = ConnectionMonitor(
        location=location,
        tags=tags,
        source=ConnectionMonitorSource(
            resource_id=source_resource,
            port=source_port
        ),
        destination=ConnectionMonitorDestination(
            resource_id=dest_resource,
            port=dest_port,
            address=dest_address
        ),
        auto_start=not do_not_start,
        monitoring_interval_in_seconds=monitoring_interval,
        endpoints=None,
        test_configurations=None,
        test_groups=None,
        outputs=None,
        notes=None
    )

    return cmv1


def _create_nw_connection_monitor_v2(cmd,
                                     location=None,
                                     tags=None,
                                     endpoint_source_name=None,
                                     endpoint_source_resource_id=None,
                                     endpoint_source_address=None,
                                     endpoint_source_type=None,
                                     endpoint_source_coverage_level=None,
                                     endpoint_dest_name=None,
                                     endpoint_dest_resource_id=None,
                                     endpoint_dest_address=None,
                                     endpoint_dest_type=None,
                                     endpoint_dest_coverage_level=None,
                                     test_config_name=None,
                                     test_config_frequency=None,
                                     test_config_protocol=None,
                                     test_config_preferred_ip_version=None,
                                     test_config_threshold_failed_percent=None,
                                     test_config_threshold_round_trip_time=None,
                                     test_config_tcp_port=None,
                                     test_config_tcp_port_behavior=None,
                                     test_config_tcp_disable_trace_route=False,
                                     test_config_icmp_disable_trace_route=False,
                                     test_config_http_port=None,
                                     test_config_http_method=None,
                                     test_config_http_path=None,
                                     test_config_http_valid_status_codes=None,
                                     test_config_http_prefer_https=None,
                                     test_group_name=None,
                                     test_group_disable=False,
                                     output_type=None,
                                     workspace_ids=None,
                                     notes=None):
    src_endpoint = _create_nw_connection_monitor_v2_endpoint(cmd,
                                                             endpoint_source_name,
                                                             endpoint_resource_id=endpoint_source_resource_id,
                                                             address=endpoint_source_address,
                                                             endpoint_type=endpoint_source_type,
                                                             coverage_level=endpoint_source_coverage_level)
    dst_endpoint = _create_nw_connection_monitor_v2_endpoint(cmd,
                                                             endpoint_dest_name,
                                                             endpoint_resource_id=endpoint_dest_resource_id,
                                                             address=endpoint_dest_address,
                                                             endpoint_type=endpoint_dest_type,
                                                             coverage_level=endpoint_dest_coverage_level)
    test_config = _create_nw_connection_monitor_v2_test_configuration(cmd,
                                                                      test_config_name,
                                                                      test_config_frequency,
                                                                      test_config_protocol,
                                                                      test_config_threshold_failed_percent,
                                                                      test_config_threshold_round_trip_time,
                                                                      test_config_preferred_ip_version,
                                                                      test_config_tcp_port,
                                                                      test_config_tcp_port_behavior,
                                                                      test_config_tcp_disable_trace_route,
                                                                      test_config_icmp_disable_trace_route,
                                                                      test_config_http_port,
                                                                      test_config_http_method,
                                                                      test_config_http_path,
                                                                      test_config_http_valid_status_codes,
                                                                      test_config_http_prefer_https)
    test_group = _create_nw_connection_monitor_v2_test_group(cmd,
                                                             test_group_name,
                                                             test_group_disable,
                                                             [test_config],
                                                             [src_endpoint],
                                                             [dst_endpoint])

    # If 'workspace_ids' option is specified but 'output_type' is not then still it should be implicit that 'output-type' is 'Workspace'
    # since only supported value for output_type is 'Workspace' currently.
    if workspace_ids and not output_type:
        output_type = 'Workspace'

    if output_type:
        outputs = []
        if workspace_ids:
            for workspace_id in workspace_ids:
                output = _create_nw_connection_monitor_v2_output(cmd, output_type, workspace_id)
                outputs.append(output)
    else:
        outputs = []

    ConnectionMonitor = cmd.get_models('ConnectionMonitor')
    cmv2 = ConnectionMonitor(location=location,
                             tags=tags,
                             auto_start=None,
                             monitoring_interval_in_seconds=None,
                             endpoints=[src_endpoint, dst_endpoint],
                             test_configurations=[test_config],
                             test_groups=[test_group],
                             outputs=outputs,
                             notes=notes)
    return cmv2


def _create_nw_connection_monitor_v2_endpoint(cmd,
                                              name,
                                              endpoint_resource_id=None,
                                              address=None,
                                              filter_type=None,
                                              filter_items=None,
                                              endpoint_type=None,
                                              coverage_level=None):
    if (filter_type and not filter_items) or (not filter_type and filter_items):
        raise CLIError('usage error: '
                       '--filter-type and --filter-item for endpoint filter must be present at the same time.')

    ConnectionMonitorEndpoint, ConnectionMonitorEndpointFilter = cmd.get_models(
        'ConnectionMonitorEndpoint', 'ConnectionMonitorEndpointFilter')

    endpoint = ConnectionMonitorEndpoint(name=name,
                                         resource_id=endpoint_resource_id,
                                         address=address,
                                         type=endpoint_type,
                                         coverage_level=coverage_level)

    if filter_type and filter_items:
        endpoint_filter = ConnectionMonitorEndpointFilter(type=filter_type, items=filter_items)
        endpoint.filter = endpoint_filter

    return endpoint


def _create_nw_connection_monitor_v2_test_configuration(cmd,
                                                        name,
                                                        test_frequency,
                                                        protocol,
                                                        threshold_failed_percent,
                                                        threshold_round_trip_time,
                                                        preferred_ip_version,
                                                        tcp_port=None,
                                                        tcp_port_behavior=None,
                                                        tcp_disable_trace_route=None,
                                                        icmp_disable_trace_route=None,
                                                        http_port=None,
                                                        http_method=None,
                                                        http_path=None,
                                                        http_valid_status_codes=None,
                                                        http_prefer_https=None,
                                                        http_request_headers=None):
    (ConnectionMonitorTestConfigurationProtocol,
     ConnectionMonitorTestConfiguration, ConnectionMonitorSuccessThreshold) = cmd.get_models(
         'ConnectionMonitorTestConfigurationProtocol',
         'ConnectionMonitorTestConfiguration', 'ConnectionMonitorSuccessThreshold')

    test_config = ConnectionMonitorTestConfiguration(name=name,
                                                     test_frequency_sec=test_frequency,
                                                     protocol=protocol,
                                                     preferred_ip_version=preferred_ip_version)

    if threshold_failed_percent or threshold_round_trip_time:
        threshold = ConnectionMonitorSuccessThreshold(checks_failed_percent=threshold_failed_percent,
                                                      round_trip_time_ms=threshold_round_trip_time)
        test_config.success_threshold = threshold

    if protocol == ConnectionMonitorTestConfigurationProtocol.tcp:
        ConnectionMonitorTcpConfiguration = cmd.get_models('ConnectionMonitorTcpConfiguration')
        tcp_config = ConnectionMonitorTcpConfiguration(
            port=tcp_port,
            destination_port_behavior=tcp_port_behavior,
            disable_trace_route=tcp_disable_trace_route
        )
        test_config.tcp_configuration = tcp_config
    elif protocol == ConnectionMonitorTestConfigurationProtocol.icmp:
        ConnectionMonitorIcmpConfiguration = cmd.get_models('ConnectionMonitorIcmpConfiguration')
        icmp_config = ConnectionMonitorIcmpConfiguration(disable_trace_route=icmp_disable_trace_route)
        test_config.icmp_configuration = icmp_config
    elif protocol == ConnectionMonitorTestConfigurationProtocol.http:
        ConnectionMonitorHttpConfiguration = cmd.get_models('ConnectionMonitorHttpConfiguration')
        http_config = ConnectionMonitorHttpConfiguration(
            port=http_port,
            method=http_method,
            path=http_path,
            request_headers=http_request_headers,
            valid_status_code_ranges=http_valid_status_codes,
            prefer_https=http_prefer_https)
        test_config.http_configuration = http_config
    else:
        raise CLIError('Unsupported protocol: "{}" for test configuration'.format(protocol))

    return test_config


def _create_nw_connection_monitor_v2_test_group(cmd,
                                                name,
                                                disable,
                                                test_configurations,
                                                source_endpoints,
                                                destination_endpoints):
    ConnectionMonitorTestGroup = cmd.get_models('ConnectionMonitorTestGroup')

    test_group = ConnectionMonitorTestGroup(name=name,
                                            disable=disable,
                                            test_configurations=[tc.name for tc in test_configurations],
                                            sources=[e.name for e in source_endpoints],
                                            destinations=[e.name for e in destination_endpoints])
    return test_group


def _create_nw_connection_monitor_v2_output(cmd,
                                            output_type,
                                            workspace_id=None):
    ConnectionMonitorOutput, OutputType = cmd.get_models('ConnectionMonitorOutput', 'OutputType')
    output = ConnectionMonitorOutput(type=output_type)

    if output_type == OutputType.workspace:
        ConnectionMonitorWorkspaceSettings = cmd.get_models('ConnectionMonitorWorkspaceSettings')
        workspace = ConnectionMonitorWorkspaceSettings(workspace_resource_id=workspace_id)
        output.workspace_settings = workspace
    else:
        raise CLIError('Unsupported output type: "{}"'.format(output_type))

    return output


def add_nw_connection_monitor_v2_endpoint(cmd,
                                          client,
                                          watcher_rg,
                                          watcher_name,
                                          connection_monitor_name,
                                          location,
                                          name,
                                          coverage_level=None,
                                          endpoint_type=None,
                                          source_test_groups=None,
                                          dest_test_groups=None,
                                          endpoint_resource_id=None,
                                          address=None,
                                          filter_type=None,
                                          filter_items=None,
                                          address_include=None,
                                          address_exclude=None):
    (ConnectionMonitorEndpoint, ConnectionMonitorEndpointFilter,
     ConnectionMonitorEndpointScope, ConnectionMonitorEndpointScopeItem) = cmd.get_models(
         'ConnectionMonitorEndpoint', 'ConnectionMonitorEndpointFilter',
         'ConnectionMonitorEndpointScope', 'ConnectionMonitorEndpointScopeItem')

    endpoint_scope = ConnectionMonitorEndpointScope(include=[], exclude=[])
    for ip in address_include or []:
        include_item = ConnectionMonitorEndpointScopeItem(address=ip)
        endpoint_scope.include.append(include_item)
    for ip in address_exclude or []:
        exclude_item = ConnectionMonitorEndpointScopeItem(address=ip)
        endpoint_scope.exclude.append(exclude_item)

    endpoint = ConnectionMonitorEndpoint(name=name,
                                         resource_id=endpoint_resource_id,
                                         address=address,
                                         type=endpoint_type,
                                         coverage_level=coverage_level,
                                         scope=endpoint_scope if address_include or address_exclude else None)

    if filter_type and filter_items:
        endpoint_filter = ConnectionMonitorEndpointFilter(type=filter_type, items=filter_items)
        endpoint.filter = endpoint_filter

    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)
    connection_monitor.endpoints.append(endpoint)

    src_test_groups, dst_test_groups = set(source_test_groups or []), set(dest_test_groups or [])
    for test_group in connection_monitor.test_groups:
        if test_group.name in src_test_groups:
            test_group.sources.append(endpoint.name)
        if test_group.name in dst_test_groups:
            test_group.destinations.append(endpoint.name)

    return client.begin_create_or_update(watcher_rg, watcher_name, connection_monitor_name, connection_monitor)


def remove_nw_connection_monitor_v2_endpoint(client,
                                             watcher_rg,
                                             watcher_name,
                                             connection_monitor_name,
                                             location,
                                             name,
                                             test_groups=None):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)

    # refresh endpoints
    new_endpoints = [endpoint for endpoint in connection_monitor.endpoints if endpoint.name != name]
    connection_monitor.endpoints = new_endpoints

    # refresh test groups
    if test_groups is not None:
        temp_test_groups = [t for t in connection_monitor.test_groups if t.name in test_groups]
    else:
        temp_test_groups = connection_monitor.test_groups

    for test_group in temp_test_groups:
        if name in test_group.sources:
            test_group.sources.remove(name)
        if name in test_group.destinations:
            test_group.destinations.remove(name)

    return client.begin_create_or_update(watcher_rg, watcher_name, connection_monitor_name, connection_monitor)


def show_nw_connection_monitor_v2_endpoint(client,
                                           watcher_rg,
                                           watcher_name,
                                           connection_monitor_name,
                                           location,
                                           name):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)

    for endpoint in connection_monitor.endpoints:
        if endpoint.name == name:
            return endpoint

    raise CLIError('unknown endpoint: {}'.format(name))


def list_nw_connection_monitor_v2_endpoint(client,
                                           watcher_rg,
                                           watcher_name,
                                           connection_monitor_name,
                                           location):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)
    return connection_monitor.endpoints


def add_nw_connection_monitor_v2_test_configuration(cmd,
                                                    client,
                                                    watcher_rg,
                                                    watcher_name,
                                                    connection_monitor_name,
                                                    location,
                                                    name,
                                                    protocol,
                                                    test_groups,
                                                    frequency=None,
                                                    threshold_failed_percent=None,
                                                    threshold_round_trip_time=None,
                                                    preferred_ip_version=None,
                                                    tcp_port=None,
                                                    tcp_port_behavior=None,
                                                    tcp_disable_trace_route=None,
                                                    icmp_disable_trace_route=None,
                                                    http_port=None,
                                                    http_method=None,
                                                    http_path=None,
                                                    http_valid_status_codes=None,
                                                    http_prefer_https=None,
                                                    http_request_headers=None):
    new_test_config = _create_nw_connection_monitor_v2_test_configuration(cmd,
                                                                          name,
                                                                          frequency,
                                                                          protocol,
                                                                          threshold_failed_percent,
                                                                          threshold_round_trip_time,
                                                                          preferred_ip_version,
                                                                          tcp_port,
                                                                          tcp_port_behavior,
                                                                          tcp_disable_trace_route,
                                                                          icmp_disable_trace_route,
                                                                          http_port,
                                                                          http_method,
                                                                          http_path,
                                                                          http_valid_status_codes,
                                                                          http_prefer_https,
                                                                          http_request_headers)

    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)
    connection_monitor.test_configurations.append(new_test_config)

    for test_group in connection_monitor.test_groups:
        if test_group.name in test_groups:
            test_group.test_configurations.append(new_test_config.name)

    return client.begin_create_or_update(watcher_rg, watcher_name, connection_monitor_name, connection_monitor)


def remove_nw_connection_monitor_v2_test_configuration(client,
                                                       watcher_rg,
                                                       watcher_name,
                                                       connection_monitor_name,
                                                       location,
                                                       name,
                                                       test_groups=None):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)

    # refresh test configurations
    new_test_configurations = [t for t in connection_monitor.test_configurations if t.name != name]
    connection_monitor.test_configurations = new_test_configurations

    if test_groups is not None:
        temp_test_groups = [t for t in connection_monitor.test_groups if t.name in test_groups]
    else:
        temp_test_groups = connection_monitor.test_groups

    # refresh test groups
    for test_group in temp_test_groups:
        test_group.test_configurations.remove(name)

    return client.begin_create_or_update(watcher_rg, watcher_name, connection_monitor_name, connection_monitor)


def show_nw_connection_monitor_v2_test_configuration(client,
                                                     watcher_rg,
                                                     watcher_name,
                                                     connection_monitor_name,
                                                     location,
                                                     name):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)

    for test_config in connection_monitor.test_configurations:
        if test_config.name == name:
            return test_config

    raise CLIError('unknown test configuration: {}'.format(name))


def list_nw_connection_monitor_v2_test_configuration(client,
                                                     watcher_rg,
                                                     watcher_name,
                                                     connection_monitor_name,
                                                     location):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)
    return connection_monitor.test_configurations


def add_nw_connection_monitor_v2_test_group(cmd,
                                            client,
                                            connection_monitor_name,
                                            watcher_rg,
                                            watcher_name,
                                            location,
                                            name,
                                            endpoint_source_name,
                                            endpoint_dest_name,
                                            test_config_name,
                                            disable=False,
                                            endpoint_source_resource_id=None,
                                            endpoint_source_address=None,
                                            endpoint_dest_resource_id=None,
                                            endpoint_dest_address=None,
                                            test_config_frequency=None,
                                            test_config_protocol=None,
                                            test_config_preferred_ip_version=None,
                                            test_config_threshold_failed_percent=None,
                                            test_config_threshold_round_trip_time=None,
                                            test_config_tcp_disable_trace_route=None,
                                            test_config_tcp_port=None,
                                            test_config_icmp_disable_trace_route=None,
                                            test_config_http_port=None,
                                            test_config_http_method=None,
                                            test_config_http_path=None,
                                            test_config_http_valid_status_codes=None,
                                            test_config_http_prefer_https=None):
    new_test_configuration_creation_requirements = [
        test_config_protocol, test_config_preferred_ip_version,
        test_config_threshold_failed_percent, test_config_threshold_round_trip_time,
        test_config_tcp_disable_trace_route, test_config_tcp_port,
        test_config_icmp_disable_trace_route,
        test_config_http_port, test_config_http_method,
        test_config_http_path, test_config_http_valid_status_codes, test_config_http_prefer_https
    ]

    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)

    new_test_group = _create_nw_connection_monitor_v2_test_group(cmd,
                                                                 name,
                                                                 disable,
                                                                 [], [], [])

    # deal with endpoint
    if any([endpoint_source_address, endpoint_source_resource_id]):
        src_endpoint = _create_nw_connection_monitor_v2_endpoint(cmd,
                                                                 endpoint_source_name,
                                                                 endpoint_source_resource_id,
                                                                 endpoint_source_address)
        connection_monitor.endpoints.append(src_endpoint)
    if any([endpoint_dest_address, endpoint_dest_resource_id]):
        dst_endpoint = _create_nw_connection_monitor_v2_endpoint(cmd,
                                                                 endpoint_dest_name,
                                                                 endpoint_dest_resource_id,
                                                                 endpoint_dest_address)
        connection_monitor.endpoints.append(dst_endpoint)

    new_test_group.sources.append(endpoint_source_name)
    new_test_group.destinations.append(endpoint_dest_name)

    # deal with test configuration
    if any(new_test_configuration_creation_requirements):
        test_config = _create_nw_connection_monitor_v2_test_configuration(cmd,
                                                                          test_config_name,
                                                                          test_config_frequency,
                                                                          test_config_protocol,
                                                                          test_config_threshold_failed_percent,
                                                                          test_config_threshold_round_trip_time,
                                                                          test_config_preferred_ip_version,
                                                                          test_config_tcp_port,
                                                                          test_config_tcp_disable_trace_route,
                                                                          test_config_icmp_disable_trace_route,
                                                                          test_config_http_port,
                                                                          test_config_http_method,
                                                                          test_config_http_path,
                                                                          test_config_http_valid_status_codes,
                                                                          test_config_http_prefer_https)
        connection_monitor.test_configurations.append(test_config)
    new_test_group.test_configurations.append(test_config_name)

    connection_monitor.test_groups.append(new_test_group)

    return client.begin_create_or_update(watcher_rg, watcher_name, connection_monitor_name, connection_monitor)


def remove_nw_connection_monitor_v2_test_group(client,
                                               watcher_rg,
                                               watcher_name,
                                               connection_monitor_name,
                                               location,
                                               name):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)

    new_test_groups, removed_test_group = [], None
    for t in connection_monitor.test_groups:
        if t.name == name:
            removed_test_group = t
        else:
            new_test_groups.append(t)

    if removed_test_group is None:
        raise CLIError('test group: "{}" not exist'.format(name))
    connection_monitor.test_groups = new_test_groups

    # deal with endpoints which are only referenced by this removed test group
    removed_endpoints = []
    for e in removed_test_group.sources + removed_test_group.destinations:
        tmp = [t for t in connection_monitor.test_groups if (e in t.sources or e in t.destinations)]
        if not tmp:
            removed_endpoints.append(e)
    connection_monitor.endpoints = [e for e in connection_monitor.endpoints if e.name not in removed_endpoints]

    # deal with test configurations which are only referenced by this remove test group
    removed_test_configurations = []
    for c in removed_test_group.test_configurations:
        tmp = [t for t in connection_monitor.test_groups if c in t.test_configurations]
        if not tmp:
            removed_test_configurations.append(c)
    connection_monitor.test_configurations = [c for c in connection_monitor.test_configurations
                                              if c.name not in removed_test_configurations]

    return client.begin_create_or_update(watcher_rg, watcher_name, connection_monitor_name, connection_monitor)


def show_nw_connection_monitor_v2_test_group(client,
                                             watcher_rg,
                                             watcher_name,
                                             connection_monitor_name,
                                             location,
                                             name):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)

    for t in connection_monitor.test_groups:
        if t.name == name:
            return t

    raise CLIError('unknown test group: {}'.format(name))


def list_nw_connection_monitor_v2_test_group(client,
                                             watcher_rg,
                                             watcher_name,
                                             connection_monitor_name,
                                             location):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)
    return connection_monitor.test_groups


def add_nw_connection_monitor_v2_output(cmd,
                                        client,
                                        watcher_rg,
                                        watcher_name,
                                        connection_monitor_name,
                                        location,
                                        out_type,
                                        workspace_id=None):
    output = _create_nw_connection_monitor_v2_output(cmd, out_type, workspace_id)

    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)

    if connection_monitor.outputs is None:
        connection_monitor.outputs = []

    connection_monitor.outputs.append(output)

    return client.begin_create_or_update(watcher_rg, watcher_name, connection_monitor_name, connection_monitor)


def remove_nw_connection_monitor_v2_output(client,
                                           watcher_rg,
                                           watcher_name,
                                           connection_monitor_name,
                                           location):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)
    connection_monitor.outputs = []

    return client.begin_create_or_update(watcher_rg, watcher_name, connection_monitor_name, connection_monitor)


def list_nw_connection_monitor_v2_output(client,
                                         watcher_rg,
                                         watcher_name,
                                         connection_monitor_name,
                                         location):
    connection_monitor = client.get(watcher_rg, watcher_name, connection_monitor_name)
    return connection_monitor.outputs


def show_topology_watcher(cmd, client, resource_group_name, network_watcher_name, target_resource_group_name=None,
                          target_vnet=None, target_subnet=None):  # pylint: disable=unused-argument
    TopologyParameters = cmd.get_models('TopologyParameters')
    return client.get_topology(
        resource_group_name=resource_group_name,
        network_watcher_name=network_watcher_name,
        parameters=TopologyParameters(
            target_resource_group_name=target_resource_group_name,
            target_virtual_network=target_vnet,
            target_subnet=target_subnet
        ))


def check_nw_connectivity(cmd, client, watcher_rg, watcher_name, source_resource, source_port=None,
                          dest_resource=None, dest_port=None, dest_address=None,
                          resource_group_name=None, protocol=None, method=None, headers=None, valid_status_codes=None):
    ConnectivitySource, ConnectivityDestination, ConnectivityParameters, ProtocolConfiguration, HTTPConfiguration = \
        cmd.get_models(
            'ConnectivitySource', 'ConnectivityDestination', 'ConnectivityParameters', 'ProtocolConfiguration',
            'HTTPConfiguration')
    params = ConnectivityParameters(
        source=ConnectivitySource(resource_id=source_resource, port=source_port),
        destination=ConnectivityDestination(resource_id=dest_resource, address=dest_address, port=dest_port),
        protocol=protocol
    )
    if any([method, headers, valid_status_codes]):
        params.protocol_configuration = ProtocolConfiguration(http_configuration=HTTPConfiguration(
            method=method,
            headers=headers,
            valid_status_codes=valid_status_codes
        ))
    return client.begin_check_connectivity(watcher_rg, watcher_name, params)


def check_nw_ip_flow(cmd, client, vm, watcher_rg, watcher_name, direction, protocol, local, remote,
                     resource_group_name=None, nic=None, location=None):
    VerificationIPFlowParameters = cmd.get_models('VerificationIPFlowParameters')

    try:
        local_ip_address, local_port = local.split(':')
        remote_ip_address, remote_port = remote.split(':')
    except:
        raise CLIError("usage error: the format of the '--local' and '--remote' should be like x.x.x.x:port")

    if not is_valid_resource_id(vm):
        if not resource_group_name:
            raise CLIError("usage error: --vm NAME --resource-group NAME | --vm ID")

        vm = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name,
            namespace='Microsoft.Compute', type='virtualMachines', name=vm)

    if nic and not is_valid_resource_id(nic):
        if not resource_group_name:
            raise CLIError("usage error: --nic NAME --resource-group NAME | --nic ID")

        nic = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name,
            namespace='Microsoft.Network', type='networkInterfaces', name=nic)

    return client.begin_verify_ip_flow(
        watcher_rg, watcher_name,
        VerificationIPFlowParameters(
            target_resource_id=vm, direction=direction, protocol=protocol, local_port=local_port,
            remote_port=remote_port, local_ip_address=local_ip_address,
            remote_ip_address=remote_ip_address, target_nic_resource_id=nic))


def show_nw_next_hop(cmd, client, resource_group_name, vm, watcher_rg, watcher_name,
                     source_ip, dest_ip, nic=None, location=None):
    NextHopParameters = cmd.get_models('NextHopParameters')

    if not is_valid_resource_id(vm):
        vm = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name,
            namespace='Microsoft.Compute', type='virtualMachines', name=vm)

    if nic and not is_valid_resource_id(nic):
        nic = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name,
            namespace='Microsoft.Network', type='networkInterfaces', name=nic)

    return client.begin_get_next_hop(
        watcher_rg, watcher_name, NextHopParameters(target_resource_id=vm,
                                                    source_ip_address=source_ip,
                                                    destination_ip_address=dest_ip,
                                                    target_nic_resource_id=nic))


def show_nw_security_view(cmd, client, resource_group_name, vm, watcher_rg, watcher_name, location=None):
    if not is_valid_resource_id(vm):
        vm = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name,
            namespace='Microsoft.Compute', type='virtualMachines', name=vm)

    security_group_view_parameters = cmd.get_models('SecurityGroupViewParameters')(target_resource_id=vm)
    return client.begin_get_vm_security_rules(watcher_rg, watcher_name, security_group_view_parameters)


def create_nw_packet_capture(cmd, client, resource_group_name, capture_name, vm,
                             watcher_rg, watcher_name, location=None,
                             storage_account=None, storage_path=None, file_path=None,
                             capture_size=None, capture_limit=None, time_limit=None, filters=None):
    PacketCapture, PacketCaptureStorageLocation = cmd.get_models('PacketCapture', 'PacketCaptureStorageLocation')

    storage_settings = PacketCaptureStorageLocation(storage_id=storage_account,
                                                    storage_path=storage_path, file_path=file_path)
    capture_params = PacketCapture(target=vm, storage_location=storage_settings,
                                   bytes_to_capture_per_packet=capture_size,
                                   total_bytes_per_session=capture_limit, time_limit_in_seconds=time_limit,
                                   filters=filters)
    return client.begin_create(watcher_rg, watcher_name, capture_name, capture_params)


def set_nsg_flow_logging(cmd, client, watcher_rg, watcher_name, nsg, storage_account=None,
                         resource_group_name=None, enabled=None, retention=0, log_format=None, log_version=None,
                         traffic_analytics_workspace=None, traffic_analytics_interval=None,
                         traffic_analytics_enabled=None):
    from azure.cli.core.commands import LongRunningOperation
    flowlog_status_parameters = cmd.get_models('FlowLogStatusParameters')(target_resource_id=nsg)
    config = LongRunningOperation(cmd.cli_ctx)(client.begin_get_flow_log_status(watcher_rg,
                                                                                watcher_name,
                                                                                flowlog_status_parameters))

    try:
        if not config.flow_analytics_configuration.network_watcher_flow_analytics_configuration.workspace_id:
            config.flow_analytics_configuration = None
    except AttributeError:
        config.flow_analytics_configuration = None

    with cmd.update_context(config) as c:
        c.set_param('enabled', enabled if enabled is not None else config.enabled)
        c.set_param('storage_id', storage_account or config.storage_id)
    if retention is not None:
        config.retention_policy = {
            'days': retention,
            'enabled': int(retention) > 0
        }
    if cmd.supported_api_version(min_api='2018-10-01') and (log_format or log_version):
        config.format = {
            'type': log_format,
            'version': log_version
        }

    if cmd.supported_api_version(min_api='2018-10-01') and \
            any([traffic_analytics_workspace is not None, traffic_analytics_enabled is not None]):
        workspace = None

        if traffic_analytics_workspace:
            from azure.cli.core.commands.arm import get_arm_resource_by_id
            workspace = get_arm_resource_by_id(cmd.cli_ctx, traffic_analytics_workspace)

        if not config.flow_analytics_configuration:
            # must create whole object
            if not workspace:
                raise CLIError('usage error (analytics not already configured): --workspace NAME_OR_ID '
                               '[--enabled {true|false}]')
            if traffic_analytics_enabled is None:
                traffic_analytics_enabled = True
            config.flow_analytics_configuration = {
                'network_watcher_flow_analytics_configuration': {
                    'enabled': traffic_analytics_enabled,
                    'workspace_id': workspace.properties['customerId'],
                    'workspace_region': workspace.location,
                    'workspace_resource_id': traffic_analytics_workspace,
                    'traffic_analytics_interval': traffic_analytics_interval
                }
            }
        else:
            # pylint: disable=line-too-long
            with cmd.update_context(config.flow_analytics_configuration.network_watcher_flow_analytics_configuration) as c:
                # update object
                c.set_param('enabled', traffic_analytics_enabled)
                if traffic_analytics_workspace == "":
                    config.flow_analytics_configuration = None
                elif workspace:
                    c.set_param('workspace_id', workspace.properties['customerId'])
                    c.set_param('workspace_region', workspace.location)
                    c.set_param('workspace_resource_id', traffic_analytics_workspace)
                    c.set_param('traffic_analytics_interval', traffic_analytics_interval)

    return client.begin_set_flow_log_configuration(watcher_rg, watcher_name, config)


# combination of resource_group_name and nsg is for old output
# combination of location and flow_log_name is for new output
def show_nsg_flow_logging(cmd, client, watcher_rg, watcher_name, location=None, resource_group_name=None, nsg=None,
                          flow_log_name=None):
    # deprecated approach to show flow log
    if nsg is not None:
        flowlog_status_parameters = cmd.get_models('FlowLogStatusParameters')(target_resource_id=nsg)
        return client.begin_get_flow_log_status(watcher_rg, watcher_name, flowlog_status_parameters)

    # new approach to show flow log
    from ._client_factory import cf_flow_logs
    client = cf_flow_logs(cmd.cli_ctx, None)
    return client.get(watcher_rg, watcher_name, flow_log_name)


def create_nw_flow_log(cmd,
                       client,
                       location,
                       watcher_rg,
                       watcher_name,
                       flow_log_name,
                       nsg,
                       storage_account=None,
                       resource_group_name=None,
                       enabled=None,
                       retention=0,
                       log_format=None,
                       log_version=None,
                       traffic_analytics_workspace=None,
                       traffic_analytics_interval=60,
                       traffic_analytics_enabled=None,
                       tags=None):
    FlowLog = cmd.get_models('FlowLog')
    flow_log = FlowLog(location=location,
                       target_resource_id=nsg,
                       storage_id=storage_account,
                       enabled=enabled,
                       tags=tags)

    if retention > 0:
        RetentionPolicyParameters = cmd.get_models('RetentionPolicyParameters')
        retention_policy = RetentionPolicyParameters(days=retention, enabled=(retention > 0))
        flow_log.retention_policy = retention_policy

    if log_format is not None or log_version is not None:
        FlowLogFormatParameters = cmd.get_models('FlowLogFormatParameters')
        format_config = FlowLogFormatParameters(type=log_format, version=log_version)
        flow_log.format = format_config

    if traffic_analytics_workspace is not None:
        TrafficAnalyticsProperties, TrafficAnalyticsConfigurationProperties = \
            cmd.get_models('TrafficAnalyticsProperties', 'TrafficAnalyticsConfigurationProperties')

        from azure.cli.core.commands.arm import get_arm_resource_by_id
        workspace = get_arm_resource_by_id(cmd.cli_ctx, traffic_analytics_workspace)
        if not workspace:
            raise CLIError('Name or ID of workspace is invalid')

        traffic_analytics_config = TrafficAnalyticsConfigurationProperties(
            enabled=traffic_analytics_enabled,
            workspace_id=workspace.properties['customerId'],
            workspace_region=workspace.location,
            workspace_resource_id=workspace.id,
            traffic_analytics_interval=traffic_analytics_interval
        )
        traffic_analytics = TrafficAnalyticsProperties(
            network_watcher_flow_analytics_configuration=traffic_analytics_config
        )

        flow_log.flow_analytics_configuration = traffic_analytics

    return client.begin_create_or_update(watcher_rg, watcher_name, flow_log_name, flow_log)


def update_nw_flow_log_getter(client, watcher_rg, watcher_name, flow_log_name):
    return client.get(watcher_rg, watcher_name, flow_log_name)


def update_nw_flow_log_setter(client, watcher_rg, watcher_name, flow_log_name, parameters):
    return client.begin_create_or_update(watcher_rg, watcher_name, flow_log_name, parameters)


def update_nw_flow_log(cmd,
                       instance,
                       location,
                       resource_group_name=None,    # dummy parameter to let it appear in command
                       enabled=None,
                       nsg=None,
                       storage_account=None,
                       retention=0,
                       log_format=None,
                       log_version=None,
                       traffic_analytics_workspace=None,
                       traffic_analytics_interval=60,
                       traffic_analytics_enabled=None,
                       tags=None):
    with cmd.update_context(instance) as c:
        c.set_param('enabled', enabled)
        c.set_param('tags', tags)
        c.set_param('storage_id', storage_account)
        c.set_param('target_resource_id', nsg)

    with cmd.update_context(instance.retention_policy) as c:
        c.set_param('days', retention)
        c.set_param('enabled', retention > 0)

    with cmd.update_context(instance.format) as c:
        c.set_param('type', log_format)
        c.set_param('version', log_version)

    if traffic_analytics_workspace is not None:
        from azure.cli.core.commands.arm import get_arm_resource_by_id
        workspace = get_arm_resource_by_id(cmd.cli_ctx, traffic_analytics_workspace)
        if not workspace:
            raise CLIError('Name or ID of workspace is invalid')

        if instance.flow_analytics_configuration.network_watcher_flow_analytics_configuration is None:
            analytics_conf = cmd.get_models('TrafficAnalyticsConfigurationProperties')
            instance.flow_analytics_configuration.network_watcher_flow_analytics_configuration = analytics_conf()

        with cmd.update_context(
                instance.flow_analytics_configuration.network_watcher_flow_analytics_configuration) as c:
            c.set_param('enabled', traffic_analytics_enabled)
            c.set_param('workspace_id', workspace.properties['customerId'])
            c.set_param('workspace_region', workspace.location)
            c.set_param('workspace_resource_id', workspace.id)
            c.set_param('traffic_analytics_interval', traffic_analytics_interval)

    return instance


def list_nw_flow_log(client, watcher_rg, watcher_name, location):
    return client.list(watcher_rg, watcher_name)


def delete_nw_flow_log(client, watcher_rg, watcher_name, location, flow_log_name):
    return client.begin_delete(watcher_rg, watcher_name, flow_log_name)


def start_nw_troubleshooting(cmd, client, watcher_name, watcher_rg, resource, storage_account,
                             storage_path, resource_type=None, resource_group_name=None,
                             no_wait=False):
    TroubleshootingParameters = cmd.get_models('TroubleshootingParameters')
    params = TroubleshootingParameters(target_resource_id=resource, storage_id=storage_account,
                                       storage_path=storage_path)
    return sdk_no_wait(no_wait, client.begin_get_troubleshooting, watcher_rg, watcher_name, params)


def show_nw_troubleshooting_result(cmd, client, watcher_name, watcher_rg, resource, resource_type=None,
                                   resource_group_name=None):
    query_troubleshooting_parameters = cmd.get_models('QueryTroubleshootingParameters')(target_resource_id=resource)
    return client.begin_get_troubleshooting_result(watcher_rg, watcher_name, query_troubleshooting_parameters)


def run_network_configuration_diagnostic(cmd, client, watcher_rg, watcher_name, resource,
                                         direction=None, protocol=None, source=None, destination=None,
                                         destination_port=None, queries=None,
                                         resource_group_name=None, resource_type=None, parent=None):
    NetworkConfigurationDiagnosticParameters, NetworkConfigurationDiagnosticProfile = \
        cmd.get_models('NetworkConfigurationDiagnosticParameters', 'NetworkConfigurationDiagnosticProfile')

    if not queries:
        queries = [NetworkConfigurationDiagnosticProfile(
            direction=direction,
            protocol=protocol,
            source=source,
            destination=destination,
            destination_port=destination_port
        )]
    params = NetworkConfigurationDiagnosticParameters(target_resource_id=resource, profiles=queries)
    return client.begin_get_network_configuration_diagnostic(watcher_rg, watcher_name, params)
# endregion


# region CustomIpPrefix
def create_custom_ip_prefix(cmd, client, resource_group_name, custom_ip_prefix_name, location=None,
                            cidr=None, tags=None, zone=None, signed_message=None, authorization_message=None,
                            custom_ip_prefix_parent=None, no_wait=False):

    CustomIpPrefix = cmd.get_models('CustomIpPrefix')
    prefix = CustomIpPrefix(
        location=location,
        cidr=cidr,
        zones=zone,
        tags=tags,
        signed_message=signed_message,
        authorization_message=authorization_message
    )

    if custom_ip_prefix_parent:
        try:
            prefix.custom_ip_prefix_parent = client.get(resource_group_name, custom_ip_prefix_name)
        except ResourceNotFoundError:
            raise ResourceNotFoundError("Custom ip prefix parent {} doesn't exist".format(custom_ip_prefix_name))

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, custom_ip_prefix_name, prefix)


def update_custom_ip_prefix(instance,
                            signed_message=None,
                            authorization_message=None,
                            tags=None,
                            commissioned_state=None):
    if tags is not None:
        instance.tags = tags
    if signed_message is not None:
        instance.signed_message = signed_message
    if authorization_message is not None:
        instance.authorization_message = authorization_message
    if commissioned_state is not None:
        instance.commissioned_state = commissioned_state[0].upper() + commissioned_state[1:] + 'ing'
    return instance
# endregion


# region PublicIPAddresses
def create_public_ip(cmd, resource_group_name, public_ip_address_name, location=None, tags=None,
                     allocation_method=None, dns_name=None,
                     idle_timeout=4, reverse_fqdn=None, version=None, sku=None, tier=None, zone=None, ip_tags=None,
                     public_ip_prefix=None, edge_zone=None, ip_address=None):

    # In the latest profile, the default public IP will be expected to be changed from Basic to Standard.
    # In order to avoid breaking change which has a big impact to users,
    # we use the hint to guide users to use Standard sku to create public IP.
    if sku is None and cmd.cli_ctx.cloud.profile == 'latest':
        logger.warning(
            'It is recommended to use parameter "--sku Standard" to create new public IP. '
            'Please note that the default public IP used for creation will be changed from Basic to Standard '
            'in the future.')

    IPAllocationMethod, PublicIPAddress, PublicIPAddressDnsSettings, SubResource = cmd.get_models(
        'IPAllocationMethod', 'PublicIPAddress', 'PublicIPAddressDnsSettings', 'SubResource')
    client = network_client_factory(cmd.cli_ctx).public_ip_addresses
    if not allocation_method:
        allocation_method = IPAllocationMethod.static.value if (sku and sku.lower() == 'standard') \
            else IPAllocationMethod.dynamic.value

    public_ip_args = {
        'location': location,
        'tags': tags,
        'public_ip_allocation_method': allocation_method,
        'idle_timeout_in_minutes': idle_timeout,
        'ip_address': ip_address,
        'dns_settings': None
    }
    if cmd.supported_api_version(min_api='2016-09-01'):
        public_ip_args['public_ip_address_version'] = version
    if cmd.supported_api_version(min_api='2017-06-01'):
        public_ip_args['zones'] = zone
    if cmd.supported_api_version(min_api='2017-11-01'):
        public_ip_args['ip_tags'] = ip_tags
    if cmd.supported_api_version(min_api='2018-07-01') and public_ip_prefix:
        public_ip_args['public_ip_prefix'] = SubResource(id=public_ip_prefix)

    if sku:
        public_ip_args['sku'] = {'name': sku}
    if tier:
        if not sku:
            public_ip_args['sku'] = {'name': 'Basic'}
        public_ip_args['sku'].update({'tier': tier})

    public_ip = PublicIPAddress(**public_ip_args)

    if dns_name or reverse_fqdn:
        public_ip.dns_settings = PublicIPAddressDnsSettings(
            domain_name_label=dns_name,
            reverse_fqdn=reverse_fqdn)

    if edge_zone:
        public_ip.extended_location = _edge_zone_model(cmd, edge_zone)
    return client.begin_create_or_update(resource_group_name, public_ip_address_name, public_ip)


def update_public_ip(cmd, instance, dns_name=None, allocation_method=None, version=None,
                     idle_timeout=None, reverse_fqdn=None, tags=None, sku=None, ip_tags=None,
                     public_ip_prefix=None):
    if dns_name is not None or reverse_fqdn is not None:
        if instance.dns_settings:
            if dns_name is not None:
                instance.dns_settings.domain_name_label = dns_name
            if reverse_fqdn is not None:
                instance.dns_settings.reverse_fqdn = reverse_fqdn
        else:
            PublicIPAddressDnsSettings = cmd.get_models('PublicIPAddressDnsSettings')
            instance.dns_settings = PublicIPAddressDnsSettings(domain_name_label=dns_name, fqdn=None,
                                                               reverse_fqdn=reverse_fqdn)
    if allocation_method is not None:
        instance.public_ip_allocation_method = allocation_method
    if version is not None:
        instance.public_ip_address_version = version
    if idle_timeout is not None:
        instance.idle_timeout_in_minutes = idle_timeout
    if tags is not None:
        instance.tags = tags
    if sku is not None:
        instance.sku.name = sku
    if ip_tags:
        instance.ip_tags = ip_tags
    if public_ip_prefix:
        SubResource = cmd.get_models('SubResource')
        instance.public_ip_prefix = SubResource(id=public_ip_prefix)
    return instance


def create_public_ip_prefix(cmd, client, resource_group_name, public_ip_prefix_name, prefix_length,
                            version=None, location=None, tags=None, zone=None, edge_zone=None,
                            custom_ip_prefix_name=None):
    PublicIPPrefix, PublicIPPrefixSku = cmd.get_models('PublicIPPrefix', 'PublicIPPrefixSku')
    prefix = PublicIPPrefix(
        location=location,
        prefix_length=prefix_length,
        sku=PublicIPPrefixSku(name='Standard'),
        tags=tags,
        zones=zone
    )

    if cmd.supported_api_version(min_api='2019-08-01'):
        prefix.public_ip_address_version = version if version is not None else 'ipv4'

    if cmd.supported_api_version(min_api='2020-06-01') and custom_ip_prefix_name:
        cip_client = network_client_factory(cmd.cli_ctx).custom_ip_prefixes
        try:
            prefix.custom_ip_prefix = cip_client.get(resource_group_name, custom_ip_prefix_name)
        except ResourceNotFoundError:
            raise ResourceNotFoundError('Custom ip prefix {} doesn\'t exist.'.format(custom_ip_prefix_name))

    if edge_zone:
        prefix.extended_location = _edge_zone_model(cmd, edge_zone)
    return client.begin_create_or_update(resource_group_name, public_ip_prefix_name, prefix)


def update_public_ip_prefix(instance, tags=None):
    if tags is not None:
        instance.tags = tags
    return instance
# endregion


# region RouteFilters
def create_route_filter(cmd, client, resource_group_name, route_filter_name, location=None, tags=None):
    RouteFilter = cmd.get_models('RouteFilter')
    return client.begin_create_or_update(resource_group_name, route_filter_name,
                                         RouteFilter(location=location, tags=tags))


def list_route_filters(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)

    return client.list()


def create_route_filter_rule(cmd, client, resource_group_name, route_filter_name, rule_name, access, communities,
                             location=None):
    RouteFilterRule = cmd.get_models('RouteFilterRule')
    return client.begin_create_or_update(resource_group_name, route_filter_name, rule_name,
                                         RouteFilterRule(access=access, communities=communities,
                                                         location=location))

# endregion


# region RouteTables
def create_route_table(cmd, resource_group_name, route_table_name, location=None, tags=None,
                       disable_bgp_route_propagation=None):
    RouteTable = cmd.get_models('RouteTable')
    ncf = network_client_factory(cmd.cli_ctx)
    route_table = RouteTable(location=location, tags=tags)
    if cmd.supported_api_version(min_api='2017-10-01'):
        route_table.disable_bgp_route_propagation = disable_bgp_route_propagation
    return ncf.route_tables.begin_create_or_update(resource_group_name, route_table_name, route_table)


def update_route_table(instance, tags=None, disable_bgp_route_propagation=None):
    if tags == '':
        instance.tags = None
    elif tags is not None:
        instance.tags = tags
    if disable_bgp_route_propagation is not None:
        instance.disable_bgp_route_propagation = disable_bgp_route_propagation
    return instance


def create_route(cmd, resource_group_name, route_table_name, route_name, next_hop_type, address_prefix,
                 next_hop_ip_address=None):
    Route = cmd.get_models('Route')
    route = Route(next_hop_type=next_hop_type, address_prefix=address_prefix,
                  next_hop_ip_address=next_hop_ip_address, name=route_name)
    ncf = network_client_factory(cmd.cli_ctx)
    return ncf.routes.begin_create_or_update(resource_group_name, route_table_name, route_name, route)


def update_route(instance, address_prefix=None, next_hop_type=None, next_hop_ip_address=None):
    if address_prefix is not None:
        instance.address_prefix = address_prefix

    if next_hop_type is not None:
        instance.next_hop_type = next_hop_type

    if next_hop_ip_address is not None:
        instance.next_hop_ip_address = next_hop_ip_address
    return instance
# endregion


# region ServiceEndpoints
def create_service_endpoint_policy(cmd, resource_group_name, service_endpoint_policy_name, location=None, tags=None):
    client = network_client_factory(cmd.cli_ctx).service_endpoint_policies
    ServiceEndpointPolicy = cmd.get_models('ServiceEndpointPolicy')
    policy = ServiceEndpointPolicy(tags=tags, location=location)
    return client.begin_create_or_update(resource_group_name, service_endpoint_policy_name, policy)


def list_service_endpoint_policies(cmd, resource_group_name=None):
    client = network_client_factory(cmd.cli_ctx).service_endpoint_policies
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()


def update_service_endpoint_policy(instance, tags=None):
    if tags is not None:
        instance.tags = tags

    return instance


def create_service_endpoint_policy_definition(cmd, resource_group_name, service_endpoint_policy_name,
                                              service_endpoint_policy_definition_name, service, service_resources,
                                              description=None):
    client = network_client_factory(cmd.cli_ctx).service_endpoint_policy_definitions
    ServiceEndpointPolicyDefinition = cmd.get_models('ServiceEndpointPolicyDefinition')
    policy_def = ServiceEndpointPolicyDefinition(description=description, service=service,
                                                 service_resources=service_resources)
    return client.begin_create_or_update(resource_group_name, service_endpoint_policy_name,
                                         service_endpoint_policy_definition_name, policy_def)


def update_service_endpoint_policy_definition(instance, service=None, service_resources=None, description=None):
    if service is not None:
        instance.service = service

    if service_resources is not None:
        instance.service_resources = service_resources

    if description is not None:
        instance.description = description

    return instance
# endregion


# region TrafficManagers
def list_traffic_manager_profiles(cmd, resource_group_name=None):
    from azure.mgmt.trafficmanager import TrafficManagerManagementClient
    client = get_mgmt_service_client(cmd.cli_ctx, TrafficManagerManagementClient).profiles
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)

    return client.list_by_subscription()


def create_traffic_manager_profile(cmd, traffic_manager_profile_name, resource_group_name,
                                   routing_method, unique_dns_name, monitor_path=None,
                                   monitor_port=80, monitor_protocol=MonitorProtocol.http.value,
                                   profile_status=ProfileStatus.enabled.value,
                                   ttl=30, tags=None, interval=None, timeout=None, max_failures=None,
                                   monitor_custom_headers=None, status_code_ranges=None, max_return=None):
    from azure.mgmt.trafficmanager import TrafficManagerManagementClient
    from azure.mgmt.trafficmanager.models import Profile, DnsConfig, MonitorConfig
    client = get_mgmt_service_client(cmd.cli_ctx, TrafficManagerManagementClient).profiles
    if monitor_path is None and monitor_protocol == 'HTTP':
        monitor_path = '/'
    profile = Profile(location='global', tags=tags, profile_status=profile_status,
                      traffic_routing_method=routing_method,
                      dns_config=DnsConfig(relative_name=unique_dns_name, ttl=ttl),
                      monitor_config=MonitorConfig(protocol=monitor_protocol,
                                                   port=monitor_port,
                                                   path=monitor_path,
                                                   interval_in_seconds=interval,
                                                   timeout_in_seconds=timeout,
                                                   tolerated_number_of_failures=max_failures,
                                                   custom_headers=monitor_custom_headers,
                                                   expected_status_code_ranges=status_code_ranges),
                      max_return=max_return)
    return client.create_or_update(resource_group_name, traffic_manager_profile_name, profile)


def update_traffic_manager_profile(instance, profile_status=None, routing_method=None, tags=None,
                                   monitor_protocol=None, monitor_port=None, monitor_path=None,
                                   ttl=None, timeout=None, interval=None, max_failures=None,
                                   monitor_custom_headers=None, status_code_ranges=None, max_return=None):
    if tags is not None:
        instance.tags = tags
    if profile_status is not None:
        instance.profile_status = profile_status
    if routing_method is not None:
        instance.traffic_routing_method = routing_method
    if ttl is not None:
        instance.dns_config.ttl = ttl

    if monitor_protocol is not None:
        instance.monitor_config.protocol = monitor_protocol
    if monitor_port is not None:
        instance.monitor_config.port = monitor_port
    if monitor_path == '':
        instance.monitor_config.path = None
    elif monitor_path is not None:
        instance.monitor_config.path = monitor_path
    if interval is not None:
        instance.monitor_config.interval_in_seconds = interval
    if timeout is not None:
        instance.monitor_config.timeout_in_seconds = timeout
    if max_failures is not None:
        instance.monitor_config.tolerated_number_of_failures = max_failures
    if monitor_custom_headers is not None:
        instance.monitor_config.custom_headers = monitor_custom_headers
    if status_code_ranges is not None:
        instance.monitor_config.expected_status_code_ranges = status_code_ranges
    if max_return is not None:
        instance.max_return = max_return

    # TODO: Remove workaround after https://github.com/Azure/azure-rest-api-specs/issues/1940 fixed
    for endpoint in instance.endpoints:
        endpoint._validation = {  # pylint: disable=protected-access
            'name': {'readonly': False},
            'type': {'readonly': False},
        }
    return instance


def create_traffic_manager_endpoint(cmd, resource_group_name, profile_name, endpoint_type, endpoint_name,
                                    target_resource_id=None, target=None,
                                    endpoint_status=None, weight=None, priority=None,
                                    endpoint_location=None, endpoint_monitor_status=None,
                                    min_child_endpoints=None, min_child_ipv4=None, min_child_ipv6=None,
                                    geo_mapping=None, monitor_custom_headers=None, subnets=None):
    from azure.mgmt.trafficmanager import TrafficManagerManagementClient
    from azure.mgmt.trafficmanager.models import Endpoint
    ncf = get_mgmt_service_client(cmd.cli_ctx, TrafficManagerManagementClient).endpoints

    endpoint = Endpoint(target_resource_id=target_resource_id, target=target,
                        endpoint_status=endpoint_status, weight=weight, priority=priority,
                        endpoint_location=endpoint_location,
                        endpoint_monitor_status=endpoint_monitor_status,
                        min_child_endpoints=min_child_endpoints,
                        min_child_endpoints_i_pv4=min_child_ipv4,
                        min_child_endpoints_i_pv6=min_child_ipv6,
                        geo_mapping=geo_mapping,
                        subnets=subnets,
                        custom_headers=monitor_custom_headers)

    return ncf.create_or_update(resource_group_name, profile_name, endpoint_type, endpoint_name,
                                endpoint)


def update_traffic_manager_endpoint(instance, endpoint_type, endpoint_location=None,
                                    endpoint_status=None, endpoint_monitor_status=None,
                                    priority=None, target=None, target_resource_id=None,
                                    weight=None, min_child_endpoints=None, min_child_ipv4=None,
                                    min_child_ipv6=None, geo_mapping=None,
                                    subnets=None, monitor_custom_headers=None):
    if endpoint_location is not None:
        instance.endpoint_location = endpoint_location
    if endpoint_status is not None:
        instance.endpoint_status = endpoint_status
    if endpoint_monitor_status is not None:
        instance.endpoint_monitor_status = endpoint_monitor_status
    if priority is not None:
        instance.priority = priority
    if target is not None:
        instance.target = target
    if target_resource_id is not None:
        instance.target_resource_id = target_resource_id
    if weight is not None:
        instance.weight = weight
    if min_child_endpoints is not None:
        instance.min_child_endpoints = min_child_endpoints
    if min_child_ipv4 is not None:
        instance.min_child_endpoints_i_pv4 = min_child_ipv4
    if min_child_ipv6 is not None:
        instance.min_child_endpoints_i_pv6 = min_child_ipv6
    if geo_mapping is not None:
        instance.geo_mapping = geo_mapping
    if subnets is not None:
        instance.subnets = subnets
    if monitor_custom_headers:
        instance.custom_headers = monitor_custom_headers

    return instance


def list_traffic_manager_endpoints(cmd, resource_group_name, profile_name, endpoint_type=None):
    from azure.mgmt.trafficmanager import TrafficManagerManagementClient
    client = get_mgmt_service_client(cmd.cli_ctx, TrafficManagerManagementClient).profiles
    profile = client.get(resource_group_name, profile_name)
    return [e for e in profile.endpoints if not endpoint_type or e.type.endswith(endpoint_type)]


def check_traffic_manager_name(cmd, client, name):
    from azure.mgmt.trafficmanager.models import CheckTrafficManagerRelativeDnsNameAvailabilityParameters
    checknameParameters = CheckTrafficManagerRelativeDnsNameAvailabilityParameters(name=name, type='Microsoft.Network/trafficManagerProfiles')
    return client.check_traffic_manager_relative_dns_name_availability(checknameParameters)

# endregion


# region VirtualNetworks
# pylint: disable=too-many-locals
def create_vnet(cmd, resource_group_name, vnet_name, vnet_prefixes='10.0.0.0/16',
                subnet_name=None, subnet_prefix=None, dns_servers=None,
                location=None, tags=None, vm_protection=None, ddos_protection=None, bgp_community=None,
                ddos_protection_plan=None, network_security_group=None, edge_zone=None, flowtimeout=None,
                enable_encryption=None, encryption_enforcement_policy=None):
    AddressSpace, DhcpOptions, Subnet, VirtualNetwork, SubResource, NetworkSecurityGroup = \
        cmd.get_models('AddressSpace', 'DhcpOptions', 'Subnet', 'VirtualNetwork',
                       'SubResource', 'NetworkSecurityGroup')
    client = network_client_factory(cmd.cli_ctx).virtual_networks
    tags = tags or {}

    vnet = VirtualNetwork(
        location=location, tags=tags,
        dhcp_options=DhcpOptions(dns_servers=dns_servers),
        address_space=AddressSpace(address_prefixes=(vnet_prefixes if isinstance(vnet_prefixes, list) else [vnet_prefixes])))  # pylint: disable=line-too-long
    if subnet_name:
        if cmd.supported_api_version(min_api='2018-08-01'):
            vnet.subnets = [Subnet(name=subnet_name,
                                   address_prefix=subnet_prefix[0] if len(subnet_prefix) == 1 else None,
                                   address_prefixes=subnet_prefix if len(subnet_prefix) > 1 else None,
                                   network_security_group=NetworkSecurityGroup(id=network_security_group)
                                   if network_security_group else None)]
        else:
            vnet.subnets = [Subnet(name=subnet_name, address_prefix=subnet_prefix)]
    if cmd.supported_api_version(min_api='2017-09-01'):
        vnet.enable_ddos_protection = ddos_protection
        vnet.enable_vm_protection = vm_protection
    if cmd.supported_api_version(min_api='2018-02-01'):
        vnet.ddos_protection_plan = SubResource(id=ddos_protection_plan) if ddos_protection_plan else None
    if edge_zone:
        vnet.extended_location = _edge_zone_model(cmd, edge_zone)
    if flowtimeout is not None:
        vnet.flow_timeout_in_minutes = flowtimeout
    if bgp_community is not None and cmd.supported_api_version(min_api='2020-06-01'):
        VirtualNetworkBgpCommunities = cmd.get_models('VirtualNetworkBgpCommunities')
        vnet.bgp_communities = VirtualNetworkBgpCommunities(virtual_network_community=bgp_community)
    if enable_encryption is not None:
        if not vnet.encryption:
            vnet.encryption = {}
        vnet.encryption["enabled"] = enable_encryption
    if encryption_enforcement_policy is not None:
        if not vnet.encryption:
            raise ArgumentUsageError('usage error: --encryption--enforcement--policy is only configurable when '
                                     '--enable-encryption is specified.')
        vnet.encryption["enforcement"] = encryption_enforcement_policy
    return cached_put(cmd, client.begin_create_or_update, vnet, resource_group_name, vnet_name)


def update_vnet(cmd, instance, vnet_prefixes=None, dns_servers=None, ddos_protection=None, vm_protection=None,
                ddos_protection_plan=None, flowtimeout=None, bgp_community=None, enable_encryption=None,
                encryption_enforcement_policy=None):
    # server side validation reports pretty good error message on invalid CIDR,
    # so we don't validate at client side
    AddressSpace, DhcpOptions, SubResource = cmd.get_models('AddressSpace', 'DhcpOptions', 'SubResource')
    if vnet_prefixes and instance.address_space:
        instance.address_space.address_prefixes = vnet_prefixes
    elif vnet_prefixes:
        instance.address_space = AddressSpace(address_prefixes=vnet_prefixes)

    if dns_servers == ['']:
        instance.dhcp_options.dns_servers = None
    elif dns_servers and instance.dhcp_options:
        instance.dhcp_options.dns_servers = dns_servers
    elif dns_servers:
        instance.dhcp_options = DhcpOptions(dns_servers=dns_servers)

    if ddos_protection is not None:
        instance.enable_ddos_protection = ddos_protection
    if vm_protection is not None:
        instance.enable_vm_protection = vm_protection
    if ddos_protection_plan == '':
        instance.ddos_protection_plan = None
    elif ddos_protection_plan is not None:
        instance.ddos_protection_plan = SubResource(id=ddos_protection_plan)
    if flowtimeout is not None:
        instance.flow_timeout_in_minutes = flowtimeout
    if bgp_community is not None and cmd.supported_api_version(min_api='2020-06-01'):
        VirtualNetworkBgpCommunities = cmd.get_models('VirtualNetworkBgpCommunities')
        instance.bgp_communities = VirtualNetworkBgpCommunities(virtual_network_community=bgp_community)
    if enable_encryption is not None:
        if not instance.encryption:
            VirtualNetworkEncryption = cmd.get_models('VirtualNetworkEncryption')
            instance.encryption = VirtualNetworkEncryption(enabled=enable_encryption)
        instance.encryption.enabled = enable_encryption
    if encryption_enforcement_policy is not None:
        if not instance.encryption:
            raise ArgumentUsageError('usage error: --encryption--enforcement--policy is only configurable when '
                                     '--enable-encryption is specified.')
        instance.encryption.enforcement = encryption_enforcement_policy
    return instance


def _set_route_table(ncf, resource_group_name, route_table, subnet):
    if route_table:
        is_id = is_valid_resource_id(route_table)
        rt = None
        if is_id:
            res_id = parse_resource_id(route_table)
            rt = ncf.route_tables.get(res_id['resource_group'], res_id['name'])
        else:
            rt = ncf.route_tables.get(resource_group_name, route_table)
        subnet.route_table = rt
    elif route_table == '':
        subnet.route_table = None


def create_subnet(cmd, resource_group_name, virtual_network_name, subnet_name,
                  address_prefix, network_security_group=None,
                  route_table=None, service_endpoints=None, service_endpoint_policy=None,
                  delegations=None, nat_gateway=None,
                  disable_private_endpoint_network_policies=None,
                  disable_private_link_service_network_policies=None):
    NetworkSecurityGroup, ServiceEndpoint, Subnet, SubResource = cmd.get_models(
        'NetworkSecurityGroup', 'ServiceEndpointPropertiesFormat', 'Subnet', 'SubResource')
    ncf = network_client_factory(cmd.cli_ctx)

    if cmd.supported_api_version(min_api='2018-08-01'):
        subnet = Subnet(
            name=subnet_name,
            address_prefixes=address_prefix if len(address_prefix) > 1 else None,
            address_prefix=address_prefix[0] if len(address_prefix) == 1 else None
        )
        if cmd.supported_api_version(min_api='2019-02-01') and nat_gateway:
            subnet.nat_gateway = SubResource(id=nat_gateway)
    else:
        subnet = Subnet(name=subnet_name, address_prefix=address_prefix)

    if network_security_group:
        subnet.network_security_group = NetworkSecurityGroup(id=network_security_group)
    _set_route_table(ncf, resource_group_name, route_table, subnet)
    if service_endpoints:
        subnet.service_endpoints = []
        for service in service_endpoints:
            subnet.service_endpoints.append(ServiceEndpoint(service=service))
    if service_endpoint_policy:
        subnet.service_endpoint_policies = []
        for policy in service_endpoint_policy:
            subnet.service_endpoint_policies.append(SubResource(id=policy))
    if delegations:
        subnet.delegations = delegations

    if disable_private_endpoint_network_policies is True:
        subnet.private_endpoint_network_policies = "Disabled"
    if disable_private_endpoint_network_policies is False:
        subnet.private_endpoint_network_policies = "Enabled"

    if disable_private_link_service_network_policies is True:
        subnet.private_link_service_network_policies = "Disabled"
    if disable_private_link_service_network_policies is False:
        subnet.private_link_service_network_policies = "Enabled"

    vnet = cached_get(cmd, ncf.virtual_networks.get, resource_group_name, virtual_network_name)
    upsert_to_collection(vnet, 'subnets', subnet, 'name')
    vnet = cached_put(
        cmd, ncf.virtual_networks.begin_create_or_update, vnet, resource_group_name, virtual_network_name).result()
    return get_property(vnet.subnets, subnet_name)


def update_subnet(cmd, instance, resource_group_name, address_prefix=None, network_security_group=None,
                  route_table=None, service_endpoints=None, delegations=None, nat_gateway=None,
                  service_endpoint_policy=None, disable_private_endpoint_network_policies=None,
                  disable_private_link_service_network_policies=None):
    NetworkSecurityGroup, ServiceEndpoint, SubResource = cmd.get_models(
        'NetworkSecurityGroup', 'ServiceEndpointPropertiesFormat', 'SubResource')

    if address_prefix:
        if cmd.supported_api_version(min_api='2018-08-01'):
            instance.address_prefixes = address_prefix if len(address_prefix) > 1 else None
            instance.address_prefix = address_prefix[0] if len(address_prefix) == 1 else None
        else:
            instance.address_prefix = address_prefix

    if cmd.supported_api_version(min_api='2019-02-01') and nat_gateway:
        instance.nat_gateway = SubResource(id=nat_gateway)
    elif nat_gateway == '':
        instance.nat_gateway = None

    if network_security_group:
        instance.network_security_group = NetworkSecurityGroup(id=network_security_group)
    elif network_security_group == '':  # clear it
        instance.network_security_group = None

    _set_route_table(network_client_factory(cmd.cli_ctx), resource_group_name, route_table, instance)

    if service_endpoints == ['']:
        instance.service_endpoints = None
    elif service_endpoints:
        instance.service_endpoints = []
        for service in service_endpoints:
            instance.service_endpoints.append(ServiceEndpoint(service=service))

    if service_endpoint_policy == '':
        instance.service_endpoint_policies = None
    elif service_endpoint_policy:
        instance.service_endpoint_policies = []
        for policy in service_endpoint_policy:
            instance.service_endpoint_policies.append(SubResource(id=policy))

    if delegations:
        instance.delegations = delegations

    if disable_private_endpoint_network_policies:
        instance.private_endpoint_network_policies = "Disabled"
    elif disable_private_endpoint_network_policies is not None:
        instance.private_endpoint_network_policies = "Enabled"

    if disable_private_link_service_network_policies:
        instance.private_link_service_network_policies = "Disabled"
    elif disable_private_link_service_network_policies is not None:
        instance.private_link_service_network_policies = "Enabled"

    return instance


def list_avail_subnet_delegations(cmd, resource_group_name=None, location=None):
    client = network_client_factory(cmd.cli_ctx)
    if resource_group_name:
        return client.available_resource_group_delegations.list(location, resource_group_name)
    return client.available_delegations.list(location)


def create_vnet_peering(cmd, resource_group_name, virtual_network_name, virtual_network_peering_name,
                        remote_virtual_network, allow_virtual_network_access=False,
                        allow_forwarded_traffic=False, allow_gateway_transit=False,
                        use_remote_gateways=False):
    if not is_valid_resource_id(remote_virtual_network):
        remote_virtual_network = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=remote_virtual_network
        )
    SubResource, VirtualNetworkPeering = cmd.get_models('SubResource', 'VirtualNetworkPeering')
    peering = VirtualNetworkPeering(
        id=resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=virtual_network_name),
        name=virtual_network_peering_name,
        remote_virtual_network=SubResource(id=remote_virtual_network),
        allow_virtual_network_access=allow_virtual_network_access,
        allow_gateway_transit=allow_gateway_transit,
        allow_forwarded_traffic=allow_forwarded_traffic,
        use_remote_gateways=use_remote_gateways)
    aux_subscription = parse_resource_id(remote_virtual_network)['subscription']
    ncf = network_client_factory(cmd.cli_ctx, aux_subscriptions=[aux_subscription])
    return ncf.virtual_network_peerings.begin_create_or_update(
        resource_group_name, virtual_network_name, virtual_network_peering_name, peering)


def sync_vnet_peering(cmd, resource_group_name, virtual_network_name, virtual_network_peering_name):
    subscription_id = get_subscription_id(cmd.cli_ctx)
    ncf = network_client_factory(cmd.cli_ctx, aux_subscriptions=[subscription_id])

    try:
        peering = ncf.virtual_network_peerings.get(resource_group_name, virtual_network_name, virtual_network_peering_name)
    except ResourceNotFoundError:
        raise ResourceNotFoundError('Virtual network peering {} doesn\'t exist.'.format(virtual_network_peering_name))

    return ncf.virtual_network_peerings.begin_create_or_update(
        resource_group_name, virtual_network_name, virtual_network_peering_name, peering, sync_remote_address_space=True)


def update_vnet_peering(cmd, resource_group_name, virtual_network_name, virtual_network_peering_name, **kwargs):
    peering = kwargs['parameters']
    aux_subscription = parse_resource_id(peering.remote_virtual_network.id)['subscription']
    ncf = network_client_factory(cmd.cli_ctx, aux_subscriptions=[aux_subscription])
    return ncf.virtual_network_peerings.begin_create_or_update(
        resource_group_name, virtual_network_name, virtual_network_peering_name, peering)


def list_available_ips(cmd, resource_group_name, virtual_network_name):
    client = network_client_factory(cmd.cli_ctx).virtual_networks
    vnet = client.get(resource_group_name=resource_group_name,
                      virtual_network_name=virtual_network_name)
    start_ip = vnet.address_space.address_prefixes[0].split('/')[0]
    available_ips = client.check_ip_address_availability(resource_group_name=resource_group_name,
                                                         virtual_network_name=virtual_network_name,
                                                         ip_address=start_ip)
    return available_ips.available_ip_addresses

# endregion


# region VirtualNetworkGateways
def create_vnet_gateway_root_cert(cmd, resource_group_name, gateway_name, public_cert_data, cert_name):
    VpnClientRootCertificate = cmd.get_models('VpnClientRootCertificate')
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)
    if not gateway.vpn_client_configuration:
        raise CLIError("Must add address prefixes to gateway '{}' prior to adding a root cert."
                       .format(gateway_name))
    config = gateway.vpn_client_configuration

    if config.vpn_client_root_certificates is None:
        config.vpn_client_root_certificates = []

    cert = VpnClientRootCertificate(name=cert_name, public_cert_data=public_cert_data)
    upsert_to_collection(config, 'vpn_client_root_certificates', cert, 'name')
    return ncf.begin_create_or_update(resource_group_name, gateway_name, gateway)


def delete_vnet_gateway_root_cert(cmd, resource_group_name, gateway_name, cert_name):
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)
    config = gateway.vpn_client_configuration

    try:
        cert = next(c for c in config.vpn_client_root_certificates if c.name == cert_name)
    except (AttributeError, StopIteration):
        raise CLIError('Certificate "{}" not found in gateway "{}"'.format(cert_name, gateway_name))
    config.vpn_client_root_certificates.remove(cert)

    return ncf.begin_create_or_update(resource_group_name, gateway_name, gateway)


def create_vnet_gateway_revoked_cert(cmd, resource_group_name, gateway_name, thumbprint, cert_name):
    VpnClientRevokedCertificate = cmd.get_models('VpnClientRevokedCertificate')
    config, gateway, ncf = _prep_cert_create(cmd, gateway_name, resource_group_name)

    cert = VpnClientRevokedCertificate(name=cert_name, thumbprint=thumbprint)
    upsert_to_collection(config, 'vpn_client_revoked_certificates', cert, 'name')
    return ncf.begin_create_or_update(resource_group_name, gateway_name, gateway)


def delete_vnet_gateway_revoked_cert(cmd, resource_group_name, gateway_name, cert_name):
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)
    config = gateway.vpn_client_configuration

    try:
        cert = next(c for c in config.vpn_client_revoked_certificates if c.name == cert_name)
    except (AttributeError, StopIteration):
        raise CLIError('Certificate "{}" not found in gateway "{}"'.format(cert_name, gateway_name))
    config.vpn_client_revoked_certificates.remove(cert)

    return ncf.begin_create_or_update(resource_group_name, gateway_name, gateway)


def _prep_cert_create(cmd, gateway_name, resource_group_name):
    VpnClientConfiguration = cmd.get_models('VpnClientConfiguration')
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)
    if not gateway.vpn_client_configuration:
        gateway.vpn_client_configuration = VpnClientConfiguration()
    config = gateway.vpn_client_configuration

    if not config.vpn_client_address_pool or not config.vpn_client_address_pool.address_prefixes:
        raise CLIError('Address prefixes must be set on VPN gateways before adding'
                       ' certificates.  Please use "update" with --address-prefixes first.')

    if config.vpn_client_revoked_certificates is None:
        config.vpn_client_revoked_certificates = []
    if config.vpn_client_root_certificates is None:
        config.vpn_client_root_certificates = []

    return config, gateway, ncf


def create_vnet_gateway(cmd, resource_group_name, virtual_network_gateway_name, public_ip_address,
                        virtual_network, location=None, tags=None,
                        no_wait=False, gateway_type=None, sku=None, vpn_type=None, vpn_gateway_generation=None,
                        asn=None, bgp_peering_address=None, peer_weight=None,
                        address_prefixes=None, radius_server=None, radius_secret=None, client_protocol=None,
                        gateway_default_site=None, custom_routes=None, aad_tenant=None, aad_audience=None,
                        aad_issuer=None, root_cert_data=None, root_cert_name=None, vpn_auth_type=None, edge_zone=None,
                        nat_rule=None):
    (VirtualNetworkGateway, BgpSettings, SubResource, VirtualNetworkGatewayIPConfiguration, VirtualNetworkGatewaySku,
     VpnClientConfiguration, AddressSpace, VpnClientRootCertificate, VirtualNetworkGatewayNatRule,
     VpnNatRuleMapping) = cmd.get_models(
         'VirtualNetworkGateway', 'BgpSettings', 'SubResource', 'VirtualNetworkGatewayIPConfiguration',
         'VirtualNetworkGatewaySku', 'VpnClientConfiguration', 'AddressSpace', 'VpnClientRootCertificate',
         'VirtualNetworkGatewayNatRule', 'VpnNatRuleMapping')

    client = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    subnet = virtual_network + '/subnets/GatewaySubnet'
    active = len(public_ip_address) == 2
    vnet_gateway = VirtualNetworkGateway(
        gateway_type=gateway_type, vpn_type=vpn_type, vpn_gateway_generation=vpn_gateway_generation, location=location,
        tags=tags, sku=VirtualNetworkGatewaySku(name=sku, tier=sku), active=active, ip_configurations=[],
        gateway_default_site=SubResource(id=gateway_default_site) if gateway_default_site else None)
    for i, public_ip in enumerate(public_ip_address):
        ip_configuration = VirtualNetworkGatewayIPConfiguration(
            subnet=SubResource(id=subnet),
            public_ip_address=SubResource(id=public_ip),
            private_ip_allocation_method='Dynamic',
            name='vnetGatewayConfig{}'.format(i)
        )
        vnet_gateway.ip_configurations.append(ip_configuration)
    if asn or bgp_peering_address or peer_weight:
        vnet_gateway.enable_bgp = True
        vnet_gateway.bgp_settings = BgpSettings(asn=asn, bgp_peering_address=bgp_peering_address,
                                                peer_weight=peer_weight)

    if any((address_prefixes, client_protocol)):
        vnet_gateway.vpn_client_configuration = VpnClientConfiguration()
        vnet_gateway.vpn_client_configuration.vpn_client_address_pool = AddressSpace()
        vnet_gateway.vpn_client_configuration.vpn_client_address_pool.address_prefixes = address_prefixes
        vnet_gateway.vpn_client_configuration.vpn_client_protocols = client_protocol
        if any((radius_secret, radius_server)) and cmd.supported_api_version(min_api='2017-06-01'):
            vnet_gateway.vpn_client_configuration.radius_server_address = radius_server
            vnet_gateway.vpn_client_configuration.radius_server_secret = radius_secret

        # multi authentication
        if cmd.supported_api_version(min_api='2020-11-01'):
            vnet_gateway.vpn_client_configuration.vpn_authentication_types = vpn_auth_type
            vnet_gateway.vpn_client_configuration.aad_tenant = aad_tenant
            vnet_gateway.vpn_client_configuration.aad_issuer = aad_issuer
            vnet_gateway.vpn_client_configuration.aad_audience = aad_audience
            vnet_gateway.vpn_client_configuration.vpn_client_root_certificates = [
                VpnClientRootCertificate(name=root_cert_name,
                                         public_cert_data=root_cert_data)] if root_cert_data else None

    if custom_routes and cmd.supported_api_version(min_api='2019-02-01'):
        vnet_gateway.custom_routes = AddressSpace()
        vnet_gateway.custom_routes.address_prefixes = custom_routes

    if edge_zone:
        vnet_gateway.extended_location = _edge_zone_model(cmd, edge_zone)
    if nat_rule:
        vnet_gateway.nat_rules = [
            VirtualNetworkGatewayNatRule(type_properties_type=rule.get('type'), mode=rule.get('mode'), name=rule.get('name'),
                                         internal_mappings=[VpnNatRuleMapping(address_space=i_map) for i_map in rule.get('internal_mappings')] if rule.get('internal_mappings') else None,
                                         external_mappings=[VpnNatRuleMapping(address_space=i_map) for i_map in rule.get('external_mappings')] if rule.get('external_mappings') else None,
                                         ip_configuration_id=rule.get('ip_config_id')) for rule in nat_rule]

    return sdk_no_wait(no_wait, client.begin_create_or_update,
                       resource_group_name, virtual_network_gateway_name, vnet_gateway)


def update_vnet_gateway(cmd, instance, sku=None, vpn_type=None, tags=None,
                        public_ip_address=None, gateway_type=None, enable_bgp=None,
                        asn=None, bgp_peering_address=None, peer_weight=None, virtual_network=None,
                        address_prefixes=None, radius_server=None, radius_secret=None, client_protocol=None,
                        gateway_default_site=None, custom_routes=None, aad_tenant=None, aad_audience=None,
                        aad_issuer=None, root_cert_data=None, root_cert_name=None, vpn_auth_type=None):
    (AddressSpace, SubResource, VirtualNetworkGatewayIPConfiguration, VpnClientConfiguration,
     VpnClientRootCertificate) = cmd.get_models('AddressSpace', 'SubResource', 'VirtualNetworkGatewayIPConfiguration',
                                                'VpnClientConfiguration', 'VpnClientRootCertificate')

    if any((address_prefixes, radius_server, radius_secret, client_protocol)) and not instance.vpn_client_configuration:
        instance.vpn_client_configuration = VpnClientConfiguration()

    if address_prefixes is not None:
        if not instance.vpn_client_configuration.vpn_client_address_pool:
            instance.vpn_client_configuration.vpn_client_address_pool = AddressSpace()
        if not instance.vpn_client_configuration.vpn_client_address_pool.address_prefixes:
            instance.vpn_client_configuration.vpn_client_address_pool.address_prefixes = []
        instance.vpn_client_configuration.vpn_client_address_pool.address_prefixes = address_prefixes

    with cmd.update_context(instance.vpn_client_configuration) as c:
        c.set_param('vpn_client_protocols', client_protocol)
        c.set_param('radius_server_address', radius_server)
        c.set_param('radius_server_secret', radius_secret)
        if cmd.supported_api_version(min_api='2020-11-01'):
            c.set_param('aad_tenant', aad_tenant)
            c.set_param('aad_audience', aad_audience)
            c.set_param('aad_issuer', aad_issuer)
            c.set_param('vpn_authentication_types', vpn_auth_type)

    if root_cert_data and cmd.supported_api_version(min_api='2020-11-01'):
        upsert_to_collection(instance.vpn_client_configuration, 'vpn_client_root_certificates',
                             VpnClientRootCertificate(name=root_cert_name, public_cert_data=root_cert_data), 'name')

    with cmd.update_context(instance.sku) as c:
        c.set_param('name', sku)
        c.set_param('tier', sku)

    with cmd.update_context(instance) as c:
        c.set_param('gateway_default_site', SubResource(id=gateway_default_site) if gateway_default_site else None)
        c.set_param('vpn_type', vpn_type)
        c.set_param('tags', tags)

    subnet_id = '{}/subnets/GatewaySubnet'.format(virtual_network) if virtual_network else \
        instance.ip_configurations[0].subnet.id
    if virtual_network is not None:
        for config in instance.ip_configurations:
            config.subnet.id = subnet_id

    if public_ip_address is not None:
        instance.ip_configurations = []
        for i, public_ip in enumerate(public_ip_address):
            ip_configuration = VirtualNetworkGatewayIPConfiguration(
                subnet=SubResource(id=subnet_id),
                public_ip_address=SubResource(id=public_ip),
                private_ip_allocation_method='Dynamic', name='vnetGatewayConfig{}'.format(i))
            instance.ip_configurations.append(ip_configuration)

        # Update active-active/active-standby status
        active = len(public_ip_address) == 2
        if instance.active and not active:
            logger.info('Placing gateway in active-standby mode.')
        elif not instance.active and active:
            logger.info('Placing gateway in active-active mode.')
        instance.active = active

    if gateway_type is not None:
        instance.gateway_type = gateway_type

    if enable_bgp is not None:
        instance.enable_bgp = enable_bgp.lower() == 'true'

    if custom_routes and cmd.supported_api_version(min_api='2019-02-01'):
        if not instance.custom_routes:
            instance.custom_routes = AddressSpace()
        instance.custom_routes.address_prefixes = custom_routes

    _validate_bgp_peering(cmd, instance, asn, bgp_peering_address, peer_weight)

    return instance


def start_vnet_gateway_package_capture(cmd, client, resource_group_name, virtual_network_gateway_name,
                                       filter_data=None, no_wait=False):
    VpnPacketCaptureStartParameters = cmd.get_models('VpnPacketCaptureStartParameters')
    parameters = VpnPacketCaptureStartParameters(filter_data=filter_data)
    return sdk_no_wait(no_wait, client.begin_start_packet_capture, resource_group_name,
                       virtual_network_gateway_name, parameters=parameters)


def stop_vnet_gateway_package_capture(cmd, client, resource_group_name, virtual_network_gateway_name,
                                      sas_url, no_wait=False):
    VpnPacketCaptureStopParameters = cmd.get_models('VpnPacketCaptureStopParameters')
    parameters = VpnPacketCaptureStopParameters(sas_url=sas_url)
    return sdk_no_wait(no_wait, client.begin_stop_packet_capture, resource_group_name,
                       virtual_network_gateway_name, parameters=parameters)


def generate_vpn_client(cmd, client, resource_group_name, virtual_network_gateway_name, processor_architecture=None,
                        authentication_method=None, radius_server_auth_certificate=None, client_root_certificates=None,
                        use_legacy=False):
    params = cmd.get_models('VpnClientParameters')(
        processor_architecture=processor_architecture
    )

    if cmd.supported_api_version(min_api='2017-06-01') and not use_legacy:
        params.authentication_method = authentication_method
        params.radius_server_auth_certificate = radius_server_auth_certificate
        params.client_root_certificates = client_root_certificates
        return client.begin_generate_vpn_profile(resource_group_name, virtual_network_gateway_name, params)
    # legacy implementation
    return client.begin_generatevpnclientpackage(resource_group_name, virtual_network_gateway_name, params)


def set_vpn_client_ipsec_policy(cmd, client, resource_group_name, virtual_network_gateway_name,
                                sa_life_time_seconds, sa_data_size_kilobytes,
                                ipsec_encryption, ipsec_integrity,
                                ike_encryption, ike_integrity, dh_group, pfs_group, no_wait=False):
    VpnClientIPsecParameters = cmd.get_models('VpnClientIPsecParameters')
    vpnclient_ipsec_params = VpnClientIPsecParameters(sa_life_time_seconds=sa_life_time_seconds,
                                                      sa_data_size_kilobytes=sa_data_size_kilobytes,
                                                      ipsec_encryption=ipsec_encryption,
                                                      ipsec_integrity=ipsec_integrity,
                                                      ike_encryption=ike_encryption,
                                                      ike_integrity=ike_integrity,
                                                      dh_group=dh_group,
                                                      pfs_group=pfs_group)
    return sdk_no_wait(no_wait, client.begin_set_vpnclient_ipsec_parameters, resource_group_name,
                       virtual_network_gateway_name, vpnclient_ipsec_params)


def disconnect_vnet_gateway_vpn_connections(cmd, client, resource_group_name, virtual_network_gateway_name,
                                            vpn_connection_ids, no_wait=False):
    P2SVpnConnectionRequest = cmd.get_models('P2SVpnConnectionRequest')
    request = P2SVpnConnectionRequest(vpn_connection_ids=vpn_connection_ids)
    return sdk_no_wait(no_wait, client.begin_disconnect_virtual_network_gateway_vpn_connections,
                       resource_group_name, virtual_network_gateway_name, request)

# endregion


# region VirtualNetworkGatewayConnections
# pylint: disable=too-many-locals
def create_vpn_connection(cmd, resource_group_name, connection_name, vnet_gateway1,
                          location=None, tags=None, no_wait=False, validate=False,
                          vnet_gateway2=None, express_route_circuit2=None, local_gateway2=None,
                          authorization_key=None, enable_bgp=False, routing_weight=10,
                          connection_type=None, shared_key=None,
                          use_policy_based_traffic_selectors=False,
                          express_route_gateway_bypass=None, ingress_nat_rule=None, egress_nat_rule=None):
    from azure.cli.core.util import random_string
    from azure.cli.core.commands.arm import ArmTemplateBuilder
    from azure.cli.command_modules.network._template_builder import build_vpn_connection_resource

    client = network_client_factory(cmd.cli_ctx).virtual_network_gateway_connections
    DeploymentProperties = cmd.get_models('DeploymentProperties', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    tags = tags or {}

    # Build up the ARM template
    master_template = ArmTemplateBuilder()
    vpn_connection_resource = build_vpn_connection_resource(
        cmd, connection_name, location, tags, vnet_gateway1,
        vnet_gateway2 or local_gateway2 or express_route_circuit2,
        connection_type, authorization_key, enable_bgp, routing_weight, shared_key,
        use_policy_based_traffic_selectors, express_route_gateway_bypass, ingress_nat_rule, egress_nat_rule)
    master_template.add_resource(vpn_connection_resource)
    master_template.add_output('resource', connection_name, output_type='object')
    if shared_key:
        master_template.add_secure_parameter('sharedKey', shared_key)
    if authorization_key:
        master_template.add_secure_parameter('authorizationKey', authorization_key)

    template = master_template.build()
    parameters = master_template.build_parameters()

    # deploy ARM template
    deployment_name = 'vpn_connection_deploy_' + random_string(32)
    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES).deployments
    properties = DeploymentProperties(template=template, parameters=parameters, mode='incremental')
    Deployment = cmd.get_models('Deployment', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    deployment = Deployment(properties=properties)

    if validate:
        _log_pprint_template(template)
        if cmd.supported_api_version(min_api='2019-10-01', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES):
            from azure.cli.core.commands import LongRunningOperation
            validation_poller = client.begin_validate(resource_group_name, deployment_name, deployment)
            return LongRunningOperation(cmd.cli_ctx)(validation_poller)

        return client.validate(resource_group_name, deployment_name, deployment)

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, deployment_name, deployment)


def update_vpn_connection(cmd, instance, routing_weight=None, shared_key=None, tags=None,
                          enable_bgp=None, use_policy_based_traffic_selectors=None,
                          express_route_gateway_bypass=None):

    with cmd.update_context(instance) as c:
        c.set_param('routing_weight', routing_weight)
        c.set_param('shared_key', shared_key)
        c.set_param('tags', tags)
        c.set_param('enable_bgp', enable_bgp)
        c.set_param('express_route_gateway_bypass', express_route_gateway_bypass)
        c.set_param('use_policy_based_traffic_selectors', use_policy_based_traffic_selectors)

    # TODO: Remove these when issue #1615 is fixed
    gateway1_id = parse_resource_id(instance.virtual_network_gateway1.id)
    ncf = network_client_factory(cmd.cli_ctx, subscription_id=gateway1_id['subscription'])
    instance.virtual_network_gateway1 = ncf.virtual_network_gateways.get(
        gateway1_id['resource_group'], gateway1_id['name'])

    if instance.virtual_network_gateway2:
        gateway2_id = parse_resource_id(instance.virtual_network_gateway2.id)
        ncf = network_client_factory(cmd.cli_ctx, subscription_id=gateway2_id['subscription'])
        instance.virtual_network_gateway2 = ncf.virtual_network_gateways.get(
            gateway2_id['resource_group'], gateway2_id['name'])

    if instance.local_network_gateway2:
        gateway2_id = parse_resource_id(instance.local_network_gateway2.id)
        ncf = network_client_factory(cmd.cli_ctx, subscription_id=gateway2_id['subscription'])
        instance.local_network_gateway2 = ncf.local_network_gateways.get(
            gateway2_id['resource_group'], gateway2_id['name'])

    return instance


def list_vpn_connections(cmd, resource_group_name, virtual_network_gateway_name=None):
    if virtual_network_gateway_name:
        client = network_client_factory(cmd.cli_ctx).virtual_network_gateways
        return client.list_connections(resource_group_name, virtual_network_gateway_name)
    client = network_client_factory(cmd.cli_ctx).virtual_network_gateway_connections
    return client.list(resource_group_name)


def start_vpn_conn_package_capture(cmd, client, resource_group_name, virtual_network_gateway_connection_name,
                                   filter_data=None, no_wait=False):
    VpnPacketCaptureStartParameters = cmd.get_models('VpnPacketCaptureStartParameters')
    parameters = VpnPacketCaptureStartParameters(filter_data=filter_data)
    return sdk_no_wait(no_wait, client.begin_start_packet_capture, resource_group_name,
                       virtual_network_gateway_connection_name, parameters=parameters)


def stop_vpn_conn_package_capture(cmd, client, resource_group_name, virtual_network_gateway_connection_name,
                                  sas_url, no_wait=False):
    VpnPacketCaptureStopParameters = cmd.get_models('VpnPacketCaptureStopParameters')
    parameters = VpnPacketCaptureStopParameters(sas_url=sas_url)
    return sdk_no_wait(no_wait, client.begin_stop_packet_capture, resource_group_name,
                       virtual_network_gateway_connection_name, parameters=parameters)


def show_vpn_connection_device_config_script(cmd, client, resource_group_name, virtual_network_gateway_connection_name,
                                             vendor, device_family, firmware_version):
    VpnDeviceScriptParameters = cmd.get_models('VpnDeviceScriptParameters')
    parameters = VpnDeviceScriptParameters(
        vendor=vendor,
        device_family=device_family,
        firmware_version=firmware_version
    )
    return client.vpn_device_configuration_script(resource_group_name, virtual_network_gateway_connection_name,
                                                  parameters=parameters)
# endregion


# region IPSec Policy Commands
def add_vnet_gateway_ipsec_policy(cmd, resource_group_name, gateway_name,
                                  sa_life_time_seconds, sa_data_size_kilobytes,
                                  ipsec_encryption, ipsec_integrity,
                                  ike_encryption, ike_integrity, dh_group, pfs_group, no_wait=False):
    IpsecPolicy = cmd.get_models('IpsecPolicy')
    new_policy = IpsecPolicy(sa_life_time_seconds=sa_life_time_seconds,
                             sa_data_size_kilobytes=sa_data_size_kilobytes,
                             ipsec_encryption=ipsec_encryption,
                             ipsec_integrity=ipsec_integrity,
                             ike_encryption=ike_encryption,
                             ike_integrity=ike_integrity,
                             dh_group=dh_group,
                             pfs_group=pfs_group)

    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)
    try:
        if gateway.vpn_client_configuration.vpn_client_ipsec_policies:
            gateway.vpn_client_configuration.vpn_client_ipsec_policies.append(new_policy)
        else:
            gateway.vpn_client_configuration.vpn_client_ipsec_policies = [new_policy]
    except AttributeError:
        raise CLIError('VPN client configuration must first be set through `az network vnet-gateway create/update`.')
    return sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, gateway_name, gateway)


def clear_vnet_gateway_ipsec_policies(cmd, resource_group_name, gateway_name, no_wait=False):
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)
    try:
        gateway.vpn_client_configuration.vpn_client_ipsec_policies = None
    except AttributeError:
        raise CLIError('VPN client configuration must first be set through `az network vnet-gateway create/update`.')
    if no_wait:
        return sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, gateway_name, gateway)

    from azure.cli.core.commands import LongRunningOperation
    poller = sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, gateway_name, gateway)
    return LongRunningOperation(cmd.cli_ctx)(poller).vpn_client_configuration.vpn_client_ipsec_policies


def list_vnet_gateway_ipsec_policies(cmd, resource_group_name, gateway_name):
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    try:
        return ncf.get(resource_group_name, gateway_name).vpn_client_configuration.vpn_client_ipsec_policies
    except AttributeError:
        raise CLIError('VPN client configuration must first be set through `az network vnet-gateway create/update`.')


def add_vpn_conn_ipsec_policy(cmd, client, resource_group_name, connection_name,
                              sa_life_time_seconds, sa_data_size_kilobytes,
                              ipsec_encryption, ipsec_integrity,
                              ike_encryption, ike_integrity, dh_group, pfs_group, no_wait=False):
    IpsecPolicy = cmd.get_models('IpsecPolicy')
    new_policy = IpsecPolicy(sa_life_time_seconds=sa_life_time_seconds,
                             sa_data_size_kilobytes=sa_data_size_kilobytes,
                             ipsec_encryption=ipsec_encryption,
                             ipsec_integrity=ipsec_integrity,
                             ike_encryption=ike_encryption,
                             ike_integrity=ike_integrity,
                             dh_group=dh_group,
                             pfs_group=pfs_group)

    conn = client.get(resource_group_name, connection_name)
    if conn.ipsec_policies:
        conn.ipsec_policies.append(new_policy)
    else:
        conn.ipsec_policies = [new_policy]
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, connection_name, conn)


def clear_vpn_conn_ipsec_policies(cmd, client, resource_group_name, connection_name, no_wait=False):
    conn = client.get(resource_group_name, connection_name)
    conn.ipsec_policies = None
    conn.use_policy_based_traffic_selectors = False
    if no_wait:
        return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, connection_name, conn)

    from azure.cli.core.commands import LongRunningOperation
    poller = sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, connection_name, conn)
    return LongRunningOperation(cmd.cli_ctx)(poller).ipsec_policies


def list_vpn_conn_ipsec_policies(cmd, client, resource_group_name, connection_name):
    return client.get(resource_group_name, connection_name).ipsec_policies


def assign_vnet_gateway_aad(cmd, resource_group_name, gateway_name,
                            aad_tenant, aad_audience, aad_issuer, no_wait=False):
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)

    if gateway.vpn_client_configuration is None:
        raise CLIError('VPN client configuration must be set first through `az network vnet-gateway create/update`.')

    gateway.vpn_client_configuration.aad_tenant = aad_tenant
    gateway.vpn_client_configuration.aad_audience = aad_audience
    gateway.vpn_client_configuration.aad_issuer = aad_issuer

    return sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, gateway_name, gateway)


def show_vnet_gateway_aad(cmd, resource_group_name, gateway_name):
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)

    if gateway.vpn_client_configuration is None:
        raise CLIError('VPN client configuration must be set first through `az network vnet-gateway create/update`.')

    return gateway.vpn_client_configuration


def remove_vnet_gateway_aad(cmd, resource_group_name, gateway_name, no_wait=False):
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)

    if gateway.vpn_client_configuration is None:
        raise CLIError('VPN client configuration must be set first through `az network vnet-gateway create/update`.')

    gateway.vpn_client_configuration.aad_tenant = None
    gateway.vpn_client_configuration.aad_audience = None
    gateway.vpn_client_configuration.aad_issuer = None
    if cmd.supported_api_version(min_api='2020-11-01'):
        gateway.vpn_client_configuration.vpn_authentication_types = None

    return sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, gateway_name, gateway)


def add_vnet_gateway_nat_rule(cmd, resource_group_name, gateway_name, name, internal_mappings, external_mappings,
                              rule_type=None, mode=None, ip_config_id=None, no_wait=False):
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)

    VirtualNetworkGatewayNatRule, VpnNatRuleMapping = cmd.get_models('VirtualNetworkGatewayNatRule',
                                                                     'VpnNatRuleMapping')
    gateway.nat_rules.append(
        VirtualNetworkGatewayNatRule(type_properties_type=rule_type, mode=mode, name=name,
                                     internal_mappings=[VpnNatRuleMapping(address_space=i_map) for i_map in internal_mappings] if internal_mappings else None,
                                     external_mappings=[VpnNatRuleMapping(address_space=e_map) for e_map in external_mappings] if external_mappings else None,
                                     ip_configuration_id=ip_config_id))

    return sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, gateway_name, gateway)


def show_vnet_gateway_nat_rule(cmd, resource_group_name, gateway_name):
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)

    return gateway.nat_rules


def remove_vnet_gateway_nat_rule(cmd, resource_group_name, gateway_name, name, no_wait=False):
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)

    for rule in gateway.nat_rules:
        if name == rule.name:
            gateway.nat_rules.remove(rule)
            return sdk_no_wait(no_wait, ncf.begin_create_or_update, resource_group_name, gateway_name, gateway)

    raise UnrecognizedArgumentError(f'Do not find nat_rules named {name}!!!')
# endregion


# region VirtualHub
def create_virtual_hub(cmd, client,
                       resource_group_name,
                       virtual_hub_name,
                       hosted_subnet,
                       public_ip_address,
                       location=None,
                       tags=None):
    from azure.core.exceptions import HttpResponseError
    from azure.cli.core.commands import LongRunningOperation

    try:
        client.get(resource_group_name, virtual_hub_name)
        raise CLIError('The VirtualHub "{}" under resource group "{}" exists'.format(
            virtual_hub_name, resource_group_name))
    except HttpResponseError:
        pass

    SubResource = cmd.get_models('SubResource')

    VirtualHub, HubIpConfiguration = cmd.get_models('VirtualHub', 'HubIpConfiguration')

    hub = VirtualHub(tags=tags, location=location,
                     virtual_wan=None,
                     sku='Standard')
    vhub_poller = client.begin_create_or_update(resource_group_name, virtual_hub_name, hub)
    LongRunningOperation(cmd.cli_ctx)(vhub_poller)

    ip_config = HubIpConfiguration(
        subnet=SubResource(id=hosted_subnet),
        public_ip_address=SubResource(id=public_ip_address),
    )
    vhub_ip_config_client = network_client_factory(cmd.cli_ctx).virtual_hub_ip_configuration
    try:
        vhub_ip_poller = vhub_ip_config_client.begin_create_or_update(
            resource_group_name, virtual_hub_name, 'Default', ip_config)
        LongRunningOperation(cmd.cli_ctx)(vhub_ip_poller)
    except Exception as ex:
        logger.error(ex)
        try:
            vhub_ip_config_client.begin_delete(resource_group_name, virtual_hub_name, 'Default')
        except HttpResponseError:
            pass
        client.begin_delete(resource_group_name, virtual_hub_name)
        raise ex

    return client.get(resource_group_name, virtual_hub_name)


def virtual_hub_update_setter(client, resource_group_name, virtual_hub_name, parameters):
    return client.begin_create_or_update(resource_group_name, virtual_hub_name, parameters)


def update_virtual_hub(cmd, instance,
                       tags=None,
                       allow_branch_to_branch_traffic=None):
    with cmd.update_context(instance) as c:
        c.set_param('tags', tags)
        c.set_param('allow_branch_to_branch_traffic', allow_branch_to_branch_traffic)
    return instance


def delete_virtual_hub(cmd, client, resource_group_name, virtual_hub_name, no_wait=False):
    from azure.cli.core.commands import LongRunningOperation
    vhub_ip_config_client = network_client_factory(cmd.cli_ctx).virtual_hub_ip_configuration
    ip_configs = list(vhub_ip_config_client.list(resource_group_name, virtual_hub_name))
    if ip_configs:
        ip_config = ip_configs[0]   # There will always be only 1
        poller = vhub_ip_config_client.begin_delete(resource_group_name, virtual_hub_name, ip_config.name)
        LongRunningOperation(cmd.cli_ctx)(poller)
    return sdk_no_wait(no_wait, client.begin_delete, resource_group_name, virtual_hub_name)


def list_virtual_hub(client, resource_group_name=None):
    if resource_group_name is not None:
        return client.list_by_resource_group(resource_group_name)
    return client.list()


def create_virtual_hub_bgp_connection(cmd, client, resource_group_name, virtual_hub_name, connection_name,
                                      peer_asn, peer_ip, no_wait=False):
    BgpConnection = cmd.get_models('BgpConnection')
    vhub_bgp_conn = BgpConnection(name=connection_name, peer_asn=peer_asn, peer_ip=peer_ip)
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name,
                       virtual_hub_name, connection_name, vhub_bgp_conn)


def virtual_hub_bgp_connection_update_setter(client, resource_group_name,
                                             virtual_hub_name, connection_name,
                                             parameters):
    return client.begin_create_or_update(resource_group_name, virtual_hub_name, connection_name, parameters)


def update_virtual_hub_bgp_connection(cmd, instance, peer_asn=None, peer_ip=None):
    with cmd.update_context(instance) as c:
        c.set_param('peer_asn', peer_asn)
        c.set_param('peer_ip', peer_ip)
    return instance


def delete_virtual_hub_bgp_connection(client, resource_group_name,
                                      virtual_hub_name, connection_name, no_wait=False):
    return sdk_no_wait(no_wait, client.begin_delete, resource_group_name, virtual_hub_name, connection_name)


def list_virtual_hub_bgp_connection_learned_routes(client, resource_group_name, virtual_hub_name, connection_name):
    return client.begin_list_learned_routes(resource_group_name, virtual_hub_name, connection_name)


def list_virtual_hub_bgp_connection_advertised_routes(client, resource_group_name, virtual_hub_name, connection_name):
    return client.begin_list_advertised_routes(resource_group_name, virtual_hub_name, connection_name)
# endregion


# region VirtualRouter
def create_virtual_router(cmd,
                          resource_group_name,
                          virtual_router_name,
                          hosted_gateway=None,
                          hosted_subnet=None,
                          location=None,
                          tags=None):
    vrouter_client = network_client_factory(cmd.cli_ctx).virtual_routers
    vhub_client = network_client_factory(cmd.cli_ctx).virtual_hubs

    from azure.core.exceptions import HttpResponseError
    try:
        vrouter_client.get(resource_group_name, virtual_router_name)
    except HttpResponseError:
        pass

    virtual_hub_name = virtual_router_name
    try:
        vhub_client.get(resource_group_name, virtual_hub_name)
        raise CLIError('The VirtualRouter "{}" under resource group "{}" exists'.format(virtual_hub_name,
                                                                                        resource_group_name))
    except HttpResponseError:
        pass

    SubResource = cmd.get_models('SubResource')

    # for old VirtualRouter
    if hosted_gateway is not None:
        VirtualRouter = cmd.get_models('VirtualRouter')
        virtual_router = VirtualRouter(virtual_router_asn=None,
                                       virtual_router_ips=[],
                                       hosted_subnet=None,
                                       hosted_gateway=SubResource(id=hosted_gateway),
                                       location=location,
                                       tags=tags)
        return vrouter_client.begin_create_or_update(resource_group_name, virtual_router_name, virtual_router)

    # for VirtualHub
    VirtualHub, HubIpConfiguration = cmd.get_models('VirtualHub', 'HubIpConfiguration')

    hub = VirtualHub(tags=tags, location=location, virtual_wan=None, sku='Standard')
    ip_config = HubIpConfiguration(subnet=SubResource(id=hosted_subnet))

    from azure.cli.core.commands import LongRunningOperation

    vhub_poller = vhub_client.begin_create_or_update(resource_group_name, virtual_hub_name, hub)
    LongRunningOperation(cmd.cli_ctx)(vhub_poller)

    vhub_ip_config_client = network_client_factory(cmd.cli_ctx).virtual_hub_ip_configuration
    try:
        vhub_ip_poller = vhub_ip_config_client.begin_create_or_update(resource_group_name,
                                                                      virtual_hub_name,
                                                                      'Default',
                                                                      ip_config)
        LongRunningOperation(cmd.cli_ctx)(vhub_ip_poller)
    except Exception as ex:
        logger.error(ex)
        vhub_ip_config_client.begin_delete(resource_group_name, virtual_hub_name, 'Default')
        vhub_client.begin_delete(resource_group_name, virtual_hub_name)
        raise ex

    return vhub_client.get(resource_group_name, virtual_hub_name)


def virtual_router_update_getter(cmd, resource_group_name, virtual_router_name):
    from azure.core.exceptions import HttpResponseError
    try:
        vrouter_client = network_client_factory(cmd.cli_ctx).virtual_routers
        return vrouter_client.get(resource_group_name, virtual_router_name)
    except HttpResponseError:  # 404
        pass

    virtual_hub_name = virtual_router_name
    vhub_client = network_client_factory(cmd.cli_ctx).virtual_hubs
    return vhub_client.get(resource_group_name, virtual_hub_name)


def virtual_router_update_setter(cmd, resource_group_name, virtual_router_name, parameters):
    if parameters.type == 'Microsoft.Network/virtualHubs':
        client = network_client_factory(cmd.cli_ctx).virtual_hubs
    else:
        client = network_client_factory(cmd.cli_ctx).virtual_routers

    # If the client is virtual_hubs,
    # the virtual_router_name represents virtual_hub_name and
    # the parameters represents VirtualHub
    return client.begin_create_or_update(resource_group_name, virtual_router_name, parameters)


def update_virtual_router(cmd, instance, tags=None):
    # both VirtualHub and VirtualRouter own those properties
    with cmd.update_context(instance) as c:
        c.set_param('tags', tags)
    return instance


def list_virtual_router(cmd, resource_group_name=None):
    vrouter_client = network_client_factory(cmd.cli_ctx).virtual_routers
    vhub_client = network_client_factory(cmd.cli_ctx).virtual_hubs

    if resource_group_name is not None:
        vrouters = vrouter_client.list_by_resource_group(resource_group_name)
        vhubs = vhub_client.list_by_resource_group(resource_group_name)
    else:
        vrouters = vrouter_client.list()
        vhubs = vhub_client.list()

    return list(vrouters) + list(vhubs)


def show_virtual_router(cmd, resource_group_name, virtual_router_name):
    vrouter_client = network_client_factory(cmd.cli_ctx).virtual_routers
    vhub_client = network_client_factory(cmd.cli_ctx).virtual_hubs

    from azure.core.exceptions import HttpResponseError
    try:
        item = vrouter_client.get(resource_group_name, virtual_router_name)
    except HttpResponseError:
        virtual_hub_name = virtual_router_name
        item = vhub_client.get(resource_group_name, virtual_hub_name)

    return item


def delete_virtual_router(cmd, resource_group_name, virtual_router_name):
    vrouter_client = network_client_factory(cmd.cli_ctx).virtual_routers
    vhub_client = network_client_factory(cmd.cli_ctx).virtual_hubs
    vhub_ip_config_client = network_client_factory(cmd.cli_ctx).virtual_hub_ip_configuration

    from azure.core.exceptions import HttpResponseError
    try:
        vrouter_client.get(resource_group_name, virtual_router_name)
        item = vrouter_client.begin_delete(resource_group_name, virtual_router_name)
    except HttpResponseError:
        from azure.cli.core.commands import LongRunningOperation

        virtual_hub_name = virtual_router_name
        poller = vhub_ip_config_client.begin_delete(resource_group_name, virtual_hub_name, 'Default')
        LongRunningOperation(cmd.cli_ctx)(poller)

        item = vhub_client.begin_delete(resource_group_name, virtual_hub_name)

    return item


def create_virtual_router_peering(cmd, resource_group_name, virtual_router_name, peering_name, peer_asn, peer_ip):

    # try VirtualRouter first
    from azure.core.exceptions import HttpResponseError
    try:
        vrouter_client = network_client_factory(cmd.cli_ctx).virtual_routers
        vrouter_client.get(resource_group_name, virtual_router_name)
    except HttpResponseError:
        pass
    else:
        vrouter_peering_client = network_client_factory(cmd.cli_ctx).virtual_router_peerings
        VirtualRouterPeering = cmd.get_models('VirtualRouterPeering')
        virtual_router_peering = VirtualRouterPeering(peer_asn=peer_asn, peer_ip=peer_ip)
        return vrouter_peering_client.begin_create_or_update(resource_group_name,
                                                             virtual_router_name,
                                                             peering_name,
                                                             virtual_router_peering)

    virtual_hub_name = virtual_router_name
    bgp_conn_name = peering_name

    # try VirtualHub then if the virtual router doesn't exist
    try:
        vhub_client = network_client_factory(cmd.cli_ctx).virtual_hubs
        vhub_client.get(resource_group_name, virtual_hub_name)
    except HttpResponseError:
        msg = 'The VirtualRouter "{}" under resource group "{}" was not found'.format(virtual_hub_name,
                                                                                      resource_group_name)
        raise CLIError(msg)

    BgpConnection = cmd.get_models('BgpConnection')
    vhub_bgp_conn = BgpConnection(name=peering_name, peer_asn=peer_asn, peer_ip=peer_ip)

    vhub_bgp_conn_client = network_client_factory(cmd.cli_ctx).virtual_hub_bgp_connection
    return vhub_bgp_conn_client.begin_create_or_update(resource_group_name, virtual_hub_name,
                                                       bgp_conn_name, vhub_bgp_conn)


def virtual_router_peering_update_getter(cmd, resource_group_name, virtual_router_name, peering_name):
    vrouter_peering_client = network_client_factory(cmd.cli_ctx).virtual_router_peerings

    from azure.core.exceptions import HttpResponseError
    try:
        return vrouter_peering_client.get(resource_group_name, virtual_router_name, peering_name)
    except HttpResponseError:  # 404
        pass

    virtual_hub_name = virtual_router_name
    bgp_conn_name = peering_name

    vhub_bgp_conn_client = network_client_factory(cmd.cli_ctx).virtual_hub_bgp_connection
    return vhub_bgp_conn_client.get(resource_group_name, virtual_hub_name, bgp_conn_name)


def virtual_router_peering_update_setter(cmd, resource_group_name, virtual_router_name, peering_name, parameters):
    if parameters.type == 'Microsoft.Network/virtualHubs/bgpConnections':
        client = network_client_factory(cmd.cli_ctx).virtual_hub_bgp_connection
    else:
        client = network_client_factory(cmd.cli_ctx).virtual_router_peerings

    # if the client is virtual_hub_bgp_connection,
    # the virtual_router_name represents virtual_hub_name and
    # the peering_name represents bgp_connection_name and
    # the parameters represents BgpConnection
    return client.begin_create_or_update(resource_group_name, virtual_router_name, peering_name, parameters)


def update_virtual_router_peering(cmd, instance, peer_asn=None, peer_ip=None):
    # both VirtualHub and VirtualRouter own those properties
    with cmd.update_context(instance) as c:
        c.set_param('peer_asn', peer_asn)
        c.set_param('peer_ip', peer_ip)
    return instance


def list_virtual_router_peering(cmd, resource_group_name, virtual_router_name):
    virtual_hub_name = virtual_router_name

    from azure.core.exceptions import HttpResponseError
    try:
        vrouter_client = network_client_factory(cmd.cli_ctx).virtual_routers
        vrouter_client.get(resource_group_name, virtual_router_name)
    except HttpResponseError:
        try:
            vhub_client = network_client_factory(cmd.cli_ctx).virtual_hubs
            vhub_client.get(resource_group_name, virtual_hub_name)
        except HttpResponseError:
            msg = 'The VirtualRouter "{}" under resource group "{}" was not found'.format(virtual_hub_name,
                                                                                          resource_group_name)
            raise CLIError(msg)

    try:
        vrouter_peering_client = network_client_factory(cmd.cli_ctx).virtual_router_peerings
        vrouter_peerings = list(vrouter_peering_client.list(resource_group_name, virtual_router_name))
    except HttpResponseError:
        vrouter_peerings = []

    virtual_hub_name = virtual_router_name
    try:
        vhub_bgp_conn_client = network_client_factory(cmd.cli_ctx).virtual_hub_bgp_connections
        vhub_bgp_connections = list(vhub_bgp_conn_client.list(resource_group_name, virtual_hub_name))
    except HttpResponseError:
        vhub_bgp_connections = []

    return list(vrouter_peerings) + list(vhub_bgp_connections)


def show_virtual_router_peering(cmd, resource_group_name, virtual_router_name, peering_name):
    from azure.core.exceptions import HttpResponseError
    try:
        vrouter_client = network_client_factory(cmd.cli_ctx).virtual_routers
        vrouter_client.get(resource_group_name, virtual_router_name)
    except HttpResponseError:
        pass
    else:
        vrouter_peering_client = network_client_factory(cmd.cli_ctx).virtual_router_peerings
        return vrouter_peering_client.get(resource_group_name, virtual_router_name, peering_name)

    virtual_hub_name = virtual_router_name
    bgp_conn_name = peering_name

    # try VirtualHub then if the virtual router doesn't exist
    try:
        vhub_client = network_client_factory(cmd.cli_ctx).virtual_hubs
        vhub_client.get(resource_group_name, virtual_hub_name)
    except HttpResponseError:
        msg = 'The VirtualRouter "{}" under resource group "{}" was not found'.format(virtual_hub_name,
                                                                                      resource_group_name)
        raise CLIError(msg)

    vhub_bgp_conn_client = network_client_factory(cmd.cli_ctx).virtual_hub_bgp_connection
    return vhub_bgp_conn_client.get(resource_group_name, virtual_hub_name, bgp_conn_name)


def delete_virtual_router_peering(cmd, resource_group_name, virtual_router_name, peering_name):
    from azure.core.exceptions import HttpResponseError
    try:
        vrouter_client = network_client_factory(cmd.cli_ctx).virtual_routers
        vrouter_client.get(resource_group_name, virtual_router_name)
    except:  # pylint: disable=bare-except
        pass
    else:
        vrouter_peering_client = network_client_factory(cmd.cli_ctx).virtual_router_peerings
        return vrouter_peering_client.begin_delete(resource_group_name, virtual_router_name, peering_name)

    virtual_hub_name = virtual_router_name
    bgp_conn_name = peering_name

    # try VirtualHub then if the virtual router doesn't exist
    try:
        vhub_client = network_client_factory(cmd.cli_ctx).virtual_hubs
        vhub_client.get(resource_group_name, virtual_hub_name)
    except HttpResponseError:
        msg = 'The VirtualRouter "{}" under resource group "{}" was not found'.format(virtual_hub_name,
                                                                                      resource_group_name)
        raise CLIError(msg)

    vhub_bgp_conn_client = network_client_factory(cmd.cli_ctx).virtual_hub_bgp_connection
    return vhub_bgp_conn_client.begin_delete(resource_group_name, virtual_hub_name, bgp_conn_name)
# endregion


# region service aliases
def list_service_aliases(cmd, location, resource_group_name=None):
    client = network_client_factory(cmd.cli_ctx).available_service_aliases
    if resource_group_name is not None:
        return client.list_by_resource_group(resource_group_name=resource_group_name, location=location)
    return client.list(location=location)
# endregion


# region bastion
def create_bastion_host(cmd, resource_group_name, bastion_host_name, virtual_network_name,
                        public_ip_address, location=None, subnet='AzureBastionSubnet', scale_units=None, sku=None, tags=None):
    client = network_client_factory(cmd.cli_ctx).bastion_hosts
    (BastionHost,
     BastionHostIPConfiguration,
     SubResource) = cmd.get_models('BastionHost',
                                   'BastionHostIPConfiguration',
                                   'SubResource')
    ip_config_name = "bastion_ip_config"
    ip_configuration = BastionHostIPConfiguration(name=ip_config_name,
                                                  subnet=SubResource(id=subnet),
                                                  public_ip_address=SubResource(id=public_ip_address))

    bastion_host = BastionHost(ip_configurations=[ip_configuration],
                               location=location,
                               tags=tags)

    if cmd.supported_api_version(min_api='2021-03-01'):
        sku_type = cmd.get_models('Sku')
        sku = sku_type(name=sku)
        bastion_host = BastionHost(ip_configurations=[ip_configuration],
                                   location=location,
                                   scale_units=scale_units,
                                   sku=sku,
                                   tags=tags)
    return client.begin_create_or_update(resource_group_name=resource_group_name,
                                         bastion_host_name=bastion_host_name,
                                         parameters=bastion_host)


def list_bastion_host(cmd, resource_group_name=None):
    client = network_client_factory(cmd.cli_ctx).bastion_hosts
    if resource_group_name is not None:
        return client.list_by_resource_group(resource_group_name=resource_group_name)
    return client.list()


SSH_EXTENSION_NAME = 'ssh'
SSH_EXTENSION_MODULE = 'azext_ssh.custom'
SSH_UTILS_EXTENSION_MODULE = 'azext_ssh.ssh_utils'
SSH_EXTENSION_VERSION = '0.1.3'


def _get_azext_module(extension_name, module_name):
    try:
        # Adding the installed extension in the path
        from azure.cli.core.extension.operations import add_extension_to_path
        add_extension_to_path(extension_name)
        # Import the extension module
        from importlib import import_module
        azext_custom = import_module(module_name)
        return azext_custom
    except ImportError as ie:
        raise CLIError(ie)


def _test_extension(extension_name):
    from azure.cli.core.extension import (get_extension)
    from pkg_resources import parse_version
    ext = get_extension(extension_name)
    if parse_version(ext.version) < parse_version(SSH_EXTENSION_VERSION):
        raise CLIError('SSH Extension (version >= "{}") must be installed'.format(SSH_EXTENSION_VERSION))


def _get_ssh_path(ssh_command="ssh"):
    import os
    ssh_path = ssh_command

    if platform.system() == 'Windows':
        arch_data = platform.architecture()
        is_32bit = arch_data[0] == '32bit'
        sys_path = 'SysNative' if is_32bit else 'System32'
        system_root = os.environ['SystemRoot']
        system32_path = os.path.join(system_root, sys_path)
        ssh_path = os.path.join(system32_path, "openSSH", (ssh_command + ".exe"))
        logger.debug("Platform architecture: %s", str(arch_data))
        logger.debug("System Root: %s", system_root)
        logger.debug("Attempting to run ssh from path %s", ssh_path)

        if not os.path.isfile(ssh_path):
            raise CLIError("Could not find " + ssh_command + ".exe. Is the OpenSSH client installed?")
    elif platform.system() in ('Linux', 'Darwin'):
        import shutil
        ssh_path = shutil.which(ssh_command)
        if not ssh_path:
            raise UnrecognizedArgumentError(f"{ssh_command} not found in path. Is the OpenSSH client installed?")
    else:
        raise UnrecognizedArgumentError("Platform is not supported for this command. Supported platforms: Windows, Darwin, Linux")

    return ssh_path


def _get_rdp_path(rdp_command="mstsc"):
    import os
    rdp_path = rdp_command

    if platform.system() == 'Windows':
        arch_data = platform.architecture()
        sys_path = 'System32'
        system_root = os.environ['SystemRoot']
        system32_path = os.path.join(system_root, sys_path)
        rdp_path = os.path.join(system32_path, (rdp_command + ".exe"))
        logger.debug("Platform architecture: %s", str(arch_data))
        logger.debug("System Root: %s", system_root)
        logger.debug("Attempting to run rdp from path %s", rdp_path)

        if not os.path.isfile(rdp_path):
            raise CLIError("Could not find " + rdp_command + ".exe. Is the rdp client installed?")
    else:
        raise UnrecognizedArgumentError("Platform is not supported for this command. Supported platforms: Windows")

    return rdp_path


def _get_host(username, ip):
    return username + "@" + ip


def _build_args(cert_file, private_key_file):
    private_key = []
    certificate = []
    if private_key_file:
        private_key = ["-i", private_key_file]
    if cert_file:
        certificate = ["-o", "CertificateFile=" + cert_file]
    return private_key + certificate


def ssh_bastion_host(cmd, auth_type, target_resource_id, resource_group_name, bastion_host_name, resource_port=None, username=None, ssh_key=None):
    import os

    _test_extension(SSH_EXTENSION_NAME)

    if not resource_port:
        resource_port = 22
    if not is_valid_resource_id(target_resource_id):
        raise InvalidArgumentValueError("Please enter a valid Virtual Machine resource Id.")

    tunnel_server = get_tunnel(cmd, resource_group_name, bastion_host_name, target_resource_id, resource_port)
    t = threading.Thread(target=_start_tunnel, args=(tunnel_server,))
    t.daemon = True
    t.start()
    if auth_type.lower() == 'password':
        if username is None:
            raise RequiredArgumentMissingError("Please enter username with --username.")
        command = [_get_ssh_path(), _get_host(username, 'localhost')]
    elif auth_type.lower() == 'aad':
        azssh = _get_azext_module(SSH_EXTENSION_NAME, SSH_EXTENSION_MODULE)
        azssh_utils = _get_azext_module(SSH_EXTENSION_NAME, SSH_UTILS_EXTENSION_MODULE)
        cert_folder = tempfile.mkdtemp(prefix="aadsshcert")
        if not os.path.isdir(cert_folder):
            os.makedirs(cert_folder)
        azssh.ssh_cert(cmd, cert_path=os.path.join(cert_folder, "id_rsa.pub-aadcert.pub"))
        private_key_file = os.path.join(cert_folder, "id_rsa")
        cert_file = os.path.join(cert_folder, "id_rsa.pub-aadcert.pub")
        username = azssh_utils.get_ssh_cert_principals(cert_file)[0]
        command = [_get_ssh_path(), _get_host(username, 'localhost')]
        command = command + _build_args(cert_file, private_key_file)
    elif auth_type.lower() == 'ssh-key':
        if username is None or ssh_key is None:
            raise RequiredArgumentMissingError("Please enter username --username and ssh cert location --ssh-key.")
        command = [_get_ssh_path(), _get_host(username, 'localhost')]
        command = command + _build_args(None, ssh_key)
    else:
        raise UnrecognizedArgumentError("Unknown auth type. Use one of password, aad or ssh-key.")
    command = command + ["-p", str(tunnel_server.local_port)]
    command = command + ['-o', "StrictHostKeyChecking=no", '-o', "UserKnownHostsFile=/dev/null"]
    command = command + ['-o', "LogLevel=Error"]
    logger.debug("Running ssh command %s", ' '.join(command))
    try:
        subprocess.call(command, shell=platform.system() == 'Windows')
    except Exception as ex:
        raise CLIInternalError(ex)
    finally:
        tunnel_server.cleanup()


def rdp_bastion_host(cmd, target_resource_id, resource_group_name, bastion_host_name, resource_port=None):
    if not resource_port:
        resource_port = 3389
    if not is_valid_resource_id(target_resource_id):
        raise InvalidArgumentValueError("Please enter a valid Virtual Machine resource Id.")

    if platform.system() == 'Windows':
        tunnel_server = get_tunnel(cmd, resource_group_name, bastion_host_name, target_resource_id, resource_port)
        t = threading.Thread(target=_start_tunnel, args=(tunnel_server,))
        t.daemon = True
        t.start()
        command = [_get_rdp_path(), "/v:localhost:{0}".format(tunnel_server.local_port)]
        logger.debug("Running rdp command %s", ' '.join(command))

        from ._process_helper import launch_and_wait
        launch_and_wait(command)
        tunnel_server.cleanup()
    else:
        raise UnrecognizedArgumentError("Platform is not supported for this command. Supported platforms: Windows")


def get_tunnel(cmd, resource_group_name, name, vm_id, resource_port, port=None):
    from .tunnel import TunnelServer
    client = network_client_factory(cmd.cli_ctx).bastion_hosts
    bastion = client.get(resource_group_name, name)
    if port is None:
        port = 0  # Will auto-select a free port from 1024-65535
    tunnel_server = TunnelServer(cmd.cli_ctx, 'localhost', port, bastion, vm_id, resource_port)
    return tunnel_server


def tunnel_close_handler(tunnel):
    logger.info("Ctrl + C received. Clean up and then exit.")
    tunnel.cleanup()
    import sys
    sys.exit()


def create_bastion_tunnel(cmd, target_resource_id, resource_group_name, bastion_host_name, resource_port, port, timeout=None):
    if not is_valid_resource_id(target_resource_id):
        raise InvalidArgumentValueError("Please enter a valid Virtual Machine resource Id.")
    tunnel_server = get_tunnel(cmd, resource_group_name, bastion_host_name, target_resource_id, resource_port, port)
    t = threading.Thread(target=_start_tunnel, args=(tunnel_server,))
    t.daemon = True
    t.start()
    logger.warning('Opening tunnel on port: %s', tunnel_server.local_port)
    logger.warning('Tunnel is ready, connect on port %s', tunnel_server.local_port)
    logger.warning('Ctrl + C to close')

    import signal
    # handle closing the tunnel with an active session still connected
    signal.signal(signal.SIGINT, lambda signum, frame: tunnel_close_handler(tunnel_server))

    if timeout:
        time.sleep(int(timeout))
    else:
        while t.is_alive():
            time.sleep(5)


def _start_tunnel(tunnel_server):
    tunnel_server.start_server()
# endregion


# region security partner provider
def create_security_partner_provider(cmd, resource_group_name, security_partner_provider_name,
                                     security_provider_name, virtual_hub, location=None, tags=None):
    client = network_client_factory(cmd.cli_ctx).security_partner_providers
    SecurityPartnerProvider, SubResource = cmd.get_models('SecurityPartnerProvider', 'SubResource')

    security_partner_provider = SecurityPartnerProvider(security_provider_name=security_provider_name,
                                                        virtual_hub=SubResource(id=virtual_hub),
                                                        location=location,
                                                        tags=tags)
    return client.begin_create_or_update(resource_group_name=resource_group_name,
                                         security_partner_provider_name=security_partner_provider_name,
                                         parameters=security_partner_provider)


def update_security_partner_provider(instance, cmd, security_provider_name=None, virtual_hub=None, tags=None):
    with cmd.update_context(instance) as c:
        c.set_param('security_provider_name', security_provider_name)
        c.set_param('virtual_hub', virtual_hub)
        c.set_param('tags', tags)
    return instance


def list_security_partner_provider(cmd, resource_group_name=None):
    client = network_client_factory(cmd.cli_ctx).security_partner_providers
    if resource_group_name is not None:
        return client.list_by_resource_group(resource_group_name=resource_group_name)
    return client.list()
# endregion


# region network gateway connection
def reset_shared_key(cmd, client, virtual_network_gateway_connection_name, key_length, resource_group_name=None):
    ConnectionResetSharedKey = cmd.get_models('ConnectionResetSharedKey')
    shared_key = ConnectionResetSharedKey(key_length=key_length)
    return client.begin_reset_shared_key(resource_group_name=resource_group_name,
                                         virtual_network_gateway_connection_name=virtual_network_gateway_connection_name,  # pylint: disable=line-too-long
                                         parameters=shared_key)


def update_shared_key(cmd, instance, value):
    with cmd.update_context(instance) as c:
        c.set_param('value', value)
    return instance
# endregion


# region network virtual appliance
def create_network_virtual_appliance(cmd, client, resource_group_name, network_virtual_appliance_name,
                                     vendor, bundled_scale_unit, market_place_version,
                                     virtual_hub, boot_strap_configuration_blobs=None,
                                     cloud_init_configuration_blobs=None,
                                     cloud_init_configuration=None, asn=None,
                                     location=None, tags=None, no_wait=False):
    (NetworkVirtualAppliance,
     SubResource,
     VirtualApplianceSkuProperties) = cmd.get_models('NetworkVirtualAppliance',
                                                     'SubResource',
                                                     'VirtualApplianceSkuProperties')

    virtual_appliance = NetworkVirtualAppliance(boot_strap_configuration_blobs=boot_strap_configuration_blobs,
                                                cloud_init_configuration_blobs=cloud_init_configuration_blobs,
                                                cloud_init_configuration=cloud_init_configuration,
                                                virtual_appliance_asn=asn,
                                                virtual_hub=SubResource(id=virtual_hub),
                                                nva_sku=VirtualApplianceSkuProperties(
                                                    vendor=vendor,
                                                    bundled_scale_unit=bundled_scale_unit,
                                                    market_place_version=market_place_version
                                                ),
                                                location=location,
                                                tags=tags)

    return sdk_no_wait(no_wait, client.begin_create_or_update,
                       resource_group_name, network_virtual_appliance_name, virtual_appliance)


def update_network_virtual_appliance(instance, cmd, cloud_init_configuration=None, asn=None):
    with cmd.update_context(instance) as c:
        c.set_param('virtual_appliance_asn', asn)
        c.set_param('cloud_init_configuration', cloud_init_configuration)
    return instance


def list_network_virtual_appliance(cmd, client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name=resource_group_name)
    return client.list()


def create_network_virtual_appliance_site(cmd, client, resource_group_name, network_virtual_appliance_name,
                                          site_name, address_prefix, allow=None, optimize=None, default=None,
                                          no_wait=False):
    (BreakOutCategoryPolicies,
     Office365PolicyProperties,
     VirtualApplianceSite) = cmd.get_models('BreakOutCategoryPolicies',
                                            'Office365PolicyProperties',
                                            'VirtualApplianceSite')

    virtual_appliance_site = VirtualApplianceSite(address_prefix=address_prefix,
                                                  o365_policy=Office365PolicyProperties(
                                                      break_out_categories=BreakOutCategoryPolicies(
                                                          allow=allow,
                                                          optimize=optimize,
                                                          default=default
                                                      )))
    return sdk_no_wait(no_wait, client.begin_create_or_update,
                       resource_group_name, network_virtual_appliance_name, site_name, virtual_appliance_site)


def update_network_virtual_appliance_site(instance, cmd, address_prefix, allow=None, optimize=None, default=None):
    with cmd.update_context(instance) as c:
        c.set_param('address_prefix', address_prefix)
        c.set_param('o365_policy.break_out_categories.allow', allow)
        c.set_param('o365_policy.break_out_categories.optimize', optimize)
        c.set_param('o365_policy.break_out_categories.default', default)
    return instance
# endregion
