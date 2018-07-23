# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from __future__ import print_function

from collections import Counter, OrderedDict
import mock

from knack.log import get_logger

from msrestazure.azure_exceptions import CloudError
from msrestazure.tools import parse_resource_id, is_valid_resource_id, resource_id

from azure.mgmt.trafficmanager.models import MonitorProtocol, ProfileStatus

# pylint: disable=no-self-use,no-member,too-many-lines,unused-argument
from azure.cli.core.commands.client_factory import get_subscription_id, get_mgmt_service_client

from azure.cli.core.util import CLIError, sdk_no_wait
from azure.cli.command_modules.network._client_factory import network_client_factory
from azure.cli.command_modules.network._util import _get_property, _set_param

from azure.mgmt.dns.models import (RecordSet, AaaaRecord, ARecord, CaaRecord, CnameRecord, MxRecord,
                                   NsRecord, PtrRecord, SoaRecord, SrvRecord, TxtRecord)

from azure.cli.command_modules.network.zone_file.parse_zone_file import parse_zone_file
from azure.cli.command_modules.network.zone_file.make_zone_file import make_zone_file
from azure.cli.core.profiles import ResourceType, supported_api_version

logger = get_logger(__name__)


# region Utility methods
def _log_pprint_template(template):
    import json
    logger.info('==== BEGIN TEMPLATE ====')
    logger.info(json.dumps(template, indent=2))
    logger.info('==== END TEMPLATE ====')


def _upsert(parent, collection_name, obj_to_add, key_name):
    if not getattr(parent, collection_name, None):
        setattr(parent, collection_name, [])
    collection = getattr(parent, collection_name, None)

    value = getattr(obj_to_add, key_name)
    if value is None:
        raise CLIError(
            "Unable to resolve a value for key '{}' with which to match.".format(key_name))
    match = next((x for x in collection if getattr(x, key_name, None) == value), None)
    if match:
        logger.warning("Item '%s' already exists. Replacing with new values.", value)
        collection.remove(match)

    collection.append(obj_to_add)


def _get_default_name(balancer, property_name, option_name):
    return _get_default_value(balancer, property_name, option_name, True)


def _get_default_id(balancer, property_name, option_name):
    return _get_default_value(balancer, property_name, option_name, False)


def _get_default_value(balancer, property_name, option_name, return_name):
    values = [x.id for x in getattr(balancer, property_name)]
    if len(values) > 1:
        raise CLIError("Multiple possible values found for '{0}': {1}\nSpecify '{0}' "
                       "explicitly.".format(option_name, ', '.join(values)))
    elif not values:
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


def list_public_ips(cmd, resource_group_name=None):
    return _generic_list(cmd.cli_ctx, 'public_ip_addresses', resource_group_name)


def list_route_tables(cmd, resource_group_name=None):
    return _generic_list(cmd.cli_ctx, 'route_tables', resource_group_name)


def list_application_gateways(cmd, resource_group_name=None):
    return _generic_list(cmd.cli_ctx, 'application_gateways', resource_group_name)


def list_network_watchers(cmd, resource_group_name=None):
    return _generic_list(cmd.cli_ctx, 'network_watchers', resource_group_name)

# endregion


# region ApplicationGateways
# pylint: disable=too-many-locals
def create_application_gateway(cmd, application_gateway_name, resource_group_name, location=None,
                               tags=None, no_wait=False, capacity=2,
                               cert_data=None, cert_password=None,
                               frontend_port=None, http_settings_cookie_based_affinity='disabled',
                               http_settings_port=80, http_settings_protocol='Http',
                               routing_rule_type='Basic', servers=None,
                               sku=None,
                               private_ip_address='', public_ip_address=None,
                               public_ip_address_allocation=None,
                               subnet='default', subnet_address_prefix='10.0.0.0/24',
                               virtual_network_name=None, vnet_address_prefix='10.0.0.0/16',
                               public_ip_address_type=None, subnet_type=None, validate=False,
                               connection_draining_timeout=0, enable_http2=None):
    from azure.cli.core.util import random_string
    from azure.cli.core.commands.arm import ArmTemplateBuilder
    from azure.cli.command_modules.network._template_builder import (
        build_application_gateway_resource, build_public_ip_resource, build_vnet_resource)

    DeploymentProperties = cmd.get_models('DeploymentProperties', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    IPAllocationMethod = cmd.get_models('IPAllocationMethod')

    tags = tags or {}
    sku_tier = sku.split('_', 1)[0]
    http_listener_protocol = 'https' if cert_data else 'http'
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
            subnet_address_prefix)
        master_template.add_resource(vnet)
        subnet_id = '{}/virtualNetworks/{}/subnets/{}'.format(network_id_template,
                                                              virtual_network_name, subnet)

    if public_ip_address_type == 'new':
        ag_dependencies.append('Microsoft.Network/publicIpAddresses/{}'.format(public_ip_address))
        master_template.add_resource(build_public_ip_resource(cmd, public_ip_address, location,
                                                              tags,
                                                              public_ip_address_allocation,
                                                              None, None, None))
        public_ip_id = '{}/publicIPAddresses/{}'.format(network_id_template,
                                                        public_ip_address)

    app_gateway_resource = build_application_gateway_resource(
        cmd, application_gateway_name, location, tags, sku, sku_tier, capacity, servers, frontend_port,
        private_ip_address, private_ip_allocation, cert_data, cert_password,
        http_settings_cookie_based_affinity, http_settings_protocol, http_settings_port,
        http_listener_protocol, routing_rule_type, public_ip_id, subnet_id,
        connection_draining_timeout, enable_http2)
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
    if validate:
        _log_pprint_template(template)
        return client.validate(resource_group_name, deployment_name, properties)

    return sdk_no_wait(no_wait, client.create_or_update, resource_group_name, deployment_name, properties)


def update_application_gateway(instance, sku=None, capacity=None, tags=None, enable_http2=None):
    if sku is not None:
        instance.sku.name = sku
        instance.sku.tier = sku.split('_', 1)[0]
    if capacity is not None:
        instance.sku.capacity = capacity
    if tags is not None:
        instance.tags = tags
    if enable_http2 is not None:
        instance.enable_http2 = enable_http2
    return instance


def create_ag_authentication_certificate(cmd, resource_group_name, application_gateway_name, item_name,
                                         cert_data, no_wait=False):
    AuthCert = cmd.get_models('ApplicationGatewayAuthenticationCertificate')
    ncf = network_client_factory(cmd.cli_ctx).application_gateways
    ag = ncf.get(resource_group_name, application_gateway_name)
    new_cert = AuthCert(data=cert_data, name=item_name)
    _upsert(ag, 'authentication_certificates', new_cert, 'name')
    return sdk_no_wait(no_wait, ncf.create_or_update, resource_group_name, application_gateway_name, ag)


def update_ag_authentication_certificate(instance, parent, item_name, cert_data):
    instance.data = cert_data
    return parent


def create_ag_backend_address_pool(cmd, resource_group_name, application_gateway_name, item_name,
                                   servers=None, no_wait=False):
    ApplicationGatewayBackendAddressPool = cmd.get_models('ApplicationGatewayBackendAddressPool')
    ncf = network_client_factory(cmd.cli_ctx)
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    new_pool = ApplicationGatewayBackendAddressPool(name=item_name, backend_addresses=servers)
    _upsert(ag, 'backend_address_pools', new_pool, 'name')
    return sdk_no_wait(no_wait, ncf.application_gateways.create_or_update,
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
    _upsert(ag, 'frontend_ip_configurations', new_config, 'name')
    return sdk_no_wait(no_wait, ncf.application_gateways.create_or_update,
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
    _upsert(ag, 'frontend_ports', new_port, 'name')
    return sdk_no_wait(no_wait, ncf.application_gateways.create_or_update,
                       resource_group_name, application_gateway_name, ag)


def update_ag_frontend_port(instance, parent, item_name, port=None):
    if port is not None:
        instance.port = port
    return parent


def create_ag_http_listener(cmd, resource_group_name, application_gateway_name, item_name,
                            frontend_port, frontend_ip=None, host_name=None, ssl_cert=None,
                            no_wait=False):
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
        ssl_certificate=SubResource(id=ssl_cert) if ssl_cert else None)
    _upsert(ag, 'http_listeners', new_listener, 'name')
    return sdk_no_wait(no_wait, ncf.application_gateways.create_or_update,
                       resource_group_name, application_gateway_name, ag)


def update_ag_http_listener(cmd, instance, parent, item_name, frontend_ip=None, frontend_port=None,
                            host_name=None, ssl_cert=None):
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
    instance.require_server_name_indication = instance.host_name and instance.protocol.lower() == 'https'
    return parent


def create_ag_backend_http_settings_collection(cmd, resource_group_name, application_gateway_name, item_name, port,
                                               probe=None, protocol='http', cookie_based_affinity=None, timeout=None,
                                               no_wait=False, connection_draining_timeout=0,
                                               host_name=None, host_name_from_backend_pool=None,
                                               affinity_cookie_name=None, enable_probe=None, path=None,
                                               auth_certs=None):
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
    _upsert(ag, 'backend_http_settings_collection', new_settings, 'name')
    return sdk_no_wait(no_wait, ncf.application_gateways.create_or_update,
                       resource_group_name, application_gateway_name, ag)


def update_ag_backend_http_settings_collection(cmd, instance, parent, item_name, port=None, probe=None, protocol=None,
                                               cookie_based_affinity=None, timeout=None,
                                               connection_draining_timeout=None,
                                               host_name=None, host_name_from_backend_pool=None,
                                               affinity_cookie_name=None, enable_probe=None, path=None,
                                               auth_certs=None):
    SubResource = cmd.get_models('SubResource')
    if auth_certs == "":
        instance.authentication_certificates = None
    elif auth_certs is not None:
        instance.authentication_certificates = [SubResource(id=x) for x in auth_certs]
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
        instance.connection_draining.enabled = bool(connection_draining_timeout)
        instance.connection_draining.drain_timeout_in_sec = connection_draining_timeout or 1
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
    _upsert(ag, 'redirect_configurations', new_config, 'name')
    return sdk_no_wait(no_wait, ncf.create_or_update, resource_group_name, application_gateway_name, ag)


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


def create_ag_probe(cmd, resource_group_name, application_gateway_name, item_name, protocol, host,
                    path, interval=30, timeout=120, threshold=8, no_wait=False, host_name_from_http_settings=None,
                    min_servers=None, match_body=None, match_status_codes=None):
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

    _upsert(ag, 'probes', new_probe, 'name')
    return sdk_no_wait(no_wait, ncf.application_gateways.create_or_update,
                       resource_group_name, application_gateway_name, ag)


def update_ag_probe(cmd, instance, parent, item_name, protocol=None, host=None, path=None,
                    interval=None, timeout=None, threshold=None, host_name_from_http_settings=None,
                    min_servers=None, match_body=None, match_status_codes=None):
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
    return parent


def create_ag_request_routing_rule(cmd, resource_group_name, application_gateway_name, item_name,
                                   address_pool=None, http_settings=None, http_listener=None, redirect_config=None,
                                   url_path_map=None, rule_type='Basic', no_wait=False):
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
        backend_address_pool=SubResource(id=address_pool) if address_pool else None,
        backend_http_settings=SubResource(id=http_settings) if http_settings else None,
        http_listener=SubResource(id=http_listener),
        url_path_map=SubResource(id=url_path_map) if url_path_map else None)
    if cmd.supported_api_version(min_api='2017-06-01'):
        new_rule.redirect_configuration = SubResource(id=redirect_config) if redirect_config else None
    _upsert(ag, 'request_routing_rules', new_rule, 'name')
    return sdk_no_wait(no_wait, ncf.application_gateways.create_or_update,
                       resource_group_name, application_gateway_name, ag)


def update_ag_request_routing_rule(cmd, instance, parent, item_name, address_pool=None,
                                   http_settings=None, http_listener=None, redirect_config=None, url_path_map=None,
                                   rule_type=None):
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
    return parent


def create_ag_ssl_certificate(cmd, resource_group_name, application_gateway_name, item_name, cert_data,
                              cert_password, no_wait=False):
    ApplicationGatewaySslCertificate = cmd.get_models('ApplicationGatewaySslCertificate')
    ncf = network_client_factory(cmd.cli_ctx)
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    new_cert = ApplicationGatewaySslCertificate(
        name=item_name, data=cert_data, password=cert_password)
    _upsert(ag, 'ssl_certificates', new_cert, 'name')
    return sdk_no_wait(no_wait, ncf.application_gateways.create_or_update,
                       resource_group_name, application_gateway_name, ag)


def update_ag_ssl_certificate(instance, parent, item_name, cert_data=None, cert_password=None):
    if cert_data is not None:
        instance.data = cert_data
    if cert_password is not None:
        instance.password = cert_password
    return parent


def set_ag_ssl_policy_2017_03_01(cmd, resource_group_name, application_gateway_name, disabled_ssl_protocols=None,
                                 clear=False, no_wait=False):
    ApplicationGatewaySslPolicy = cmd.get_models('ApplicationGatewaySslPolicy')
    ncf = network_client_factory(cmd.cli_ctx).application_gateways
    ag = ncf.get(resource_group_name, application_gateway_name)
    ag.ssl_policy = None if clear else ApplicationGatewaySslPolicy(
        disabled_ssl_protocols=disabled_ssl_protocols)
    return sdk_no_wait(no_wait, ncf.create_or_update, resource_group_name, application_gateway_name, ag)


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
    return sdk_no_wait(no_wait, ncf.create_or_update, resource_group_name, application_gateway_name, ag)


def show_ag_ssl_policy(cmd, resource_group_name, application_gateway_name):
    return network_client_factory(cmd.cli_ctx).application_gateways.get(
        resource_group_name, application_gateway_name).ssl_policy


def create_ag_url_path_map(cmd, resource_group_name, application_gateway_name, item_name, paths,
                           address_pool=None, http_settings=None, redirect_config=None,
                           default_address_pool=None, default_http_settings=None, default_redirect_config=None,
                           no_wait=False, rule_name='default'):
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

    # pull defaults from the rule specific properties if the default-* option isn't specified
    if new_rule.backend_address_pool and not new_map.default_backend_address_pool:
        new_map.default_backend_address_pool = new_rule.backend_address_pool

    if new_rule.backend_http_settings and not new_map.default_backend_http_settings:
        new_map.default_backend_http_settings = new_rule.backend_http_settings

    if new_rule.redirect_configuration and not new_map.default_redirect_configuration:
        new_map.default_redirect_configuration = new_rule.redirect_configuration

    new_map.path_rules.append(new_rule)
    _upsert(ag, 'url_path_maps', new_map, 'name')
    return sdk_no_wait(no_wait, ncf.application_gateways.create_or_update,
                       resource_group_name, application_gateway_name, ag)


def update_ag_url_path_map(cmd, instance, parent, item_name, default_address_pool=None,
                           default_http_settings=None, default_redirect_config=None, raw=False):
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
    return parent


def create_ag_url_path_map_rule(cmd, resource_group_name, application_gateway_name, url_path_map_name,
                                item_name, paths, address_pool=None, http_settings=None, redirect_config=None,
                                no_wait=False):
    ApplicationGatewayPathRule, SubResource = cmd.get_models('ApplicationGatewayPathRule', 'SubResource')
    ncf = network_client_factory(cmd.cli_ctx)
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    url_map = next((x for x in ag.url_path_maps if x.name == url_path_map_name), None)
    if not url_map:
        raise CLIError('URL path map "{}" not found.'.format(url_path_map_name))
    default_backend_pool = SubResource(id=url_map.default_backend_address_pool.id) \
        if url_map.default_backend_address_pool else None
    default_http_settings = SubResource(id=url_map.default_backend_http_settings.id) \
        if url_map.default_backend_http_settings else None
    new_rule = ApplicationGatewayPathRule(
        name=item_name,
        paths=paths,
        backend_address_pool=SubResource(id=address_pool) if address_pool else default_backend_pool,
        backend_http_settings=SubResource(id=http_settings) if http_settings else default_http_settings)
    if cmd.supported_api_version(min_api='2017-06-01'):
        default_redirect = SubResource(id=url_map.default_redirect_configuration.id) \
            if url_map.default_redirect_configuration else None
        new_rule.redirect_configuration = SubResource(id=redirect_config) if redirect_config else default_redirect
    _upsert(url_map, 'path_rules', new_rule, 'name')
    return sdk_no_wait(no_wait, ncf.application_gateways.create_or_update,
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
    return sdk_no_wait(no_wait, ncf.application_gateways.create_or_update,
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

    return sdk_no_wait(no_wait, ncf.create_or_update, resource_group_name, application_gateway_name, ag)


def set_ag_waf_config_2017_03_01(cmd, resource_group_name, application_gateway_name, enabled,
                                 firewall_mode=None,
                                 rule_set_type='OWASP', rule_set_version=None,
                                 disabled_rule_groups=None,
                                 disabled_rules=None, no_wait=False):
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

    return sdk_no_wait(no_wait, ncf.create_or_update, resource_group_name, application_gateway_name, ag)


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


# region ApplicationSecurityGroups
def create_asg(cmd, client, resource_group_name, application_security_group_name, location=None, tags=None):
    ApplicationSecurityGroup = cmd.get_models('ApplicationSecurityGroup')
    asg = ApplicationSecurityGroup(location=location, tags=tags)
    return client.create_or_update(resource_group_name, application_security_group_name, asg)


def update_asg(instance, tags=None):
    if tags is not None:
        instance.tags = tags
    return instance

# endregion


# region DdosProtectionPlans
def create_ddos_plan(cmd, resource_group_name, ddos_plan_name, location=None, tags=None, vnets=None):
    from azure.cli.core.commands import LongRunningOperation

    ddos_client = network_client_factory(cmd.cli_ctx).ddos_protection_plans
    DdosProtectionPlan, SubResource = cmd.get_models('DdosProtectionPlan', 'SubResource')
    plan = DdosProtectionPlan(
        name=ddos_plan_name,
        location=location,
        tags=tags
    )
    if not vnets:
        # if no VNETs can do a simple PUT
        return ddos_client.create_or_update(resource_group_name, ddos_plan_name, plan)

    # if VNETs specified, have to create the protection plan and then add the VNETs
    plan_id = LongRunningOperation(cmd.cli_ctx)(
        ddos_client.create_or_update(resource_group_name, ddos_plan_name, plan)).id

    logger.info('Attempting to attach VNets to newly created DDoS protection plan.')
    for subresource in vnets:
        vnet_client = network_client_factory(cmd.cli_ctx).virtual_networks
        id_parts = parse_resource_id(subresource.id)
        vnet = vnet_client.get(id_parts['resource_group'], id_parts['name'])
        vnet.ddos_protection_plan = SubResource(id=plan_id)
        vnet_client.create_or_update(id_parts['resource_group'], id_parts['name'], vnet)
    return ddos_client.get(resource_group_name, ddos_plan_name)


def update_ddos_plan(cmd, instance, tags=None, vnets=None):
    SubResource = cmd.get_models('SubResource')

    if tags is not None:
        instance.tags = tags
    if vnets == "":
        vnets = []
    if vnets is not None:
        logger.info('Attempting to update the VNets attached to the DDoS protection plan.')
        vnet_ids = set([x.id for x in vnets])
        existing_vnet_ids = set([x.id for x in instance.virtual_networks or []])
        client = network_client_factory(cmd.cli_ctx).virtual_networks
        for vnet_id in vnet_ids.difference(existing_vnet_ids):
            logger.info("Adding VNet '%s' to plan.", vnet_id)
            id_parts = parse_resource_id(vnet_id)
            vnet = client.get(id_parts['resource_group'], id_parts['name'])
            vnet.ddos_protection_plan = SubResource(id=instance.id)
            client.create_or_update(id_parts['resource_group'], id_parts['name'], vnet)
        for vnet_id in existing_vnet_ids.difference(vnet_ids):
            logger.info("Removing VNet '%s' from plan.", vnet_id)
            id_parts = parse_resource_id(vnet_id)
            vnet = client.get(id_parts['resource_group'], id_parts['name'])
            vnet.ddos_protection_plan = None
            client.create_or_update(id_parts['resource_group'], id_parts['name'], vnet)
    return instance


def list_ddos_plans(cmd, resource_group_name=None):
    client = network_client_factory(cmd.cli_ctx).ddos_protection_plans
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()
# endregion


# region DNS Commands
def create_dns_zone(cmd, client, resource_group_name, zone_name, location='global', tags=None,
                    if_none_match=False, zone_type='Public', resolution_vnets=None, registration_vnets=None):
    Zone = cmd.get_models('Zone', resource_type=ResourceType.MGMT_NETWORK_DNS)
    zone = Zone(location=location, tags=tags)

    if hasattr(zone, 'zone_type'):
        zone.zone_type = zone_type
        zone.registration_virtual_networks = registration_vnets
        zone.resolution_virtual_networks = resolution_vnets

    return client.create_or_update(resource_group_name, zone_name, zone, if_none_match='*' if if_none_match else None)


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
                          metadata=None, if_match=None, if_none_match=None, ttl=3600):
    ncf = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_NETWORK_DNS).record_sets
    record_set = RecordSet(ttl=ttl, metadata=metadata)
    return ncf.create_or_update(resource_group_name, zone_name, record_set_name,
                                record_set_type, record_set, if_match=if_match,
                                if_none_match='*' if if_none_match else None)


def list_dns_record_set(client, resource_group_name, zone_name, record_type=None):
    if record_type:
        return client.list_by_type(resource_group_name, zone_name, record_type)

    return client.list_by_dns_zone(resource_group_name, zone_name)


def update_dns_record_set(instance, metadata=None):
    if metadata is not None:
        instance.metadata = metadata
    return instance


def _type_to_property_name(key):
    type_dict = {
        'a': 'arecords',
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
                record_obj.update({'value': record.value, 'tag': record.tag, 'flags': record.flags})
            elif record_type == 'cname':
                record_obj.update({'alias': record.cname})
            elif record_type == 'mx':
                record_obj.update({'preference': record.preference, 'host': record.exchange})
            elif record_type == 'ns':
                record_obj.update({'host': record.nsdname})
            elif record_type == 'ptr':
                record_obj.update({'host': record.ptrdname})
            elif record_type == 'soa':
                record_obj.update({
                    'mname': record.host.rstrip('.') + '.',
                    'rname': record.email.rstrip('.') + '.',
                    'serial': record.serial_number, 'refresh': record.refresh_time,
                    'retry': record.retry_time, 'expire': record.expire_time,
                    'minimum': record.minimum_ttl
                })
                zone_obj['$ttl'] = record.minimum_ttl
            elif record_type == 'srv':
                record_obj.update({'priority': record.priority, 'weight': record.weight,
                                   'port': record.port, 'target': record.target})
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
    record_type = data['type'].lower()
    try:
        if record_type == 'aaaa':
            return AaaaRecord(ipv6_address=data['ip'])
        elif record_type == 'a':
            return ARecord(ipv4_address=data['ip'])
        elif (record_type == 'caa' and
              supported_api_version(cmd.cli_ctx, ResourceType.MGMT_NETWORK_DNS, min_api='2018-03-01-preview')):
            return CaaRecord(value=data['value'], flags=data['flags'], tag=data['tag'])
        elif record_type == 'cname':
            return CnameRecord(cname=data['alias'])
        elif record_type == 'mx':
            return MxRecord(preference=data['preference'], exchange=data['host'])
        elif record_type == 'ns':
            return NsRecord(nsdname=data['host'])
        elif record_type == 'ptr':
            return PtrRecord(ptrdname=data['host'])
        elif record_type == 'soa':
            return SoaRecord(host=data['host'], email=data['email'], serial_number=data['serial'],
                             refresh_time=data['refresh'], retry_time=data['retry'], expire_time=data['expire'],
                             minimum_ttl=data['minimum'])
        elif record_type == 'srv':
            return SrvRecord(priority=data['priority'], weight=data['weight'], port=data['port'], target=data['target'])
        elif record_type in ['txt', 'spf']:
            text_data = data['txt']
            return TxtRecord(value=text_data) if isinstance(text_data, list) else TxtRecord(value=[text_data])
    except KeyError as ke:
        raise CLIError("The {} record '{}' is missing a property.  {}"
                       .format(record_type, data['name'], ke))


# pylint: disable=too-many-statements
def import_zone(cmd, resource_group_name, zone_name, file_name):
    from azure.cli.core.util import read_file_content
    import sys
    file_text = read_file_content(file_name)
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
                    logger.warning('Cannot import %s. RecordType is not found. Skipping...', entry['type'].lower())
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
        except CloudError as ex:
            logger.error(ex)
    print("\n== {}/{} RECORDS IMPORTED SUCCESSFULLY: '{}' =="
          .format(cum_records, total_records, zone_name), file=sys.stderr)


def add_dns_aaaa_record(cmd, resource_group_name, zone_name, record_set_name, ipv6_address):
    record = AaaaRecord(ipv6_address=ipv6_address)
    record_type = 'aaaa'
    return _add_save_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name)


def add_dns_a_record(cmd, resource_group_name, zone_name, record_set_name, ipv4_address):
    record = ARecord(ipv4_address=ipv4_address)
    record_type = 'a'
    return _add_save_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                            'arecords')


def add_dns_caa_record(cmd, resource_group_name, zone_name, record_set_name, value, flags, tag):
    record = CaaRecord(flags=flags, tag=tag, value=value)
    record_type = 'caa'
    return _add_save_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name)


def add_dns_cname_record(cmd, resource_group_name, zone_name, record_set_name, cname):
    record = CnameRecord(cname=cname)
    record_type = 'cname'
    return _add_save_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                            is_list=False)


def add_dns_mx_record(cmd, resource_group_name, zone_name, record_set_name, preference, exchange):
    record = MxRecord(preference=int(preference), exchange=exchange)
    record_type = 'mx'
    return _add_save_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name)


def add_dns_ns_record(cmd, resource_group_name, zone_name, record_set_name, dname):
    record = NsRecord(nsdname=dname)
    record_type = 'ns'
    return _add_save_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name)


def add_dns_ptr_record(cmd, resource_group_name, zone_name, record_set_name, dname):
    record = PtrRecord(ptrdname=dname)
    record_type = 'ptr'
    return _add_save_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name)


def update_dns_soa_record(cmd, resource_group_name, zone_name, host=None, email=None,
                          serial_number=None, refresh_time=None, retry_time=None, expire_time=None,
                          minimum_ttl=None):
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

    return _add_save_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                            is_list=False)


def add_dns_srv_record(cmd, resource_group_name, zone_name, record_set_name, priority, weight,
                       port, target):
    record = SrvRecord(priority=priority, weight=weight, port=port, target=target)
    record_type = 'srv'
    return _add_save_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name)


def add_dns_txt_record(cmd, resource_group_name, zone_name, record_set_name, value):
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
    return _add_save_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name)


def remove_dns_aaaa_record(cmd, resource_group_name, zone_name, record_set_name, ipv6_address,
                           keep_empty_record_set=False):
    record = AaaaRecord(ipv6_address=ipv6_address)
    record_type = 'aaaa'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_a_record(cmd, resource_group_name, zone_name, record_set_name, ipv4_address,
                        keep_empty_record_set=False):
    record = ARecord(ipv4_address=ipv4_address)
    record_type = 'a'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_caa_record(cmd, resource_group_name, zone_name, record_set_name, value,
                          flags, tag, keep_empty_record_set=False):
    record = CaaRecord(flags=flags, tag=tag, value=value)
    record_type = 'caa'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_cname_record(cmd, resource_group_name, zone_name, record_set_name, cname,
                            keep_empty_record_set=False):
    record = CnameRecord(cname=cname)
    record_type = 'cname'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          is_list=False, keep_empty_record_set=keep_empty_record_set)


def remove_dns_mx_record(cmd, resource_group_name, zone_name, record_set_name, preference, exchange,
                         keep_empty_record_set=False):
    record = MxRecord(preference=int(preference), exchange=exchange)
    record_type = 'mx'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_ns_record(cmd, resource_group_name, zone_name, record_set_name, dname,
                         keep_empty_record_set=False):
    record = NsRecord(nsdname=dname)
    record_type = 'ns'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_ptr_record(cmd, resource_group_name, zone_name, record_set_name, dname,
                          keep_empty_record_set=False):
    record = PtrRecord(ptrdname=dname)
    record_type = 'ptr'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_srv_record(cmd, resource_group_name, zone_name, record_set_name, priority, weight,
                          port, target, keep_empty_record_set=False):
    record = SrvRecord(priority=priority, weight=weight, port=port, target=target)
    record_type = 'srv'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_txt_record(cmd, resource_group_name, zone_name, record_set_name, value,
                          keep_empty_record_set=False):
    record = TxtRecord(value=value)
    record_type = 'txt'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def _add_record(record_set, record, record_type, is_list=False):
    record_property = _type_to_property_name(record_type)

    if is_list:
        record_list = getattr(record_set, record_property)
        if record_list is None:
            setattr(record_set, record_property, [])
            record_list = getattr(record_set, record_property)
        record_list.append(record)
    else:
        setattr(record_set, record_property, record)


def _add_save_record(cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                     is_list=True):
    ncf = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_NETWORK_DNS).record_sets
    try:
        record_set = ncf.get(resource_group_name, zone_name, record_set_name, record_type)
    except CloudError:
        record_set = RecordSet(ttl=3600)

    _add_record(record_set, record, record_type, is_list)

    return ncf.create_or_update(resource_group_name, zone_name, record_set_name,
                                record_type, record_set)


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
        return Counter(l1) == Counter(l2)
    except TypeError:
        return False


# endregion


# region ExpressRoutes
def create_express_route(cmd, circuit_name, resource_group_name, bandwidth_in_mbps, peering_location,
                         service_provider_name, location=None, tags=None, no_wait=False,
                         sku_family=None, sku_tier=None):
    ExpressRouteCircuit, ExpressRouteCircuitSku, ExpressRouteCircuitServiceProviderProperties = cmd.get_models(
        'ExpressRouteCircuit', 'ExpressRouteCircuitSku', 'ExpressRouteCircuitServiceProviderProperties')
    client = network_client_factory(cmd.cli_ctx).express_route_circuits
    sku_name = '{}_{}'.format(sku_tier, sku_family)
    circuit = ExpressRouteCircuit(
        location=location, tags=tags,
        service_provider_properties=ExpressRouteCircuitServiceProviderProperties(
            service_provider_name=service_provider_name,
            peering_location=peering_location,
            bandwidth_in_mbps=bandwidth_in_mbps),
        sku=ExpressRouteCircuitSku(name=sku_name, tier=sku_tier, family=sku_family)
    )
    return sdk_no_wait(no_wait, client.create_or_update, resource_group_name, circuit_name, circuit)


def update_express_route(instance, bandwidth_in_mbps=None, peering_location=None,
                         service_provider_name=None, sku_family=None, sku_tier=None, tags=None):
    if bandwidth_in_mbps is not None:
        instance.service_provider_properties.bandwith_in_mbps = bandwidth_in_mbps

    if peering_location is not None:
        instance.service_provider_properties.peering_location = peering_location

    if service_provider_name is not None:
        instance.service_provider_properties.service_provider_name = service_provider_name

    if sku_family is not None:
        instance.sku.family = sku_family

    if sku_tier is not None:
        instance.sku.tier = sku_tier

    if tags is not None:
        instance.tags = tags

    return instance


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
                if not isinstance(network, version):
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
        route_filter=None):
    (ExpressRouteCircuitPeering, ExpressRouteCircuitPeeringConfig, RouteFilter) = \
        cmd.get_models('ExpressRouteCircuitPeering', 'ExpressRouteCircuitPeeringConfig', 'RouteFilter')

    if cmd.supported_api_version(min_api='2018-02-01'):
        ExpressRoutePeeringType = cmd.get_models('ExpressRoutePeeringType')
    else:
        ExpressRoutePeeringType = cmd.get_models('ExpressRouteCircuitPeeringType')

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

    return client.create_or_update(resource_group_name, circuit_name, peering_type, peering)


def _create_or_update_ipv6_peering(cmd, config, primary_peer_address_prefix, secondary_peer_address_prefix,
                                   route_filter, advertised_public_prefixes, customer_asn, routing_registry_name):
    if config:
        # update scenario
        if primary_peer_address_prefix:
            config.primary_peer_address_prefix = primary_peer_address_prefix

        if secondary_peer_address_prefix:
            config.secondary_peer_address_prefix = secondary_peer_address_prefix

        if route_filter:
            RouteFilter = cmd.get_models('RouteFilter')
            config.route_filter = RouteFilter(id=route_filter)

        if advertised_public_prefixes:
            config.microsoft_peering_config.advertised_public_prefixes = advertised_public_prefixes

        if customer_asn:
            config.microsoft_peering_config.customer_asn = customer_asn

        if routing_registry_name:
            config.microsoft_peering_config.routing_registry_name = routing_registry_name
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
                                 routing_registry_name=None, route_filter=None, ip_version='IPv4'):

    # update settings common to all peering types
    if peer_asn is not None:
        instance.peer_asn = peer_asn

    if vlan_id is not None:
        instance.vlan_id = vlan_id

    if shared_key is not None:
        instance.shared_key = shared_key

    if ip_version == 'IPv6':
        # update is the only way to add IPv6 peering options
        instance.ipv6_peering_config = _create_or_update_ipv6_peering(cmd, instance.ipv6_peering_config,
                                                                      primary_peer_address_prefix,
                                                                      secondary_peer_address_prefix, route_filter,
                                                                      advertised_public_prefixes, customer_asn,
                                                                      routing_registry_name)
    else:
        # IPv4 Microsoft Peering (or non-Microsoft Peering)
        if primary_peer_address_prefix is not None:
            instance.primary_peer_address_prefix = primary_peer_address_prefix

        if secondary_peer_address_prefix is not None:
            instance.secondary_peer_address_prefix = secondary_peer_address_prefix

        if route_filter is not None:
            RouteFilter = cmd.get_models('RouteFilter')
            instance.route_filter = RouteFilter(id=route_filter)

        try:
            if advertised_public_prefixes is not None:
                instance.microsoft_peering_config.advertised_public_prefixes = advertised_public_prefixes

            if customer_asn is not None:
                instance.microsoft_peering_config.customer_asn = customer_asn

            if routing_registry_name is not None:
                instance.microsoft_peering_config.routing_registry_name = routing_registry_name
        except AttributeError:
            raise CLIError('--advertised-public-prefixes, --customer-asn and --routing-registry-name are only '
                           'applicable for Microsoft Peering.')

    return instance
# endregion


# region LoadBalancers
def create_load_balancer(cmd, load_balancer_name, resource_group_name, location=None, tags=None,
                         backend_pool_name=None, frontend_ip_name='LoadBalancerFrontEnd',
                         private_ip_address=None, public_ip_address=None,
                         public_ip_address_allocation=None,
                         public_ip_dns_name=None, subnet=None, subnet_address_prefix='10.0.0.0/24',
                         virtual_network_name=None, vnet_address_prefix='10.0.0.0/16',
                         public_ip_address_type=None, subnet_type=None, validate=False,
                         no_wait=False, sku=None, frontend_ip_zone=None, public_ip_zone=None):
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
                                                              sku, public_ip_zone))
        public_ip_id = '{}/publicIPAddresses/{}'.format(network_id_template,
                                                        public_ip_address)

    load_balancer_resource = build_load_balancer_resource(
        cmd, load_balancer_name, location, tags, backend_pool_name, frontend_ip_name,
        public_ip_id, subnet_id, private_ip_address, private_ip_allocation, sku,
        frontend_ip_zone)
    load_balancer_resource['dependsOn'] = lb_dependencies
    master_template.add_resource(load_balancer_resource)
    master_template.add_output('loadBalancer', load_balancer_name, output_type='object')

    template = master_template.build()

    # deploy ARM template
    deployment_name = 'lb_deploy_' + random_string(32)
    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES).deployments
    properties = DeploymentProperties(template=template, parameters={}, mode='incremental')
    if validate:
        _log_pprint_template(template)
        return client.validate(resource_group_name, deployment_name, properties)

    return sdk_no_wait(no_wait, client.create_or_update, resource_group_name, deployment_name, properties)


def create_lb_inbound_nat_rule(
        cmd, resource_group_name, load_balancer_name, item_name, protocol, frontend_port,
        backend_port, frontend_ip_name=None, floating_ip="false", idle_timeout=None):
    InboundNatRule = cmd.get_models('InboundNatRule')
    ncf = network_client_factory(cmd.cli_ctx)
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    if not frontend_ip_name:
        frontend_ip_name = _get_default_name(lb, 'frontend_ip_configurations', '--frontend-ip-name')
    frontend_ip = _get_property(lb.frontend_ip_configurations, frontend_ip_name)  # pylint: disable=no-member
    new_rule = InboundNatRule(
        name=item_name, protocol=protocol,
        frontend_port=frontend_port, backend_port=backend_port,
        frontend_ip_configuration=frontend_ip,
        enable_floating_ip=floating_ip == 'true',
        idle_timeout_in_minutes=idle_timeout)
    _upsert(lb, 'inbound_nat_rules', new_rule, 'name')
    poller = ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)
    return _get_property(poller.result().inbound_nat_rules, item_name)


def set_lb_inbound_nat_rule(
        instance, parent, item_name, protocol=None, frontend_port=None,
        frontend_ip_name=None, backend_port=None, floating_ip=None, idle_timeout=None):
    if frontend_ip_name:
        instance.frontend_ip_configuration = \
            _get_property(parent.frontend_ip_configurations, frontend_ip_name)

    if floating_ip is not None:
        instance.enable_floating_ip = floating_ip == 'true'

    _set_param(instance, 'protocol', protocol)
    _set_param(instance, 'frontend_port', frontend_port)
    _set_param(instance, 'backend_port', backend_port)
    _set_param(instance, 'idle_timeout_in_minutes', idle_timeout)

    return parent


def create_lb_inbound_nat_pool(
        cmd, resource_group_name, load_balancer_name, item_name, protocol, frontend_port_range_start,
        frontend_port_range_end, backend_port, frontend_ip_name=None):
    InboundNatPool = cmd.get_models('InboundNatPool')
    ncf = network_client_factory(cmd.cli_ctx)
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    if not frontend_ip_name:
        frontend_ip_name = _get_default_name(lb, 'frontend_ip_configurations', '--frontend-ip-name')
    frontend_ip = _get_property(lb.frontend_ip_configurations, frontend_ip_name) \
        if frontend_ip_name else None
    new_pool = InboundNatPool(
        name=item_name,
        protocol=protocol,
        frontend_ip_configuration=frontend_ip,
        frontend_port_range_start=frontend_port_range_start,
        frontend_port_range_end=frontend_port_range_end,
        backend_port=backend_port)
    _upsert(lb, 'inbound_nat_pools', new_pool, 'name')
    poller = ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)
    return _get_property(poller.result().inbound_nat_pools, item_name)


def set_lb_inbound_nat_pool(
        instance, parent, item_name, protocol=None,
        frontend_port_range_start=None, frontend_port_range_end=None, backend_port=None,
        frontend_ip_name=None):
    _set_param(instance, 'protocol', protocol)
    _set_param(instance, 'frontend_port_range_start', frontend_port_range_start)
    _set_param(instance, 'frontend_port_range_end', frontend_port_range_end)
    _set_param(instance, 'backend_port', backend_port)

    if frontend_ip_name == '':
        instance.frontend_ip_configuration = None
    elif frontend_ip_name is not None:
        instance.frontend_ip_configuration = \
            _get_property(parent.frontend_ip_configurations, frontend_ip_name)

    return parent


def create_lb_frontend_ip_configuration(
        cmd, resource_group_name, load_balancer_name, item_name, public_ip_address=None,
        subnet=None, virtual_network_name=None, private_ip_address=None,
        private_ip_address_allocation='dynamic', zone=None):
    FrontendIPConfiguration, PublicIPAddress, Subnet = cmd.get_models(
        'FrontendIPConfiguration', 'PublicIPAddress', 'Subnet')
    ncf = network_client_factory(cmd.cli_ctx)
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    new_config = FrontendIPConfiguration(
        name=item_name,
        private_ip_address=private_ip_address,
        private_ip_allocation_method=private_ip_address_allocation,
        public_ip_address=PublicIPAddress(id=public_ip_address) if public_ip_address else None,
        subnet=Subnet(id=subnet) if subnet else None)

    if zone and cmd.supported_api_version(min_api='2017-06-01'):
        new_config.zones = zone

    _upsert(lb, 'frontend_ip_configurations', new_config, 'name')
    poller = ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)
    return _get_property(poller.result().frontend_ip_configurations, item_name)


def set_lb_frontend_ip_configuration(
        cmd, instance, parent, item_name, private_ip_address=None,
        private_ip_address_allocation=None, public_ip_address=None, subnet=None,
        virtual_network_name=None):
    PublicIPAddress, Subnet = cmd.get_models('PublicIPAddress', 'Subnet')
    if private_ip_address == '':
        instance.private_ip_allocation_method = private_ip_address_allocation
        instance.private_ip_address = None
    elif private_ip_address is not None:
        instance.private_ip_allocation_method = private_ip_address_allocation
        instance.private_ip_address = private_ip_address

    if subnet == '':
        instance.subnet = None
    elif subnet is not None:
        instance.subnet = Subnet(id=subnet)

    if public_ip_address == '':
        instance.public_ip_address = None
    elif public_ip_address is not None:
        instance.public_ip_address = PublicIPAddress(id=public_ip_address)

    return parent


def create_lb_backend_address_pool(cmd, resource_group_name, load_balancer_name, item_name):
    BackendAddressPool = cmd.get_models('BackendAddressPool')
    ncf = network_client_factory(cmd.cli_ctx)
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    new_pool = BackendAddressPool(name=item_name)
    _upsert(lb, 'backend_address_pools', new_pool, 'name')
    poller = ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)
    return _get_property(poller.result().backend_address_pools, item_name)


def create_lb_probe(cmd, resource_group_name, load_balancer_name, item_name, protocol, port,
                    path=None, interval=None, threshold=None):
    Probe = cmd.get_models('Probe')
    ncf = network_client_factory(cmd.cli_ctx)
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    new_probe = Probe(
        protocol=protocol, port=port, interval_in_seconds=interval, number_of_probes=threshold,
        request_path=path, name=item_name)
    _upsert(lb, 'probes', new_probe, 'name')
    poller = ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)
    return _get_property(poller.result().probes, item_name)


def set_lb_probe(instance, parent, item_name, protocol=None, port=None,
                 path=None, interval=None, threshold=None):
    _set_param(instance, 'protocol', protocol)
    _set_param(instance, 'port', port)
    _set_param(instance, 'request_path', path)
    _set_param(instance, 'interval_in_seconds', interval)
    _set_param(instance, 'number_of_probes', threshold)

    return parent


def create_lb_rule(
        cmd, resource_group_name, load_balancer_name, item_name,
        protocol, frontend_port, backend_port, frontend_ip_name=None,
        backend_address_pool_name=None, probe_name=None, load_distribution='default',
        floating_ip='false', idle_timeout=None):
    LoadBalancingRule = cmd.get_models('LoadBalancingRule')
    ncf = network_client_factory(cmd.cli_ctx)
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    if not frontend_ip_name:
        frontend_ip_name = _get_default_name(lb, 'frontend_ip_configurations', '--frontend-ip-name')
    if not backend_address_pool_name:
        backend_address_pool_name = _get_default_name(lb, 'backend_address_pools', '--backend-pool-name')
    new_rule = LoadBalancingRule(
        name=item_name,
        protocol=protocol,
        frontend_port=frontend_port,
        backend_port=backend_port,
        frontend_ip_configuration=_get_property(lb.frontend_ip_configurations,
                                                frontend_ip_name),
        backend_address_pool=_get_property(lb.backend_address_pools,
                                           backend_address_pool_name),
        probe=_get_property(lb.probes, probe_name) if probe_name else None,
        load_distribution=load_distribution,
        enable_floating_ip=floating_ip == 'true',
        idle_timeout_in_minutes=idle_timeout)
    _upsert(lb, 'load_balancing_rules', new_rule, 'name')
    poller = ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)
    return _get_property(poller.result().load_balancing_rules, item_name)


def set_lb_rule(
        instance, parent, item_name, protocol=None, frontend_port=None,
        frontend_ip_name=None, backend_port=None, backend_address_pool_name=None, probe_name=None,
        load_distribution='default', floating_ip=None, idle_timeout=None):
    _set_param(instance, 'protocol', protocol)
    _set_param(instance, 'frontend_port', frontend_port)
    _set_param(instance, 'backend_port', backend_port)
    _set_param(instance, 'idle_timeout_in_minutes', idle_timeout)
    _set_param(instance, 'load_distribution', load_distribution)

    if frontend_ip_name is not None:
        instance.frontend_ip_configuration = \
            _get_property(parent.frontend_ip_configurations, frontend_ip_name)

    if floating_ip is not None:
        instance.enable_floating_ip = floating_ip == 'true'

    if backend_address_pool_name is not None:
        instance.backend_address_pool = \
            _get_property(parent.backend_address_pools, backend_address_pool_name)

    if probe_name == '':
        instance.probe = None
    elif probe_name is not None:
        instance.probe = _get_property(parent.probes, probe_name)

    return parent


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
    return sdk_no_wait(no_wait, client.create_or_update,
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
               application_security_groups=None, no_wait=False):
    client = network_client_factory(cmd.cli_ctx).network_interfaces
    (NetworkInterface, NetworkInterfaceDnsSettings, NetworkInterfaceIPConfiguration, NetworkSecurityGroup,
     PublicIPAddress, Subnet) = cmd.get_models(
         'NetworkInterface', 'NetworkInterfaceDnsSettings', 'NetworkInterfaceIPConfiguration',
         'NetworkSecurityGroup', 'PublicIPAddress', 'Subnet')

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
        'subnet': Subnet(id=subnet)
    }
    if cmd.supported_api_version(min_api='2016-09-01'):
        ip_config_args['private_ip_address_version'] = private_ip_address_version
    if cmd.supported_api_version(min_api='2017-09-01'):
        ip_config_args['application_security_groups'] = application_security_groups
    ip_config = NetworkInterfaceIPConfiguration(**ip_config_args)

    if public_ip_address:
        ip_config.public_ip_address = PublicIPAddress(id=public_ip_address)
    nic.ip_configurations = [ip_config]
    return sdk_no_wait(no_wait, client.create_or_update, resource_group_name, network_interface_name, nic)


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
                         private_ip_address_allocation=None,
                         private_ip_address_version=None,
                         make_primary=False,
                         application_security_groups=None):
    NetworkInterfaceIPConfiguration, PublicIPAddress, Subnet = cmd.get_models(
        'NetworkInterfaceIPConfiguration', 'PublicIPAddress', 'Subnet')
    ncf = network_client_factory(cmd.cli_ctx)
    nic = ncf.network_interfaces.get(resource_group_name, network_interface_name)

    if cmd.supported_api_version(min_api='2016-09-01'):
        IPVersion = cmd.get_models('IPVersion')
        private_ip_address_version = private_ip_address_version or IPVersion.ipv4.value
        if private_ip_address_version == IPVersion.ipv4.value and not subnet:
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
        'private_ip_allocation_method': private_ip_address_allocation,
    }
    if cmd.supported_api_version(min_api='2016-09-01'):
        new_config_args['private_ip_address_version'] = private_ip_address_version
        new_config_args['primary'] = make_primary
    if cmd.supported_api_version(min_api='2017-09-01'):
        new_config_args['application_security_groups'] = application_security_groups
    new_config = NetworkInterfaceIPConfiguration(**new_config_args)

    _upsert(nic, 'ip_configurations', new_config, 'name')
    poller = ncf.network_interfaces.create_or_update(
        resource_group_name, network_interface_name, nic)
    return _get_property(poller.result().ip_configurations, ip_config_name)


def set_nic_ip_config(cmd, instance, parent, ip_config_name, subnet=None,
                      virtual_network_name=None, public_ip_address=None, load_balancer_name=None,
                      load_balancer_backend_address_pool_ids=None,
                      load_balancer_inbound_nat_rule_ids=None,
                      private_ip_address=None, private_ip_address_allocation=None,
                      private_ip_address_version='ipv4', make_primary=False,
                      application_security_groups=None):
    PublicIPAddress, Subnet = cmd.get_models('PublicIPAddress', 'Subnet')

    if make_primary:
        for config in parent.ip_configurations:
            config.primary = False
        instance.primary = True

    if private_ip_address == '':
        instance.private_ip_address = None
        instance.private_ip_allocation_method = 'dynamic'
        if cmd.supported_api_version(min_api='2016-09-01'):
            instance.private_ip_address_version = 'ipv4'
    elif private_ip_address is not None:
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
        load_balancer_name=None):
    BackendAddressPool = cmd.get_models('BackendAddressPool')
    client = network_client_factory(cmd.cli_ctx).network_interfaces
    nic = client.get(resource_group_name, network_interface_name)
    ip_config = _get_nic_ip_config(nic, ip_config_name)
    _upsert(ip_config, 'load_balancer_backend_address_pools',
            BackendAddressPool(id=backend_address_pool),
            'id')
    poller = client.create_or_update(resource_group_name, network_interface_name, nic)
    return _get_property(poller.result().ip_configurations, ip_config_name)


def remove_nic_ip_config_address_pool(
        cmd, resource_group_name, network_interface_name, ip_config_name, backend_address_pool,
        load_balancer_name=None):
    client = network_client_factory(cmd.cli_ctx).network_interfaces
    nic = client.get(resource_group_name, network_interface_name)
    ip_config = _get_nic_ip_config(nic, ip_config_name)
    keep_items = [x for x in ip_config.load_balancer_backend_address_pools or [] if x.id != backend_address_pool]
    ip_config.load_balancer_backend_address_pools = keep_items
    poller = client.create_or_update(resource_group_name, network_interface_name, nic)
    return _get_property(poller.result().ip_configurations, ip_config_name)


def add_nic_ip_config_inbound_nat_rule(
        cmd, resource_group_name, network_interface_name, ip_config_name, inbound_nat_rule,
        load_balancer_name=None):
    InboundNatRule = cmd.get_models('InboundNatRule')
    client = network_client_factory(cmd.cli_ctx).network_interfaces
    nic = client.get(resource_group_name, network_interface_name)
    ip_config = _get_nic_ip_config(nic, ip_config_name)
    _upsert(ip_config, 'load_balancer_inbound_nat_rules',
            InboundNatRule(id=inbound_nat_rule),
            'id')
    poller = client.create_or_update(resource_group_name, network_interface_name, nic)
    return _get_property(poller.result().ip_configurations, ip_config_name)


def remove_nic_ip_config_inbound_nat_rule(
        cmd, resource_group_name, network_interface_name, ip_config_name, inbound_nat_rule,
        load_balancer_name=None):
    client = network_client_factory(cmd.cli_ctx).network_interfaces
    nic = client.get(resource_group_name, network_interface_name)
    ip_config = _get_nic_ip_config(nic, ip_config_name)
    keep_items = \
        [x for x in ip_config.load_balancer_inbound_nat_rules if x.id != inbound_nat_rule]
    ip_config.load_balancer_inbound_nat_rules = keep_items
    poller = client.create_or_update(resource_group_name, network_interface_name, nic)
    return _get_property(poller.result().ip_configurations, ip_config_name)


# endregion


# region NetworkSecurityGroups
def create_nsg(cmd, resource_group_name, network_security_group_name, location=None, tags=None):
    client = network_client_factory(cmd.cli_ctx).network_security_groups
    NetworkSecurityGroup = cmd.get_models('NetworkSecurityGroup')
    nsg = NetworkSecurityGroup(location=location, tags=tags)
    return client.create_or_update(resource_group_name, network_security_group_name, nsg)


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
        if kwargs[prefix + 'address_prefix'].is_default:
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
    return ncf.security_rules.create_or_update(
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
    return ncf.security_rules.create_or_update(
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
        LongRunningOperation(cmd.cli_ctx)(client.delete(watcher_rg, watcher_name))


def configure_network_watcher(cmd, client, locations, resource_group_name=None, enabled=None, tags=None):
    watcher_list = list(client.list_all())
    existing_watchers = [w for w in watcher_list if w.location in locations]
    nonenabled_regions = list(set(locations) - set(l.location for l in existing_watchers))

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


def create_nw_connection_monitor(cmd, client, connection_monitor_name, watcher_rg, watcher_name,  # pylint: disable=unused-argument
                                 source_resource, resource_group_name=None, source_port=None, location=None,
                                 dest_resource=None, dest_port=None, dest_address=None,
                                 tags=None, do_not_start=None, monitoring_interval=60):
    ConnectionMonitor, ConnectionMonitorSource, ConnectionMonitorDestination = cmd.get_models(
        'ConnectionMonitor', 'ConnectionMonitorSource', 'ConnectionMonitorDestination')
    connection_monitor = ConnectionMonitor(
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
        monitoring_interval_in_seconds=monitoring_interval)
    return client.create_or_update(watcher_rg, watcher_name, connection_monitor_name, connection_monitor)


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
                          resource_group_name=None):
    ConnectivitySource, ConnectivityDestination = cmd.get_models('ConnectivitySource', 'ConnectivityDestination')
    source = ConnectivitySource(resource_id=source_resource, port=source_port)
    dest = ConnectivityDestination(resource_id=dest_resource, address=dest_address, port=dest_port)
    return client.check_connectivity(watcher_rg, watcher_name, source, dest)


def check_nw_ip_flow(cmd, client, vm, watcher_rg, watcher_name, direction, protocol, local, remote,
                     resource_group_name=None, nic=None, location=None):
    VerificationIPFlowParameters = cmd.get_models('VerificationIPFlowParameters')

    local_ip_address, local_port = local.split(':')
    remote_ip_address, remote_port = remote.split(':')
    if not is_valid_resource_id(vm):
        vm = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name,
            namespace='Microsoft.Compute', type='virtualMachines', name=vm)

    if nic and not is_valid_resource_id(nic):
        nic = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name,
            namespace='Microsoft.Network', type='networkInterfaces', name=nic)

    return client.verify_ip_flow(
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

    return client.get_next_hop(
        watcher_rg, watcher_name, NextHopParameters(target_resource_id=vm,
                                                    source_ip_address=source_ip,
                                                    destination_ip_address=dest_ip,
                                                    target_nic_resource_id=nic))


def show_nw_security_view(cmd, client, resource_group_name, vm, watcher_rg, watcher_name, location=None):
    if not is_valid_resource_id(vm):
        vm = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name,
            namespace='Microsoft.Compute', type='virtualMachines', name=vm)

    return client.get_vm_security_rules(watcher_rg, watcher_name, vm)


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
    return client.create(watcher_rg, watcher_name, capture_name, capture_params)


def set_nsg_flow_logging(cmd, client, watcher_rg, watcher_name, nsg, storage_account=None,
                         resource_group_name=None, enabled=None, retention=0):
    from azure.cli.core.commands import LongRunningOperation
    config = LongRunningOperation(cmd.cli_ctx)(client.get_flow_log_status(watcher_rg, watcher_name, nsg))
    if enabled is not None:
        config.enabled = enabled
    if storage_account is not None:
        config.storage_id = storage_account
    if retention is not None:
        RetentionPolicyParameters = cmd.get_models('RetentionPolicyParameters')
        config.retention_policy = RetentionPolicyParameters(days=retention, enabled=int(retention) > 0)
    return client.set_flow_log_configuration(watcher_rg, watcher_name, config)


def show_nsg_flow_logging(client, watcher_rg, watcher_name, nsg, resource_group_name=None):
    return client.get_flow_log_status(watcher_rg, watcher_name, nsg)


def start_nw_troubleshooting(cmd, client, watcher_name, watcher_rg, resource, storage_account,
                             storage_path, resource_type=None, resource_group_name=None,
                             no_wait=False):
    TroubleshootingParameters = cmd.get_models('TroubleshootingParameters')
    params = TroubleshootingParameters(target_resource_id=resource, storage_id=storage_account,
                                       storage_path=storage_path)
    return sdk_no_wait(no_wait, client.get_troubleshooting, watcher_rg, watcher_name, params)


def show_nw_troubleshooting_result(client, watcher_name, watcher_rg, resource, resource_type=None,
                                   resource_group_name=None):
    return client.get_troubleshooting_result(watcher_rg, watcher_name, resource)

# endregion


# region PublicIPAddresses
def create_public_ip(cmd, resource_group_name, public_ip_address_name, location=None, tags=None,
                     allocation_method=None, dns_name=None,
                     idle_timeout=4, reverse_fqdn=None, version=None, sku=None, zone=None, ip_tags=None):
    IPAllocationMethod, PublicIPAddress, PublicIPAddressDnsSettings = cmd.get_models(
        'IPAllocationMethod', 'PublicIPAddress', 'PublicIPAddressDnsSettings')
    client = network_client_factory(cmd.cli_ctx).public_ip_addresses
    if not allocation_method:
        allocation_method = IPAllocationMethod.static.value if (sku and sku.lower() == 'standard') \
            else IPAllocationMethod.dynamic.value

    public_ip_args = {
        'location': location,
        'tags': tags,
        'public_ip_allocation_method': allocation_method,
        'idle_timeout_in_minutes': idle_timeout,
        'dns_settings': None
    }
    if cmd.supported_api_version(min_api='2016-09-01'):
        public_ip_args['public_ip_address_version'] = version
    if cmd.supported_api_version(min_api='2017-06-01'):
        public_ip_args['zones'] = zone
    if cmd.supported_api_version(min_api='2017-11-01'):
        public_ip_args['ip_tags'] = ip_tags
    if sku:
        public_ip_args['sku'] = {'name': sku}
    public_ip = PublicIPAddress(**public_ip_args)

    if dns_name or reverse_fqdn:
        public_ip.dns_settings = PublicIPAddressDnsSettings(
            domain_name_label=dns_name,
            reverse_fqdn=reverse_fqdn)
    return client.create_or_update(resource_group_name, public_ip_address_name, public_ip)


def update_public_ip(cmd, instance, dns_name=None, allocation_method=None, version=None,
                     idle_timeout=None, reverse_fqdn=None, tags=None, sku=None, ip_tags=None):
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
    return instance


# endregion


# region RouteFilters
def create_route_filter(cmd, client, resource_group_name, route_filter_name, location=None, tags=None):
    RouteFilter = cmd.get_models('RouteFilter')
    return client.create_or_update(resource_group_name, route_filter_name,
                                   RouteFilter(location=location, tags=tags))


def list_route_filters(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)

    return client.list()


def create_route_filter_rule(cmd, client, resource_group_name, route_filter_name, rule_name, access, communities,
                             location=None):
    RouteFilterRule = cmd.get_models('RouteFilterRule')
    return client.create_or_update(resource_group_name, route_filter_name, rule_name,
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
    return ncf.route_tables.create_or_update(resource_group_name, route_table_name, route_table)


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
    return ncf.routes.create_or_update(resource_group_name, route_table_name, route_name, route)


def update_route(instance, address_prefix=None, next_hop_type=None, next_hop_ip_address=None):
    if address_prefix is not None:
        instance.address_prefix = address_prefix

    if next_hop_type is not None:
        instance.next_hop_type = next_hop_type

    if next_hop_ip_address is not None:
        instance.next_hop_ip_address = next_hop_ip_address
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
                                   routing_method, unique_dns_name, monitor_path='/',
                                   monitor_port=80, monitor_protocol=MonitorProtocol.http.value,
                                   profile_status=ProfileStatus.enabled.value,
                                   ttl=30, tags=None):
    from azure.mgmt.trafficmanager import TrafficManagerManagementClient
    from azure.mgmt.trafficmanager.models import Profile, DnsConfig, MonitorConfig
    client = get_mgmt_service_client(cmd.cli_ctx, TrafficManagerManagementClient).profiles
    profile = Profile(location='global', tags=tags, profile_status=profile_status,
                      traffic_routing_method=routing_method,
                      dns_config=DnsConfig(relative_name=unique_dns_name, ttl=ttl),
                      monitor_config=MonitorConfig(protocol=monitor_protocol,
                                                   port=monitor_port, path=monitor_path))
    return client.create_or_update(resource_group_name, traffic_manager_profile_name, profile)


def update_traffic_manager_profile(instance, profile_status=None, routing_method=None, tags=None,
                                   monitor_protocol=None, monitor_port=None, monitor_path=None,
                                   ttl=None):
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
    if monitor_path is not None:
        instance.monitor_config.path = monitor_path

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
                                    min_child_endpoints=None, geo_mapping=None):
    from azure.mgmt.trafficmanager import TrafficManagerManagementClient
    from azure.mgmt.trafficmanager.models import Endpoint
    ncf = get_mgmt_service_client(cmd.cli_ctx, TrafficManagerManagementClient).endpoints

    endpoint = Endpoint(target_resource_id=target_resource_id, target=target,
                        endpoint_status=endpoint_status, weight=weight, priority=priority,
                        endpoint_location=endpoint_location,
                        endpoint_monitor_status=endpoint_monitor_status,
                        min_child_endpoints=min_child_endpoints,
                        geo_mapping=geo_mapping)

    return ncf.create_or_update(resource_group_name, profile_name, endpoint_type, endpoint_name,
                                endpoint)


def update_traffic_manager_endpoint(instance, endpoint_type=None, endpoint_location=None,
                                    endpoint_status=None, endpoint_monitor_status=None,
                                    priority=None, target=None, target_resource_id=None,
                                    weight=None, min_child_endpoints=None, geo_mapping=None):
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
    if geo_mapping is not None:
        instance.geo_mapping = geo_mapping

    return instance


def list_traffic_manager_endpoints(cmd, resource_group_name, profile_name, endpoint_type=None):
    from azure.mgmt.trafficmanager import TrafficManagerManagementClient
    client = get_mgmt_service_client(cmd.cli_ctx, TrafficManagerManagementClient).profiles
    profile = client.get(resource_group_name, profile_name)
    return [e for e in profile.endpoints if not endpoint_type or e.type.endswith(endpoint_type)]


# endregion


# region VirtualNetworks
# pylint: disable=too-many-locals
def create_vnet(cmd, resource_group_name, vnet_name, vnet_prefixes='10.0.0.0/16',
                subnet_name=None, subnet_prefix=None, dns_servers=None,
                location=None, tags=None, vm_protection=None, ddos_protection=None,
                ddos_protection_plan=None):
    AddressSpace, DhcpOptions, Subnet, VirtualNetwork, SubResource = \
        cmd.get_models('AddressSpace', 'DhcpOptions', 'Subnet', 'VirtualNetwork', 'SubResource')
    client = network_client_factory(cmd.cli_ctx).virtual_networks
    tags = tags or {}

    vnet = VirtualNetwork(
        location=location, tags=tags,
        dhcp_options=DhcpOptions(dns_servers=dns_servers),
        address_space=AddressSpace(address_prefixes=(vnet_prefixes if isinstance(vnet_prefixes, list) else [vnet_prefixes])))  # pylint: disable=line-too-long
    if subnet_name:
        vnet.subnets = [Subnet(name=subnet_name, address_prefix=subnet_prefix)]
    if cmd.supported_api_version(min_api='2017-09-01'):
        vnet.enable_ddos_protection = ddos_protection
        vnet.enable_vm_protection = vm_protection
    if cmd.supported_api_version(min_api='2018-02-01'):
        vnet.ddos_protection_plan = SubResource(id=ddos_protection_plan) if ddos_protection_plan else None
    return client.create_or_update(resource_group_name, vnet_name, vnet)


def update_vnet(cmd, instance, vnet_prefixes=None, dns_servers=None, ddos_protection=None, vm_protection=None,
                ddos_protection_plan=None):
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
                  route_table=None, service_endpoints=None):
    '''Create a virtual network (VNet) subnet.
    :param str address_prefix: address prefix in CIDR format.
    :param str network_security_group: Name or ID of network security
        group to associate with the subnet.
    '''
    NetworkSecurityGroup, ServiceEndpoint, Subnet = cmd.get_models(
        'NetworkSecurityGroup', 'ServiceEndpointPropertiesFormat', 'Subnet')
    ncf = network_client_factory(cmd.cli_ctx)
    subnet = Subnet(name=subnet_name, address_prefix=address_prefix)

    if network_security_group:
        subnet.network_security_group = NetworkSecurityGroup(id=network_security_group)
    _set_route_table(ncf, resource_group_name, route_table, subnet)
    if service_endpoints:
        subnet.service_endpoints = []
        for service in service_endpoints:
            subnet.service_endpoints.append(ServiceEndpoint(service=service))

    return ncf.subnets.create_or_update(resource_group_name, virtual_network_name,
                                        subnet_name, subnet)


def update_subnet(cmd, instance, resource_group_name, address_prefix=None, network_security_group=None,
                  route_table=None, service_endpoints=None):
    '''update existing virtual sub network
    :param str address_prefix: New address prefix in CIDR format, for example 10.0.0.0/24.
    :param str network_security_group: attach with existing network security group,
        both name or id are accepted. Use empty string "" to detach it.
    '''
    NetworkSecurityGroup, ServiceEndpoint = cmd.get_models('NetworkSecurityGroup', 'ServiceEndpointPropertiesFormat')

    if address_prefix:
        instance.address_prefix = address_prefix

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

    return instance


def create_vnet_peering(cmd, resource_group_name, virtual_network_name, virtual_network_peering_name,
                        remote_virtual_network, allow_virtual_network_access=False,
                        allow_forwarded_traffic=False, allow_gateway_transit=False,
                        use_remote_gateways=False):
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
    return ncf.virtual_network_peerings.create_or_update(
        resource_group_name, virtual_network_name, virtual_network_peering_name, peering)


def update_vnet_peering(cmd, resource_group_name, virtual_network_name, virtual_network_peering_name, **kwargs):
    peering = kwargs['parameters']
    aux_subscription = parse_resource_id(peering.remote_virtual_network.id)['subscription']
    ncf = network_client_factory(cmd.cli_ctx, aux_subscriptions=[aux_subscription])
    return ncf.virtual_network_peerings.create_or_update(
        resource_group_name, virtual_network_name, virtual_network_peering_name, peering)

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
    _upsert(config, 'vpn_client_root_certificates', cert, 'name')
    return ncf.create_or_update(resource_group_name, gateway_name, gateway)


def delete_vnet_gateway_root_cert(cmd, resource_group_name, gateway_name, cert_name):
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)
    config = gateway.vpn_client_configuration

    try:
        cert = next(c for c in config.vpn_client_root_certificates if c.name == cert_name)
    except (AttributeError, StopIteration):
        raise CLIError('Certificate "{}" not found in gateway "{}"'.format(cert_name, gateway_name))
    config.vpn_client_root_certificates.remove(cert)

    return ncf.create_or_update(resource_group_name, gateway_name, gateway)


def create_vnet_gateway_revoked_cert(cmd, resource_group_name, gateway_name, thumbprint, cert_name):
    VpnClientRevokedCertificate = cmd.get_models('VpnClientRevokedCertificate')
    config, gateway, ncf = _prep_cert_create(cmd, gateway_name, resource_group_name)

    cert = VpnClientRevokedCertificate(name=cert_name, thumbprint=thumbprint)
    _upsert(config, 'vpn_client_revoked_certificates', cert, 'name')
    return ncf.create_or_update(resource_group_name, gateway_name, gateway)


def delete_vnet_gateway_revoked_cert(cmd, resource_group_name, gateway_name, cert_name):
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)
    config = gateway.vpn_client_configuration

    try:
        cert = next(c for c in config.vpn_client_revoked_certificates if c.name == cert_name)
    except (AttributeError, StopIteration):
        raise CLIError('Certificate "{}" not found in gateway "{}"'.format(cert_name, gateway_name))
    config.vpn_client_revoked_certificates.remove(cert)

    return ncf.create_or_update(resource_group_name, gateway_name, gateway)


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
                        no_wait=False, gateway_type=None, sku=None, vpn_type=None,
                        asn=None, bgp_peering_address=None, peer_weight=None,
                        address_prefixes=None, radius_server=None, radius_secret=None, client_protocol=None):
    (VirtualNetworkGateway, BgpSettings, SubResource, VirtualNetworkGatewayIPConfiguration, VirtualNetworkGatewaySku,
     VpnClientConfiguration, AddressSpace) = cmd.get_models(
         'VirtualNetworkGateway', 'BgpSettings', 'SubResource', 'VirtualNetworkGatewayIPConfiguration',
         'VirtualNetworkGatewaySku', 'VpnClientConfiguration', 'AddressSpace')

    client = network_client_factory(cmd.cli_ctx).virtual_network_gateways
    subnet = virtual_network + '/subnets/GatewaySubnet'
    active_active = len(public_ip_address) == 2
    vnet_gateway = VirtualNetworkGateway(
        gateway_type=gateway_type, vpn_type=vpn_type, location=location, tags=tags,
        sku=VirtualNetworkGatewaySku(name=sku, tier=sku), active_active=active_active,
        ip_configurations=[])
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

    if any((address_prefixes, radius_secret, radius_server, client_protocol)):
        vnet_gateway.vpn_client_configuration = VpnClientConfiguration()
        vnet_gateway.vpn_client_configuration.vpn_client_address_pool = AddressSpace()
        vnet_gateway.vpn_client_configuration.vpn_client_address_pool.address_prefixes = address_prefixes
        if cmd.supported_api_version(min_api='2017-06-01'):
            vnet_gateway.vpn_client_configuration.vpn_client_protocols = client_protocol
            vnet_gateway.vpn_client_configuration.radius_server_address = radius_server
            vnet_gateway.vpn_client_configuration.radius_server_secret = radius_secret

    return sdk_no_wait(no_wait, client.create_or_update,
                       resource_group_name, virtual_network_gateway_name, vnet_gateway)


def update_vnet_gateway(cmd, instance, sku=None, vpn_type=None, tags=None,
                        public_ip_address=None, gateway_type=None, enable_bgp=None,
                        asn=None, bgp_peering_address=None, peer_weight=None, virtual_network=None,
                        address_prefixes=None, radius_server=None, radius_secret=None, client_protocol=None):
    AddressSpace, SubResource, VirtualNetworkGatewayIPConfiguration, VpnClientConfiguration = cmd.get_models(
        'AddressSpace', 'SubResource', 'VirtualNetworkGatewayIPConfiguration', 'VpnClientConfiguration')

    if any((address_prefixes, radius_server, radius_secret, client_protocol)) and not instance.vpn_client_configuration:
        instance.vpn_client_configuration = VpnClientConfiguration()

    if address_prefixes is not None:
        if not instance.vpn_client_configuration.vpn_client_address_pool:
            instance.vpn_client_configuration.vpn_client_address_pool = AddressSpace()
        if not instance.vpn_client_configuration.vpn_client_address_pool.address_prefixes:
            instance.vpn_client_configuration.vpn_client_address_pool.address_prefixes = []
        instance.vpn_client_configuration.vpn_client_address_pool.address_prefixes = address_prefixes

    if client_protocol is not None:
        instance.vpn_client_configuration.vpn_client_protocols = client_protocol

    if radius_server is not None:
        instance.vpn_client_configuration.radius_server_address = radius_server

    if radius_secret is not None:
        instance.vpn_client_configuration.radius_server_secret = radius_secret

    if sku is not None:
        instance.sku.name = sku
        instance.sku.tier = sku

    if vpn_type is not None:
        instance.vpn_type = vpn_type

    if tags is not None:
        instance.tags = tags

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
        active_active = len(public_ip_address) == 2
        if instance.active_active and not active_active:
            logger.info('Placing gateway in active-standby mode.')
        elif not instance.active_active and active_active:
            logger.info('Placing gateway in active-active mode.')
        instance.active_active = active_active

    if gateway_type is not None:
        instance.gateway_type = gateway_type

    if enable_bgp is not None:
        instance.enable_bgp = enable_bgp.lower() == 'true'

    _validate_bgp_peering(cmd, instance, asn, bgp_peering_address, peer_weight)

    return instance


# region VPN CLIENT WORKAROUND
# This is needed due to NRP doing exactly the opposite of what the specification says they should do.
# pylint: disable=line-too-long, protected-access, mixed-line-endings
def _poll(self, update_cmd):
    from msrestazure.azure_operation import finished, failed, BadResponse, OperationFailed
    initial_url = self._response.request.url

    while not finished(self.status()):
        self._delay()
        headers = self._polling_cookie()

        if self._operation.location_url:
            self._response = update_cmd(
                self._operation.location_url, headers)
            self._operation.set_async_url_if_present(self._response)
            self._operation.get_status_from_location(
                self._response)
        elif self._operation.method == "PUT":
            self._response = update_cmd(initial_url, headers)
            self._operation.set_async_url_if_present(self._response)
            self._operation.get_status_from_resource(
                self._response)
        else:
            raise BadResponse(
                'Location header is missing from long-running operation.')

    if failed(self._operation.status):
        raise OperationFailed("Operation failed or cancelled")
    elif self._operation.should_do_final_get():
        self._response = update_cmd(initial_url)
        self._operation.get_status_from_resource(
            self._response)


# This is needed due to a bug in autorest code generation. It adds 202 as a valid status code.
def _vpn_client_core(self, url, resource_group_name, virtual_network_gateway_name, parameters, custom_headers=None, raw=False, **operation_config):
    import uuid
    from msrest.pipeline import ClientRawResponse
    from msrestazure.azure_operation import AzureOperationPoller
    path_format_arguments = {
        'resourceGroupName': self._serialize.url("resource_group_name", resource_group_name, 'str'),
        'virtualNetworkGatewayName': self._serialize.url("virtual_network_gateway_name", virtual_network_gateway_name, 'str'),
        'subscriptionId': self._serialize.url("self.config.subscription_id", self.config.subscription_id, 'str')
    }
    url = self._client.format_url(url, **path_format_arguments)

    # Construct parameters
    query_parameters = {}
    query_parameters['api-version'] = self._serialize.query("self.api_version", self.api_version, 'str')

    # Construct headers
    header_parameters = {}
    header_parameters['Content-Type'] = 'application/json; charset=utf-8'
    if self.config.generate_client_request_id:
        header_parameters['x-ms-client-request-id'] = str(uuid.uuid1())
    if custom_headers:
        header_parameters.update(custom_headers)
    if self.config.accept_language is not None:
        header_parameters['accept-language'] = self._serialize.header("self.config.accept_language", self.config.accept_language, 'str')

    # Construct body
    body_content = self._serialize.body(parameters, 'VpnClientParameters')

    # Construct and send request
    def long_running_send():

        request = self._client.post(url, query_parameters)
        return self._client.send(
            request, header_parameters, body_content, **operation_config)

    def get_long_running_status(status_link, headers=None):

        request = self._client.get(status_link)
        if headers:
            request.headers.update(headers)
        return self._client.send(
            request, header_parameters, **operation_config)

    def get_long_running_output(response):

        if response.status_code not in [200, 202]:
            exp = CloudError(response)
            exp.request_id = response.headers.get('x-ms-request-id')
            raise exp

        deserialized = None

        if response.status_code in [200, 202]:
            deserialized = self._deserialize('str', response)

        if raw:
            client_raw_response = ClientRawResponse(deserialized, response)
            return client_raw_response

        return deserialized

    if raw:
        response = long_running_send()
        return get_long_running_output(response)

    long_running_operation_timeout = operation_config.get(
        'long_running_operation_timeout',
        self.config.long_running_operation_timeout)
    return AzureOperationPoller(
        long_running_send, get_long_running_output,
        get_long_running_status, long_running_operation_timeout)


@mock.patch('msrestazure.azure_operation.AzureOperationPoller._poll', _poll)
def _generate_vpn_profile(
        self, resource_group_name, virtual_network_gateway_name, parameters, custom_headers=None, raw=False, **operation_config):
    # Construct URL
    url = '/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Network/virtualNetworkGateways/{virtualNetworkGatewayName}/generatevpnprofile'
    return _vpn_client_core(self, url, resource_group_name, virtual_network_gateway_name, parameters, custom_headers, raw, **operation_config)


@mock.patch('msrestazure.azure_operation.AzureOperationPoller._poll', _poll)
def _generatevpnclientpackage(
        self, resource_group_name, virtual_network_gateway_name, parameters, custom_headers=None, raw=False, **operation_config):
    # Construct URL
    url = '/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Network/virtualNetworkGateways/{virtualNetworkGatewayName}/generatevpnclientpackage'
    return _vpn_client_core(self, url, resource_group_name, virtual_network_gateway_name, parameters, custom_headers, raw, **operation_config)

# endregion VPN CLIENT WORKAROUND`


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
        return _generate_vpn_profile(client, resource_group_name, virtual_network_gateway_name, params)

    # legacy implementation
    return _generatevpnclientpackage(client, resource_group_name, virtual_network_gateway_name, params)

# endregion


# region VirtualNetworkGatewayConnections
# pylint: disable=too-many-locals
def create_vpn_connection(cmd, resource_group_name, connection_name, vnet_gateway1,
                          location=None, tags=None, no_wait=False, validate=False,
                          vnet_gateway2=None, express_route_circuit2=None, local_gateway2=None,
                          authorization_key=None, enable_bgp=False, routing_weight=10,
                          connection_type=None, shared_key=None,
                          use_policy_based_traffic_selectors=False):
    """
    :param str vnet_gateway1: Name or ID of the source virtual network gateway.
    :param str vnet_gateway2: Name or ID of the destination virtual network gateway to connect to
        using a 'Vnet2Vnet' connection.
    :param str local_gateway2: Name or ID of the destination local network gateway to connect to
        using an 'IPSec' connection.
    :param str express_route_circuit2: Name or ID of the destination ExpressRoute to connect to
        using an 'ExpressRoute' connection.
    :param str authorization_key: The authorization key for the VPN connection.
    :param bool enable_bgp: Enable BGP for this VPN connection.
    :param bool no_wait: Do not wait for the long-running operation to finish.
    :param bool validate: Display and validate the ARM template but do not create any resources.
    """
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
        use_policy_based_traffic_selectors)
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
    if validate:
        _log_pprint_template(template)
        return client.validate(resource_group_name, deployment_name, properties)

    return sdk_no_wait(no_wait, client.create_or_update,
                       resource_group_name, deployment_name, properties)


def update_vpn_connection(cmd, instance, routing_weight=None, shared_key=None, tags=None,
                          enable_bgp=None, use_policy_based_traffic_selectors=None):
    ncf = network_client_factory(cmd.cli_ctx)

    if routing_weight is not None:
        instance.routing_weight = routing_weight

    if shared_key is not None:
        instance.shared_key = shared_key

    if tags is not None:
        instance.tags = tags

    if enable_bgp is not None:
        instance.enable_bgp = enable_bgp

    if use_policy_based_traffic_selectors is not None:
        instance.use_policy_based_traffic_selectors = use_policy_based_traffic_selectors

    # TODO: Remove these when issue #1615 is fixed
    gateway1_id = parse_resource_id(instance.virtual_network_gateway1.id)
    instance.virtual_network_gateway1 = ncf.virtual_network_gateways.get(
        gateway1_id['resource_group'], gateway1_id['name'])

    if instance.virtual_network_gateway2:
        gateway2_id = parse_resource_id(instance.virtual_network_gateway2.id)
        instance.virtual_network_gateway2 = ncf.virtual_network_gateways.get(
            gateway2_id['resource_group'], gateway2_id['name'])

    if instance.local_network_gateway2:
        gateway2_id = parse_resource_id(instance.local_network_gateway2.id)
        instance.local_network_gateway2 = ncf.local_network_gateways.get(
            gateway2_id['resource_group'], gateway2_id['name'])

    return instance


def add_vpn_conn_ipsec_policy(cmd, resource_group_name, connection_name,
                              sa_life_time_seconds, sa_data_size_kilobytes,
                              ipsec_encryption, ipsec_integrity,
                              ike_encryption, ike_integrity, dh_group, pfs_group, no_wait=False):
    IpsecPolicy = cmd.get_models('IpsecPolicy')
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateway_connections
    conn = ncf.get(resource_group_name, connection_name)
    new_policy = IpsecPolicy(sa_life_time_seconds=sa_life_time_seconds,
                             sa_data_size_kilobytes=sa_data_size_kilobytes,
                             ipsec_encryption=ipsec_encryption,
                             ipsec_integrity=ipsec_integrity,
                             ike_encryption=ike_encryption,
                             ike_integrity=ike_integrity,
                             dh_group=dh_group,
                             pfs_group=pfs_group)
    if conn.ipsec_policies:
        conn.ipsec_policies.append(new_policy)
    else:
        conn.ipsec_policies = [new_policy]
    return sdk_no_wait(no_wait, ncf.create_or_update, resource_group_name, connection_name, conn)


def clear_vpn_conn_ipsec_policies(cmd, resource_group_name, connection_name, no_wait=False):
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateway_connections
    conn = ncf.get(resource_group_name, connection_name)
    conn.ipsec_policies = None
    conn.use_policy_based_traffic_selectors = False
    if no_wait:
        return sdk_no_wait(no_wait, ncf.create_or_update, resource_group_name, connection_name, conn)

    from azure.cli.core.commands import LongRunningOperation
    poller = sdk_no_wait(no_wait, ncf.create_or_update, resource_group_name, connection_name, conn)
    return LongRunningOperation(cmd.cli_ctx)(poller).ipsec_policies


def list_vpn_conn_ipsec_policies(cmd, resource_group_name, connection_name):
    ncf = network_client_factory(cmd.cli_ctx).virtual_network_gateway_connections
    return ncf.get(resource_group_name, connection_name).ipsec_policies
# endregion
