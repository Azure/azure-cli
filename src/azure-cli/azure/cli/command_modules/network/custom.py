# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=no-self-use, no-member, too-many-lines, unused-argument
# pylint: disable=protected-access, too-few-public-methods, line-too-long

from collections import Counter, OrderedDict

import socket
from knack.log import get_logger
from azure.mgmt.core.tools import parse_resource_id, is_valid_resource_id, resource_id

from azure.cli.core.aaz import AAZClientConfiguration, has_value, register_client, AAZFileArgTextFormat
from azure.cli.core.aaz._client import AAZMgmtClient
from azure.cli.core.aaz.utils import assign_aaz_list_arg
from azure.cli.core.commands.client_factory import get_subscription_id, get_mgmt_service_client

from azure.cli.core.util import CLIError, sdk_no_wait
from azure.cli.core.azclierror import InvalidArgumentValueError, ValidationError, \
    UnrecognizedArgumentError, ResourceNotFoundError, ArgumentUsageError
from azure.cli.core.profiles import ResourceType

from azure.cli.command_modules.network.zone_file.parse_zone_file import parse_zone_file
from azure.cli.command_modules.network.zone_file.make_zone_file import make_zone_file

from .aaz.latest.network import ListUsages as _UsagesList
from .aaz.latest.network.application_gateway import Update as _ApplicationGatewayUpdate
from .aaz.latest.network.application_gateway.address_pool import Create as _AddressPoolCreate, \
    Update as _AddressPoolUpdate
from .aaz.latest.network.application_gateway.auth_cert import Create as _AuthCertCreate, Update as _AuthCertUpdate
from .aaz.latest.network.application_gateway.client_cert import Add as _ClientCertAdd, Update as _ClientCertUpdate
from .aaz.latest.network.application_gateway.frontend_ip import Create as _FrontendIPCreate, Update as _FrontendIPUpdate
from .aaz.latest.network.application_gateway.http_listener import Create as _HTTPListenerCreate, \
    Update as _HTTPListenerUpdate
from .aaz.latest.network.application_gateway.http_settings import Create as _HTTPSettingsCreate, \
    Update as _HTTPSettingsUpdate
from .aaz.latest.network.application_gateway.identity import Assign as _IdentityAssign
from .aaz.latest.network.application_gateway.private_link import Add as _AGPrivateLinkAdd, \
    Remove as _AGPrivateLinkRemove
from .aaz.latest.network.application_gateway.private_link.ip_config import Add as _AGPrivateLinkIPConfigAdd
from .aaz.latest.network.application_gateway.listener import Create as _ListenerCreate, Update as _ListenerUpdate
from .aaz.latest.network.application_gateway.redirect_config import Create as _RedirectConfigCreate, \
    Update as _RedirectConfigUpdate
from .aaz.latest.network.application_gateway.rewrite_rule import Create as _AGRewriteRuleCreate, \
    Update as _AGRewriteRuleUpdate
from .aaz.latest.network.application_gateway.root_cert import Create as _RootCertCreate, Update as _RootCertUpdate
from .aaz.latest.network.application_gateway.routing_rule import Create as _RoutingRuleCreate, \
    Update as _RoutingRuleUpdate
from .aaz.latest.network.application_gateway.rule import Create as _RuleCreate, Update as _RuleUpdate
from .aaz.latest.network.application_gateway.settings import Create as _SettingsCreate, Update as _SettingsUpdate
from .aaz.latest.network.application_gateway.ssl_cert import Create as _SSLCertCreate, Update as _SSLCertUpdate
from .aaz.latest.network.application_gateway.ssl_policy import Set as _SSLPolicySet
from .aaz.latest.network.application_gateway.ssl_profile import Add as _SSLProfileAdd, Update as _SSLProfileUpdate
from .aaz.latest.network.application_gateway.url_path_map import Create as _URLPathMapCreate, \
    Update as _URLPathMapUpdate
from .aaz.latest.network.application_gateway.url_path_map.rule import Create as _URLPathMapRuleCreate
from .aaz.latest.network.application_gateway.waf_policy import Create as _WAFCreate
from .aaz.latest.network.application_gateway.waf_policy.custom_rule.match_condition import \
    Add as _WAFCustomRuleMatchConditionAdd
from .aaz.latest.network.application_gateway.waf_policy.policy_setting import Update as _WAFPolicySettingUpdate
from .aaz.latest.network.custom_ip.prefix import Create as _CustomIpPrefixCreate, Update as _CustomIpPrefixUpdate
from .aaz.latest.network.ddos_custom_policy import Update as _DdosCustomPolicyUpdate
from .aaz.latest.network.dns.record_set import List as _DNSRecordSetListByZone
from .aaz.latest.network.dns.zone import Create as _DNSZoneCreate
from .aaz.latest.network.express_route import Create as _ExpressRouteCreate, Update as _ExpressRouteUpdate
from .aaz.latest.network.express_route.gateway import Create as _ExpressRouteGatewayCreate, \
    Update as _ExpressRouteGatewayUpdate
from .aaz.latest.network.express_route.gateway.connection import Create as _ExpressRouteConnectionCreate, \
    Update as _ExpressRouteConnectionUpdate
from .aaz.latest.network.express_route.peering import Create as _ExpressRoutePeeringCreate, \
    Update as _ExpressRoutePeeringUpdate
from .aaz.latest.network.express_route.peering.connection import Create as _ExpressRoutePeeringConnectionCreate
from .aaz.latest.network.express_route.port import Create as _ExpressRoutePortCreate
from .aaz.latest.network.express_route.port.identity import Assign as _ExpressRoutePortIdentityAssign
from .aaz.latest.network.express_route.port.link import Update as _ExpressRoutePortLinkUpdate
from .aaz.latest.network.nic import Create as _NICCreate, Update as _NICUpdate
from .aaz.latest.network.nic.ip_config import Create as _NICIPConfigCreate, Update as _NICIPConfigUpdate
from .aaz.latest.network.nic.ip_config.inbound_nat_rule import Add as _NICIPConfigNATAdd, \
    Remove as _NICIPConfigNATRemove
from .aaz.latest.network.nsg import Create as _NSGCreate
from .aaz.latest.network.nsg.rule import Create as _NSGRuleCreate, Update as _NSGRuleUpdate
from .aaz.latest.network.public_ip import Create as _PublicIPCreate, Update as _PublicIPUpdate
from .aaz.latest.network.private_endpoint import Create as _PrivateEndpointCreate, Update as _PrivateEndpointUpdate
from .aaz.latest.network.private_endpoint.asg import Add as _PrivateEndpointAsgAdd
from .aaz.latest.network.private_endpoint.dns_zone_group import Create as _PrivateEndpointPrivateDnsZoneGroupCreate, \
    Add as _PrivateEndpointPrivateDnsZoneAdd
from .aaz.latest.network.private_endpoint.ip_config import Add as _PrivateEndpointIpConfigAdd
from .aaz.latest.network.private_link_service import Create as _PrivateLinkServiceCreate, \
    Update as _PrivateLinkServiceUpdate
from .aaz.latest.network.private_link_service.connection import Update as _PrivateEndpointConnectionUpdate
from .aaz.latest.network.public_ip.prefix import Create as _PublicIpPrefixCreate
from .aaz.latest.network.security_partner_provider import Create as _SecurityPartnerProviderCreate, \
    Update as _SecurityPartnerProviderUpdate
from .aaz.latest.network.virtual_appliance import Create as _VirtualApplianceCreate, Update as _VirtualApplianceUpdate
from .aaz.latest.network.vnet import Create as _VNetCreate, Update as _VNetUpdate
from .aaz.latest.network.vnet.peering import Create as _VNetPeeringCreate
from .aaz.latest.network.vnet.subnet import Create as _VNetSubnetCreate, Update as _VNetSubnetUpdate
from .aaz.latest.network.vnet_gateway import Create as _VnetGatewayCreate, Update as _VnetGatewayUpdate, \
    DisconnectVpnConnections as _VnetGatewayVpnConnectionsDisconnect, Show as _VNetGatewayShow, List as _VNetGatewayList
from .aaz.latest.network.vnet_gateway.aad import Assign as _VnetGatewayAadAssign
from .aaz.latest.network.vnet_gateway.ipsec_policy import Add as _VnetGatewayIpsecPolicyAdd
from .aaz.latest.network.vnet_gateway.nat_rule import Add as _VnetGatewayNatRuleAdd, List as _VnetGatewayNatRuleShow, \
    Remove as _VnetGatewayNatRuleRemove
from .aaz.latest.network.vnet_gateway.revoked_cert import Create as _VnetGatewayRevokedCertCreate
from .aaz.latest.network.vnet_gateway.root_cert import Create as _VnetGatewayRootCertCreate
from .aaz.latest.network.vnet_gateway.vpn_client import GenerateVpnProfile as _VpnProfileGenerate, \
    Generate as _VpnClientPackageGenerate
from .aaz.latest.network.vpn_connection import Update as _VpnConnectionUpdate, \
    ShowDeviceConfigScript as _VpnConnectionDeviceConfigScriptShow
from .aaz.latest.network.vpn_connection.ipsec_policy import Add as _VpnConnIpsecPolicyAdd
from .aaz.latest.network.vpn_connection.packet_capture import Stop as _VpnConnPackageCaptureStop
from .aaz.latest.network.vpn_connection.shared_key import Update as _VpnConnSharedKeyUpdate
from .operations.dns import (RecordSetAShow as DNSRecordSetAShow, RecordSetAAAAShow as DNSRecordSetAAAAShow,  # pylint: disable=unused-import
                             RecordSetDSShow as DNSRecordSetDSShow, RecordSetMXShow as DNSRecordSetMXShow,
                             RecordSetNAPTRShow as DNSRecordSetNAPTRShow, RecordSetNSShow as DNSRecordSetNSShow,
                             RecordSetPTRShow as DNSRecordSetPTRShow, RecordSetSRVShow as DNSRecordSetSRVShow,
                             RecordSetTLSAShow as DNSRecordSetTLSAShow, RecordSetTXTShow as DNSRecordSetTXTShow,
                             RecordSetCAAShow as DNSRecordSetCAAShow, RecordSetCNAMEShow as DNSRecordSetCNAMEShow,
                             RecordSetSOAShow as DNSRecordSetSOAShow)
from .operations.dns import (RecordSetACreate as DNSRecordSetACreate, RecordSetAAAACreate as DNSRecordSetAAAACreate,  # pylint: disable=unused-import
                             RecordSetDSCreate as DNSRecordSetDSCreate, RecordSetMXCreate as DNSRecordSetMXCreate,
                             RecordSetNAPTRCreate as DNSRecordSetNAPTRCreate, RecordSetNSCreate as DNSRecordSetNSCreate,
                             RecordSetPTRCreate as DNSRecordSetPTRCreate, RecordSetSRVCreate as DNSRecordSetSRVCreate,
                             RecordSetTLSACreate as DNSRecordSetTLSACreate, RecordSetTXTCreate as DNSRecordSetTXTCreate,
                             RecordSetCAACreate as DNSRecordSetCAACreate, RecordSetCNAMECreate as DNSRecordSetCNAMECreate,
                             RecordSetSOACreate as DNSRecordSetSOACreate)
from .operations.dns import (RecordSetAUpdate as DNSRecordSetAUpdate, RecordSetAAAAUpdate as DNSRecordSetAAAAUpdate,  # pylint: disable=unused-import
                             RecordSetDSUpdate as DNSRecordSetDSUpdate, RecordSetMXUpdate as DNSRecordSetMXUpdate,
                             RecordSetNAPTRUpdate as DNSRecordSetNAPTRUpdate, RecordSetNSUpdate as DNSRecordSetNSUpdate,
                             RecordSetPTRUpdate as DNSRecordSetPTRUpdate, RecordSetSRVUpdate as DNSRecordSetSRVUpdate,
                             RecordSetTLSAUpdate as DNSRecordSetTLSAUpdate, RecordSetTXTUpdate as DNSRecordSetTXTUpdate,
                             RecordSetCAAUpdate as DNSRecordSetCAAUpdate, RecordSetCNAMEUpdate as DNSRecordSetCNAMEUpdate)
from .operations.dns import (RecordSetADelete as DNSRecordSetADelete, RecordSetAAAADelete as DNSRecordSetAAAADelete,  # pylint: disable=unused-import
                             RecordSetDSDelete as DNSRecordSetDSDelete, RecordSetMXDelete as DNSRecordSetMXDelete,
                             RecordSetNAPTRDelete as DNSRecordSetNAPTRDelete, RecordSetNSDelete as DNSRecordSetNSDelete,
                             RecordSetPTRDelete as DNSRecordSetPTRDelete, RecordSetSRVDelete as DNSRecordSetSRVDelete,
                             RecordSetTLSADelete as DNSRecordSetTLSADelete, RecordSetTXTDelete as DNSRecordSetTXTDelete,
                             RecordSetCAADelete as DNSRecordSetCAADelete, RecordSetCNAMEDelete as DNSRecordSetCNAMEDelete)

logger = get_logger(__name__)

remove_basic_option_msg = "It's recommended to create with `%s`. " \
                          "Please be aware that Basic option will be removed in the future."

subnet_disable_ple_msg = ("`--disable-private-endpoint-network-policies` will be deprecated in the future, if you wanna"
                          "disable network policy for private endpoint, please use "
                          "`--private-endpoint-network-policies Disabled` instead.")

subnet_disable_pls_msg = ("`--disable-private-link-service-network-policies` will be deprecated in the future, if you "
                          "wanna disable network policy for private link service, please use "
                          "`--private-link-service-network-policies Disabled` instead.")


@register_client("NonRetryableClient")
class AAZNonRetryableClient(AAZMgmtClient):
    @classmethod
    def _build_configuration(cls, ctx, credential, **kwargs):
        from azure.cli.core.auth.util import resource_to_scopes
        from azure.core.pipeline.policies import RetryPolicy

        retry_policy = RetryPolicy(**kwargs)
        retry_policy._retry_on_status_codes.discard(429)
        kwargs["retry_policy"] = retry_policy

        return AAZClientConfiguration(
            credential=credential,
            credential_scopes=resource_to_scopes(ctx.cli_ctx.cloud.endpoints.active_directory_resource_id),
            **kwargs
        )


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


# region ApplicationGateways
# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
def _is_v2_sku(sku):
    return 'v2' in sku


def _add_aux_subscription(aux_subscriptions, added_resource_id):
    if added_resource_id and is_valid_resource_id(added_resource_id):
        res_parts = parse_resource_id(added_resource_id)
        aux_sub = res_parts['subscription']
        if aux_sub and aux_sub not in aux_subscriptions:
            aux_subscriptions.append(aux_sub)


def create_application_gateway(cmd, application_gateway_name, resource_group_name, location=None,
                               tags=None, no_wait=False, capacity=2,
                               cert_data=None, cert_password=None, key_vault_secret_id=None,
                               frontend_port=None, http_settings_cookie_based_affinity='disabled',
                               http_settings_port=80, http_settings_protocol='Http',
                               routing_rule_type='Basic', servers=None,
                               sku=None, priority=None, private_ip_address=None, public_ip_address=None,
                               public_ip_address_allocation=None,
                               subnet='default', subnet_address_prefix='10.0.0.0/24',
                               virtual_network_name=None, vnet_address_prefix='10.0.0.0/16',
                               public_ip_address_type=None, subnet_type=None, validate=False,
                               connection_draining_timeout=0, enable_http2=None, min_capacity=None, zones=None,
                               custom_error_pages=None, firewall_policy=None, max_capacity=None,
                               user_assigned_identity=None, enable_fips=None,
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
        private_link_ip_allocation_method = 'Static' if private_link_ip_address else 'Dynamic'

    app_gateway_resource = build_application_gateway_resource(
        cmd, application_gateway_name, location, tags, sku, sku_tier, capacity, servers, frontend_port,
        private_ip_address, private_ip_allocation, priority, cert_data, cert_password, key_vault_secret_id,
        http_settings_cookie_based_affinity, http_settings_protocol, http_settings_port,
        http_listener_protocol, routing_rule_type, public_ip_id, subnet_id,
        connection_draining_timeout, enable_http2, min_capacity, zones, custom_error_pages,
        firewall_policy, max_capacity, user_assigned_identity, enable_fips,
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


class ApplicationGatewayUpdate(_ApplicationGatewayUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZDictArg, AAZStrArg, AAZArgEnum
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.custom_error_pages = AAZDictArg(
            options=["--custom-error-pages"],
            help="Space-separated list of custom error pages in `STATUS_CODE=URL` format.",
            nullable=True,
        )
        args_schema.custom_error_pages.Element = AAZStrArg(
            nullable=True,
        )
        args_schema.http2.enum = AAZArgEnum({"Enabled": True, "Disabled": False})
        args_schema.custom_error_configurations._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.custom_error_pages):
            configurations = []
            for code, url in args.custom_error_pages.items():
                configurations.append({
                    "status_code": code,
                    "custom_error_page_url": url,
                })
            args.custom_error_configurations = configurations
        if has_value(args.sku):
            sku = str(args.sku)
            args.sku.tier = sku.split("_", 1)[0] if not _is_v2_sku(sku) else sku


class AuthCertCreate(_AuthCertCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZFileArg, AAZFileArgBase64EncodeFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.cert_file = AAZFileArg(
            options=["--cert-file"],
            help="Path to the certificate file.",
            required=True,
            fmt=AAZFileArgBase64EncodeFormat(),
        )
        args_schema.data._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.cert_file):
            args.data = args.cert_file


class AuthCertUpdate(_AuthCertUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZFileArg, AAZFileArgBase64EncodeFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.cert_file = AAZFileArg(
            options=["--cert-file"],
            help="Path to the certificate file.",
            required=True,
            fmt=AAZFileArgBase64EncodeFormat(),
            nullable=True,
        )
        args_schema.data._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.cert_file):
            args.data = args.cert_file


class AddressPoolCreate(_AddressPoolCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.servers = AAZListArg(
            options=["--servers"],
            help="Space-separated list of IP addresses or DNS names corresponding to backend servers."
        )
        args_schema.servers.Element = AAZStrArg()
        args_schema.backend_addresses._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args

        def server_trans(_, server):
            try:
                socket.inet_aton(str(server))  # pylint:disable=no-member
                return {"ip_address": server}
            except OSError:  # pylint:disable=no-member
                return {"fqdn": server}

        args.backend_addresses = assign_aaz_list_arg(
            args.backend_addresses,
            args.servers,
            element_transformer=server_trans
        )


class AddressPoolUpdate(_AddressPoolUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.servers = AAZListArg(
            options=["--servers"],
            help="Space-separated list of IP addresses or DNS names corresponding to backend servers.",
            nullable=True,
        )
        args_schema.servers.Element = AAZStrArg(
            nullable=True,
        )
        args_schema.backend_addresses._registered = False
        return args_schema

    class NonRetryableCreateOrUpdate(_AddressPoolUpdate.ApplicationGatewaysCreateOrUpdate):
        CLIENT_TYPE = "NonRetryableClient"

    def _execute_operations(self):
        self.pre_operations()
        self.ApplicationGatewaysGet(ctx=self.ctx)()
        self.pre_instance_update(self.ctx.selectors.subresource.required())
        self.InstanceUpdateByJson(ctx=self.ctx)()
        self.InstanceUpdateByGeneric(ctx=self.ctx)()
        self.post_instance_update(self.ctx.selectors.subresource.required())
        yield self.NonRetryableCreateOrUpdate(ctx=self.ctx)()
        self.post_operations()

    def pre_operations(self):
        args = self.ctx.args

        def server_trans(_, server):
            try:
                socket.inet_aton(str(server))  # pylint:disable=no-member
                return {"ip_address": server}
            except OSError:  # pylint:disable=no-member
                return {"fqdn": server}

        args.backend_addresses = assign_aaz_list_arg(
            args.backend_addresses,
            args.servers,
            element_transformer=server_trans
        )


class FrontedIPCreate(_FrontendIPCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vnet_name = AAZStrArg(
            options=["--vnet-name"],
            help="Name of the virtual network corresponding to the subnet."
        )
        args_schema.public_ip_address._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/publicIpAddresses/{}",
        )
        args_schema.subnet._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/virtualNetworks/{vnet_name}/subnets/{}",
        )
        args_schema.private_ip_allocation_method._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.private_ip_allocation_method = "Static" if has_value(args.private_ip_address) else "Dynamic"


class FrontedIPUpdate(_FrontendIPUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vnet_name = AAZStrArg(
            options=["--vnet-name"],
            help="Name of the virtual network corresponding to the subnet."
        )
        args_schema.subnet._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/virtualNetworks/{vnet_name}/subnets/{}",
        )
        args_schema.private_ip_allocation_method._registered = False
        return args_schema

    def post_instance_update(self, instance):
        instance.properties.private_ip_allocation_method = "Static" if has_value(instance.properties.private_ip_address) else "Dynamic"


class HTTPListenerCreate(_HTTPListenerCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.frontend_ip._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/frontendIPConfigurations/{}",
        )
        args_schema.frontend_port._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/frontendPorts/{}",
        )
        args_schema.ssl_cert._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/sslCertificates/{}",
        )
        args_schema.ssl_profile_id._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/sslProfiles/{}",
        )
        args_schema.waf_policy._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/ApplicationGatewayWebApplicationFirewallPolicies/{}",
        )
        args_schema.frontend_port._required = True
        args_schema.protocol._registered = False
        args_schema.require_server_name_indication._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.ssl_cert):
            args.protocol = "Https"
            args.require_server_name_indication = True if has_value(args.host_name) else None
        else:
            args.protocol = "Http"

    def pre_instance_create(self):
        args = self.ctx.args
        if not has_value(args.frontend_ip):
            instance = self.ctx.vars.instance
            frontend_ip_configurations = instance.properties.frontend_ip_configurations
            if len(frontend_ip_configurations) == 1:
                args.frontend_ip = instance.properties.frontend_ip_configurations[0].id
            elif len(frontend_ip_configurations) > 1:
                err_msg = "Multiple frontend IP configurations found. Specify --frontend-ip explicitly."
                raise ArgumentUsageError(err_msg)


class HTTPListenerUpdate(_HTTPListenerUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.frontend_ip._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/frontendIPConfigurations/{}",
        )
        args_schema.frontend_port._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/frontendPorts/{}",
        )
        args_schema.ssl_cert._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/sslCertificates/{}",
        )
        args_schema.ssl_profile_id._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/sslProfiles/{}",
        )
        args_schema.waf_policy._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/ApplicationGatewayWebApplicationFirewallPolicies/{}",
        )
        args_schema.frontend_port._nullable = False
        args_schema.protocol._registered = False
        args_schema.require_server_name_indication._registered = False
        return args_schema

    def post_instance_update(self, instance):
        instance.properties.protocol = "Https" if has_value(instance.properties.ssl_certificate) else "Http"
        cond1 = instance.properties.host_name
        cond2 = instance.properties.protocol.to_serialized_data().lower() == "https"
        instance.properties.require_server_name_indication = cond1 and cond2
        if not has_value(instance.properties.frontend_ip_configuration.id):
            instance.properties.frontend_ip_configuration = None
        if not has_value(instance.properties.ssl_certificate.id):
            instance.properties.ssl_certificate = None
        if not has_value(instance.properties.ssl_profile.id):
            instance.properties.ssl_profile = None
        if not has_value(instance.properties.firewall_policy.id):
            instance.properties.firewall_policy = None


class ListenerCreate(_ListenerCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.frontend_ip._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/frontendIPConfigurations/{}",
        )
        args_schema.frontend_port._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/frontendPorts/{}",
        )
        args_schema.ssl_cert._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/sslCertificates/{}",
        )
        args_schema.ssl_profile_id._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/sslProfiles/{}",
        )
        args_schema.frontend_port._required = True
        args_schema.protocol._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.protocol = "Tls" if has_value(args.ssl_cert) else "Tcp"

    def pre_instance_create(self):
        args = self.ctx.args
        if not has_value(args.frontend_ip):
            instance = self.ctx.vars.instance
            frontend_ip_configurations = instance.properties.frontend_ip_configurations
            if len(frontend_ip_configurations) == 1:
                args.frontend_ip = instance.properties.frontend_ip_configurations[0].id
            elif len(frontend_ip_configurations) > 1:
                err_msg = "Multiple frontend IP configurations found. Specify --frontend-ip explicitly."
                raise ArgumentUsageError(err_msg)

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class ListenerUpdate(_ListenerUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.frontend_ip._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/frontendIPConfigurations/{}",
        )
        args_schema.frontend_port._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/frontendPorts/{}",
        )
        args_schema.ssl_cert._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/sslCertificates/{}",
        )
        args_schema.ssl_profile_id._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/sslProfiles/{}",
        )
        args_schema.frontend_port._nullable = False
        args_schema.protocol._registered = False
        return args_schema

    def post_instance_update(self, instance):
        instance.properties.protocol = "Tls" if has_value(instance.properties.ssl_certificate) else "Tcp"
        if not has_value(instance.properties.frontend_ip_configuration.id):
            instance.properties.frontend_ip_configuration = None
        if not has_value(instance.properties.ssl_certificate.id):
            instance.properties.ssl_certificate = None
        if not has_value(instance.properties.ssl_profile.id):
            instance.properties.ssl_profile = None


class IdentityAssign(_IdentityAssign):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.identity = AAZResourceIdArg(
            options=["--identity"],
            help="Name or ID of the ManagedIdentity Resource.",
            required=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.ManagedIdentity"
                         "/userAssignedIdentities/{}",
            ),
        )
        args_schema.type._registered = False
        args_schema.user_assigned_identities._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.type = "UserAssigned"
        args.user_assigned_identities = {args.identity.to_serialized_data(): {}}

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


def remove_ag_identity(cmd, resource_group_name, application_gateway_name, no_wait=False):
    class IdentityRemove(_ApplicationGatewayUpdate):
        def pre_operations(self):
            args = self.ctx.args
            args.no_wait = no_wait

        def pre_instance_update(self, instance):
            instance.identity = None

    return IdentityRemove(cli_ctx=cmd.cli_ctx)(command_args={
        "name": application_gateway_name,
        "resource_group": resource_group_name
    })


class AGPrivateLinkAdd(_AGPrivateLinkAdd):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZBoolArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.frontend_ip = AAZStrArg(
            options=["--frontend-ip"],
            help="Frontend IP that the private link will associate to.",
            required=True,
        )
        args_schema.subnet = AAZStrArg(
            options=["--subnet"],
            help="Name or ID of a subnet within the same vnet of an application gateway.",
            arg_group="Properties",
            required=True,
        )
        args_schema.subnet_prefix = AAZStrArg(
            options=["--subnet-prefix"],
            help="CIDR prefix to use when creating a new subnet.",
            arg_group="Properties",
        )
        args_schema.ip_address = AAZStrArg(
            options=["--ip-address"],
            help="Static private IP address of a subnet for private link. If omitting, a dynamic one will be created.",
            arg_group="Properties",
        )
        args_schema.primary = AAZBoolArg(
            options=["--primary"],
            help="Whether the IP configuration is primary or not.",
            arg_group="Properties",
        )
        args_schema.ip_configurations._registered = False
        return args_schema

    def pre_instance_create(self):
        args = self.ctx.args
        instance = self.ctx.vars.instance
        if not any(fic for fic in instance.properties.frontend_ip_configurations if fic.name == args.frontend_ip):
            err_msg = "Frontend IP doesn't exist."
            raise ValidationError(err_msg)

        private_link_id = resource_id(
            subscription=self.ctx.subscription_id,
            resource_group=args.resource_group,
            namespace="Microsoft.Network",
            type="applicationGateways",
            name=args.gateway_name,
            child_type_1="privateLinkConfigurations",
            child_name_1=args.name
        )
        for fic in instance.properties.frontend_ip_configurations:
            if has_value(fic.properties.private_link_configuration) \
                    and fic.properties.private_link_configuration.id == private_link_id:
                err_msg = "Frontend IP already reference an existing private link."
                raise ValidationError(err_msg)
        # associate private link with frontend IP configuration
        for fic in instance.properties.frontend_ip_configurations:
            if fic.name == args.frontend_ip:
                fic.properties.private_link_configuration = {"id": private_link_id}

        if has_value(instance.properties.private_link_configurations):
            for plc in instance.properties.private_link_configurations:
                if plc.name == args.name:
                    err_msg = "Private link name duplicates."
                    raise ValidationError(err_msg)
        # prepare subnet for new private link
        rid = instance.properties.gateway_ip_configurations[0].properties.subnet.id.to_serialized_data()
        metadata = parse_resource_id(rid)
        if not is_valid_resource_id(args.subnet.to_serialized_data()):
            args.subnet = resource_id(
                subscription=metadata["subscription"],
                resource_group=metadata["resource_group"],
                namespace="Microsoft.Network",
                type="virtualNetworks",
                name=metadata["name"],
                child_type_1="subnets",
                child_name_1=args.subnet
            )

        from .aaz.latest.network.vnet import Show
        vnet = Show(cli_ctx=self.cli_ctx)(command_args={
            "name": metadata["name"],
            "resource_group": metadata["resource_group"]
        })
        for subnet in vnet["subnets"]:
            if subnet["id"] == args.subnet:
                break
        else:
            subnet_name = parse_resource_id(args.subnet.to_serialized_data())["child_name_1"]

            from azure.cli.core.commands import LongRunningOperation
            poller = VNetSubnetCreate(cli_ctx=self.cli_ctx)(command_args={
                "name": subnet_name,
                "vnet_name": metadata["name"],
                "resource_group": metadata["resource_group"],
                "address_prefix": args.subnet_prefix,
                "private_link_service_network_policies": "Disabled"
            })
            LongRunningOperation(self.cli_ctx)(poller)

        args.ip_configurations = [{
            "name": "PrivateLinkDefaultIPConfiguration",
            "private_ip_address": args.ip_address,
            "private_ip_allocation_method": "Static" if has_value(args.ip_address) else "Dynamic",
            "subnet": {"id": args.subnet},
            "primary": args.primary
        }]


class AGPrivateLinkRemove(_AGPrivateLinkRemove):
    def pre_instance_delete(self):
        args = self.ctx.args
        instance = self.ctx.vars.instance
        for plc in instance.properties.private_link_configurations:
            if plc.name == args.name:
                to_be_removed = plc
                break
        else:
            err_msg = "Private link doesn't exist."
            raise ValidationError(err_msg)

        for fic in instance.properties.frontend_ip_configurations:
            if has_value(fic.properties.private_link_configuration) \
                    and fic.properties.private_link_configuration.id == to_be_removed.id:
                fic.properties.private_link_configuration = None


class AGPrivateLinkIPConfigAdd(_AGPrivateLinkIPConfigAdd):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.private_ip_allocation_method._registered = False
        args_schema.subnet._registered = False
        return args_schema

    def pre_instance_create(self):
        args = self.ctx.args
        instance = self.ctx.vars.instance
        for plc in instance.properties.private_link_configurations:
            if plc.name == args.private_link:
                target_private_link = plc
                break
        else:
            err_msg = "Private link doesn't exist."
            raise ValidationError(err_msg)

        args.private_ip_allocation_method = "Static" if has_value(args.ip_address) else "Dynamic"
        subnet_id = target_private_link.properties.ip_configurations[0].properties.subnet.id
        args.subnet.id = subnet_id


# region application-gateway trusted-client-certificates
class ClientCertAdd(_ClientCertAdd):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZFileArg, AAZFileArgBase64EncodeFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.data = AAZFileArg(
            options=["--data"],
            help="Path to the certificate file.",
            required=True,
            fmt=AAZFileArgBase64EncodeFormat(),
        )
        args_schema.cert_data._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.data):
            args.cert_data = args.data

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class ClientCertUpdate(_ClientCertUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZFileArg, AAZFileArgBase64EncodeFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.data = AAZFileArg(
            options=["--data"],
            help="Path to the certificate file.",
            required=True,
            fmt=AAZFileArgBase64EncodeFormat(),
            nullable=True,
        )
        args_schema.cert_data._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.data):
            args.cert_data = args.data


def show_ag_backend_health(cmd, resource_group_name, application_gateway_name, expand=None,
                           protocol=None, host=None, path=None, timeout=None, host_name_from_http_settings=None,
                           match_body=None, match_status_codes=None, address_pool=None, http_settings=None):
    from azure.cli.core.commands import LongRunningOperation
    on_demand_arguments = {protocol, host, path, timeout, host_name_from_http_settings, match_body, match_status_codes,
                           address_pool, http_settings}
    if on_demand_arguments.difference({None}):
        if address_pool is not None and not is_valid_resource_id(address_pool):
            address_pool = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=resource_group_name,
                namespace="Microsoft.Network",
                type="applicationGateways",
                name=application_gateway_name,
                child_type_1="backendAddressPools",
                child_name_1=address_pool
            )
        if http_settings is not None and not is_valid_resource_id(http_settings):
            http_settings = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=resource_group_name,
                namespace="Microsoft.Network",
                type="applicationGateways",
                name=application_gateway_name,
                child_type_1="backendHttpSettingsCollection",
                child_name_1=http_settings
            )

        from .aaz.latest.network.application_gateway import HealthOnDemand
        return LongRunningOperation(cmd.cli_ctx)(
            HealthOnDemand(cli_ctx=cmd.cli_ctx)(command_args={
                "name": application_gateway_name,
                "resource_group": resource_group_name,
                "expand": expand,
                "protocol": protocol,
                "host": host,
                "path": path,
                "timeout": timeout,
                "host_name_from_http_settings": host_name_from_http_settings,
                "match_body": match_body,
                "match_status_codes": match_status_codes,
                "backend_address_pool": {"id": address_pool},
                "backend_http_settings": {"id": http_settings}
            })
        )

    from .aaz.latest.network.application_gateway import Health
    return LongRunningOperation(cmd.cli_ctx)(
        Health(cli_ctx=cmd.cli_ctx)(command_args={
            "name": application_gateway_name,
            "resource_group": resource_group_name,
            "expand": expand
        })
    )
# endregion


# region application-gateway ssl-profile
class SSLProfileAdd(_SSLProfileAdd):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZBoolArg, AAZListArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.client_auth_config = AAZBoolArg(
            options=["--client-auth-configuration", "--client-auth-config"],
            help="Client authentication configuration of the application gateway resource.",
        )
        args_schema.trusted_client_certs = AAZListArg(
            options=["--trusted-client-certificates", "--trusted-client-cert"],
            help="Array of references to application gateway trusted client certificates.",
        )
        args_schema.trusted_client_certs.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/trustedClientCertificates/{}",
            ),
        )
        args_schema.auth_configuration._registered = False
        args_schema.client_certificates._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.client_auth_config):
            args.auth_configuration.verify_client_cert_issuer_dn = args.client_auth_config
        args.client_certificates = assign_aaz_list_arg(
            args.client_certificates,
            args.trusted_client_certs,
            element_transformer=lambda _, cert_id: {"id": cert_id}
        )

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class SSLProfileUpdate(_SSLProfileUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZBoolArg, AAZListArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.client_auth_config = AAZBoolArg(
            options=["--client-auth-configuration", "--client-auth-config"],
            help="Client authentication configuration of the application gateway resource.",
            nullable=True,
        )
        args_schema.trusted_client_certs = AAZListArg(
            options=["--trusted-client-certificates", "--trusted-client-cert"],
            help="Array of references to application gateway trusted client certificates.",
            nullable=True,
        )
        args_schema.trusted_client_certs.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/trustedClientCertificates/{}",
            ),
            nullable=True,
        )
        args_schema.auth_configuration._registered = False
        args_schema.client_certificates._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.client_auth_config):
            args.auth_configuration.verify_client_cert_issuer_dn = args.client_auth_config
        args.client_certificates = assign_aaz_list_arg(
            args.client_certificates,
            args.trusted_client_certs,
            element_transformer=lambda _, cert_id: {"id": cert_id}
        )

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result
# endregion


class HTTPSettingsCreate(_HTTPSettingsCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZIntArg, AAZIntArgFormat, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.auth_certs = AAZListArg(
            options=["--auth-certs"],
            help="Space-separated list of authentication certificates (Names and IDs) to associate with the HTTP settings.",
        )
        args_schema.auth_certs.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/authenticationCertificates/{}",
            ),
        )
        args_schema.root_certs = AAZListArg(
            options=["--root-certs"],
            help="Space-separated list of trusted root certificates (Names and IDs) to associate with the HTTP settings. "
                 "`--host-name` or `--host-name-from-backend-pool` is required when this field is set.",
        )
        args_schema.root_certs.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/trustedRootCertificates/{}",
            ),
        )
        args_schema.connection_draining_timeout = AAZIntArg(
            options=["--connection-draining-timeout"],
            help="Time in seconds after a backend server is removed during which on open connection remains active. "
                 "Range from 0 (Disabled) to 3600.",
            default=0,
            fmt=AAZIntArgFormat(
                maximum=3600,
                minimum=0,
            ),
        )
        args_schema.probe._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/probes/{}",
        )
        args_schema.cookie_based_affinity._blank = "Enabled"
        args_schema.port._required = True
        args_schema.authentication_certificates._registered = False
        args_schema.trusted_root_certificates._registered = False
        args_schema.connection_draining._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.authentication_certificates = assign_aaz_list_arg(
            args.authentication_certificates,
            args.auth_certs,
            element_transformer=lambda _, auth_cert_id: {"id": auth_cert_id}
        )
        args.trusted_root_certificates = assign_aaz_list_arg(
            args.trusted_root_certificates,
            args.root_certs,
            element_transformer=lambda _, root_cert_id: {"id": root_cert_id}
        )
        timeout = args.connection_draining_timeout.to_serialized_data()
        args.connection_draining.enabled = bool(timeout)
        args.connection_draining.drain_timeout_in_sec = timeout or 1


class HTTPSettingsUpdate(_HTTPSettingsUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZIntArg, AAZIntArgFormat, AAZResourceIdArg, AAZResourceIdArgFormat

        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.auth_certs = AAZListArg(
            options=["--auth-certs"],
            help="Space-separated list of authentication certificates (Names and IDs) to associate with the HTTP settings.",
            nullable=True,
        )
        args_schema.auth_certs.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/authenticationCertificates/{}",
            ),
            nullable=True,
        )
        args_schema.root_certs = AAZListArg(
            options=["--root-certs"],
            help="Space-separated list of trusted root certificates (Names and IDs) to associate with the HTTP settings. "
                 "`--host-name` or `--host-name-from-backend-pool` is required when this field is set.",
            nullable=True,
        )
        args_schema.root_certs.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/trustedRootCertificates/{}",
            ),
            nullable=True,
        )
        args_schema.connection_draining_timeout = AAZIntArg(
            options=["--connection-draining-timeout"],
            help="Time in seconds after a backend server is removed during which on open connection remains active. "
                 "Range from 0 (Disabled) to 3600.",
            fmt=AAZIntArgFormat(
                maximum=3600,
                minimum=0,
            ),
            nullable=True,
        )
        args_schema.probe._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/probes/{}",
        )
        args_schema.cookie_based_affinity._blank = "Enabled"
        args_schema.authentication_certificates._registered = False
        args_schema.trusted_root_certificates._registered = False
        args_schema.connection_draining._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.authentication_certificates = assign_aaz_list_arg(
            args.authentication_certificates,
            args.auth_certs,
            element_transformer=lambda _, auth_cert_id: {"id": auth_cert_id}
        )
        args.trusted_root_certificates = assign_aaz_list_arg(
            args.trusted_root_certificates,
            args.root_certs,
            element_transformer=lambda _, root_cert_id: {"id": root_cert_id}
        )
        if has_value(args.connection_draining_timeout):
            timeout = args.connection_draining_timeout.to_serialized_data()
            args.connection_draining.enabled = bool(timeout)
            args.connection_draining.drain_timeout_in_sec = timeout or 1

    def post_instance_update(self, instance):
        if not has_value(instance.properties.probe.id):
            instance.properties.probe = None


class SettingsCreate(_SettingsCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.root_certs = AAZListArg(
            options=["--root-certs"],
            help="Space-separated list of trusted root certificates (Names and IDs) to associate with the HTTP settings. "
                 "`--host-name` or `--backend-pool-host-name` is required when this field is set.",
        )
        args_schema.root_certs.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/trustedRootCertificates/{}",
            ),
        )
        args_schema.probe._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/probes/{}",
        )
        args_schema.port._required = True
        args_schema.trusted_root_certificates._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.trusted_root_certificates = assign_aaz_list_arg(
            args.trusted_root_certificates,
            args.root_certs,
            element_transformer=lambda _, root_cert_id: {"id": root_cert_id}
        )

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class SettingsUpdate(_SettingsUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.root_certs = AAZListArg(
            options=["--root-certs"],
            help="Space-separated list of trusted root certificates (Names and IDs) to associate with the HTTP settings. "
                 "`--host-name` or `--backend-pool-host-name` is required when this field is set.",
            nullable=True,
        )
        args_schema.root_certs.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/trustedRootCertificates/{}",
            ),
            nullable=True,
        )
        args_schema.probe._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/probes/{}",
        )
        args_schema.trusted_root_certificates._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.trusted_root_certificates = assign_aaz_list_arg(
            args.trusted_root_certificates,
            args.root_certs,
            element_transformer=lambda _, root_cert_id: {"id": root_cert_id}
        )

    def post_instance_update(self, instance):
        if not has_value(instance.properties.probe.id):
            instance.properties.probe = None


class RedirectConfigCreate(_RedirectConfigCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.target_listener._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/httpListeners/{}",
        )
        args_schema.type._required = True
        return args_schema


class RedirectConfigUpdate(_RedirectConfigUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.target_listener._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/httpListeners/{}",
        )
        return args_schema

    def post_instance_update(self, instance):
        if not has_value(instance.properties.target_listener.id):
            instance.properties.target_listener = None
        if has_value(instance.properties.target_listener):
            instance.properties.target_url = None
        if has_value(instance.properties.target_url):
            instance.properties.target_listener = None


class AGRewriteRuleCreate(_AGRewriteRuleCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZDictArg, AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.request_headers = AAZDictArg(
            options=["--request-headers"],
            help="Space-separated list of HEADER=VALUE pairs. "
                 "Values from: `az network application-gateway rewrite-rule list-request-headers`.",
        )
        args_schema.request_headers.Element = AAZStrArg()
        args_schema.response_headers = AAZDictArg(
            options=["--response-headers"],
            help="Space-separated list of HEADER=VALUE pairs. "
                 "Values from: `az network application-gateway rewrite-rule list-response-headers`.",
        )
        args_schema.response_headers.Element = AAZStrArg()
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.request_headers):
            configurations = []
            for k, v in args.request_headers.items():
                configurations.append({"header_name": k, "header_value": v})
            args.request_header_configurations = configurations
        if has_value(args.response_headers):
            configurations = []
            for k, v in args.response_headers.items():
                configurations.append({"header_name": k, "header_value": v})
            args.response_header_configurations = configurations


class AGRewriteRuleUpdate(_AGRewriteRuleUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZDictArg, AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.request_headers = AAZDictArg(
            options=["--request-headers"],
            help="Space-separated list of HEADER=VALUE pairs. "
                 "Values from: `az network application-gateway rewrite-rule list-request-headers`.",
            nullable=True,
        )
        args_schema.request_headers.Element = AAZStrArg(
            nullable=True,
        )
        args_schema.response_headers = AAZDictArg(
            options=["--response-headers"],
            help="Space-separated list of HEADER=VALUE pairs. "
                 "Values from: `az network application-gateway rewrite-rule list-response-headers`.",
            nullable=True,
        )
        args_schema.response_headers.Element = AAZStrArg(
            nullable=True,
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.request_headers):
            if args.request_headers.to_serialized_data() is None:
                args.request_header_configurations = None
            else:
                configurations = []
                for k, v in args.request_headers.items():
                    configurations.append({"header_name": k, "header_value": v})
                args.request_header_configurations = configurations
        if has_value(args.response_headers):
            if args.response_headers.to_serialized_data() is None:
                args.response_header_configurations = None
            else:
                configurations = []
                for k, v in args.response_headers.items():
                    configurations.append({"header_name": k, "header_value": v})
                args.response_header_configurations = configurations


class RuleCreate(_RuleCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.address_pool._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/backendAddressPools/{}",
        )
        args_schema.http_listener._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/httpListeners/{}",
        )
        args_schema.http_settings._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/backendHttpSettingsCollection/{}",
        )
        args_schema.redirect_config._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/redirectConfigurations/{}",
        )
        args_schema.rewrite_rule_set._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/rewriteRuleSets/{}",
        )
        args_schema.url_path_map._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/urlPathMaps/{}",
        )
        return args_schema

    def pre_instance_create(self):
        args = self.ctx.args
        instance = self.ctx.vars.instance
        if not has_value(args.address_pool) and not has_value(args.redirect_config):
            address_pools = instance.properties.backend_address_pools
            if len(address_pools) == 1:
                args.address_pool = instance.properties.backend_address_pools[0].id
            elif len(address_pools) > 1:
                err_msg = "Multiple backend address pools found. Specify --address-pool explicitly."
                raise ArgumentUsageError(err_msg)
        if not has_value(args.http_settings) and not has_value(args.redirect_config):
            settings = instance.properties.backend_http_settings_collection
            if len(settings) == 1:
                args.http_settings = instance.properties.backend_http_settings_collection[0].id
            elif len(settings) > 1:
                err_msg = "Multiple backend settings found. Specify --http-settings explicitly."
                raise ArgumentUsageError(err_msg)
        if not has_value(args.http_listener):
            listeners = instance.properties.http_listeners
            if len(listeners) == 1:
                args.http_listener = instance.properties.http_listeners[0].id
            elif len(listeners) > 1:
                err_msg = "Multiple HTTP listeners found. Specify --http-listener explicitly."
                raise ArgumentUsageError(err_msg)

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class RuleUpdate(_RuleUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.address_pool._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/backendAddressPools/{}",
        )
        args_schema.http_listener._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/httpListeners/{}",
        )
        args_schema.http_settings._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/backendHttpSettingsCollection/{}",
        )
        args_schema.redirect_config._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/redirectConfigurations/{}",
        )
        args_schema.rewrite_rule_set._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/rewriteRuleSets/{}",
        )
        args_schema.url_path_map._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/urlPathMaps/{}",
        )
        return args_schema

    def post_instance_update(self, instance):
        if not has_value(instance.properties.backend_address_pool.id):
            instance.properties.backend_address_pool = None
        if not has_value(instance.properties.backend_http_settings.id):
            instance.properties.backend_http_settings = None
        if not has_value(instance.properties.http_listener.id):
            instance.properties.http_listener = None
        if not has_value(instance.properties.redirect_configuration.id):
            instance.properties.redirect_configuration = None
        if not has_value(instance.properties.rewrite_rule_set.id):
            instance.properties.rewrite_rule_set = None
        if not has_value(instance.properties.url_path_map.id):
            instance.properties.url_path_map = None


class RoutingRuleCreate(_RoutingRuleCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.address_pool._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/backendAddressPools/{}",
        )
        args_schema.listener._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/listeners/{}",
        )
        args_schema.settings._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/backendSettingsCollection/{}",
        )
        return args_schema

    def pre_instance_create(self):
        args = self.ctx.args
        instance = self.ctx.vars.instance
        if not has_value(args.address_pool):
            address_pools = instance.properties.backend_address_pools
            if len(address_pools) == 1:
                args.address_pool = instance.properties.backend_address_pools[0].id
            elif len(address_pools) > 1:
                err_msg = "Multiple backend address pools found. Specify --address-pool explicitly."
                raise ArgumentUsageError(err_msg)
        if not has_value(args.listener):
            listeners = instance.properties.listeners
            if len(listeners) == 1:
                args.listener = instance.properties.listeners[0].id
            elif len(listeners) > 1:
                err_msg = "Multiple listeners found. Specify --listener explicitly."
                raise ArgumentUsageError(err_msg)
        if not has_value(args.settings):
            settings = instance.properties.backend_settings_collection
            if len(settings) == 1:
                args.settings = instance.properties.backend_settings_collection[0].id
            elif len(settings) > 1:
                err_msg = "Multiple backend settings found. Specify --settings explicitly."
                raise ArgumentUsageError(err_msg)

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class RoutingRuleUpdate(_RoutingRuleUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.address_pool._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/backendAddressPools/{}",
        )
        args_schema.listener._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/listeners/{}",
        )
        args_schema.settings._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/backendSettingsCollection/{}",
        )
        return args_schema

    def post_instance_update(self, instance):
        if not has_value(instance.properties.backend_address_pool.id):
            instance.properties.backend_address_pool = None
        if not has_value(instance.properties.backend_settings.id):
            instance.properties.backend_settings = None
        if not has_value(instance.properties.listener.id):
            instance.properties.listener = None


class SSLCertCreate(_SSLCertCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZFileArg, AAZFileArgBase64EncodeFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.cert_file = AAZFileArg(
            options=["--cert-file"],
            help="Path to the pfx certificate file.",
            fmt=AAZFileArgBase64EncodeFormat(),
        )
        args_schema.data._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.cert_file):
            args.data = args.cert_file


class SSLCertUpdate(_SSLCertUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZFileArg, AAZFileArgBase64EncodeFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.cert_file = AAZFileArg(
            options=["--cert-file"],
            help="Path to the pfx certificate file.",
            fmt=AAZFileArgBase64EncodeFormat(),
            nullable=True,
        )
        args_schema.data._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.cert_file):
            args.data = args.cert_file


class SSLPolicySet(_SSLPolicySet):
    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.name):
            args.policy_type = "Predefined"
        elif not has_value(args.policy_type) \
                and (has_value(args.cipher_suites) or has_value(args.min_protocol_version)):
            args.policy_type = "Custom"


class RootCertCreate(_RootCertCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZFileArg, AAZFileArgBase64EncodeFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.cert_file = AAZFileArg(
            options=["--cert-file"],
            help="Path to the certificate file.",
            fmt=AAZFileArgBase64EncodeFormat(),
        )
        args_schema.data._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.cert_file):
            args.data = args.cert_file

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class RootCertUpdate(_RootCertUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZFileArg, AAZFileArgBase64EncodeFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.cert_file = AAZFileArg(
            options=["--cert-file"],
            help="Path to the certificate file.",
            fmt=AAZFileArgBase64EncodeFormat(),
            nullable=True,
        )
        args_schema.data._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.cert_file):
            args.data = args.cert_file


class URLPathMapCreate(_URLPathMapCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.rule_name = AAZStrArg(
            options=["--rule-name"],
            arg_group="First Rule",
            help="Name of the rule for a URL path map.",
            default="default",
        )
        args_schema.paths = AAZListArg(
            options=["--paths"],
            arg_group="First Rule",
            help="Space-separated list of paths to associate with the rule. "
                 "Valid paths start and end with \"/\", e.g, \"/bar/\".",
            required=True,
        )
        args_schema.paths.Element = AAZStrArg()
        args_schema.address_pool = AAZResourceIdArg(
            options=["--address-pool"],
            arg_group="First Rule",
            help="Name or ID of the backend address pool to use with the created rule.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/backendAddressPools/{}",
            ),
        )
        args_schema.http_settings = AAZResourceIdArg(
            options=["--http-settings"],
            arg_group="First Rule",
            help="Name or ID of the HTTP settings to use with the created rule.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/backendHttpSettingsCollection/{}",
            ),
        )
        args_schema.redirect_config = AAZResourceIdArg(
            options=["--redirect-config"],
            arg_group="First Rule",
            help="Name or ID of the redirect configuration to use with the created rule.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/redirectConfigurations/{}",
            ),
        )
        args_schema.rewrite_rule_set = AAZResourceIdArg(
            options=["--rewrite-rule-set"],
            arg_group="First Rule",
            help="Name or ID of the rewrite rule set. If not specified, the default for the map will be used.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/rewriteRuleSets/{}",
            ),
        )
        args_schema.waf_policy = AAZResourceIdArg(
            options=["--waf-policy"],
            arg_group="First Rule",
            help="Name or ID of a web application firewall policy resource.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/ApplicationGatewayWebApplicationFirewallPolicies/{}",
            ),
        )
        # add templates for resource id
        args_schema.default_address_pool._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/backendAddressPools/{}",
        )
        args_schema.default_http_settings._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/backendHttpSettingsCollection/{}",
        )
        args_schema.default_redirect_config._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/redirectConfigurations/{}",
        )
        args_schema.default_rewrite_rule_set._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/rewriteRuleSets/{}",
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        rules = [{
            "name": args.rule_name,
            "paths": args.paths,
            "backend_address_pool": {"id": args.address_pool} if has_value(args.address_pool) else None,
            "backend_http_settings": {"id": args.http_settings} if has_value(args.http_settings) else None,
            "redirect_configuration": {"id": args.redirect_config} if has_value(args.redirect_config) else None,
            "rewrite_rule_set": {"id": args.rewrite_rule_set} if has_value(args.rewrite_rule_set) else None,
            "firewall_policy": {"id": args.waf_policy} if has_value(args.waf_policy) else None,
        }]
        args.rules = rules


class URLPathMapUpdate(_URLPathMapUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        # apply templates for resource id
        args_schema.default_address_pool._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/backendAddressPools/{}",
        )
        args_schema.default_http_settings._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/backendHttpSettingsCollection/{}",
        )
        args_schema.default_redirect_config._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/redirectConfigurations/{}",
        )
        args_schema.default_rewrite_rule_set._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/rewriteRuleSets/{}",
        )
        return args_schema


class URLPathMapRuleCreate(_URLPathMapRuleCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.paths._required = True
        # add templates for resource id
        args_schema.address_pool._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/backendAddressPools/{}",
        )
        args_schema.http_settings._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/backendHttpSettingsCollection/{}",
        )
        args_schema.redirect_config._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/redirectConfigurations/{}",
        )
        args_schema.rewrite_rule_set._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/rewriteRuleSets/{}",
        )
        args_schema.waf_policy._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/ApplicationGatewayWebApplicationFirewallPolicies/{}",
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.address_pool) and has_value(args.redirect_config):
            err_msg = "Cannot reference a BackendAddressPool when Redirect Configuration is specified."
            raise ArgumentUsageError(err_msg)


def set_ag_waf_config(cmd, resource_group_name, application_gateway_name, enabled,
                      firewall_mode=None, rule_set_type="OWASP", rule_set_version=None,
                      disabled_rule_groups=None, disabled_rules=None, no_wait=False,
                      request_body_check=None, max_request_body_size=None, file_upload_limit=None, exclusions=None):
    waf_config = {
        "enabled": enabled == "true",
        "firewall_mode": firewall_mode,
        "rule_set_type": rule_set_type,
        "rule_set_version": rule_set_version
    }

    class WAFConfigSet(_ApplicationGatewayUpdate):
        def pre_operations(self):
            args = self.ctx.args
            args.no_wait = no_wait

        def pre_instance_update(self, instance):
            def _flatten(collection, expand_property_fn):
                for each in collection:
                    yield from expand_property_fn(each)

            if disabled_rule_groups or disabled_rules:
                disabled_groups = []
                # disabled groups can be added directly
                for group in disabled_rule_groups or []:
                    disabled_groups.append({"rule_group_name": group})
                # for disabled rules, we have to look up the IDs
                if disabled_rules:
                    rule_sets = list_ag_waf_rule_sets(cmd, _type=rule_set_type, version=rule_set_version, group='*')
                    for group in _flatten(rule_sets, lambda r: r["ruleGroups"]):
                        disabled_group = {
                            "rule_group_name": group["ruleGroupName"],
                            "rules": []
                        }
                        for rule in group["rules"]:
                            if str(rule["ruleId"]) in disabled_rules:
                                disabled_group["rules"].append(rule["ruleId"])
                        if disabled_group["rules"]:
                            disabled_groups.append(disabled_group)
                waf_config["disabled_rule_groups"] = disabled_groups
            waf_config["request_body_check"] = request_body_check
            waf_config["max_request_body_size_in_kb"] = max_request_body_size
            waf_config["file_upload_limit_in_mb"] = file_upload_limit
            waf_config["exclusions"] = exclusions

            instance.properties.web_application_firewall_configuration = waf_config

    return WAFConfigSet(cli_ctx=cmd.cli_ctx)(command_args={
        "name": application_gateway_name,
        "resource_group": resource_group_name
    })


def show_ag_waf_config(cmd, resource_group_name, application_gateway_name):
    from .aaz.latest.network.application_gateway import Show
    return Show(cli_ctx=cmd.cli_ctx)(command_args={
        "name": application_gateway_name,
        "resource_group": resource_group_name
    })["webApplicationFirewallConfiguration"]


def list_ag_waf_rule_sets(cmd, _type=None, version=None, group=None):
    from .aaz.latest.network.application_gateway.waf_config import ListRuleSets
    rule_sets = ListRuleSets(cli_ctx=cmd.cli_ctx)(command_args={})["value"]

    filtered_sets = []
    # filter by rule set name or version
    for rule_set in rule_sets:
        if _type and _type.lower() != rule_set["ruleSetType"].lower():
            continue
        if version and version.lower() != rule_set["ruleSetVersion"].lower():
            continue

        filtered_groups = []
        for rule_group in rule_set["ruleGroups"]:
            if not group:
                rule_group["rules"] = None
                filtered_groups.append(rule_group)
                continue

            if group.lower() == rule_group["ruleGroupName"].lower() or group == "*":
                filtered_groups.append(rule_group)
        if filtered_groups:
            rule_set["ruleGroups"] = filtered_groups
            filtered_sets.append(rule_set)
    return filtered_sets
# endregion


# region ApplicationGatewayWAFPolicy
class WAFCreate(_WAFCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.rule_set_type = AAZStrArg(
            options=["--type"],
            help="Type of the web application firewall rule set.",
            default="Microsoft_DefaultRuleSet",
            enum={
                "Microsoft_BotManagerRuleSet": "Microsoft_BotManagerRuleSet",
                "Microsoft_DefaultRuleSet": "Microsoft_DefaultRuleSet",
                "OWASP": "OWASP",
                "Microsoft_HTTPDDoSRuleSet": "Microsoft_HTTPDDoSRuleSet"
            },
        )
        args_schema.rule_set_version = AAZStrArg(
            options=["--version"],
            help="Version of the web application firewall rule set type. "
                 "0.1, 1.0, and 1.1 are used for Microsoft_BotManagerRuleSet",
            default="2.1"
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        managed_rule_set = {
            "rule_set_type": args.rule_set_type,
            "rule_set_version": args.rule_set_version
        }
        managed_rule_definition = {
            "managed_rule_sets": [managed_rule_set]
        }
        args.managed_rules = managed_rule_definition
# endregion


# region ApplicationGatewayWAFPolicyRules PolicySettings
def list_waf_policy_setting(cmd, resource_group_name, policy_name):
    from .aaz.latest.network.application_gateway.waf_policy import Show
    return Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "name": policy_name}
    )["policySettings"]
# endregion


# region ApplicationGatewayWAFPolicyRuleMatchConditions
class WAFCustomRuleMatchConditionAdd(_WAFCustomRuleMatchConditionAdd):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.match_variables = AAZListArg(
            options=["--match-variables"],
            help="Space-separated list of variables to use when matching. Variable values: RemoteAddr, RequestMethod, "
                 "QueryString, PostArgs, RequestUri, RequestHeaders, RequestBody, RequestCookies.",
            required=True,
        )
        args_schema.match_variables.Element = AAZStrArg()
        # filter arguments
        args_schema.variables._required = False
        args_schema.variables._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        variables = []
        for variable in args.match_variables:
            try:
                name, selector = str(variable).split(".", 1)
            except ValueError:
                name, selector = variable, None
            variables.append({
                "variable_name": name,
                "selector": selector,
            })
        args.variables = variables
        # validate
        if str(args.operator).lower() == "any" and has_value(args.values):
            raise ArgumentUsageError("\"Any\" operator does not require --values.")
        if str(args.operator).lower() != "any" and not has_value(args.values):
            raise ArgumentUsageError("Non-any operator requires --values.")


class WAFPolicySettingUpdate(_WAFPolicySettingUpdate):
    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result
# endregion


# region ApplicationGatewayWAFPolicy ManagedRule ManagedRuleSet
def add_waf_managed_rule_set(cmd, resource_group_name, policy_name,
                             rule_set_type, rule_set_version, rule_group_name=None, rules=None):
    """
    Add managed rule set to the WAF policy managed rules.
    Visit: https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-crs-rulegroups-rules
    """
    if rules is None:
        managed_rule_overrides = []
    else:
        managed_rule_overrides = rules

    if rule_set_type.lower() == "microsoft_httpddosruleset":
        for r in managed_rule_overrides:
            if not r.get('sensitivity', None):
                r['sensitivity'] = 'Medium'

    rule_group_override = None
    if rule_group_name is not None:
        rule_group_override = {
            "rule_group_name": rule_group_name,
            "rules": managed_rule_overrides
        }

    if rule_group_override is None:
        rule_group_overrides = []
    else:
        rule_group_overrides = [rule_group_override]

    new_managed_rule_set = {
        "rule_set_type": rule_set_type,
        "rule_set_version": rule_set_version,
        "rule_group_overrides": rule_group_overrides
    }

    from .aaz.latest.network.application_gateway.waf_policy import Update

    class WAFManagedRuleSetAdd(Update):
        def pre_instance_update(self, instance):
            for rule_set in instance.properties.managed_rules.managed_rule_sets:
                if rule_set.rule_set_type == rule_set_type and rule_set.rule_set_version == rule_set_version:
                    for rule_override in rule_set.rule_group_overrides:
                        if rule_override.rule_group_name == rule_group_name:
                            # add one rule
                            rule_override.rules.extend(managed_rule_overrides)
                            break
                    else:
                        # add one rule group
                        if rule_group_override is not None:
                            rule_set.rule_group_overrides.append(rule_group_override)
                    break
            else:
                # add new rule set
                instance.properties.managed_rules.managed_rule_sets.append(new_managed_rule_set)

    return WAFManagedRuleSetAdd(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "name": policy_name
    })


def update_waf_managed_rule_set(cmd, resource_group_name, policy_name,
                                rule_set_type, rule_set_version, rule_group_name=None, rules=None):
    """
    Update (Override) existing rule set of a WAF policy managed rules.
    """
    managed_rule_overrides = rules if rules else None

    rule_group_override = {
        "rule_group_name": rule_group_name,
        "rules": managed_rule_overrides
    } if managed_rule_overrides else None

    if rule_group_override is None:
        rule_group_overrides = []
    else:
        rule_group_overrides = [rule_group_override]

    new_managed_rule_set = {
        "rule_set_type": rule_set_type,
        "rule_set_version": rule_set_version,
        "rule_group_overrides": rule_group_overrides
    }

    from .aaz.latest.network.application_gateway.waf_policy import Update

    class WAFManagedRuleSetUpdate(Update):
        def pre_instance_update(self, instance):
            updated_rule_set = None
            for rule_set in instance.properties.managed_rules.managed_rule_sets:
                if rule_set.rule_set_type == rule_set_type and rule_set.rule_set_version != rule_set_version:
                    updated_rule_set = rule_set
                    break

                if rule_set.rule_set_type == rule_set_type and rule_set.rule_set_version == rule_set_version:
                    if rule_group_name is None:
                        updated_rule_set = rule_set
                        break

                    rg = next((g for g in rule_set.rule_group_overrides if g.rule_group_name == rule_group_name), None)
                    if rg:
                        rg.rules = managed_rule_overrides
                    else:
                        rule_set.rule_group_overrides.append(rule_group_override)

            if updated_rule_set:
                new_managed_rule_sets = []
                for rule_set in instance.properties.managed_rules.managed_rule_sets:
                    if rule_set == updated_rule_set:
                        continue

                    new_managed_rule_sets.append(rule_set)
                new_managed_rule_sets.append(new_managed_rule_set)

                instance.properties.managed_rules.managed_rule_sets = new_managed_rule_sets

    return WAFManagedRuleSetUpdate(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "name": policy_name
    })


def remove_waf_managed_rule_set(cmd, resource_group_name, policy_name,
                                rule_set_type, rule_set_version, rule_group_name=None):
    """
    Remove a managed rule set by rule set group name if rule_group_name is specified. Otherwise, remove all rule set.
    """
    from .aaz.latest.network.application_gateway.waf_policy import Update

    class WAFManagedRuleSetRemove(Update):
        def pre_instance_update(self, instance):
            delete_rule_set = None
            for rule_set in instance.properties.managed_rules.managed_rule_sets:
                if rule_set.rule_set_type == rule_set_type or rule_set.rule_set_version == rule_set_version:
                    if rule_group_name is None:
                        delete_rule_set = rule_set
                        break
                    # remove one rule from rule group
                    is_removed = False
                    new_rule_group_overrides = []
                    for rg in rule_set.rule_group_overrides:
                        if rg.rule_group_name == rule_group_name and not is_removed:
                            is_removed = True
                            continue

                        new_rule_group_overrides.append(rg)
                    if not is_removed:
                        err_msg = f"Rule set group [{rule_group_name}] is not found."
                        raise ResourceNotFoundError(err_msg)

                    rule_set.rule_group_overrides = new_rule_group_overrides

            if delete_rule_set:
                new_managed_rule_sets = []
                for rule_set in instance.properties.managed_rules.managed_rule_sets:
                    if rule_set == delete_rule_set:
                        continue

                    new_managed_rule_sets.append(rule_set)
                instance.properties.managed_rules.managed_rule_sets = new_managed_rule_sets

    return WAFManagedRuleSetRemove(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "name": policy_name
    })


def list_waf_managed_rules(cmd, resource_group_name, policy_name):
    from .aaz.latest.network.application_gateway.waf_policy import Show
    return Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "name": policy_name
    })["managedRules"]
# endregion


# region ApplicationGatewayWAFPolicy ManagedRule Exception
def remove_waf_managed_rule_exception(cmd, resource_group_name, policy_name):
    from .aaz.latest.network.application_gateway.waf_policy import Update

    class WAFExceptionRemove(Update):
        def pre_instance_update(self, instance):
            instance.properties.managed_rules.exceptions = []

    return WAFExceptionRemove(cli_ctx=cmd.cli_ctx)(command_args={
        "name": policy_name,
        "resource_group": resource_group_name,
    })
# endregion


# region ApplicationGatewayWAFPolicy ManagedRule OwaspCrsExclusionEntry
# pylint: disable=too-many-nested-blocks
def remove_waf_managed_rule_exclusion(cmd, resource_group_name, policy_name):
    from .aaz.latest.network.application_gateway.waf_policy import Update

    class WAFExclusionRemove(Update):
        def pre_instance_update(self, instance):
            instance.properties.managed_rules.exclusions = []

    return WAFExclusionRemove(cli_ctx=cmd.cli_ctx)(command_args={
        "name": policy_name,
        "resource_group": resource_group_name,
    })


def add_waf_exclusion_rule_set(cmd, resource_group_name, policy_name,
                               rule_set_type, rule_set_version, match_variable, selector_match_operator, selector,
                               rule_group_name=None, rule_ids=None):
    # build current rules from ids
    if rule_ids is None:
        rules = []
    else:
        rules = [{"rule_id": rule_id} for rule_id in rule_ids]
    # build current rule group from rules
    curr_rule_group = None
    if rule_group_name is not None:
        curr_rule_group = {
            "rule_group_name": rule_group_name,
            "rules": rules,
        }
    # build current rule set from rule group
    if curr_rule_group is None:
        rule_groups = []
    else:
        rule_groups = [curr_rule_group]
    curr_rule_set = {
        "rule_set_type": rule_set_type,
        "rule_set_version": rule_set_version,
        "rule_groups": rule_groups,
    }

    from .aaz.latest.network.application_gateway.waf_policy import Update

    class WAFExclusionRuleSetAdd(Update):
        def pre_instance_update(self, instance):
            def _has_exclusion():
                for e in instance.properties.managed_rules.exclusions:
                    if (e.match_variable, e.selector_match_operator, e.selector) == (match_variable, selector_match_operator, selector):
                        return True

                return False

            if not _has_exclusion():
                exclusion = {
                    "match_variable": match_variable,
                    "selector_match_operator": selector_match_operator,
                    "selector": selector,
                    "exclusion_managed_rule_sets": [curr_rule_set],
                }
                instance.properties.managed_rules.exclusions.append(exclusion)
            else:
                for exclusion in instance.properties.managed_rules.exclusions:
                    if (exclusion.match_variable, exclusion.selector_match_operator, exclusion.selector) == (match_variable, selector_match_operator, selector):
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

    return WAFExclusionRuleSetAdd(cli_ctx=cmd.cli_ctx)(command_args={
        "name": policy_name,
        "resource_group": resource_group_name,
    })


def remove_waf_exclusion_rule_set(cmd, resource_group_name, policy_name,
                                  rule_set_type, rule_set_version, match_variable, selector_match_operator, selector,
                                  rule_group_name=None):
    from .aaz.latest.network.application_gateway.waf_policy import Update

    class WAFExclusionRuleSetRemove(Update):
        def pre_instance_update(self, instance):
            remove_rule_set, remove_exclusion = None, None
            for exclusion in instance.properties.managed_rules.exclusions:
                if (exclusion.match_variable, exclusion.selector_match_operator, exclusion.selector) == (match_variable, selector_match_operator, selector):
                    for rule_set in exclusion.exclusion_managed_rule_sets:
                        if rule_set.rule_set_type == rule_set_type or rule_set.rule_set_version == rule_set_version:
                            if rule_group_name is None:
                                remove_rule_set = rule_set
                                break
                        # remove one rule from rule group
                        is_removed = False
                        new_rule_groups = []
                        for rg in rule_set.rule_groups:
                            if rg.rule_group_name == rule_group_name and not is_removed:
                                is_removed = True
                                continue

                            new_rule_groups.append(rg)
                        if not is_removed:
                            err_msg = f"Rule set group [{rule_group_name}] is not found."
                            raise ResourceNotFoundError(err_msg)

                        rule_set.rule_groups = new_rule_groups

                        if not rule_set.rule_groups:
                            new_rule_sets = []
                            for rs in exclusion.exclusion_managed_rule_sets:
                                if rs == rule_set:
                                    continue

                                new_rule_sets.append(rs)
                            exclusion.exclusion_managed_rule_sets = new_rule_sets
                            if not exclusion.exclusion_managed_rule_sets:
                                remove_exclusion = exclusion

                    if remove_rule_set:
                        new_rule_sets = []
                        for rs in exclusion.exclusion_managed_rule_sets:
                            if rs == remove_rule_set:
                                continue

                            new_rule_sets.append(rs)
                        exclusion.exclusion_managed_rule_sets = new_rule_sets
                        if not exclusion.exclusion_managed_rule_sets:
                            remove_exclusion = exclusion

            if remove_exclusion:
                new_exclusions = []
                for exclusion in instance.properties.managed_rules.exclusions:
                    if exclusion == remove_exclusion:
                        continue

                    new_exclusions.append(exclusion)
                instance.properties.managed_rules.exclusions = new_exclusions

    return WAFExclusionRuleSetRemove(cli_ctx=cmd.cli_ctx)(command_args={
        "name": policy_name,
        "resource_group": resource_group_name,
    })
# endregion


# region DdosProtectionPlans
def create_ddos_plan(cmd, resource_group_name, ddos_plan_name, location=None, tags=None, vnets=None):
    from azure.cli.core.commands import LongRunningOperation
    from azure.cli.command_modules.network.aaz.latest.network.ddos_protection import Create
    Create_Ddos_Protection = Create(cli_ctx=cmd.cli_ctx)
    args = {
        "name": ddos_plan_name,
        "resource_group": resource_group_name,
    }
    if location:
        args['location'] = location
    if tags:
        args['tags'] = tags
    if not vnets:
        # if no VNETs can do a simple PUT
        return Create_Ddos_Protection(args)

    # if VNETs specified, have to create the protection plan and then add the VNETs
    plan_id = LongRunningOperation(cmd.cli_ctx)(Create_Ddos_Protection(args))['id']

    logger.info('Attempting to attach VNets to newly created DDoS protection plan.')
    for vnet_subresource in vnets:
        id_parts = parse_resource_id(vnet_subresource.id)
        poller = VNetUpdate(cli_ctx=cmd.cli_ctx)(command_args={
            'name': id_parts['name'],
            'resource_group': id_parts['resource_group'],
            'ddos_protection_plan': plan_id
        })
        LongRunningOperation(cmd.cli_ctx)(poller)

    show_args = {
        "name": ddos_plan_name,
        "resource_group": resource_group_name,
    }
    from azure.cli.command_modules.network.aaz.latest.network.ddos_protection import Show
    Show_Ddos_Protection = Show(cli_ctx=cmd.cli_ctx)
    return Show_Ddos_Protection(show_args)


def update_ddos_plan(cmd, resource_group_name, ddos_plan_name, tags=None, vnets=None):
    from azure.cli.command_modules.network.aaz.latest.network.ddos_protection import Update
    Update_Ddos_Protection = Update(cli_ctx=cmd.cli_ctx)
    args = {
        "name": ddos_plan_name,
        "resource_group": resource_group_name,
    }
    if tags is not None:
        args['tags'] = tags
    if vnets is not None:
        from azure.cli.command_modules.network.aaz.latest.network.ddos_protection import Show
        show_args = {
            "name": ddos_plan_name,
            "resource_group": resource_group_name,
        }
        Show_Ddos_Protection = Show(cli_ctx=cmd.cli_ctx)
        show_args = Show_Ddos_Protection(show_args)
        logger.info('Attempting to update the VNets attached to the DDoS protection plan.')
        vnet_ids = set()
        if len(vnets) == 1 and not vnets[0]:
            pass
        else:
            vnet_ids = {x.id for x in vnets}
        if 'virtualNetworks' in show_args:
            existing_vnet_ids = {x['id'] for x in show_args['virtualNetworks']}
        else:
            existing_vnet_ids = set()
        from azure.cli.core.commands import LongRunningOperation
        for vnet_id in vnet_ids.difference(existing_vnet_ids):
            logger.info("Adding VNet '%s' to plan.", vnet_id)
            id_parts = parse_resource_id(vnet_id)
            poller = VNetUpdate(cli_ctx=cmd.cli_ctx)(command_args={
                'name': id_parts['name'],
                'resource_group': id_parts['resource_group'],
                'ddos_protection_plan': show_args['id']
            })
            LongRunningOperation(cmd.cli_ctx)(poller)
        for vnet_id in existing_vnet_ids.difference(vnet_ids):
            logger.info("Removing VNet '%s' from plan.", vnet_id)
            id_parts = parse_resource_id(vnet_id)
            poller = VNetUpdate(cli_ctx=cmd.cli_ctx)(command_args={
                'name': id_parts['name'],
                'resource_group': id_parts['resource_group'],
                'ddos_protection_plan': None
            })
            LongRunningOperation(cmd.cli_ctx)(poller)
    return Update_Ddos_Protection(args)
# endregion


# region DNS Commands
# add delegation name server record for the created child zone in it's parent zone.
def _to_snake(s):
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)

    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def _convert_to_snake_case(element):
    if isinstance(element, dict):
        ret = {}
        for k, v in element.items():
            ret[_to_snake(k)] = _convert_to_snake_case(v)

        return ret

    if isinstance(element, list):
        return [_convert_to_snake_case(i) for i in element]

    return element


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
            for dname in child_zone["nameServers"]:
                add_dns_ns_record(cmd, parent_rg, parent_zone_name, record_set_name, dname, parent_subscription_id)
            print('Delegation added successfully in \'{}\'\n'.format(parent_zone_name), file=sys.stderr)
        except HttpResponseError as ex:
            logger.error(ex)
            print('Could not add delegation in \'{}\'\n'.format(parent_zone_name), file=sys.stderr)


def create_dns_zone(cmd, resource_group_name, zone_name, parent_zone_name=None, tags=None, if_none_match=False):
    created_zone = _DNSZoneCreate(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "zone_name": zone_name,
        "if_none_match": '*' if if_none_match else None,
        "location": 'global',
        "tags": tags
    })

    if parent_zone_name is not None:
        logger.info('Attempting to add delegation in the parent zone')
        add_dns_delegation(cmd, created_zone, parent_zone_name, resource_group_name, zone_name)
    return created_zone


def show_dns_soa_record_set(cmd, resource_group_name, zone_name, record_type):
    return DNSRecordSetSOAShow(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "zone_name": zone_name
    })


def update_dns_soa_record(cmd, resource_group_name, zone_name, host=None, email=None,
                          serial_number=None, refresh_time=None, retry_time=None, expire_time=None,
                          minimum_ttl=3600, if_none_match=None):
    record_set_name = '@'
    record_type = 'soa'

    record_set = DNSRecordSetSOAShow(cli_ctx=cmd.cli_ctx)(command_args={
        "zone_name": zone_name,
        "resource_group": resource_group_name
    })

    record_camal = record_set["SOARecord"]
    record = {}
    record["host"] = host or record_camal.get("host", None)
    record["email"] = email or record_camal.get("email", None)
    record["serial_number"] = serial_number or record_camal.get("serialNumber", None)
    record["refresh_time"] = refresh_time or record_camal.get("refreshTime", None)
    record["retry_time"] = retry_time or record_camal.get("retryTime", None)
    record["expire_time"] = expire_time or record_camal.get("expireTime", None)
    record["minimum_ttl"] = minimum_ttl or record_camal.get("minimumTTL", None)

    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            is_list=False, if_none_match=if_none_match)


def _type_to_property_name(key):
    type_dict = {
        # `record_type`: (`snake_case`, `camel_case`)
        'a': ('a_records', "ARecords"),
        'aaaa': ('aaaa_records', "AAAARecords"),
        'caa': ('caa_records', "caaRecords"),
        'cname': ('cname_record', "CNAMERecord"),
        'ds': ('ds_records', "DSRecords"),
        'mx': ('mx_records', "MXRecords"),
        'naptr': ('naptr_records', "NAPTRRecords"),
        'ns': ('ns_records', "NSRecords"),
        'ptr': ('ptr_records', "PTRRecords"),
        'soa': ('soa_record', "SOARecord"),
        'spf': ('txt_records', "TXTRecords"),
        'srv': ('srv_records', "SRVRecords"),
        'tlsa': ('tlsa_records', "TLSARecords"),
        'txt': ('txt_records', "TXTRecords"),
        'alias': ('target_resource', "targetResource"),
    }
    return type_dict[key.lower()]


def export_zone(cmd, resource_group_name, zone_name, file_name=None):  # pylint: disable=too-many-branches
    from time import localtime, strftime

    record_sets = _DNSRecordSetListByZone(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "zone_name": zone_name
    })

    zone_obj = OrderedDict({
        '$origin': zone_name.rstrip('.') + '.',
        'resource-group': resource_group_name,
        'zone-name': zone_name.rstrip('.'),
        'datetime': strftime('%a, %d %b %Y %X %z', localtime())
    })

    for record_set in record_sets:
        record_set = _convert_to_snake_case(record_set)
        record_type = record_set["type"].rsplit('/', 1)[1].lower()
        record_set_name = record_set["name"]
        record_data = record_set.get(_type_to_property_name(record_type)[0])

        if not record_data:
            record_data = []
        if not isinstance(record_data, list):
            record_data = [record_data]

        if record_set_name not in zone_obj:
            zone_obj[record_set_name] = OrderedDict()

        for record in record_data:
            record_obj = {'ttl': record_set["ttl"]}

            if record_type not in zone_obj[record_set_name]:
                zone_obj[record_set_name][record_type] = []
            if record_type == 'aaaa':
                record_obj.update({'ip': record["ipv6_address"]})
            elif record_type == 'a':
                record_obj.update({'ip': record["ipv4_address"]})
            elif record_type == 'caa':
                record_obj.update({'val': record["value"], 'tag': record["tag"], 'flags': record["flags"]})
            elif record_type == 'cname':
                record_obj.update({'alias': record["cname"].rstrip('.') + '.'})
            elif record_type == 'ds':
                record_obj.update({'key_tag': record["key_tag"], 'algorithm': record["algorithm"], 'digest_type': record["digest"]["algorithm_type"], 'digest': record["digest"]["value"]})
            elif record_type == 'mx':
                record_obj.update({'preference': record["preference"], 'host': record["exchange"].rstrip('.') + '.'})
            elif record_type == 'naptr':
                regexp_value = record["regexp"] if record["regexp"] != "" else "EMPTY"
                record_obj.update({'order': record["order"], 'preference': record["preference"], 'flags': record["flags"], 'services': record["services"], 'regexp': regexp_value, 'replacement': record["replacement"].rstrip('.') + '.'})
            elif record_type == 'ns':
                record_obj.update({'host': record["nsdname"].rstrip('.') + '.'})
            elif record_type == 'ptr':
                record_obj.update({'host': record["ptrdname"].rstrip('.') + '.'})
            elif record_type == 'soa':
                record_obj.update({
                    'mname': record["host"].rstrip('.') + '.',
                    'rname': record["email"].rstrip('.') + '.',
                    'serial': int(record["serial_number"]),
                    'refresh': record["refresh_time"],
                    'retry': record["retry_time"],
                    'expire': record["expire_time"],
                    'minimum': record["minimum_ttl"]
                })
                zone_obj['$ttl'] = record["minimum_ttl"]
            elif record_type == 'srv':
                record_obj.update({'priority': record["priority"], 'weight': record["weight"],
                                   'port': record["port"], 'target': record["target"].rstrip('.') + '.'})
            elif record_type == 'tlsa':
                record_obj.update({'usage': record["usage"], 'selector': record["selector"], 'matching_type': record["matching_type"], 'certificate': record["cert_association_data"]})
            elif record_type == 'txt':
                record_obj.update({'txt': ''.join(record["value"])})
            zone_obj[record_set_name][record_type].append(record_obj)

        if len(record_data) == 0:
            record_obj = {'ttl': record_set["ttl"]}

            if record_type not in zone_obj[record_set_name]:
                zone_obj[record_set_name][record_type] = []
            # Checking for alias record
            if (record_type == 'a' or record_type == 'aaaa' or record_type == 'cname') and record_set["target_resource"].get("id", ""):
                target_resource_id = record_set["target_resource"]["id"]
                record_obj.update({'target-resource-id': record_type.upper() + " " + target_resource_id})
                record_type = 'alias'
                if record_type not in zone_obj[record_set_name]:
                    zone_obj[record_set_name][record_type] = []
            elif record_type == 'aaaa' or record_type == 'a':
                record_obj.update({'ip': ''})
            elif record_type == 'cname':
                record_obj.update({'alias': ''})
            zone_obj[record_set_name][record_type].append(record_obj)
    zone_file_content = make_zone_file(zone_obj)
    print(zone_file_content)
    if file_name:
        try:
            with open(file_name, 'w') as f:
                f.write(zone_file_content)
        except OSError:
            raise CLIError('Unable to export to file: {}'.format(file_name))


# pylint: disable=too-many-return-statements, inconsistent-return-statements, too-many-branches
def _build_record(cmd, data):
    record_type = data['delim'].lower()
    try:
        if record_type == 'aaaa':
            return {"ipv6_address": data["ip"]}
        if record_type == 'a':
            return {"ipv4_address": data["ip"]}
        if record_type == 'caa':
            return {"value": data["val"], "flags": int(data["flags"]), "tag": data["tag"]}
        if record_type == 'cname':
            return {"cname": data["alias"]}
        if record_type == 'ds':
            return {"key_tag": int(data["key_tag"]), "algorithm": int(data["algorithm"]),
                    "digest": {"algorithm_type": int(data["digest_type"]), "value": data["digest"]}}
        if record_type == 'mx':
            return {"preference": int(data["preference"]), "exchange": data["host"]}
        if record_type == 'naptr':
            return {"order": int(data["order"]), "preference": int(data["preference"]), "flags": data["flags"],
                    "services": data["services"], "regexp": data["regexp"], "replacement": data["replacement"]}
        if record_type == 'ns':
            return {"nsdname": data["host"]}
        if record_type == 'ptr':
            return {"ptrdname": data["host"]}
        if record_type == 'soa':
            return {"host": data["host"], "email": data["email"], "serial_number": int(data["serial"]),
                    "refresh_time": data["refresh"], "retry_time": data["retry"], "expire_time": data["expire"],
                    "minimum_ttl": data["minimum"]}
        if record_type == 'srv':
            return {"priority": int(data["priority"]), "weight": int(data["weight"]), "port": int(data["port"]),
                    "target": data["target"]}
        if record_type == 'tlsa':
            return {"usage": int(data["usage"]), "selector": int(data["selector"]),
                    "matching_type": int(data["matching_type"]), "cert_association_data": data["certificate"]}
        if record_type in ['txt', 'spf']:
            text_data = data['txt']
            return {"value": text_data} if isinstance(text_data, list) else {"value": [text_data]}
        if record_type == 'alias':
            return {"id": data["resourceId"]}
    except KeyError as ke:
        raise CLIError("The {} record '{}' is missing a property.  {}"
                       .format(record_type, data['name'], ke))


# pylint: disable=too-many-statements
def import_zone(cmd, resource_group_name, zone_name, file_name):
    from azure.cli.core.util import read_file_content
    from azure.core.exceptions import HttpResponseError
    import sys
    logger.warning("In the future, zone name will be case insensitive.")

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
                alias_record_type = entry.get("aliasDelim", None)

                if alias_record_type:
                    alias_record_type = alias_record_type.lower()
                    record_set_key = '{}{}'.format(record_set_name.lower(), alias_record_type)

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

                    record_set = {"ttl": record_set_ttl}
                    record_sets[record_set_key] = record_set

                _add_record(record_set, record, record_set_type,
                            is_list=record_set_type.lower() not in ['soa', 'cname', 'alias'])

    total_records = 0
    for key, rs in record_sets.items():
        rs_name, rs_type = key.lower().rsplit('.', 1)
        rs_name = rs_name[:-(len(origin) + 1)] if rs_name != origin else '@'
        try:
            records_temp = rs[_type_to_property_name(rs_type)[0]]
            record_count = len(records_temp) if isinstance(records_temp, list) else 1
        except (TypeError, KeyError):
            # There is some bug with `alias records` being mapped from `AZURE ALIAS A` to `ARecords`,
            # but `rs` does not contain `a_records`.  We could fix it, but this is just logging, so
            # lets not fail the whole import and hope someone refactors this method
            record_count = 1
        total_records += record_count
    cum_records = 0

    print('== BEGINNING ZONE IMPORT: {} ==\n'.format(zone_name), file=sys.stderr)

    _DNSZoneCreate(cli_ctx=cmd.cli_ctx)(command_args={
        'resource_group': resource_group_name,
        'zone_name': zone_name,
        'location': 'global'
    })

    for key, rs in record_sets.items():
        rs_name, rs_type = key.lower().rsplit('.', 1)
        rs_name = '@' if rs_name == origin else rs_name

        if rs_name.endswith(origin):
            rs_name = rs_name[:-(len(origin) + 1)]

        try:
            records_temp = rs[_type_to_property_name(rs_type)[0]]
            record_count = len(records_temp) if isinstance(records_temp, list) else 1
        except (TypeError, KeyError):
            record_count = 1

        if rs_name == '@' and rs_type == 'soa':
            root_soa = DNSRecordSetSOAShow(cli_ctx=cmd.cli_ctx)(command_args={
                'resource_group': resource_group_name,
                'zone_name': zone_name,
            })
            rs["soa_record"]["host"] = root_soa["SOARecord"]["host"]
            rs_name = '@'
        elif rs_name == '@' and rs_type == 'ns':
            root_ns = DNSRecordSetNSShow(cli_ctx=cmd.cli_ctx)(command_args={
                'resource_group': resource_group_name,
                'zone_name': zone_name,
                'name': '@'
            })
            root_ns["ttl"] = rs["ttl"]
            rs = _convert_to_snake_case(root_ns)
        try:
            rs["target_resource"] = rs.get("target_resource").get("id") if rs.get("target_resource") else None
            rs["traffic_management_profile"] = rs.get("traffic_management_profile").get("id") if rs.get("traffic_management_profile") else None
            _record_create = _record_create_func(rs_type)
            _record_create(cli_ctx=cmd.cli_ctx)(command_args={
                'resource_group': resource_group_name,
                'zone_name': zone_name,
                'name': rs_name,
                **rs
            })

            cum_records += record_count
            print("({}/{}) Imported {} records of type '{}' and name '{}'"
                  .format(cum_records, total_records, record_count, rs_type, rs_name), file=sys.stderr)
        except HttpResponseError as ex:
            logger.error(ex)
    print("\n== {}/{} RECORDS IMPORTED SUCCESSFULLY: '{}' =="
          .format(cum_records, total_records, zone_name), file=sys.stderr)


def add_dns_aaaa_record(cmd, resource_group_name, zone_name, record_set_name, ipv6_address,
                        ttl=3600, if_none_match=None):
    record = {"ipv6_address": ipv6_address}
    record_type = 'aaaa'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            ttl=ttl, if_none_match=if_none_match)


def add_dns_a_record(cmd, resource_group_name, zone_name, record_set_name, ipv4_address,
                     ttl=3600, if_none_match=None):
    record = {"ipv4_address": ipv4_address}
    record_type = 'a'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name, 'arecords',
                            ttl=ttl, if_none_match=if_none_match)


def add_dns_caa_record(cmd, resource_group_name, zone_name, record_set_name, value, flags, tag,
                       ttl=3600, if_none_match=None):
    record = {"flags": flags, "tag": tag, "value": value}
    record_type = 'caa'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            ttl=ttl, if_none_match=if_none_match)


def add_dns_cname_record(cmd, resource_group_name, zone_name, record_set_name, cname, ttl=3600, if_none_match=None):
    record = {"cname": cname}
    record_type = 'cname'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            is_list=False, ttl=ttl, if_none_match=if_none_match)


def add_dns_ds_record(cmd, resource_group_name, zone_name, record_set_name, key_tag, algorithm, digest_type, digest,
                      ttl=3600, if_none_match=None):
    record = {"algorithm": algorithm, "key_tag": key_tag, "digest": {"algorithm_type": digest_type, "value": digest}}
    record_type = 'ds'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            ttl=ttl, if_none_match=if_none_match)


def add_dns_mx_record(cmd, resource_group_name, zone_name, record_set_name, preference, exchange,
                      ttl=3600, if_none_match=None):
    record = {"preference": int(preference), "exchange": exchange}
    record_type = 'mx'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            ttl=ttl, if_none_match=if_none_match)


def add_dns_naptr_record(cmd, resource_group_name, zone_name, record_set_name, order, preference, flags, services, regexp, replacement,
                         ttl=3600, if_none_match=None):
    record = {"flags": flags, "order": order, "preference": preference, "regexp": regexp, "replacement": replacement, "services": services}
    record_type = 'naptr'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            ttl=ttl, if_none_match=if_none_match)


def add_dns_ns_record(cmd, resource_group_name, zone_name, record_set_name, dname,
                      subscription_id=None, ttl=3600, if_none_match=None):
    record = {"nsdname": dname}
    record_type = 'ns'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            subscription_id=subscription_id, ttl=ttl, if_none_match=if_none_match)


def add_dns_ptr_record(cmd, resource_group_name, zone_name, record_set_name, dname, ttl=3600, if_none_match=None):
    record = {"ptrdname": dname}
    record_type = 'ptr'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            ttl=ttl, if_none_match=if_none_match)


def add_dns_srv_record(cmd, resource_group_name, zone_name, record_set_name, priority, weight,
                       port, target, if_none_match=None):
    record = {"priority": priority, "weight": weight, "port": port, "target": target}
    record_type = 'srv'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            if_none_match=if_none_match)


def add_dns_tlsa_record(cmd, resource_group_name, zone_name, record_set_name, certificate_usage, selector, matching_type, certificate_data,
                        ttl=3600, if_none_match=None):
    record = {"cert_association_data": certificate_data, "matching_type": matching_type, "selector": selector, "usage": certificate_usage}
    record_type = 'tlsa'
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            ttl=ttl, if_none_match=if_none_match)


def add_dns_txt_record(cmd, resource_group_name, zone_name, record_set_name, value, if_none_match=None):
    record = {"value": value}
    record_type = 'txt'
    long_text = ''.join(x for x in record["value"])
    original_len = len(long_text)
    record["value"] = []
    while len(long_text) > 255:
        record["value"].append(long_text[:255])
        long_text = long_text[255:]
    record["value"].append(long_text)
    final_str = ''.join(record["value"])
    final_len = len(final_str)
    assert original_len == final_len
    return _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                            if_none_match=if_none_match)


def remove_dns_aaaa_record(cmd, resource_group_name, zone_name, record_set_name, ipv6_address,
                           keep_empty_record_set=False):
    record = {"ipv6_address": ipv6_address}
    record_type = 'aaaa'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_a_record(cmd, resource_group_name, zone_name, record_set_name, ipv4_address,
                        keep_empty_record_set=False):
    record = {"ipv4_address": ipv4_address}
    record_type = 'a'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_caa_record(cmd, resource_group_name, zone_name, record_set_name, value,
                          flags, tag, keep_empty_record_set=False):
    record = {"flags": flags, "tag": tag, "value": value}
    record_type = 'caa'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_cname_record(cmd, resource_group_name, zone_name, record_set_name, cname,
                            keep_empty_record_set=False):
    record = {"cname": cname}
    record_type = 'cname'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          is_list=False, keep_empty_record_set=keep_empty_record_set)


def remove_dns_ds_record(cmd, resource_group_name, zone_name, record_set_name, key_tag, algorithm, digest_type, digest, keep_empty_record_set=False):
    record = {"algorithm": algorithm, "key_tag": key_tag, "digest": {"algorithm_type": digest_type, "value": digest}}
    record_type = 'ds'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_mx_record(cmd, resource_group_name, zone_name, record_set_name, preference, exchange,
                         keep_empty_record_set=False):
    record = {"preference": int(preference), "exchange": exchange}
    record_type = 'mx'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_naptr_record(cmd, resource_group_name, zone_name, record_set_name, order, preference, flags, services, regexp, replacement, keep_empty_record_set=False):
    record = {"flags": flags, "order": order, "preference": preference, "regexp": regexp, "replacement": replacement, "services": services}
    record_type = 'naptr'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_ns_record(cmd, resource_group_name, zone_name, record_set_name, dname,
                         keep_empty_record_set=False):
    record = {"nsdname": dname}
    record_type = 'ns'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_ptr_record(cmd, resource_group_name, zone_name, record_set_name, dname,
                          keep_empty_record_set=False):
    record = {"ptrdname": dname}
    record_type = 'ptr'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_srv_record(cmd, resource_group_name, zone_name, record_set_name, priority, weight,
                          port, target, keep_empty_record_set=False):
    record = {"priority": priority, "weight": weight, "port": port, "target": target}
    record_type = 'srv'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_tlsa_record(cmd, resource_group_name, zone_name, record_set_name, certificate_usage, selector, matching_type, certificate_data, keep_empty_record_set=False):
    record = {"cert_association_data": certificate_data, "matching_type": matching_type, "selector": selector, "usage": certificate_usage}
    record_type = 'tlsa'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def remove_dns_txt_record(cmd, resource_group_name, zone_name, record_set_name, value,
                          keep_empty_record_set=False):
    record = {"value": value}
    record_type = 'txt'
    return _remove_record(cmd.cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                          keep_empty_record_set=keep_empty_record_set)


def _check_a_record_exist(record, exist_list):
    for r in exist_list:
        if r["ipv4_address"] == record["ipv4_address"]:
            return True
    return False


def _check_aaaa_record_exist(record, exist_list):
    for r in exist_list:
        if r["ipv6_address"] == record["ipv6_address"]:
            return True
    return False


def _check_caa_record_exist(record, exist_list):
    for r in exist_list:
        if (r["flags"], r["tag"], r["value"]) == (record["flags"], record["tag"], record["value"]):
            return True
    return False


def _check_cname_record_exist(record, exist_list):
    for r in exist_list:
        if r["cname"] == record["cname"]:
            return True
    return False


def _check_ds_record_exist(record, exist_list):
    for r in exist_list:
        if (r["algorithm"], r["key_tag"], r["digest"]["algorithm_type"], r["digest"]["value"]) == (record["algorithm"], record["key_tag"], record["digest"]["algorithm_type"], record["digest"]["value"]):
            return True
    return False


def _check_mx_record_exist(record, exist_list):
    for r in exist_list:
        if (r["preference"], r["exchange"]) == (record["preference"], record["exchange"]):
            return True
    return False


def _check_naptr_record_exist(record, exist_list):
    for r in exist_list:
        if (r["flags"], r["order"], r["preference"], r["regexp"], r["replacement"], r["services"]) == (record["flags"], record["order"], record["preference"], record["regexp"], record["replacement"], record["services"]):
            return True
    return False


def _check_ns_record_exist(record, exist_list):
    for r in exist_list:
        if r["nsdname"] == record["nsdname"]:
            return True
    return False


def _check_ptr_record_exist(record, exist_list):
    for r in exist_list:
        if r["ptrdname"] == record["ptrdname"]:
            return True
    return False


def _check_srv_record_exist(record, exist_list):
    for r in exist_list:
        if (r["priority"], r["weight"], r["port"], r["target"]) == (record["priority"], record["weight"], record["port"], record["target"]):
            return True
    return False


def _check_tlsa_record_exist(record, exist_list):
    for r in exist_list:
        if (r["cert_association_data"], r["matching_type"], r["selector"], r["usage"]) == (record["cert_association_data"], record["matching_type"], record["selector"], record["usage"]):
            return True
    return False


def _check_txt_record_exist(record, exist_list):
    for r in exist_list:
        if r["value"] == record["value"]:
            return True
    return False


def _record_exist_func(record_type):
    return globals()["_check_{}_record_exist".format(record_type)]


def _add_record(record_set, record, record_type, is_list=False):
    record_property, _ = _type_to_property_name(record_type)

    if is_list:
        record_list = record_set.get(record_property, None)
        if record_list is None:
            record_set[record_property] = []
            record_list = []

        _record_exist = _record_exist_func(record_type)
        if not _record_exist(record, record_list):
            record_set[record_property].append(record)
    else:
        record_set[record_property] = record


def _record_show_func(record_type):
    return globals()["DNSRecordSet{}Show".format(record_type.upper())]


def _record_create_func(record_type):
    return globals()["DNSRecordSet{}Create".format(record_type.upper())]


def _record_delete_func(record_type):
    return globals()["DNSRecordSet{}Delete".format(record_type.upper())]


def _record_update_func(record_type):
    return globals()["DNSRecordSet{}Update".format(record_type.upper())]


def _add_save_record(cmd, record, record_type, record_set_name, resource_group_name, zone_name,
                     is_list=True, subscription_id=None, ttl=None, if_none_match=None):
    from azure.core.exceptions import HttpResponseError

    record_snake, record_camel = _type_to_property_name(record_type)
    try:
        _record_show = _record_show_func(record_type)
        ret = _record_show(cli_ctx=cmd.cli_ctx)(command_args={
            "name": record_set_name,
            "zone_name": zone_name,
            "subscription": subscription_id,
            "resource_group": resource_group_name
        })
        record_set = {}
        record_set["ttl"] = ret.get("TTL", None)
        record_set[record_snake] = ret.get(record_camel, None)
        record_set = _convert_to_snake_case(record_set)
    except HttpResponseError:
        record_set = {"ttl": 3600}

    if ttl is not None:
        record_set["ttl"] = ttl

    _add_record(record_set, record, record_type, is_list)

    record_set["target_resource"] = record_set.get("target_resource").get("id") if record_set.get("target_resource") else None
    _record_create = _record_create_func(record_type)
    return _record_create(cli_ctx=cmd.cli_ctx)(command_args={
        "name": record_set_name,
        "zone_name": zone_name,
        "subscription": subscription_id,
        "resource_group": resource_group_name,
        "if_none_match": "*" if if_none_match else None,
        **record_set
    })


def _remove_record(cli_ctx, record, record_type, record_set_name, resource_group_name, zone_name,
                   keep_empty_record_set, is_list=True):
    record_snake, record_camel = _type_to_property_name(record_type)

    _record_show = _record_show_func(record_type)
    ret = _record_show(cli_ctx=cli_ctx)(command_args={
        "name": record_set_name,
        "zone_name": zone_name,
        "resource_group": resource_group_name,
        "record_type": record_type
    })
    record_set = {}
    record_set["ttl"] = ret.get("TTL", None)
    record_set[record_snake] = ret.get(record_camel, None)
    record_set = _convert_to_snake_case(record_set)

    logger.debug('Retrieved record: %s', str(record_set))

    if is_list:
        record_list = record_set[record_snake]
        if record_list is not None:
            keep_list = [r for r in record_list if not dict_matches_filter(r, record)]
            if len(keep_list) == len(record_list):
                raise CLIError('Record {} not found.'.format(str(record)))

            record_set[record_snake] = keep_list
    else:
        record_set[record_snake] = None

    if is_list:
        records_remaining = len(record_set[record_snake]) if record_set[record_snake] is not None else 0
    else:
        records_remaining = 1 if record_set[record_snake] is not None else 0

    if not records_remaining and not keep_empty_record_set:
        logger.info('Removing empty %s record set: %s', record_type, record_set_name)

        _record_delete = _record_delete_func(record_type)
        return _record_delete(cli_ctx=cli_ctx)(command_args={
            "name": record_set_name,
            "zone_name": zone_name,
            "resource_group": resource_group_name
        })

    _record_update = _record_update_func(record_type)
    return _record_update(cli_ctx=cli_ctx)(command_args={
        "name": record_set_name,
        "zone_name": zone_name,
        "resource_group": resource_group_name,
        **record_set
    })


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
class ExpressRouteCreate(_ExpressRouteCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.bandwidth = AAZListArg(
            options=["--bandwidth"],
            help="Bandwidth of the circuit. Usage: INT {Mbps,Gbps}. Defaults to Mbps."
        )
        args_schema.bandwidth.Element = AAZStrArg()
        args_schema.bandwidth_in_mbps._registered = False
        args_schema.bandwidth_in_gbps._registered = False
        args_schema.sku_name._registered = False
        args_schema.express_route_port._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/expressRoutePorts/{}",
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.bandwidth):
            converted_bandwidth = _validate_bandwidth(args.bandwidth)
        args.sku_name = '{}_{}'.format(args.sku_tier, args.sku_family)

        if has_value(args.express_route_port):
            args.provider = None
            args.peering_location = None
            args.bandwidth_in_gbps = converted_bandwidth / 1000.0
        else:
            args.bandwidth_in_mbps = int(converted_bandwidth)


class ExpressRouteUpdate(_ExpressRouteUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.bandwidth = AAZListArg(
            options=["--bandwidth"],
            help="Bandwidth of the circuit. Usage: INT {Mbps,Gbps}. Defaults to Mbps.",
            nullable=True
        )
        args_schema.bandwidth.Element = AAZStrArg(nullable=True)
        args_schema.bandwidth_in_mbps._registered = False
        args_schema.bandwidth_in_gbps._registered = False
        args_schema.sku_name._registered = False
        args_schema.express_route_port._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/expressRoutePorts/{}"
        )

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.sku_tier) and has_value(args.sku_family):
            args.sku_name = f"{args.sku_tier}_{args.sku_family}"

        if has_value(args.bandwidth):
            converted_bandwidth = _validate_bandwidth(args.bandwidth)
            args.bandwidth_in_gbps = converted_bandwidth / 1000
            args.bandwidth_in_mbps = int(converted_bandwidth)

    def post_instance_update(self, instance):
        if not has_value(instance.properties.express_route_port.id):
            instance.properties.express_route_port = None

        if has_value(instance.properties.express_route_port):
            instance.properties.service_provider_properties = None
        else:
            instance.properties.bandwidth_in_gbps = None


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


class ExpressRoutePeeringCreate(_ExpressRoutePeeringCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZResourceIdArgFormat, AAZArgEnum
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.ip_version = AAZStrArg(
            options=['--ip-version'],
            arg_group="Microsoft Peering",
            help="The IP version to update Microsoft Peering settings for. Allowed values: IPv4, IPv6. Default: IPv4.",
            default='IPv4'
        )
        args_schema.route_filter._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/routeFilters/{}",
        )
        # taken from Xplat. No enums in SDK
        args_schema.routing_registry_name.enum = AAZArgEnum({"ARIN": "ARIN", "APNIC": "APNIC", "AFRINIC": "AFRINIC", "LACNIC": "LACNIC", "RIPENCC": "RIPENCC", "RADB": "RADB", "ALTDB": "ALTDB", "LEVEL3": "LEVEL3"})
        args_schema.ipv6_peering_config._registered = False
        args_schema.peering_name._required = False
        args_schema.peering_name._registered = False

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.peering_name = args.peering_type
        if args.ip_version.to_serialized_data().lower() == 'ipv6':
            if args.peering_type.to_serialized_data().lower() == 'microsoftpeering':
                microsoft_config = {'advertised_public_prefixes': args.advertised_public_prefixes,
                                    'customer_asn': args.customer_asn,
                                    'routing_registry_name': args.routing_registry_name}
            else:
                microsoft_config = None
            args.ipv6_peering_config = {
                'primary_peer_address_prefix': args.primary_peer_subnet,
                'secondary_peer_address_prefix': args.secondary_peer_subnet,
                'microsoft_peering_config': microsoft_config,
                'route_filter': args.route_filter
            }
            args.primary_peer_subnet = None
            args.secondary_peer_subnet = None
            args.route_filter = None
            args.advertised_public_prefixes = None
            args.customer_asn = None
            args.routing_registry_name = None

        else:
            if has_value(args.peering_type) and args.peering_type.to_serialized_data().lower() != 'microsoftpeering':
                args.advertised_public_prefixes = None
                args.customer_asn = None
                args.routing_registry_name = None
                args.legacy_mode = None


class ExpressRoutePeeringUpdate(_ExpressRoutePeeringUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZResourceIdArgFormat, AAZArgEnum
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.ip_version = AAZStrArg(
            options=['--ip-version'],
            arg_group="Microsoft Peering",
            help="The IP version to update Microsoft Peering settings for. Allowed values: IPv4, IPv6. Default: IPv4.",
            default='IPv4'
        )
        args_schema.route_filter._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/routeFilters/{}",
        )
        # taken from Xplat. No enums in SDK
        args_schema.routing_registry_name.enum = AAZArgEnum({"ARIN": "ARIN", "APNIC": "APNIC", "AFRINIC": "AFRINIC", "LACNIC": "LACNIC", "RIPENCC": "RIPENCC", "RADB": "RADB", "ALTDB": "ALTDB", "LEVEL3": "LEVEL3"})
        args_schema.ipv6_peering_config._registered = False
        args_schema.peering_type._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if args.ip_version.to_serialized_data().lower() == 'ipv6':
            microsoft_config = {}
            args.ipv6_peering_config = {}
            if has_value(args.primary_peer_subnet):
                args.ipv6_peering_config['primary_peer_address_prefix'] = args.primary_peer_subnet
                args.primary_peer_subnet = None
            if has_value(args.secondary_peer_subnet):
                args.ipv6_peering_config['secondary_peer_address_prefix'] = args.secondary_peer_subnet
                args.secondary_peer_subnet = None
            if has_value(args.advertised_public_prefixes):
                microsoft_config['advertised_public_prefixes'] = args.advertised_public_prefixes
                args.advertised_public_prefixes = None
            if has_value(args.customer_asn):
                microsoft_config['customer_asn'] = args.customer_asn
                args.customer_asn = None
            if has_value(args.routing_registry_name):
                microsoft_config['routing_registry_name'] = args.routing_registry_name
                args.routing_registry_name = None
            if has_value(args.route_filter):
                args.ipv6_peering_config['route_filter'] = args.route_filter
                args.route_filter = None
            if microsoft_config is not None:
                args.ipv6_peering_config['microsoft_peering_config'] = microsoft_config


class ExpressRoutePeeringConnectionCreate(_ExpressRoutePeeringConnectionCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.peer_circuit._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/expressRouteCircuits/{}/peerings/{peering_name}",
        )
        args_schema.source_circuit._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/expressRouteCircuits/{circuit_name}/peerings/{peering_name}",
        )

        return args_schema
# endregion


# region ExpressRoute Connection
# pylint: disable=unused-argument
class ExpressRouteGatewayCreate(_ExpressRouteGatewayCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.virtual_hub._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualHubs/{}",
        )

        return args_schema


class ExpressRouteGatewayUpdate(_ExpressRouteGatewayUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.virtual_hub._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualHubs/{}",
        )

        return args_schema


class ExpressRouteConnectionCreate(_ExpressRouteConnectionCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.associated_route_table = AAZStrArg(
            options=['--associated-route-table', '--associated'],
            arg_group="Routing Configuration",
            help="The resource id of route table associated with this routing configuration.",
            is_preview=True)
        args_schema.propagated_route_tables = AAZListArg(
            options=['--propagated-route-tables', '--propagated'],
            arg_group="Routing Configuration",
            help="Space-separated list of resource id of propagated route tables.",
            is_preview=True)
        args_schema.propagated_route_tables.Element = AAZStrArg()
        args_schema.circuit_name = AAZStrArg(
            options=['--circuit-name'],
            arg_group="Peering",
            help="ExpressRoute circuit name."
        )
        args_schema.peering._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/expressRouteCircuits/{circuit_name}/peerings/{}"
        )
        args_schema.associated_id._registered = False
        args_schema.propagated_ids._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args

        if has_value(args.associated_route_table):
            args.associated_id = {"id": args.associated_route_table}
        if has_value(args.propagated_route_tables):
            args.propagated_ids = [{"id": propagated_route_table} for propagated_route_table in args.propagated_route_tables]


# pylint: disable=unused-argument
class ExpressRouteConnectionUpdate(_ExpressRouteConnectionUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.associated_route_table = AAZStrArg(
            options=['--associated-route-table', '--associated'],
            arg_group="Routing Configuration",
            help="The resource id of route table associated with this routing configuration.",
            is_preview=True,
            nullable=True)
        args_schema.propagated_route_tables = AAZListArg(
            options=['--propagated-route-tables', '--propagated'],
            arg_group="Routing Configuration",
            help="Space-separated list of resource id of propagated route tables.",
            is_preview=True,
            nullable=True)
        args_schema.propagated_route_tables.Element = AAZStrArg(nullable=True)
        args_schema.circuit_name = AAZStrArg(
            options=['--circuit-name'],
            arg_group="Peering",
            help="ExpressRoute circuit name.",
            nullable=True
        )
        args_schema.peering._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/expressRouteCircuits/{circuit_name}/peerings/{}"
        )
        args_schema.associated_id._registered = False
        args_schema.propagated_ids._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args

        if has_value(args.associated_route_table):
            args.associated_id = {"id": args.associated_route_table}

        args.propagated_ids = assign_aaz_list_arg(
            args.propagated_ids,
            args.propagated_route_tables,
            element_transformer=lambda _, propagated_route_table: {"id": propagated_route_table}
        )
# endregion


# region ExpressRoute ports
class ExpressRoutePortCreate(_ExpressRoutePortCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.bandwidth = AAZListArg(
            options=["--bandwidth"],
            help="Bandwidth of the circuit. Usage: INT {Mbps,Gbps}. Defaults to Mbps."
        )
        args_schema.bandwidth.Element = AAZStrArg()
        args_schema.bandwidth_in_gbps._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.bandwidth):
            converted_bandwidth = _validate_bandwidth(args.bandwidth, mbps=False)
            args.bandwidth_in_gbps = int(converted_bandwidth)


def _validate_bandwidth(bandwidth, mbps=True):
    unit = 'mbps' if mbps else 'gbps'
    if bandwidth is None:
        return
    if len(bandwidth) == 1:
        bandwidth_comps = bandwidth[0].to_serialized_data().split(' ')
    else:
        bandwidth_comps = bandwidth.to_serialized_data()

    usage_error = InvalidArgumentValueError('--bandwidth INT {Mbps,Gbps}')
    if len(bandwidth_comps) == 1:
        bandwidth_comps.append(unit)
    if len(bandwidth_comps) > 2:
        raise usage_error
    input_value = bandwidth_comps[0]
    input_unit = bandwidth_comps[1].lower()
    if float(input_value) and input_unit in ['mbps', 'gbps']:
        if input_unit == unit:
            converted_bandwidth = float(bandwidth_comps[0])
        elif input_unit == 'gbps':
            converted_bandwidth = float(bandwidth_comps[0]) * 1000
        else:
            converted_bandwidth = float(bandwidth_comps[0]) / 1000
    else:
        raise usage_error
    return converted_bandwidth


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
    from .aaz.latest.network.express_route.port import GenerateLoa
    response = GenerateLoa(cli_ctx=cmd.cli_ctx)(command_args={'resource_group': resource_group_name,
                                                              'name': express_route_port_name,
                                                              'customer_name': customer_name})

    encoded_content = base64.b64decode(response['encodedContent'])

    from azure.cli.core.azclierror import FileOperationError
    try:
        with open(file_path, 'wb') as f:
            f.write(encoded_content)
    except OSError as ex:
        raise FileOperationError(ex)

    logger.warning("The generated letter of authorization is saved at %s", file_path)


class ExpressRoutePortIdentityAssign(_ExpressRoutePortIdentityAssign):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.identity = AAZResourceIdArg(
            options=['--identity'],
            arg_group="Identity",
            help="Name or ID of the ManagedIdentity Resource.",
            required=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/{}"
            )
        )

        args_schema.user_assigned_identities._registered = False
        args_schema.type._registered = False

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        identity = args.identity.to_serialized_data()
        args.user_assigned_identities = {identity: {}}


class ExpressRoutePortLinkUpdate(_ExpressRoutePortLinkUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.admin_state._blank = "Enabled"

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        # TODO https://github.com/Azure/azure-rest-api-specs/issues/7569
        # need to remove this conversion when the issue is fixed.
        if has_value(args.macsec_cipher):
            macsec_cipher = args.macsec_cipher.to_serialized_data()
            macsec_ciphers_tmp = {'gcm-aes-128': 'GcmAes128', 'gcm-aes-256': 'GcmAes256'}
            macsec_cipher = macsec_ciphers_tmp.get(macsec_cipher, macsec_cipher)
            args.macsec_cipher = macsec_cipher
# endregion


# region PrivateEndpoint
class PrivateEndpointCreate(_PrivateEndpointCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZBoolArg, AAZListArg, AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.private_connection_resource_id = AAZStrArg(
            options=['--private-connection-resource-id'],
            help="The resource id of the private endpoint to connect to.",
            required=True)
        args_schema.group_ids = AAZListArg(
            options=["--group-ids", "--group-id"],
            help="The ID of the group obtained from the remote resource that this private endpoint should connect to. You can use \"az network private-link-resource list\" to obtain the supported group ids. You must provide this except for PrivateLinkService.,"
        )
        args_schema.group_ids.Element = AAZStrArg()
        args_schema.request_message = AAZStrArg(
            options=['--request-message'],
            help="A message passed to the owner of the remote resource with this connection request. Restricted to 140 chars.")
        args_schema.connection_name = AAZStrArg(
            options=['--connection-name'],
            help="Name of the private link service connection.",
            required=True)
        args_schema.manual_request = AAZBoolArg(
            options=['--manual-request'],
            help="Use manual request to establish the connection. Configure it as 'true' when you don't have access to the subscription of private link service.")
        args_schema.vnet_name = AAZStrArg(
            options=['--vnet-name'],
            help="The virtual network (VNet) associated with the subnet (Omit if supplying a subnet id).")
        args_schema.subnet = AAZResourceIdArg(
            options=['--subnet'],
            help="Name or ID of an existing subnet. If name specified, also specify --vnet-name. "
                 "If you want to use an existing subnet in other resource group or subscription, please provide the ID instead of the name of the subnet and do not specify the--vnet-name.",
            required=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{vnet_name}/subnets/{}"
            )
        )
        args_schema.manual_private_link_service_connections._registered = False
        args_schema.private_link_service_connections._registered = False
        args_schema.edge_zone_type._registered = False
        args_schema.subnet_id._registered = False

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        pls_connection = {'name': args.connection_name,
                          'group_ids': args.group_ids,
                          'request_message': args.request_message,
                          'private_link_service_id': args.private_connection_resource_id}

        if args.manual_request:
            args.manual_private_link_service_connections = [pls_connection]
        else:
            args.private_link_service_connections = [pls_connection]

        if has_value(args.subnet):
            args.subnet_id = args.subnet

        if has_value(args.edge_zone):
            args.edge_zone_type = 'EdgeZone'


class PrivateEndpointUpdate(_PrivateEndpointUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.request_message = AAZStrArg(
            options=['--request-message'],
            help="A message passed to the owner of the remote resource with this connection request. Restricted to 140 chars.")

        args_schema.manual_private_link_service_connections._registered = False
        args_schema.private_link_service_connections._registered = False

        return args_schema

    def pre_instance_update(self, instance):
        args = self.ctx.args
        if has_value(args.request_message):
            if has_value(instance.properties.private_link_service_connections):
                instance.properties.private_link_service_connections[0].properties.request_message = args.request_message
            elif has_value(instance.properties.manual_private_link_service_connections):
                instance.properties.manual_private_link_service_connections[0].properties.request_message = args.request_message


class PrivateEndpointPrivateDnsZoneGroupCreate(_PrivateEndpointPrivateDnsZoneGroupCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.private_dns_zone = AAZResourceIdArg(
            options=['--private-dns-zone'],
            help="Name or ID of the private dns zone.",
            required=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/privateDnsZones/{}"
            )
        )
        args_schema.zone_name = AAZStrArg(options=['--zone-name'], help="Name of the private dns zone.", required=True)
        args_schema.private_dns_zone_configs._registered = False

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.private_dns_zone_configs = [{'name': args.zone_name, 'private_dns_zone_id': args.private_dns_zone}]


class PrivateEndpointPrivateDnsZoneAdd(_PrivateEndpointPrivateDnsZoneAdd):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.private_dns_zone = AAZResourceIdArg(
            options=['--private-dns-zone'],
            help="Name or ID of the private dns zone.",
            required=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/privateDnsZones/{}"
            )
        )
        args_schema.private_dns_zone_id._registered = False

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.private_dns_zone_id = args.private_dns_zone

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class PrivateEndpointIpConfigAdd(_PrivateEndpointIpConfigAdd):

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class PrivateEndpointAsgAdd(_PrivateEndpointAsgAdd):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.asg_id._required = False

        return args_schema

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result
# endregion


# region PrivateLinkService
class PrivateLinkServiceCreate(_PrivateLinkServiceCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vnet_name = AAZStrArg(options=['--vnet-name'], arg_group="IP Configuration", help="The virtual network (VNet) name.")
        args_schema.subnet = AAZResourceIdArg(
            options=['--subnet'],
            arg_group="IP Configuration",
            help="Name or ID of subnet to use. If name provided, also supply `--vnet-name`.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{vnet_name}/subnets/{}"
            )
        )
        args_schema.private_ip_address = AAZStrArg(options=['--private-ip-address'], arg_group="IP Configuration", help="Static private IP address to use.")
        args_schema.private_ip_address_version = AAZStrArg(options=['--private-ip-address-version'], arg_group="IP Configuration", help="IP version of the private IP address.",
                                                           default="IPv4", enum={"IPv4": "IPv4", "IPv6": "IPv6"})
        args_schema.private_ip_allocation_method = AAZStrArg(options=['--private-ip-allocation-method'], arg_group="IP Configuration", help="Private IP address allocation method.",
                                                             enum={"Dynamic": "Dynamic", "Static": "Static"})
        args_schema.lb_name = AAZStrArg(options=['--lb-name'], help="Name of the load balancer to retrieve frontend IP configs from. Ignored if a frontend IP configuration ID is supplied.")
        args_schema.lb_frontend_ip_configs = AAZListArg(options=['--lb-frontend-ip-configs'], help="Space-separated list of names or IDs of load balancer frontend IP configurations to link to. If names are used, also supply `--lb-name`.")
        args_schema.lb_frontend_ip_configs.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIpConfigurations/{}"
            )
        )

        args_schema.load_balancer_frontend_ip_configurations._registered = False
        args_schema.edge_zone_type._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args

        if not has_value(args.ip_configurations):
            args.ip_configurations = [{
                'name': '{}_ipconfig_0'.format(args.name.to_serialized_data()),
                'private_ip_address': args.private_ip_address,
                'private_ip_allocation_method': args.private_ip_allocation_method,
                'private_ip_address_version': args.private_ip_address_version,
                'subnet': {'id': args.subnet}
            }]

        args.load_balancer_frontend_ip_configurations = assign_aaz_list_arg(
            args.load_balancer_frontend_ip_configurations,
            args.lb_frontend_ip_configs,
            element_transformer=lambda _, lb_frontend_ip_config: {"id": lb_frontend_ip_config}
        )

        if has_value(args.edge_zone):
            args.edge_zone_type = 'EdgeZone'
        if not has_value(args.lb_frontend_ip_configs) and not has_value(args.destination_ip_address):
            raise CLIError("usage error: either --lb-frontend-ip-configs or --destination-ip-address is required")


class PrivateLinkServiceUpdate(_PrivateLinkServiceUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZListArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.lb_name = AAZStrArg(options=['--lb-name'], help="Name of the load balancer to retrieve frontend IP configs from. Ignored if a frontend IP configuration ID is supplied.")
        args_schema.lb_frontend_ip_configs = AAZListArg(options=['--lb-frontend-ip-configs'], help="Space-separated list of names or IDs of load balancer frontend IP configurations to link to. If names are used, also supply `--lb-name`.", nullable=True)
        args_schema.lb_frontend_ip_configs.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIpConfigurations/{}"
            ),
            nullable=True
        )
        args_schema.load_balancer_frontend_ip_configurations._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args

        if has_value(args.lb_frontend_ip_configs):
            args.load_balancer_frontend_ip_configurations = assign_aaz_list_arg(
                args.load_balancer_frontend_ip_configurations,
                args.lb_frontend_ip_configs,
                element_transformer=lambda _, lb_frontend_ip_config: {"id": lb_frontend_ip_config}
            )


class PrivateEndpointConnectionUpdate(_PrivateEndpointConnectionUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZArgEnum
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.connection_status._required = True
        args_schema.connection_status.enum = AAZArgEnum({"Approved": "Approved", "Rejected": "Rejected", "Removed": "Removed"})
        return args_schema
# endregion


# region LoadBalancers
def _get_lb_create_aux_subscriptions(public_ip_address, subnet):
    aux_subscriptions = []
    _add_aux_subscription(aux_subscriptions, public_ip_address)
    _add_aux_subscription(aux_subscriptions, subnet)
    return aux_subscriptions


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
    aux_subscriptions = _get_lb_create_aux_subscriptions(public_ip_address, subnet)

    if public_ip_address is None:
        logger.warning(
            "Please note that the default public IP used for creation will be changed from Basic to Standard "
            "in the future."
        )

    if sku.lower() == "basic":
        logger.warning(remove_basic_option_msg, "--sku standard")

    tags = tags or {}
    public_ip_address = public_ip_address or 'PublicIP{}'.format(load_balancer_name)
    backend_pool_name = backend_pool_name or '{}bepool'.format(load_balancer_name)
    if not public_ip_address_allocation:
        public_ip_address_allocation = 'Static' if (sku and sku.lower() == 'standard') else 'Dynamic'

    # Build up the ARM template
    master_template = ArmTemplateBuilder()
    lb_dependencies = []

    public_ip_id = public_ip_address if is_valid_resource_id(public_ip_address) else None
    subnet_id = subnet if is_valid_resource_id(subnet) else None
    private_ip_allocation = 'Static' if private_ip_address else 'Dynamic'

    network_id_template = resource_id(
        subscription=get_subscription_id(cmd.cli_ctx), resource_group=resource_group_name,
        namespace='Microsoft.Network')

    if edge_zone:
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
    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES, aux_subscriptions=aux_subscriptions).deployments
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


def list_load_balancer_mapping(cmd, resource_group_name, load_balancer_name, backend_pool_name, request):
    args = {
        "resource_group": resource_group_name,
        "name": load_balancer_name,
        "backend_pool_name": backend_pool_name
    }
    if 'ip_configuration' in request:
        args["ip_configuration"] = {'id': request['ip_configuration']}
    if 'ip_address' in request:
        args["ip_address"] = request['ip_address']
    from .aaz.latest.network.lb import ListMapping
    return ListMapping(cli_ctx=cmd.cli_ctx)(command_args=args)


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
# endregion


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

    sku = 'standard'
    tier = 'Global'

    tags = tags or {}
    public_ip_address = public_ip_address or 'PublicIP{}'.format(load_balancer_name)
    backend_pool_name = backend_pool_name or '{}bepool'.format(load_balancer_name)
    if not public_ip_address_allocation:
        public_ip_address_allocation = 'Static' if (sku and sku.lower() == 'standard') else 'Dynamic'

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
# endregion


# region NetworkInterfaces (NIC)
class NICCreate(_NICCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vnet_name = AAZStrArg(
            options=["--vnet-name"],
            arg_group="IP Configuration",
            help="Name of the virtual network.",
        )
        args_schema.subnet = AAZResourceIdArg(
            options=["--subnet"],
            arg_group="IP Configuration",
            help="Name or ID of an existing subnet. If name specified, please also specify `--vnet-name`; "
                 "If you want to use an existing subnet in other resource group, "
                 "please provide the ID instead of the name of the subnet.",
            required=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/virtualNetworks/{vnet_name}/subnets/{}",
            ),
        )
        args_schema.application_security_groups = AAZListArg(
            options=["--application-security-groups", "--asgs"],
            arg_group="IP Configuration",
            help="Space-separated list of application security groups.",
        )
        args_schema.application_security_groups.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationSecurityGroups/{}",
            ),
        )
        args_schema.private_ip_address = AAZStrArg(
            options=["--private-ip-address"],
            arg_group="IP Configuration",
            help="Static private IP address to use.",
        )
        args_schema.private_ip_address_version = AAZStrArg(
            options=["--private-ip-address-version"],
            arg_group="IP Configuration",
            help="Version of private IP address to use.",
            enum=["IPv4", "IPv6"],
            default="IPv4",
        )
        args_schema.public_ip_address = AAZResourceIdArg(
            options=["--public-ip-address"],
            arg_group="IP Configuration",
            help="Name or ID of an existing public IP address.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/"
                         "publicIPAddresses/{}"
            ),
        )
        args_schema.gateway_name = AAZStrArg(
            options=["--gateway-name"],
            arg_group="Application Gateway",
            help="Name of the application gateway."
        )
        args_schema.app_gateway_address_pools = AAZListArg(
            options=["--app-gateway-address-pools", "--ag-address-pools"],
            arg_group="Application Gateway",
            help="Space-separated list of names or IDs of application gateway backend address pools to "
                 "associate with the NIC. If names are used, `--gateway-name` must be specified.",
        )
        args_schema.app_gateway_address_pools.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/backendAddressPools/{}",
            ),
        )
        args_schema.lb_name = AAZStrArg(
            options=["--lb-name"],
            arg_group="Load Balancer",
            help="Name of the load balancer",
        )
        args_schema.lb_address_pools = AAZListArg(
            options=["--lb-address-pools"],
            arg_group="Load Balancer",
            help="Space-separated list of names or IDs of load balancer address pools to associate with the NIC. "
                 "If names are used, `--lb-name` must be specified.",
        )
        args_schema.lb_address_pools.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/loadBalancers/{lb_name}/backendAddressPools/{}",
            ),
        )
        args_schema.lb_inbound_nat_rules = AAZListArg(
            options=["--lb-inbound-nat-rules"],
            arg_group="Load Balancer",
            help="Space-separated list of names or IDs of load balancer inbound NAT rules to associate with the NIC. "
                 "If names are used, `--lb-name` must be specified.",
        )
        args_schema.lb_inbound_nat_rules.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/loadBalancers/{lb_name}/inboundNatRules/{}",
            ),
        )
        args_schema.edge_zone = AAZStrArg(
            options=["--edge-zone"],
            help="Name of edge zone."
        )
        args_schema.network_security_group = AAZResourceIdArg(
            options=["--network-security-group"],
            help="Name or ID of an existing network security group",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/networkSecurityGroups/{}",
            ),
        )
        args_schema.extended_location._registered = False
        args_schema.ip_configurations._registered = False
        args_schema.nsg._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.network_security_group):
            args.nsg.id = args.network_security_group
        if has_value(args.edge_zone):
            args.extended_location.name = args.edge_zone
            args.extended_location.type = "EdgeZone"
        ip_configuration = {
            "name": "ipconfig1",
            "private_ip_address": args.private_ip_address,
            "private_ip_address_version": args.private_ip_address_version,  # when address doesn't exist, version should be ipv4 (default)
            "private_ip_allocation_method": "Static" if has_value(args.private_ip_address) else "Dynamic",
            "subnet": {"id": args.subnet} if has_value(args.subnet) else None,
            "public_ip_address": {"id": args.public_ip_address} if has_value(args.public_ip_address) else None,
            "application_security_groups": [{"id": x} for x in args.application_security_groups] if has_value(args.application_security_groups) else None,
            "application_gateway_backend_address_pools": [{"id": x} for x in args.app_gateway_address_pools] if has_value(args.app_gateway_address_pools) else None,
            "load_balancer_backend_address_pools": [{"id": x} for x in args.lb_address_pools] if has_value(args.lb_address_pools) else None,
            "load_balancer_inbound_nat_rules": [{"id": x} for x in args.lb_inbound_nat_rules] if has_value(args.lb_inbound_nat_rules) else None,
        }
        args.ip_configurations = [ip_configuration]

    def _output(self, *args, **kwargs):
        result = super()._output(*args, **kwargs)
        return {"NewNIC": result}


class NICUpdate(_NICUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.network_security_group = AAZResourceIdArg(
            options=["--network-security-group"],
            help="Name or ID of an existing network security group",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/networkSecurityGroups/{}",
            ),
            nullable=True,
        )
        args_schema.nsg._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.network_security_group):
            args.nsg.id = args.network_security_group
        if has_value(args.internal_dns_name) and args.internal_dns_name == "":
            args.internal_dns_name = None

    def post_instance_update(self, instance):
        if not has_value(instance.properties.network_security_group.id):
            instance.properties.network_security_group = None


def _get_nic_ip_config(nic, name):
    if nic.ip_configurations:
        ip_config = next(
            (x for x in nic.ip_configurations if x.name.lower() == name.lower()), None)
    else:
        ip_config = None
    if not ip_config:
        raise CLIError('IP configuration {} not found.'.format(name))
    return ip_config


class NICIPConfigCreate(_NICIPConfigCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vnet_name = AAZStrArg(
            options=["--vnet-name"],
            arg_group="IP Configuration",
            help="Name of the virtual network.",
        )
        args_schema.subnet._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/virtualNetworks/{vnet_name}/subnets/{}",
        )
        args_schema.public_ip_address._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/"
                     "publicIPAddresses/{}"
        )
        args_schema.application_security_groups = AAZListArg(
            options=["--application-security-groups", "--asgs"],
            arg_group="IP Configuration",
            help="Space-separated list of application security groups.",
        )
        args_schema.application_security_groups.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationSecurityGroups/{}",
            ),
        )
        args_schema.gateway_name = AAZStrArg(
            options=["--gateway-name"],
            arg_group="Application Gateway",
            help="Name of the application gateway."
        )
        args_schema.app_gateway_address_pools = AAZListArg(
            options=["--app-gateway-address-pools", "--ag-address-pools"],
            arg_group="Application Gateway",
            help="Space-separated list of names or IDs of application gateway backend address pools to "
                 "associate with the NIC. If names are used, `--gateway-name` must be specified.",
        )
        args_schema.app_gateway_address_pools.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/backendAddressPools/{}",
            ),
        )
        args_schema.lb_name = AAZStrArg(
            options=["--lb-name"],
            arg_group="Load Balancer",
            help="Name of the load balancer",
        )
        args_schema.lb_address_pools = AAZListArg(
            options=["--lb-address-pools"],
            arg_group="Load Balancer",
            help="Space-separated list of names or IDs of load balancer address pools to associate with the NIC. "
                 "If names are used, `--lb-name` must be specified.",
        )
        args_schema.lb_address_pools.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/loadBalancers/{lb_name}/backendAddressPools/{}",
            ),
        )
        args_schema.lb_inbound_nat_rules = AAZListArg(
            options=["--lb-inbound-nat-rules"],
            arg_group="Load Balancer",
            help="Space-separated list of names or IDs of load balancer inbound NAT rules to associate with the NIC. "
                 "If names are used, `--lb-name` must be specified.",
        )
        args_schema.lb_inbound_nat_rules.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/loadBalancers/{lb_name}/inboundNatRules/{}",
            ),
        )
        args_schema.application_gateway_backend_address_pools._registered = False
        args_schema.load_balancer_backend_address_pools._registered = False
        args_schema.load_balancer_inbound_nat_rules._registered = False
        args_schema.private_ip_allocation_method._registered = False
        args_schema.asgs_obj._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.private_ip_allocation_method = "Static" if has_value(args.private_ip_address) else "Dynamic"
        if has_value(args.private_ip_address_prefix_length) and has_value(args.make_primary) and \
                args.make_primary.to_serialized_data() is True:
            raise ArgumentUsageError(
                'usage error: When `--private-ip-address-prefix-length` is specified, `--make-primary` must be false')

        args.asgs_obj = assign_aaz_list_arg(
            args.asgs_obj,
            args.application_security_groups,
            element_transformer=lambda _, asg_id: {"id": asg_id}
        )
        args.application_gateway_backend_address_pools = assign_aaz_list_arg(
            args.application_gateway_backend_address_pools,
            args.app_gateway_address_pools,
            element_transformer=lambda _, pool_id: {"id": pool_id}
        )
        args.load_balancer_backend_address_pools = assign_aaz_list_arg(
            args.load_balancer_backend_address_pools,
            args.lb_address_pools,
            element_transformer=lambda _, pool_id: {"id": pool_id}
        )
        args.load_balancer_inbound_nat_rules = assign_aaz_list_arg(
            args.load_balancer_inbound_nat_rules,
            args.lb_inbound_nat_rules,
            element_transformer=lambda _, rule_id: {"id": rule_id}
        )

    def pre_instance_create(self):
        args = self.ctx.args
        instance = self.ctx.vars.instance
        if args.private_ip_address_version.to_serialized_data().lower() == "ipv4" and not has_value(args.subnet):
            primary = next(x for x in instance.properties.ip_configurations if x.properties.primary)
            args.subnet = primary.properties.subnet.id
        if args.make_primary.to_serialized_data():
            for config in instance.properties.ip_configurations:
                config.properties.primary = False


class NICIPConfigUpdate(_NICIPConfigUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vnet_name = AAZStrArg(
            options=["--vnet-name"],
            arg_group="IP Configuration",
            help="Name of the virtual network.",
            nullable=True,
        )
        args_schema.subnet._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/virtualNetworks/{vnet_name}/subnets/{}",
        )
        args_schema.public_ip_address._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/"
                     "publicIPAddresses/{}"
        )
        args_schema.gateway_lb._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/"
                     "loadBalancers/{}/frontendIPConfigurations/{}",
        )
        args_schema.application_security_groups = AAZListArg(
            options=["--application-security-groups", "--asgs"],
            arg_group="IP Configuration",
            help="Space-separated list of application security groups.",
            nullable=True,
        )
        args_schema.application_security_groups.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationSecurityGroups/{}",
            ),
            nullable=True,
        )
        args_schema.gateway_name = AAZStrArg(
            options=["--gateway-name"],
            arg_group="Application Gateway",
            help="Name of the application gateway.",
            nullable=True,
        )
        args_schema.app_gateway_address_pools = AAZListArg(
            options=["--app-gateway-address-pools", "--ag-address-pools"],
            arg_group="Application Gateway",
            help="Space-separated list of names or IDs of application gateway backend address pools to "
                 "associate with the NIC. If names are used, `--gateway-name` must be specified.",
            nullable=True,
        )
        args_schema.app_gateway_address_pools.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/backendAddressPools/{}",
            ),
            nullable=True,
        )
        args_schema.lb_name = AAZStrArg(
            options=["--lb-name"],
            arg_group="Load Balancer",
            help="Name of the load balancer",
            nullable=True,
        )
        args_schema.lb_address_pools = AAZListArg(
            options=["--lb-address-pools"],
            arg_group="Load Balancer",
            help="Space-separated list of names or IDs of load balancer address pools to associate with the NIC. "
                 "If names are used, `--lb-name` must be specified.",
            nullable=True,
        )
        args_schema.lb_address_pools.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/loadBalancers/{lb_name}/backendAddressPools/{}",
            ),
            nullable=True,
        )
        args_schema.lb_inbound_nat_rules = AAZListArg(
            options=["--lb-inbound-nat-rules"],
            arg_group="Load Balancer",
            help="Space-separated list of names or IDs of load balancer inbound NAT rules to associate with the NIC. "
                 "If names are used, `--lb-name` must be specified.",
            nullable=True,
        )
        args_schema.lb_inbound_nat_rules.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/loadBalancers/{lb_name}/inboundNatRules/{}",
            ),
            nullable=True,
        )
        args_schema.application_gateway_backend_address_pools._registered = False
        args_schema.load_balancer_backend_address_pools._registered = False
        args_schema.load_balancer_inbound_nat_rules._registered = False
        args_schema.private_ip_allocation_method._registered = False
        args_schema.asgs_obj._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.private_ip_address):
            if args.private_ip_address is None or args.private_ip_address == "":
                # switch private IP address allocation to dynamic if empty string is used
                args.private_ip_address = None
                args.private_ip_allocation_method = "Dynamic"
                args.private_ip_address_version = "IPv4"
            else:
                # if specific address provided, allocation is static
                args.private_ip_allocation_method = "Static"

        if has_value(args.private_ip_address_prefix_length) and has_value(args.make_primary) and \
                args.make_primary.to_serialized_data() is True:
            raise ArgumentUsageError(
                'usage error: When `--private-ip-address-prefix-length` is specified, `--make-primary` must be false')

    def pre_instance_update(self, instance):
        args = self.ctx.args
        instance = self.ctx.vars.instance
        args.asgs_obj = assign_aaz_list_arg(
            args.asgs_obj,
            args.application_security_groups,
            element_transformer=lambda _, asg_id: {"id": asg_id}
        )
        args.application_gateway_backend_address_pools = assign_aaz_list_arg(
            args.application_gateway_backend_address_pools,
            args.app_gateway_address_pools,
            element_transformer=lambda _, pool_id: {"id": pool_id}
        )
        args.load_balancer_backend_address_pools = assign_aaz_list_arg(
            args.load_balancer_backend_address_pools,
            args.lb_address_pools,
            element_transformer=lambda _, pool_id: {"id": pool_id}
        )
        args.load_balancer_inbound_nat_rules = assign_aaz_list_arg(
            args.load_balancer_inbound_nat_rules,
            args.lb_inbound_nat_rules,
            element_transformer=lambda _, rule_id: {"id": rule_id}
        )
        # all ip configurations must belong to the same asgs
        is_primary = args.make_primary.to_serialized_data()
        for config in instance.properties.ip_configurations:
            if is_primary:
                config.properties.primary = False
            config.properties.application_security_groups = args.asgs_obj

    def post_instance_update(self, instance):
        if not has_value(instance.properties.subnet.id):
            instance.properties.subnet = None
        if not has_value(instance.properties.public_ip_address.id):
            instance.properties.public_ip_address = None
        if not has_value(instance.properties.gateway_load_balancer.id):
            instance.properties.gateway_load_balancer = None


def add_nic_ip_config_address_pool(cmd, resource_group_name, network_interface_name, ip_config_name,
                                   backend_address_pool, load_balancer_name=None, application_gateway_name=None):
    from .aaz.latest.network.nic.ip_config.lb_pool import Add as _LBPoolAdd
    from .aaz.latest.network.nic.ip_config.ag_pool import Add as _AGPoolAdd

    class LBPoolAdd(_LBPoolAdd):
        def _output(self, *args, **kwargs):
            result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
            return result["ipConfigurations"][0]

    class AGPoolAdd(_AGPoolAdd):
        def _output(self, *args, **kwargs):
            result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
            return result["ipConfigurations"][0]

    arguments = {
        "ip_config_name": ip_config_name,
        "nic_name": network_interface_name,
        "resource_group": resource_group_name,
        "pool_id": backend_address_pool
    }
    if load_balancer_name:
        return LBPoolAdd(cli_ctx=cmd.cli_ctx)(command_args=arguments)
    if application_gateway_name:
        return AGPoolAdd(cli_ctx=cmd.cli_ctx)(command_args=arguments)


def remove_nic_ip_config_address_pool(cmd, resource_group_name, network_interface_name, ip_config_name,
                                      backend_address_pool, load_balancer_name=None, application_gateway_name=None):
    from .aaz.latest.network.nic.ip_config.lb_pool import Remove as LBPoolRemove
    from .aaz.latest.network.nic.ip_config.ag_pool import Remove as AGPoolRemove

    arguments = {
        "ip_config_name": ip_config_name,
        "nic_name": network_interface_name,
        "resource_group": resource_group_name,
        "pool_id": backend_address_pool
    }
    if load_balancer_name:
        return LBPoolRemove(cli_ctx=cmd.cli_ctx)(command_args=arguments)
    if application_gateway_name:
        return AGPoolRemove(cli_ctx=cmd.cli_ctx)(command_args=arguments)


class NICIPConfigNATAdd(_NICIPConfigNATAdd):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.lb_name = AAZStrArg(
            options=["--lb-name"],
            help="Name of the load balancer",
        )
        args_schema.inbound_nat_rule._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/loadBalancers/{lb_name}/inboundNatRules/{}",
        )
        return args_schema

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result["ipConfigurations"][0]


class NICIPConfigNATRemove(_NICIPConfigNATRemove):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.lb_name = AAZStrArg(
            options=["--lb-name"],
            help="Name of the load balancer",
        )
        args_schema.inbound_nat_rule._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/loadBalancers/{lb_name}/inboundNatRules/{}",
        )
        return args_schema
# endregion


# region NetworkSecurityGroups
def _handle_plural_or_singular(args, plural_name, singular_name):
    values = getattr(args, plural_name)
    if not has_value(values):
        return

    setattr(args, plural_name, values if len(values) > 1 else None)
    setattr(args, singular_name, values[0] if len(values) == 1 else None)


class NSGCreate(_NSGCreate):
    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return {"NewNSG": result}


class NSGRuleCreate(_NSGRuleCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.priority._required = True
        args_schema.destination_asgs = AAZListArg(
            options=["--destination-asgs"],
            arg_group="Destination",
            help="Space-separated list of application security group names or IDs. Limited by backend server, "
                 "temporarily this argument only supports one application security group name or ID.",
        )
        args_schema.destination_asgs.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationSecurityGroups/{}",
            ),
        )
        args_schema.source_asgs = AAZListArg(
            options=["--source-asgs"],
            arg_group="Source",
            help="Space-separated list of application security group names or IDs. Limited by backend server, "
                 "temporarily this argument only supports one application security group name or ID.",
        )
        args_schema.source_asgs.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationSecurityGroups/{}",
            ),
        )
        # filter arguments
        args_schema.destination_address_prefix._registered = False
        args_schema.destination_application_security_groups._registered = False
        args_schema.destination_port_range._registered = False
        args_schema.source_address_prefix._registered = False
        args_schema.source_application_security_groups._registered = False
        args_schema.source_port_range._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        _handle_plural_or_singular(args, "destination_address_prefixes", "destination_address_prefix")
        _handle_plural_or_singular(args, "destination_port_ranges", "destination_port_range")
        _handle_plural_or_singular(args, "source_address_prefixes", "source_address_prefix")
        _handle_plural_or_singular(args, "source_port_ranges", "source_port_range")
        # handle application security groups
        if has_value(args.destination_asgs):
            args.destination_application_security_groups = [{"id": asg_id} for asg_id in args.destination_asgs]
            if has_value(args.destination_address_prefix):
                args.destination_address_prefix = None
        if has_value(args.source_asgs):
            args.source_application_security_groups = [{"id": asg_id} for asg_id in args.source_asgs]
            if has_value(args.source_address_prefix):
                args.source_address_prefix = None


class NSGRuleUpdate(_NSGRuleUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.destination_asgs = AAZListArg(
            options=["--destination-asgs"],
            arg_group="Destination",
            help="Space-separated list of application security group names or IDs. Limited by backend server, "
                 "temporarily this argument only supports one application security group name or ID.",
            nullable=True,
        )
        args_schema.destination_asgs.Element = AAZResourceIdArg(
            nullable=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationSecurityGroups/{}",
            ),
        )
        args_schema.source_asgs = AAZListArg(
            options=["--source-asgs"],
            arg_group="Source",
            help="Space-separated list of application security group names or IDs. Limited by backend server, "
                 "temporarily this argument only supports one application security group name or ID.",
            nullable=True,
        )
        args_schema.source_asgs.Element = AAZResourceIdArg(
            nullable=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationSecurityGroups/{}",
            ),
        )
        # filter arguments
        args_schema.destination_address_prefix._registered = False
        args_schema.destination_application_security_groups._registered = False
        args_schema.destination_port_range._registered = False
        args_schema.source_address_prefix._registered = False
        args_schema.source_application_security_groups._registered = False
        args_schema.source_port_range._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        # handle application security groups
        args.destination_application_security_groups = assign_aaz_list_arg(
            args.destination_application_security_groups,
            args.destination_asgs,
            element_transformer=lambda _, asg_id: {"id": asg_id}
        )
        args.source_application_security_groups = assign_aaz_list_arg(
            args.source_application_security_groups,
            args.source_asgs,
            element_transformer=lambda _, asg_id: {"id": asg_id}
        )

    def pre_instance_update(self, instance):
        if instance.properties.sourceAddressPrefix:
            instance.properties.sourceAddressPrefixes = [instance.properties.sourceAddressPrefix]
            instance.properties.sourceAddressPrefix = None
        if instance.properties.destinationAddressPrefix:
            instance.properties.destinationAddressPrefixes = [instance.properties.destinationAddressPrefix]
            instance.properties.destinationAddressPrefix = None
        if instance.properties.sourcePortRange:
            instance.properties.sourcePortRanges = [instance.properties.sourcePortRange]
            instance.properties.sourcePortRange = None
        if instance.properties.destinationPortRange:
            instance.properties.destinationPortRanges = [instance.properties.destinationPortRange]
            instance.properties.destinationPortRange = None

    def post_instance_update(self, instance):
        if instance.properties.sourceAddressPrefixes and len(instance.properties.sourceAddressPrefixes) == 1:
            instance.properties.sourceAddressPrefix = instance.properties.sourceAddressPrefixes[0]
            instance.properties.sourceAddressPrefixes = None
        if instance.properties.destinationAddressPrefixes and len(instance.properties.destinationAddressPrefixes) == 1:
            instance.properties.destinationAddressPrefix = instance.properties.destinationAddressPrefixes[0]
            instance.properties.destinationAddressPrefixes = None
        if instance.properties.sourcePortRanges and len(instance.properties.sourcePortRanges) == 1:
            instance.properties.sourcePortRange = instance.properties.sourcePortRanges[0]
            instance.properties.sourcePortRanges = None
        if instance.properties.destinationPortRanges and len(instance.properties.destinationPortRanges) == 1:
            instance.properties.destinationPortRange = instance.properties.destinationPortRanges[0]
            instance.properties.destinationPortRanges = None


def list_nsg_rules(cmd, resource_group_name, network_security_group_name, include_default=False):
    from .aaz.latest.network.nsg import Show
    nsg = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "name": network_security_group_name
    })

    rules = nsg["securityRules"]
    return rules + nsg["defaultSecurityRules"] if include_default else rules
# endregion


# region NetworkWatchers
def _create_network_watchers(cmd, resource_group_name, locations, tags):
    if resource_group_name is None:
        raise CLIError("usage error: '--resource-group' required when enabling new regions")

    from .aaz.latest.network.watcher import Create
    for location in locations:
        Create(cli_ctx=cmd.cli_ctx)(command_args={
            'name': 'NetworkWatcher_{}'.format(location),
            'resource_group': resource_group_name,
            'location': location,
            'tags': tags
        })


def _update_network_watchers(cmd, watchers, tags):
    from .aaz.latest.network.watcher import Update
    for watcher in watchers:
        id_parts = parse_resource_id(watcher['id'])
        watcher_rg = id_parts['resource_group']
        watcher_name = id_parts['name']
        watcher_tags = watcher.get('tag', None) if tags is None else tags
        Update(cli_ctx=cmd.cli_ctx)(command_args={
            'name': watcher_name,
            'resource_group': watcher_rg,
            'location': watcher['location'],
            'tags': watcher_tags
        })


def _delete_network_watchers(cmd, watchers):
    from .aaz.latest.network.watcher import Delete
    for watcher in watchers:
        from azure.cli.core.commands import LongRunningOperation
        id_parts = parse_resource_id(watcher['id'])
        watcher_rg = id_parts['resource_group']
        watcher_name = id_parts['name']
        logger.warning(
            "Disabling Network Watcher for region '%s' by deleting resource '%s'",
            watcher['location'], watcher['id'])
        poller = Delete(cli_ctx=cmd.cli_ctx)(command_args={
            'name': watcher_name,
            'resource_group': watcher_rg
        })
        LongRunningOperation(cmd.cli_ctx)(poller)


def configure_network_watcher(cmd, locations, resource_group_name=None, enabled=None, tags=None):
    from .aaz.latest.network.watcher import List
    watcher_list = List(cli_ctx=cmd.cli_ctx)(command_args={})
    locations_list = [location.lower() for location in locations]
    existing_watchers = [w for w in watcher_list if w["location"] in locations_list]
    nonenabled_regions = list(set(locations) - set(watcher["location"] for watcher in existing_watchers))

    if enabled is None:
        if resource_group_name is not None:
            logger.warning(
                "Resource group '%s' is only used when enabling new regions and will be ignored.",
                resource_group_name)
        for location in nonenabled_regions:
            logger.warning(
                "Region '%s' is not enabled for Network Watcher and will be ignored.", location)
        _update_network_watchers(cmd, existing_watchers, tags)

    elif enabled:
        _create_network_watchers(cmd, resource_group_name, nonenabled_regions, tags)
        _update_network_watchers(cmd, existing_watchers, tags)

    else:
        if tags is not None:
            raise CLIError("usage error: '--tags' cannot be used when disabling regions")
        _delete_network_watchers(cmd, existing_watchers)

    return List(cli_ctx=cmd.cli_ctx)(command_args={})


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


# combination of resource_group_name and nsg is for old output
# combination of location and flow_log_name is for new output
def show_nw_flow_logging(cmd, watcher_rg, watcher_name, location=None, resource_group_name=None, nsg=None,
                         flow_log_name=None):
    # deprecated approach to show flow log
    if nsg is not None:
        from .aaz.latest.network.watcher.flow_log import ConfigureFlowLog
        return ConfigureFlowLog(cli_ctx=cmd.cli_ctx)(command_args={"network_watcher_name": watcher_name,
                                                                   "resource_group": watcher_rg,
                                                                   "target_resource_id": nsg})

    # new approach to show flow log
    from .aaz.latest.network.watcher.flow_log import Show
    return Show(cli_ctx=cmd.cli_ctx)(command_args={"network_watcher_name": watcher_name,
                                                   "resource_group": watcher_rg,
                                                   "name": flow_log_name})


def update_nw_flow_log_getter(client, watcher_rg, watcher_name, flow_log_name):
    return client.get(watcher_rg, watcher_name, flow_log_name)


def update_nw_flow_log_setter(client, watcher_rg, watcher_name, flow_log_name, parameters):
    return client.begin_create_or_update(watcher_rg, watcher_name, flow_log_name, parameters)
# endregion


# region PublicIPAddresses
def create_public_ip(cmd, resource_group_name, public_ip_address_name, location=None, tags=None,
                     allocation_method=None, dns_name=None, dns_name_scope=None,
                     idle_timeout=4, reverse_fqdn=None, version=None, sku=None, tier=None, zone=None, ip_tags=None,
                     public_ip_prefix=None, edge_zone=None, ip_address=None,
                     protection_mode=None, ddos_protection_plan=None):
    public_ip_args = {
        'name': public_ip_address_name,
        "resource_group": resource_group_name,
        'location': location,
        'tags': tags,
        'allocation_method': allocation_method,
        'idle_timeout': idle_timeout,
        'ip_address': ip_address,
        'ip_tags': ip_tags
    }

    if public_ip_prefix:
        metadata = parse_resource_id(public_ip_prefix)
        resource_group_name = metadata["resource_group"]
        public_ip_prefix_name = metadata["resource_name"]
        public_ip_args["public_ip_prefix"] = public_ip_prefix

        # reuse prefix information
        from .aaz.latest.network.public_ip.prefix import Show
        pip_obj = Show(cli_ctx=cmd.cli_ctx)(command_args={'resource_group': resource_group_name, 'name': public_ip_prefix_name})
        version = pip_obj['publicIPAddressVersion']
        sku = pip_obj['sku']['name']
        tier = pip_obj['sku']['tier']
        zone = pip_obj['zones'] if 'zones' in pip_obj else None

    if sku.lower() == "basic":
        logger.warning(remove_basic_option_msg, "--sku standard")

    if not allocation_method:
        if sku and sku.lower() == 'standard':
            public_ip_args['allocation_method'] = 'Static'
        else:
            public_ip_args['allocation_method'] = 'Dynamic'

    public_ip_args['version'] = version
    public_ip_args['zone'] = zone

    if sku:
        public_ip_args['sku'] = sku
    if tier:
        if not sku:
            public_ip_args['sku'] = 'Basic'
        public_ip_args['tier'] = tier

    if dns_name or dns_name_scope or reverse_fqdn:
        public_ip_args['dns_name'] = dns_name
        public_ip_args['dns_name_scope'] = dns_name_scope
        public_ip_args['reverse_fqdn'] = reverse_fqdn

    if edge_zone:
        public_ip_args['edge_zone'] = edge_zone
        public_ip_args['type'] = 'EdgeZone'
    if protection_mode:
        public_ip_args['ddos_protection_mode'] = protection_mode
    if ddos_protection_plan:
        public_ip_args['ddos_protection_plan'] = ddos_protection_plan

    return PublicIPCreate(cli_ctx=cmd.cli_ctx)(command_args=public_ip_args)


class PublicIPCreate(_PublicIPCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.public_ip_prefix._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/publicIPPrefixes/{}",
        )
        args_schema.ddos_protection_plan._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/ddosProtectionPlans/{}",
        )
        return args_schema


class PublicIPUpdate(_PublicIPUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg, AAZDictArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.public_ip_prefix._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/publicIPPrefixes/{}",
        )
        args_schema.ddos_protection_plan._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/ddosProtectionPlans/{}",
        )
        args_schema.ip_tags = AAZDictArg(
            options=["--ip-tags"],
            help="Space-separated list of IP tags in `TYPE=VAL` format.",
            nullable=True
        )
        args_schema.ip_tags.Element = AAZStrArg()
        args_schema.ip_tags_list._registered = False

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.ip_tags):
            if (ip_tags := args.ip_tags.to_serialized_data()) is None:
                args.ip_tags_list = []
            else:
                args.ip_tags_list = [{"ip_tag_type": k, "tag": v} for k, v in ip_tags.items()]

    def post_instance_update(self, instance):
        if not has_value(instance.properties.ddos_settings.ddos_protection_plan.id):
            instance.properties.ddos_settings.ddos_protection_plan = None


class PublicIpPrefixCreate(_PublicIpPrefixCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZDictArg, AAZStrArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.custom_ip_prefix_name._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/customIPPrefixes/{}"
        )
        args_schema.ip_tags = AAZDictArg(
            options=["--ip-tags"],
            help="The list of tags associated with the public IP prefix in 'TYPE=VAL' format.",
        )
        args_schema.ip_tags.Element = AAZStrArg()
        args_schema.type._registered = False
        args_schema.ip_tags_list._registered = False

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.edge_zone):
            args.type = 'EdgeZone'
        if has_value(args.ip_tags):
            ip_tags = []
            for k, v in args.ip_tags.to_serialized_data().items():
                ip_tags.append({"ip_tag_type": k, "tag": v})
            args.ip_tags_list = ip_tags
# endregion


# region TrafficManagers
def create_traffic_manager_profile(cmd, traffic_manager_profile_name, resource_group_name,
                                   routing_method, unique_dns_name, monitor_path=None,
                                   monitor_port=80, monitor_protocol="HTTP",
                                   profile_status="Enabled",
                                   ttl=30, tags=None, interval=None, timeout=None, max_failures=None,
                                   monitor_custom_headers=None, status_code_ranges=None, max_return=None):
    from .aaz.latest.network.traffic_manager.profile import Create
    if monitor_path is None and monitor_protocol == 'HTTP':
        monitor_path = '/'
    args = {
        "name": traffic_manager_profile_name,
        "location": "global",
        "resource_group": resource_group_name,
        "unique_dns_name": unique_dns_name,
        "ttl": ttl,
        "max_return": max_return,
        "status": profile_status,
        "routing_method": routing_method,
        "tags": tags,
        "custom_headers": monitor_custom_headers,
        "status_code_ranges": status_code_ranges,
        "interval": interval,
        "path": monitor_path,
        "port": monitor_port,
        "protocol": monitor_protocol,
        "timeout": timeout,
        "max_failures": max_failures
    }

    return Create(cli_ctx=cmd.cli_ctx)(command_args=args)


def update_traffic_manager_profile(cmd, traffic_manager_profile_name, resource_group_name,
                                   profile_status=None, routing_method=None, tags=None,
                                   monitor_protocol=None, monitor_port=None, monitor_path=None,
                                   ttl=None, timeout=None, interval=None, max_failures=None,
                                   monitor_custom_headers=None, status_code_ranges=None, max_return=None):
    from .aaz.latest.network.traffic_manager.profile import Update
    args = {
        "name": traffic_manager_profile_name,
        "resource_group": resource_group_name
    }
    if ttl is not None:
        args["ttl"] = ttl
    if max_return is not None:
        args["max_return"] = max_return
    if profile_status is not None:
        args["status"] = profile_status
    if routing_method is not None:
        args["routing_method"] = routing_method
    if tags is not None:
        args["tags"] = tags
    if monitor_custom_headers is not None:
        args["custom_headers"] = monitor_custom_headers
    if status_code_ranges is not None:
        args["status_code_ranges"] = status_code_ranges
    if interval is not None:
        args["interval"] = interval
    if monitor_path is not None:
        args["path"] = monitor_path
    if monitor_port is not None:
        args["port"] = monitor_port
    if monitor_protocol is not None:
        args["protocol"] = monitor_protocol
    if timeout is not None:
        args["timeout"] = timeout
    if max_failures is not None:
        args["max_failures"] = max_failures

    return Update(cli_ctx=cmd.cli_ctx)(command_args=args)


def create_traffic_manager_endpoint(cmd, resource_group_name, profile_name, endpoint_type, endpoint_name,
                                    target_resource_id=None, target=None,
                                    endpoint_status=None, weight=None, priority=None,
                                    endpoint_location=None, endpoint_monitor_status=None,
                                    min_child_endpoints=None, min_child_ipv4=None, min_child_ipv6=None,
                                    geo_mapping=None, monitor_custom_headers=None, subnets=None, always_serve=None):
    from .aaz.latest.network.traffic_manager.endpoint import Create
    args = {
        "name": endpoint_name,
        "type": endpoint_type,
        "profile_name": profile_name,
        "resource_group": resource_group_name,
        "custom_headers": monitor_custom_headers,
        "endpoint_location": endpoint_location,
        "endpoint_monitor_status": endpoint_monitor_status,
        "endpoint_status": endpoint_status,
        "geo_mapping": geo_mapping,
        "min_child_endpoints": min_child_endpoints,
        "min_child_ipv4": min_child_ipv4,
        "min_child_ipv6": min_child_ipv6,
        "priority": priority,
        "subnets": subnets,
        "target": target,
        "target_resource_id": target_resource_id,
        "weight": weight,
        "always_serve": always_serve,
    }

    return Create(cli_ctx=cmd.cli_ctx)(command_args=args)


def update_traffic_manager_endpoint(cmd, resource_group_name, profile_name, endpoint_name,
                                    endpoint_type, endpoint_location=None,
                                    endpoint_status=None, endpoint_monitor_status=None,
                                    priority=None, target=None, target_resource_id=None,
                                    weight=None, min_child_endpoints=None, min_child_ipv4=None,
                                    min_child_ipv6=None, geo_mapping=None,
                                    subnets=None, monitor_custom_headers=None, always_serve=None):
    from .aaz.latest.network.traffic_manager.endpoint import Update
    args = {
        "name": endpoint_name,
        "type": endpoint_type,
        "profile_name": profile_name,
        "resource_group": resource_group_name
    }
    if monitor_custom_headers is not None:
        args["custom_headers"] = monitor_custom_headers
    if endpoint_location is not None:
        args["endpoint_location"] = endpoint_location
    if endpoint_monitor_status is not None:
        args["endpoint_monitor_status"] = endpoint_monitor_status
    if endpoint_status is not None:
        args["endpoint_status"] = endpoint_status
    if geo_mapping is not None:
        args["geo_mapping"] = geo_mapping
    if min_child_endpoints is not None:
        args["min_child_endpoints"] = min_child_endpoints
    if min_child_ipv4 is not None:
        args["min_child_ipv4"] = min_child_ipv4
    if min_child_ipv6 is not None:
        args["min_child_ipv6"] = min_child_ipv6
    if priority is not None:
        args["priority"] = priority
    if subnets is not None:
        args["subnets"] = subnets
    if target is not None:
        args["target"] = target
    if target_resource_id is not None:
        args["target_resource_id"] = target_resource_id
    if weight is not None:
        args["weight"] = weight
    if always_serve is not None:
        args["always_serve"] = always_serve

    return Update(cli_ctx=cmd.cli_ctx)(command_args=args)


def list_traffic_manager_endpoints(cmd, resource_group_name, profile_name, endpoint_type=None):
    from .aaz.latest.network.traffic_manager.profile import Show
    profile = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "profile_name": profile_name,
        "resource_group": resource_group_name,
    })

    return [endpoint for endpoint in profile["endpoints"] if not endpoint_type or endpoint["type"].endswith(endpoint_type)]
# endregion


# region VirtualNetworks
class VNetCreate(_VNetCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.edge_zone = AAZStrArg(
            options=["--edge-zone"],
            help="The name of edge zone.",
        )
        # add subnet arguments
        args_schema.subnet_name = AAZStrArg(
            options=["--subnet-name"],
            arg_group="Subnet",
            help="Name of a new subnet to create within the VNet.",
        )
        args_schema.subnet_prefixes = AAZListArg(
            options=["--subnet-prefixes"],
            arg_group="Subnet",
            help="Space-separated list of address prefixes in CIDR format for the new subnet. If omitted, "
                 "automatically reserves a /24 (or as large as available) block within the VNet address space.",
        )
        args_schema.subnet_prefixes.Element = AAZStrArg()
        args_schema.subnet_nsg = AAZResourceIdArg(
            options=["--nsg", "--network-security-group"],
            arg_group="Subnet",
            help="Name or ID of a network security group (NSG).",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/networkSecurityGroups/{}",
            ),
        )
        args_schema.ddos_protection_plan._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/ddosProtectionPlans/{}",
        )
        # filter arguments
        args_schema.extended_location._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.edge_zone):
            args.extended_location.name = args.edge_zone
            args.extended_location.type = "EdgeZone"

        if has_value(args.subnet_name):
            subnet = {"name": args.subnet_name}
            if not has_value(args.subnet_prefixes):
                # set default value
                address, bit_mask = str(args.address_prefixes[0]).split("/")
                subnet_mask = 24 if int(bit_mask) < 24 else bit_mask
                subnet["address_prefix"] = f"{address}/{subnet_mask}"
            elif len(args.subnet_prefixes) == 1:
                subnet["address_prefix"] = args.subnet_prefixes[0]
            else:
                subnet["address_prefixes"] = args.subnet_prefixes
            if has_value(args.subnet_nsg):
                subnet["network_security_group"] = {"id": args.subnet_nsg}
            args.subnets = [subnet]

        if has_value(args.ipam_pool_prefix_allocations):
            args.address_prefixes = []

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return {"newVNet": result}


class VNetUpdate(_VNetUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        # handle detach logic
        args_schema.ddos_protection_plan._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/ddosProtectionPlans/{}",
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if args.ipam_pool_prefix_allocations.to_serialized_data():
            args.address_prefixes = []

    def post_instance_update(self, instance):
        if not has_value(instance.properties.ddos_protection_plan.id):
            instance.properties.ddos_protection_plan = None


class VNetSubnetCreate(_VNetSubnetCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.delegations = AAZListArg(
            options=["--delegations"],
            help="Space-separated list of services to whom the subnet should be delegated, e.g., Microsoft.Sql/servers."
        )
        args_schema.delegations.Element = AAZStrArg()
        # add endpoint/policy arguments
        args_schema.service_endpoints = AAZListArg(
            options=["--service-endpoints"],
            help="Space-separated list of services allowed private access to this subnet. "
                 "Values from: az network vnet list-endpoint-services.",
        )
        args_schema.service_endpoints.Element = AAZStrArg()
        args_schema.service_endpoint_policy = AAZListArg(
            options=["--service-endpoint-policy"],
            help="Space-separated list of names or IDs of service endpoint policies to apply.",
        )
        args_schema.service_endpoint_policy.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/serviceEndpointPolicies/{}",
            ),
        )
        # add ple/pls arguments
        args_schema.disable_private_endpoint_network_policies = AAZStrArg(
            options=["--disable-private-endpoint-network-policies"],
            help="Disable private endpoint network policies on the subnet. Please note that it will be replaced by `--private-endpoint-network-policies` soon.",
            enum={
                "true": "Disabled", "t": "Disabled", "yes": "Disabled", "y": "Disabled", "1": "Disabled",
                "false": "Enabled", "f": "Enabled", "no": "Enabled", "n": "Enabled", "0": "Enabled",
            },
            blank="Disabled",
        )
        args_schema.disable_private_link_service_network_policies = AAZStrArg(
            options=["--disable-private-link-service-network-policies"],
            help="Disable private link service network policies on the subnet. Please note that it will be replaced by `--private-link-service-network-policies` soon.",
            enum={
                "true": "Disabled", "t": "Disabled", "yes": "Disabled", "y": "Disabled", "1": "Disabled",
                "false": "Enabled", "f": "Enabled", "no": "Enabled", "n": "Enabled", "0": "Enabled",
            },
            blank="Disabled",
        )
        args_schema.nat_gateway._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/natGateways/{}",
        )
        args_schema.network_security_group._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/networkSecurityGroups/{}",
        )
        args_schema.route_table._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/routeTables/{}",
        )
        # filter arguments
        args_schema.policies._registered = False
        args_schema.delegated_services._registered = False
        args_schema.address_prefix._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        _handle_plural_or_singular(args, "address_prefixes", "address_prefix")

        def delegation_trans(index, service_name):
            service_name = str(service_name)
            # covert name to service name
            if "/" not in service_name and len(service_name.split(".")) == 3:
                _, service, resource_type = service_name.split(".")
                service_name = f"Microsoft.{service}/{resource_type}"
            return {
                "name": str(index),
                "service_name": service_name,
            }

        if has_value(args.endpoints) and has_value(args.service_endpoints):
            raise ArgumentUsageError("usage error: `--endpoints` and `--service-endpoints` cannot be used together, we prefer to use `endpoints` instead")
        args.delegated_services = assign_aaz_list_arg(
            args.delegated_services,
            args.delegations,
            element_transformer=delegation_trans
        )
        args.endpoints = assign_aaz_list_arg(
            args.endpoints,
            args.service_endpoints,
            element_transformer=lambda _, service_name: {"service": service_name}
        )
        args.policies = assign_aaz_list_arg(
            args.policies,
            args.service_endpoint_policy,
            element_transformer=lambda _, policy_id: {"id": policy_id}
        )
        # use string instead of bool
        if has_value(args.disable_private_endpoint_network_policies):
            logger.warning(subnet_disable_ple_msg)
            args.private_endpoint_network_policies = args.disable_private_endpoint_network_policies
        if has_value(args.disable_private_link_service_network_policies):
            logger.warning(subnet_disable_pls_msg)
            args.private_link_service_network_policies = args.disable_private_link_service_network_policies

        if has_value(args.ipam_pool_prefix_allocations):
            args.address_prefixes = []


class VNetSubnetUpdate(_VNetSubnetUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.delegations = AAZListArg(
            options=["--delegations"],
            help="Space-separated list of services to whom the subnet should be delegated, e.g., Microsoft.Sql/servers.",
            nullable=True,
        )
        args_schema.delegations.Element = AAZStrArg(
            nullable=True,
        )
        # add endpoint/policy arguments
        args_schema.service_endpoints = AAZListArg(
            options=["--service-endpoints"],
            help="Space-separated list of services allowed private access to this subnet. "
                 "Values from: az network vnet list-endpoint-services.",
            nullable=True,
        )
        args_schema.service_endpoints.Element = AAZStrArg(
            nullable=True,
        )
        args_schema.service_endpoint_policy = AAZListArg(
            options=["--service-endpoint-policy"],
            help="Space-separated list of names or IDs of service endpoint policies to apply.",
            nullable=True,
        )
        args_schema.service_endpoint_policy.Element = AAZResourceIdArg(
            nullable=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/serviceEndpointPolicies/{}",
            ),
        )
        # add ple/pls arguments
        args_schema.disable_private_endpoint_network_policies = AAZStrArg(
            options=["--disable-private-endpoint-network-policies"],
            help="Disable private endpoint network policies on the subnet. Please note that it will be replaced by `--private-endpoint-network-policies` soon.",
            nullable=True,
            enum={
                "true": "Disabled", "t": "Disabled", "yes": "Disabled", "y": "Disabled", "1": "Disabled",
                "false": "Enabled", "f": "Enabled", "no": "Enabled", "n": "Enabled", "0": "Enabled",
            },
            blank="Disabled",
        )
        args_schema.disable_private_link_service_network_policies = AAZStrArg(
            options=["--disable-private-link-service-network-policies"],
            help="Disable private link service network policies on the subnet. Please note that it will be replaced by `--private-link-service-network-policies` soon.",
            nullable=True,
            enum={
                "true": "Disabled", "t": "Disabled", "yes": "Disabled", "y": "Disabled", "1": "Disabled",
                "false": "Enabled", "f": "Enabled", "no": "Enabled", "n": "Enabled", "0": "Enabled",
            },
            blank="Disabled",
        )
        # filter arguments
        args_schema.address_prefix._registered = False
        args_schema.delegated_services._registered = False
        args_schema.policies._registered = False
        # handle detach logic
        args_schema.nat_gateway._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/natGateways/{}",
        )
        args_schema.network_security_group._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/networkSecurityGroups/{}",
        )
        args_schema.route_table._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/routeTables/{}",
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        _handle_plural_or_singular(args, "address_prefixes", "address_prefix")

        def delegation_trans(index, service_name):
            service_name = str(service_name)
            # covert name to service name
            if "/" not in service_name and len(service_name.split(".")) == 3:
                _, service, resource_type = service_name.split(".")
                service_name = f"Microsoft.{service}/{resource_type}"
            return {
                "name": str(index),
                "service_name": service_name,
            }

        if has_value(args.endpoints) and has_value(args.service_endpoints):
            raise ArgumentUsageError("usage error: `--endpoints` and `--service-endpoints` cannot be used together, we prefer to use `endpoints` instead")
        args.delegated_services = assign_aaz_list_arg(
            args.delegated_services,
            args.delegations,
            element_transformer=delegation_trans
        )
        args.endpoints = assign_aaz_list_arg(
            args.endpoints,
            args.service_endpoints,
            element_transformer=lambda _, service_name: {"service": service_name}
        )
        args.policies = assign_aaz_list_arg(
            args.policies,
            args.service_endpoint_policy,
            element_transformer=lambda _, policy_id: {"id": policy_id}
        )
        # use string instead of bool
        if has_value(args.disable_private_endpoint_network_policies):
            logger.warning(subnet_disable_ple_msg)
            args.private_endpoint_network_policies = args.disable_private_endpoint_network_policies
        if has_value(args.disable_private_link_service_network_policies):
            logger.warning(subnet_disable_pls_msg)
            args.private_link_service_network_policies = args.disable_private_link_service_network_policies

        if args.ipam_pool_prefix_allocations.to_serialized_data():
            args.address_prefixes = []

    def post_instance_update(self, instance):
        if not has_value(instance.properties.network_security_group.id):
            instance.properties.network_security_group = None
        if not has_value(instance.properties.route_table.id):
            instance.properties.route_table = None
        if not has_value(instance.properties.nat_gateway.id):
            instance.properties.nat_gateway = None


class VNetPeeringCreate(_VNetPeeringCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.sync_remote._registered = False
        args_schema.remote_vnet._required = True
        args_schema.remote_vnet._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{}",
        )
        return args_schema


def list_available_ips(cmd, resource_group_name, virtual_network_name):
    from .aaz.latest.network.vnet import Show
    vnet = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "name": virtual_network_name,
        "resource_group": resource_group_name,
    })

    start_ip = vnet["addressSpace"]["addressPrefixes"][0].split("/")[0]

    from .aaz.latest.network.vnet import CheckIpAddress
    return CheckIpAddress(cli_ctx=cmd.cli_ctx)(command_args={
        "name": virtual_network_name,
        "resource_group": resource_group_name,
        "ip_address": start_ip,
    }).get("availableIPAddresses", [])


def subnet_list_available_ips(cmd, resource_group_name, virtual_network_name, subnet_name):
    from .aaz.latest.network.vnet.subnet import Show
    subnet = Show(cli_ctx=cmd.cli_ctx)(command_args={
        "name": subnet_name,
        "resource_group": resource_group_name,
        "vnet_name": virtual_network_name,
    })

    try:
        address_prefix = subnet["addressPrefixes"][0]
    except KeyError:
        address_prefix = subnet["addressPrefix"]
    start_ip = address_prefix.split("/")[0]

    from .aaz.latest.network.vnet import CheckIpAddress
    return CheckIpAddress(cli_ctx=cmd.cli_ctx)(command_args={
        "name": virtual_network_name,
        "resource_group": resource_group_name,
        "ip_address": start_ip,
    }).get("availableIPAddresses", [])


def sync_vnet_peering(cmd, resource_group_name, virtual_network_name, virtual_network_peering_name):
    from .aaz.latest.network.vnet.peering import Show
    try:
        peering = Show(cli_ctx=cmd.cli_ctx)(command_args={
            "name": virtual_network_peering_name,
            "resource_group": resource_group_name,
            "vnet_name": virtual_network_name,
        })
    except ResourceNotFoundError:
        err_msg = f"Virtual network peering {virtual_network_name} doesn't exist."
        raise ResourceNotFoundError(err_msg)

    return VNetPeeringCreate(cli_ctx=cmd.cli_ctx)(command_args={
        "name": virtual_network_peering_name,
        "resource_group": resource_group_name,
        "vnet_name": virtual_network_name,
        "remote_vnet": peering["remoteVirtualNetwork"].pop("id", None),
        "allow_vnet_access": peering.pop("allowVirtualNetworkAccess", None),
        "allow_gateway_transit": peering.pop("allowGatewayTransit", None),
        "allow_forwarded_traffic": peering.pop("allowForwardedTraffic", None),
        "use_remote_gateways": peering.pop("useRemoteGateways", None),
        "sync_remote": "true",
    })
# endregion


# region VirtualNetworkGateways
class VnetGatewayRootCertCreate(_VnetGatewayRootCertCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZFileArg, AAZFileArgBase64EncodeFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.public_cert_data = AAZFileArg(options=['--public-cert-data'],
                                                  help="Base64 contents of the root certificate file or file path.",
                                                  required=True,
                                                  fmt=AAZFileArgBase64EncodeFormat())
        args_schema.root_cert_data._required = False
        args_schema.root_cert_data._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.public_cert_data):
            import os
            path = os.path.expanduser(args.public_cert_data.to_serialized_data())
        else:
            path = None
        args.root_cert_data = path


class VnetGatewayRevokedCertCreate(_VnetGatewayRevokedCertCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.thumbprint._required = True

        return args_schema


class RootCertFormat(AAZFileArgTextFormat):
    def read_file(self, file_path):
        with open(file_path, 'r', encoding=self._encoding) as cert_file:
            lines = cert_file.readlines()

        cert_data = ''.join(line.strip() for line in lines if not line.startswith('-----'))
        return cert_data


class VnetGatewayCreate(_VnetGatewayCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZFileArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.public_ip_addresses = AAZListArg(options=['--public-ip-addresses', '--public-ip-address'],
                                                     help="Specify a single public IP (name or ID) for an active-standby gateway. Specify two space-separated public IPs for an active-active gateway.")
        args_schema.public_ip_addresses.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/publicIPAddresses/{}"
            )
        )
        args_schema.vnet = AAZResourceIdArg(
            options=['--vnet'],
            help="Name or ID of an existing virtual network which has a subnet named 'GatewaySubnet'.",
            required=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{}"
            )
        )
        args_schema.nat_rules.Element.external_mappings = AAZStrArg(
            options=["external-mappings"],
            help="Required.The private IP address external mapping for NAT.",
        )
        args_schema.nat_rules.Element.internal_mappings = AAZStrArg(
            options=["internal-mappings"],
            help="Required.The private IP address internal mapping for NAT.",
        )
        args_schema.root_cert_data = AAZFileArg(options=['--root-cert-data'], arg_group="Root Cert Authentication",
                                                help="Base64 contents of the root certificate file or file path.",
                                                fmt=RootCertFormat())
        args_schema.root_cert_name = AAZStrArg(options=['--root-cert-name'], arg_group="Root Cert Authentication",
                                               help="Root certificate name.")
        args_schema.gateway_default_site._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/localNetworkGateways/{}"
        )
        args_schema.virtual_network_gateway_migration_status._registered = False
        args_schema.ip_configurations._registered = False
        args_schema.edge_zone_type._registered = False
        args_schema.active._registered = False
        args_schema.vpn_client_root_certificates._registered = False
        args_schema.sku_tier._registered = False
        args_schema.enable_bgp._registered = False
        args_schema.nat_rules.Element.external_mappings_ip._registered = False
        args_schema.nat_rules.Element.internal_mappings_ip._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        subnet = args.vnet.to_serialized_data() + '/subnets/GatewaySubnet'
        args.sku_tier = args.sku
        if has_value(args.gateway_type) and args.gateway_type != "LocalGateway":
            args.active = len(args.public_ip_addresses) == 2
        else:
            args.active = False

        args.ip_configurations = []
        if args.gateway_type != "LocalGateway":
            if has_value(args.public_ip_addresses):
                public_ip_addresses = args.public_ip_addresses.to_serialized_data()
                ip_configuration = {}
                for i, public_ip in enumerate(public_ip_addresses):
                    ip_configuration[i] = {'subnet': subnet, 'public_ip_address': public_ip,
                                           'private_ip_allocation_method': 'Dynamic',
                                           'name': 'vnetGatewayConfig{}'.format(i)}
                    args.ip_configurations.append(ip_configuration[i])
            else:
                ip_configuration = {'subnet': subnet,
                                    'private_ip_allocation_method': 'Dynamic',
                                    'name': 'vnetGatewayConfig'}
                args.ip_configurations.append(ip_configuration)

        else:
            args.vpn_type = None
            args.sku = None
            args.sku_tier = None

        if has_value(args.asn) or has_value(args.bgp_peering_address) or has_value(args.peer_weight):
            args.enable_bgp = True
        else:
            args.asn = None
            args.bgp_peering_address = None
            args.peer_weight = None

        if has_value(args.nat_rules):
            rules = args.nat_rules.to_serialized_data()
            for rule in rules:
                if 'internal_mappings' in rule:
                    internal_mappings = rule['internal_mappings'].split(',')
                    rule['internal_mappings_ip'] = [{"address_space": internal_mapping} for internal_mapping in
                                                    internal_mappings]
                if 'external_mappings' in rule:
                    external_mappings = rule['external_mappings'].split(',')
                    rule['external_mappings_ip'] = [{"address_space": external_mapping} for external_mapping in
                                                    external_mappings]
            args.nat_rules = rules

        if has_value(args.address_prefixes) or has_value(args.client_protocol):
            if has_value(args.root_cert_data):
                data = args.root_cert_data.to_serialized_data()
            else:
                data = None
            if has_value(args.root_cert_name):
                args.vpn_client_root_certificates = [{'name': args.root_cert_name, 'public_cert_data': data}]
            else:
                args.vpn_client_root_certificates = []

        if has_value(args.edge_zone):
            args.edge_zone_type = 'EdgeZone'

    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined
        if has_value(self.ctx.vars.instance.properties.nat_rules):
            nat_rules = self.ctx.vars.instance.properties.natRules.to_serialized_data()
            for nat_rule in nat_rules:
                if 'type' in nat_rule['properties']:
                    # `properties.type` conflict with the `type` property when flatten `properties`
                    nat_rule['properties']['type'] = AAZUndefined
            self.ctx.vars.instance.properties.nat_rules = nat_rules
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return {'vnetGateway': result}


class VnetGatewayUpdate(_VnetGatewayUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZFileArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.public_ip_addresses = AAZListArg(options=['--public-ip-addresses', '--public-ip-address'],
                                                     help="Specify a single public IP (name or ID) for an active-standby gateway. Specify two space-separated public IPs for an active-active gateway.",
                                                     nullable=True)
        args_schema.public_ip_addresses.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/publicIPAddresses/{}"
            ),
            nullable=True,
        )
        args_schema.vnet = AAZResourceIdArg(
            options=['--vnet'],
            help="Name or ID of an existing virtual network which has a subnet named 'GatewaySubnet'.",
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{}"
            ),
        )
        args_schema.root_cert_data = AAZFileArg(options=['--root-cert-data'], arg_group="Root Cert Authentication",
                                                help="Base64 contents of the root certificate file or file path.",
                                                fmt=RootCertFormat(), nullable=True)
        args_schema.root_cert_name = AAZStrArg(options=['--root-cert-name'], arg_group="Root Cert Authentication",
                                               help="Root certificate name.", nullable=True,)
        args_schema.gateway_default_site._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/localNetworkGateways/{}"
        )
        args_schema.enable_high_bandwidth_vpn_gateway._registered = False
        args_schema.virtual_network_gateway_migration_status._registered = False
        args_schema.ip_configurations._registered = False
        args_schema.active._registered = False
        args_schema.vpn_client_root_certificates._registered = False
        args_schema.sku_tier._registered = False
        args_schema.vpn_client_ipsec_policies._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args

        if has_value(args.sku):
            args.sku_tier = args.sku

    def pre_instance_update(self, instance):
        args = self.ctx.args
        if has_value(args.root_cert_data):
            collection = instance.properties.vpn_client_configuration.vpn_client_root_certificates.to_serialized_data()
            root_certificate = {'name': args.root_cert_name, 'public_cert_data': args.root_cert_data}
            value = args.root_cert_name.to_serialized_data()
            match = next((x for x in collection if getattr(x, 'name', None) == value), None)
            if match:
                collection.remove(match)
            collection.append(root_certificate)
            args.vpn_client_root_certificates = collection

        subnet_id = '{}/subnets/GatewaySubnet'.format(args.vnet) if has_value(args.vnet) else \
            instance.properties.ip_configurations[0].properties.subnet.id

        if has_value(args.vnet):
            if has_value(instance.properties.ip_configurations):
                for config in instance.properties.ip_configurations:
                    config.properties.subnet.id = subnet_id

        if has_value(args.public_ip_addresses):
            instance.properties.ip_configurations = []
            public_ip_addresses = args.public_ip_addresses.to_serialized_data()
            args.ip_configurations = []
            ip_configuration = {}
            for i, public_ip in enumerate(public_ip_addresses):
                ip_configuration[i] = {'subnet': subnet_id, 'public_ip_address': {'id': public_ip},
                                       'private_ip_allocation_method': 'Dynamic',
                                       'name': 'vnetGatewayConfig{}'.format(i)}
                args.ip_configurations.append(ip_configuration[i])

            # Update active-active/active-standby status
            active = len(args.public_ip_addresses) == 2
            if instance.properties.active_active and not active:
                logger.info('Placing gateway in active-standby mode.')
            elif not instance.properties.active_active and active:
                logger.info('Placing gateway in active-active mode.')
            args.active = active


class VNetGatewayShow(_VNetGatewayShow):
    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined

        # resolve flatten conflict
        # when the type field conflicts, the type in inner layer is ignored and the outer layer is applied
        props = self.ctx.vars.instance.properties
        if has_value(props.nat_rules):
            for rule in props.nat_rules:
                if has_value(rule.properties) and has_value(rule.properties.type):
                    rule.properties.type = AAZUndefined

        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)

        return result


class VNetGatewayList(_VNetGatewayList):
    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined

        # resolve flatten conflict
        # when the type field conflicts, the type in inner layer is ignored and the outer layer is applied
        for item in self.ctx.vars.instance.value:
            props = item.properties
            if has_value(props.nat_rules):
                for rule in props.nat_rules:
                    if has_value(rule.properties) and has_value(rule.properties.type):
                        rule.properties.type = AAZUndefined

        result = self.deserialize_output(self.ctx.vars.instance.value, client_flatten=True)
        next_link = self.deserialize_output(self.ctx.vars.instance.next_link)

        return result, next_link


def generate_vpn_client(cmd, resource_group_name, virtual_network_gateway_name, processor_architecture=None,
                        authentication_method=None, radius_server_auth_certificate=None, client_root_certificates=None,
                        use_legacy=False):
    generate_args = {"name": virtual_network_gateway_name,
                     "resource_group": resource_group_name,
                     "processor_architecture": processor_architecture}
    if not use_legacy:
        generate_args['authentication_method'] = authentication_method
        generate_args['radius_server_auth_certificate'] = radius_server_auth_certificate
        generate_args['client_root_certificates'] = client_root_certificates
        return _VpnProfileGenerate(cli_ctx=cmd.cli_ctx)(command_args=generate_args)
    # legacy implementation
    return _VpnClientPackageGenerate(cli_ctx=cmd.cli_ctx)(command_args=generate_args)


class VnetGatewayVpnConnectionsDisconnect(_VnetGatewayVpnConnectionsDisconnect):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vpn_connections.Element._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/connections/{}"
        )

        return args_schema
# endregion


# region VirtualNetworkGatewayConnections
# pylint: disable=too-many-locals
def _get_vpn_connection_aux_subscriptions(local_gateway, vnet_gateway):
    aux_subscriptions = []
    _add_aux_subscription(aux_subscriptions, local_gateway)
    _add_aux_subscription(aux_subscriptions, vnet_gateway)

    return aux_subscriptions


def create_vpn_connection(cmd, resource_group_name, connection_name, vnet_gateway1,
                          location=None, tags=None, no_wait=False, validate=False,
                          vnet_gateway2=None, express_route_circuit2=None, local_gateway2=None,
                          authorization_key=None, enable_bgp=False, routing_weight=10,
                          connection_type=None, shared_key=None,
                          use_policy_based_traffic_selectors=False,
                          express_route_gateway_bypass=None, ingress_nat_rule=None, egress_nat_rule=None, auth_type=None, cert_auth=None):
    from azure.cli.core.util import random_string
    from azure.cli.core.commands.arm import ArmTemplateBuilder
    from azure.cli.command_modules.network._template_builder import build_vpn_connection_resource

    DeploymentProperties = cmd.get_models('DeploymentProperties', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    tags = tags or {}

    # Build up the ARM template
    master_template = ArmTemplateBuilder()
    vpn_connection_resource = build_vpn_connection_resource(
        cmd, connection_name, location, tags, vnet_gateway1,
        vnet_gateway2 or local_gateway2 or express_route_circuit2,
        connection_type, authorization_key, enable_bgp, routing_weight, shared_key,
        use_policy_based_traffic_selectors, express_route_gateway_bypass, ingress_nat_rule, egress_nat_rule, auth_type, cert_auth)
    master_template.add_resource(vpn_connection_resource)
    master_template.add_output('resource', connection_name, output_type='object')
    if shared_key:
        master_template.add_secure_parameter('sharedKey', shared_key)
    if authorization_key:
        master_template.add_secure_parameter('authorizationKey', authorization_key)

    template = master_template.build()
    parameters = master_template.build_parameters()

    aux_subscriptions = _get_vpn_connection_aux_subscriptions(local_gateway2, vnet_gateway2)

    # deploy ARM template
    deployment_name = 'vpn_connection_deploy_' + random_string(32)
    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES, aux_subscriptions=aux_subscriptions).deployments
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


class VpnConnectionUpdate(_VpnConnectionUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.ipsec_policies._registered = False

        return args_schema


def list_vpn_connections(cmd, resource_group_name, virtual_network_gateway_name=None):
    from .aaz.latest.network.vpn_connection import List, ListConnection
    if virtual_network_gateway_name:
        return ListConnection(cli_ctx=cmd.cli_ctx)(command_args={"resource_group": resource_group_name,
                                                                 "vnet_gateway": virtual_network_gateway_name})
    return List(cli_ctx=cmd.cli_ctx)(command_args={"resource_group": resource_group_name})


class VpnConnPackageCaptureStop(_VpnConnPackageCaptureStop):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.sas_url._required = True
        return args_schema


class VpnConnectionDeviceConfigScriptShow(_VpnConnectionDeviceConfigScriptShow):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.device_family._required = True
        args_schema.firmware_version._required = True
        args_schema.vendor._required = True

        return args_schema
# endregion


# region IPSec Policy Commands
class VnetGatewayIpsecPolicyAdd(_VnetGatewayIpsecPolicyAdd):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vpn_client_ipsec_policy_index._registered = False

        return args_schema


def clear_vnet_gateway_ipsec_policies(cmd, resource_group_name, gateway_name, no_wait=False):

    class VnetGatewayIpsecPoliciesClear(_VnetGatewayUpdate):

        def _output(self, *args, **kwargs):
            result = self.deserialize_output(
                self.ctx.vars.instance.properties.vpn_client_configuration.vpn_client_ipsec_policies,
                client_flatten=True
            )
            return result

        def pre_instance_update(self, instance):
            instance.properties.vpn_client_configuration.vpn_client_ipsec_policies = None

    ipsec_policies_args = {
        "resource_group": resource_group_name,
        "name": gateway_name,
        "no_wait": no_wait
    }

    return VnetGatewayIpsecPoliciesClear(cli_ctx=cmd.cli_ctx)(command_args=ipsec_policies_args)


class VpnConnIpsecPolicyAdd(_VpnConnIpsecPolicyAdd):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.ipsec_policy_index._registered = False
        return args_schema


def clear_vpn_conn_ipsec_policies(cmd, resource_group_name, connection_name, no_wait=False):
    class VpnConnIpsecPoliciesClear(_VpnConnectionUpdate):

        def _output(self, *args, **kwargs):
            result = self.deserialize_output(self.ctx.vars.instance.properties.ipsec_policies, client_flatten=True)
            return result

        def pre_operations(self):
            args = self.ctx.args
            args.ipsec_policies = None
            args.use_policy_based_traffic_selectors = False

    ipsec_policies_args = {
        "resource_group": resource_group_name,
        "name": connection_name,
        "no_wait": no_wait,
    }
    return VpnConnIpsecPoliciesClear(cli_ctx=cmd.cli_ctx)(command_args=ipsec_policies_args)


class VnetGatewayAadAssign(_VnetGatewayAadAssign):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.audience._required = True
        args_schema.issuer._required = True
        args_schema.tenant._required = True

        return args_schema


def remove_vnet_gateway_aad(cmd, resource_group_name, gateway_name, no_wait=False):
    class VnetGatewayAadRemove(_VnetGatewayUpdate):
        def pre_operations(self):
            args = self.ctx.args
            args.no_wait = no_wait

    aad_args = {"resource_group": resource_group_name,
                "name": gateway_name,
                "aad_audience": None,
                "aad_issuer": None,
                "aad_tenant": None,
                "vpn_auth_type": None}
    from azure.cli.core.commands import LongRunningOperation
    poller = VnetGatewayAadRemove(cli_ctx=cmd.cli_ctx)(command_args=aad_args)
    return LongRunningOperation(cmd.cli_ctx)(poller)['vpnClientConfiguration']


class VnetGatewayNatRuleAdd(_VnetGatewayNatRuleAdd):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.external_mappings = AAZListArg(
            options=["--external-mappings"],
            help="The private IP address external mapping for NAT.",
            required=True
        )
        args_schema.external_mappings.Element = AAZStrArg()
        args_schema.internal_mappings = AAZListArg(
            options=["--internal-mappings"],
            help="The private IP address internal mapping for NAT.",
            required=True
        )
        args_schema.internal_mappings.Element = AAZStrArg()

        args_schema.external_mappings_ip._registered = False
        args_schema.internal_mappings_ip._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.external_mappings):
            args.external_mappings_ip = assign_aaz_list_arg(
                args.external_mappings_ip,
                args.external_mappings,
                element_transformer=lambda _, external_mapping: {"address_space": external_mapping}
            )

        if has_value(args.internal_mappings):
            args.internal_mappings_ip = assign_aaz_list_arg(
                args.internal_mappings_ip,
                args.internal_mappings,
                element_transformer=lambda _, internal_mapping: {"address_space": internal_mapping}
            )

    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined
        if has_value(self.ctx.vars.instance.properties.nat_rules):
            nat_rules = self.ctx.vars.instance.properties.natRules.to_serialized_data()
            for nat_rule in nat_rules:
                if 'type' in nat_rule['properties']:
                    nat_rule['properties']['type'] = AAZUndefined
            self.ctx.vars.instance.properties.nat_rules = nat_rules
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class VnetGatewayNatRuleShow(_VnetGatewayNatRuleShow):

    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined
        if has_value(self.ctx.vars.instance.properties.nat_rules):
            nat_rules = self.ctx.vars.instance.properties.natRules.to_serialized_data()
            for nat_rule in nat_rules:
                if 'type' in nat_rule['properties']:
                    nat_rule['properties']['type'] = AAZUndefined
            self.ctx.vars.instance.properties.nat_rules = nat_rules
        result = self.deserialize_output(self.ctx.selectors.subresource.required(), client_flatten=True)
        return result


class VnetGatewayNatRuleRemove(_VnetGatewayNatRuleRemove):

    def _handler(self, command_args):
        lro_poller = super()._handler(command_args)
        lro_poller._result_callback = self._output
        return lro_poller

    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined
        if has_value(self.ctx.vars.instance.properties.nat_rules):
            nat_rules = self.ctx.vars.instance.properties.natRules.to_serialized_data()
            for nat_rule in nat_rules:
                if 'type' in nat_rule['properties']:
                    nat_rule['properties']['type'] = AAZUndefined
            self.ctx.vars.instance.properties.nat_rules = nat_rules
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result
# endregion


# region VirtualHub
def create_virtual_hub(cmd,
                       resource_group_name,
                       virtual_hub_name,
                       hosted_subnet,
                       public_ip_address,
                       hub_routing_preference=None,
                       auto_scale_config=None,
                       location=None,
                       tags=None):
    from azure.core.exceptions import HttpResponseError
    from azure.cli.core.commands import LongRunningOperation
    from .aaz.latest.network.routeserver import Show
    from .aaz.latest.network.routeserver import List

    list_result = List(cli_ctx=cmd.cli_ctx)(command_args={'resource_group': resource_group_name})
    for x in list_result:
        if x['name'] == virtual_hub_name:
            raise CLIError('The VirtualHub "{}" under resource group "{}" exists'.format(
                virtual_hub_name, resource_group_name))

    args = {
        'resource_group': resource_group_name,
        'name': virtual_hub_name,
        'location': location,
        'tags': tags,
        'sku': 'Standard',
        "hub_routing_preference": hub_routing_preference,
        "auto_scale_config": auto_scale_config
    }
    from .aaz.latest.network.routeserver import Create
    vhub_poller = Create(cli_ctx=cmd.cli_ctx)(command_args=args)
    LongRunningOperation(cmd.cli_ctx)(vhub_poller)

    from .aaz.latest.network.routeserver.ip_config import Create as IPConfigCreate, Delete as IPConfigDelete
    try:
        create_poller = IPConfigCreate(cli_ctx=cmd.cli_ctx)(command_args={
            'name': 'Default',
            'vhub_name': virtual_hub_name,
            'resource_group': resource_group_name,
            'subnet': hosted_subnet,
            'public_ip_address': public_ip_address
        })
        LongRunningOperation(cmd.cli_ctx)(create_poller)
    except Exception as ex:
        logger.error(ex)
        try:
            delete_poller = IPConfigDelete(cli_ctx=cmd.cli_ctx)(command_args={
                'name': 'Default',
                'vhub_name': virtual_hub_name,
                'resource_group': resource_group_name
            })
            LongRunningOperation(cmd.cli_ctx)(delete_poller)
        except HttpResponseError:
            pass
        from .aaz.latest.network.routeserver import Delete
        Delete(cli_ctx=cmd.cli_ctx)(command_args={'resource_group': resource_group_name, 'name': virtual_hub_name})
        raise ex

    return Show(cli_ctx=cmd.cli_ctx)(command_args={'resource_group': resource_group_name, 'name': virtual_hub_name})


def delete_virtual_hub(cmd, resource_group_name, virtual_hub_name):
    from azure.cli.core.commands import LongRunningOperation
    from .aaz.latest.network.routeserver.ip_config import List as IPConfigList, Delete as IPConfigDelete
    ip_configs = IPConfigList(cli_ctx=cmd.cli_ctx)(command_args={
        'vhub_name': virtual_hub_name,
        'resource_group': resource_group_name
    })
    try:
        ip_config = next(ip_configs)  # there will always be only 1
        poller = IPConfigDelete(cli_ctx=cmd.cli_ctx)(command_args={
            'name': ip_config['name'],
            'vhub_name': virtual_hub_name,
            'resource_group': resource_group_name
        })
        LongRunningOperation(cmd.cli_ctx)(poller)
    except StopIteration:
        pass
    from .aaz.latest.network.routeserver import Delete
    return Delete(cli_ctx=cmd.cli_ctx)(command_args={'resource_group': resource_group_name, 'name': virtual_hub_name})
# endregion


# region network gateway connection
class VpnConnSharedKeyUpdate(_VpnConnSharedKeyUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.value._required = True
        return args_schema
# endregion


# region usages
class UsagesList(_UsagesList):
    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance.value, client_flatten=True)
        next_link = self.deserialize_output(self.ctx.vars.instance.next_link)
        result = list(result)
        for item in result:
            item['currentValue'] = str(item['currentValue'])
            item['limit'] = str(item['limit'])
            item['localName'] = item['name']['localizedValue']
        return result, next_link
# endregion


def remove_nw_connection_monitor_output(cmd, connection_monitor_name, location):

    update_args = {
        'connection_monitor_name': connection_monitor_name,
        'location': location
    }
    from .operations.watcher import WatcherConnectionMonitorOutputRemove
    return WatcherConnectionMonitorOutputRemove(cli_ctx=cmd.cli_ctx)(command_args=update_args)


def remove_nw_connection_monitor_test_group(cmd, connection_monitor_name, location, name):
    update_args = {
        'connection_monitor_name': connection_monitor_name,
        'location': location,
        'test_group_name': name
    }
    from .operations.watcher import WatcherConnectionMonitorTestGroupRemove
    return WatcherConnectionMonitorTestGroupRemove(cli_ctx=cmd.cli_ctx)(command_args=update_args)


class SecurityPartnerProviderCreate(_SecurityPartnerProviderCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vhub._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualHubs/{}",
        )

        return args_schema


class SecurityPartnerProviderUpdate(_SecurityPartnerProviderUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vhub._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualHubs/{}",
        )

        return args_schema


class VirtualApplianceCreate(_VirtualApplianceCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vhub._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualHubs/{}",
        )

        return args_schema


class VirtualApplianceUpdate(_VirtualApplianceUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.vhub._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualHubs/{}",
        )

        return args_schema


class CustomIpPrefixCreate(_CustomIpPrefixCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZBoolArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.is_parent = AAZBoolArg(
            options=["--is-parent"],
            help="Denotes that resource is being created as a Parent CustomIpPrefix",
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if args.is_parent:
            args.prefix_type = "Parent"
        elif has_value(args.cip_prefix_parent):
            args.prefix_type = "Child"


class CustomIpPrefixUpdate(_CustomIpPrefixUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZArgEnum
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.state.enum = AAZArgEnum({"commission": "Commissioning", "decommission": "Decommissioning", "deprovision": "Deprovisioning", "provision": "Provisioning"})

        return args_schema


def create_ddos_custom_policy(cmd, ddos_custom_policy_name, resource_group_name, location=None, tags=None,
                              detection_rule_name=None, detection_mode=None, traffic_type=None,
                              packets_per_second=None, no_wait=None):
    from .aaz.latest.network.ddos_custom_policy import Create as DdosCustomPolicyCreate, Show as DdosCustomPolicyShow
    from .operations.ddos_custom_policy import convert_ddos_custom_policy_to_snake_case, combine_old_and_new_custom_policy
    from ._template_builder import build_ddos_custom_policy

    existing_policy = None

    try:
        existing_policy = DdosCustomPolicyShow(cli_ctx=cmd.cli_ctx)(command_args={
            'ddos_custom_policy_name': ddos_custom_policy_name,
            'resource_group': resource_group_name
        })

        existing_policy = convert_ddos_custom_policy_to_snake_case(existing_policy)
    except ResourceNotFoundError:
        # No existing DDoS custom policy; proceed with creation.
        logger.debug("DDoS custom policy '%s' not found in resource group '%s'.",
                     ddos_custom_policy_name, resource_group_name)
    except Exception as err:  # pylint: disable=broad-except
        # Log unexpected errors while preserving previous behavior of not failing the command.
        logger.warning("Failed to retrieve existing DDoS custom policy '%s' in resource group '%s': %s",
                       ddos_custom_policy_name, resource_group_name, err)

    policy = build_ddos_custom_policy(cmd, ddos_custom_policy_name, location, tags, detection_rule_name, detection_mode,
                                      packets_per_second, traffic_type)

    if existing_policy:
        policy = combine_old_and_new_custom_policy(existing_policy, policy)

    policy['resource_group'] = resource_group_name
    policy['no_wait'] = no_wait

    return DdosCustomPolicyCreate(cli_ctx=cmd.cli_ctx)(command_args=policy)
