# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from ..aaz.latest.network.virtual_network_appliance import (Create as _VirtualNetworkApplianceCreate, List as _VirtualNetworkApplianceList,
                                                            Show as _VirtualNetworkApplianceShow, Update as _VirtualNetworkApplianceUpdate)
from azure.cli.core.aaz import AAZIntType, AAZStrType, AAZBoolType, AAZObjectType, AAZDictType, AAZListType


class VirtualNetworkApplianceCreate(_VirtualNetworkApplianceCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.bandwidth_in_gbps._fmt = AAZStrArgFormat(pattern="^[0-9a-zA-Z]([0-9a-zA-Z_.-]{0,62}[0-9a-zA-Z_])?$")
        return args_schema

    class VirtualNetworkAppliancesCreateOrUpdate(_VirtualNetworkApplianceCreate.VirtualNetworkAppliancesCreateOrUpdate):
        @classmethod
        def _build_schema_on_200_201(cls):
            schema = super()._build_schema_on_200_201()
            del schema.properties._fields['bandwidth_in_gbps']
            schema.properties.bandwidth_in_gbps = AAZIntType(
                serialized_name="bandwidthInGbps",
            )
            return schema


class VirtualNetworkApplianceList(_VirtualNetworkApplianceList):

    class VirtualNetworkAppliancesList(_VirtualNetworkApplianceList.VirtualNetworkAppliancesList):
        @classmethod
        def _build_schema_on_200(cls):
            schema = super()._build_schema_on_200()
            del schema.value.Element.properties._fields['bandwidth_in_gbps']
            schema.value.Element.properties.bandwidth_in_gbps = AAZIntType(
                serialized_name="bandwidthInGbps",
            )
            return schema


class VirtualNetworkApplianceShow(_VirtualNetworkApplianceShow):

    class VirtualNetworkAppliancesGet(_VirtualNetworkApplianceShow.VirtualNetworkAppliancesGet):
        @classmethod
        def _build_schema_on_200(cls):
            schema = super()._build_schema_on_200()
            del schema.properties._fields['bandwidth_in_gbps']
            schema.properties.bandwidth_in_gbps = AAZIntType(
                serialized_name="bandwidthInGbps",
            )
            return schema


class VirtualNetworkApplianceUpdate(_VirtualNetworkApplianceUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.bandwidth_in_gbps._fmt = AAZStrArgFormat(pattern="^[0-9a-zA-Z]([0-9a-zA-Z_.-]{0,62}[0-9a-zA-Z_])?$")
        return args_schema

    class VirtualNetworkAppliancesGet(_VirtualNetworkApplianceUpdate.VirtualNetworkAppliancesGet):

        @classmethod
        def _build_schema_on_200(cls):
            schema = super()._build_schema_on_200()
            del schema.properties._fields['bandwidth_in_gbps']
            schema.properties.bandwidth_in_gbps = AAZIntType(
                serialized_name="bandwidthInGbps",
            )
            return schema

    class VirtualNetworkAppliancesCreateOrUpdate(_VirtualNetworkApplianceUpdate.VirtualNetworkAppliancesCreateOrUpdate):

        @classmethod
        def _build_schema_on_200_201(cls):
            schema = super()._build_schema_on_200_201()
            del schema.properties._fields['bandwidth_in_gbps']
            schema.properties.bandwidth_in_gbps = AAZIntType(
                serialized_name="bandwidthInGbps",
            )
            return schema

    class InstanceUpdateByJson(_VirtualNetworkApplianceUpdate.InstanceUpdateByJson):

        def _update_instance(self, instance):
            _instance_value, _builder = self.new_content_builder(
                self.ctx.args,
                value=instance,
                typ=AAZObjectType
            )
            _builder.set_prop("location", AAZStrType, ".location")
            _builder.set_prop("properties", AAZObjectType, typ_kwargs={"flags": {"client_flatten": True}})
            _builder.set_prop("tags", AAZDictType, ".tags")

            properties = _builder.get(".properties")
            if properties is not None:
                properties.set_prop("bandwidthInGbps", AAZIntType, ".bandwidth_in_gbps")
                properties.set_prop("subnet", AAZObjectType, ".subnet")

            subnet = _builder.get(".properties.subnet")
            if subnet is not None:
                subnet.set_prop("id", AAZStrType, ".id")
                subnet.set_prop("name", AAZStrType, ".name")
                subnet.set_prop("properties", AAZObjectType, typ_kwargs={"flags": {"client_flatten": True}})
                subnet.set_prop("type", AAZStrType, ".type")

            properties = _builder.get(".properties.subnet.properties")
            if properties is not None:
                properties.set_prop("addressPrefix", AAZStrType, ".address_prefix")
                properties.set_prop("addressPrefixes", AAZListType, ".address_prefixes")
                properties.set_prop("applicationGatewayIPConfigurations", AAZListType,
                                    ".application_gateway_ip_configurations")
                properties.set_prop("defaultOutboundAccess", AAZBoolType, ".default_outbound_access")
                properties.set_prop("delegations", AAZListType, ".delegations")
                properties.set_prop("ipAllocations", AAZListType, ".ip_allocations")
                properties.set_prop("ipamPoolPrefixAllocations", AAZListType, ".ipam_pool_prefix_allocations")
                _UpdateHelper._build_schema_sub_resource_update(
                    properties.set_prop("natGateway", AAZObjectType, ".nat_gateway"))
                properties.set_prop("networkSecurityGroup", AAZObjectType, ".network_security_group")
                properties.set_prop("privateEndpointNetworkPolicies", AAZStrType, ".private_endpoint_network_policies")
                properties.set_prop("privateLinkServiceNetworkPolicies", AAZStrType,
                                    ".private_link_service_network_policies")
                properties.set_prop("routeTable", AAZObjectType, ".route_table")
                properties.set_prop("serviceEndpointPolicies", AAZListType, ".service_endpoint_policies")
                properties.set_prop("serviceEndpoints", AAZListType, ".service_endpoints")
                _UpdateHelper._build_schema_sub_resource_update(
                    properties.set_prop("serviceGateway", AAZObjectType, ".service_gateway"))
                properties.set_prop("sharingScope", AAZStrType, ".sharing_scope")

            address_prefixes = _builder.get(".properties.subnet.properties.addressPrefixes")
            if address_prefixes is not None:
                address_prefixes.set_elements(AAZStrType, ".")

            application_gateway_ip_configurations = _builder.get(
                ".properties.subnet.properties.applicationGatewayIPConfigurations")
            if application_gateway_ip_configurations is not None:
                application_gateway_ip_configurations.set_elements(AAZObjectType, ".")

            _elements = _builder.get(".properties.subnet.properties.applicationGatewayIPConfigurations[]")
            if _elements is not None:
                _elements.set_prop("id", AAZStrType, ".id")
                _elements.set_prop("name", AAZStrType, ".name")
                _elements.set_prop("properties", AAZObjectType, typ_kwargs={"flags": {"client_flatten": True}})

            properties = _builder.get(".properties.subnet.properties.applicationGatewayIPConfigurations[].properties")
            if properties is not None:
                _UpdateHelper._build_schema_sub_resource_update(properties.set_prop("subnet", AAZObjectType, ".subnet"))

            delegations = _builder.get(".properties.subnet.properties.delegations")
            if delegations is not None:
                delegations.set_elements(AAZObjectType, ".")

            _elements = _builder.get(".properties.subnet.properties.delegations[]")
            if _elements is not None:
                _elements.set_prop("id", AAZStrType, ".id")
                _elements.set_prop("name", AAZStrType, ".name")
                _elements.set_prop("properties", AAZObjectType, typ_kwargs={"flags": {"client_flatten": True}})
                _elements.set_prop("type", AAZStrType, ".type")

            properties = _builder.get(".properties.subnet.properties.delegations[].properties")
            if properties is not None:
                properties.set_prop("serviceName", AAZStrType, ".service_name")

            ip_allocations = _builder.get(".properties.subnet.properties.ipAllocations")
            if ip_allocations is not None:
                _UpdateHelper._build_schema_sub_resource_update(ip_allocations.set_elements(AAZObjectType, "."))

            ipam_pool_prefix_allocations = _builder.get(".properties.subnet.properties.ipamPoolPrefixAllocations")
            if ipam_pool_prefix_allocations is not None:
                ipam_pool_prefix_allocations.set_elements(AAZObjectType, ".")

            _elements = _builder.get(".properties.subnet.properties.ipamPoolPrefixAllocations[]")
            if _elements is not None:
                _elements.set_prop("numberOfIpAddresses", AAZStrType, ".number_of_ip_addresses")
                _elements.set_prop("pool", AAZObjectType, typ_kwargs={"flags": {"client_flatten": True}})

            pool = _builder.get(".properties.subnet.properties.ipamPoolPrefixAllocations[].pool")
            if pool is not None:
                pool.set_prop("id", AAZStrType, ".id")

            network_security_group = _builder.get(".properties.subnet.properties.networkSecurityGroup")
            if network_security_group is not None:
                network_security_group.set_prop("id", AAZStrType, ".id")
                network_security_group.set_prop("location", AAZStrType, ".location")
                network_security_group.set_prop("properties", AAZObjectType,
                                                typ_kwargs={"flags": {"client_flatten": True}})
                network_security_group.set_prop("tags", AAZDictType, ".tags")

            properties = _builder.get(".properties.subnet.properties.networkSecurityGroup.properties")
            if properties is not None:
                properties.set_prop("flushConnection", AAZBoolType, ".flush_connection")
                properties.set_prop("securityRules", AAZListType, ".security_rules")

            security_rules = _builder.get(".properties.subnet.properties.networkSecurityGroup.properties.securityRules")
            if security_rules is not None:
                security_rules.set_elements(AAZObjectType, ".")

            _elements = _builder.get(".properties.subnet.properties.networkSecurityGroup.properties.securityRules[]")
            if _elements is not None:
                _elements.set_prop("id", AAZStrType, ".id")
                _elements.set_prop("name", AAZStrType, ".name")
                _elements.set_prop("properties", AAZObjectType, typ_kwargs={"flags": {"client_flatten": True}})
                _elements.set_prop("type", AAZStrType, ".type")

            properties = _builder.get(
                ".properties.subnet.properties.networkSecurityGroup.properties.securityRules[].properties")
            if properties is not None:
                properties.set_prop("access", AAZStrType, ".access", typ_kwargs={"flags": {"required": True}})
                properties.set_prop("description", AAZStrType, ".description")
                properties.set_prop("destinationAddressPrefix", AAZStrType, ".destination_address_prefix")
                properties.set_prop("destinationAddressPrefixes", AAZListType, ".destination_address_prefixes")
                properties.set_prop("destinationApplicationSecurityGroups", AAZListType,
                                    ".destination_application_security_groups")
                properties.set_prop("destinationPortRange", AAZStrType, ".destination_port_range")
                properties.set_prop("destinationPortRanges", AAZListType, ".destination_port_ranges")
                properties.set_prop("direction", AAZStrType, ".direction", typ_kwargs={"flags": {"required": True}})
                properties.set_prop("priority", AAZIntType, ".priority", typ_kwargs={"flags": {"required": True}})
                properties.set_prop("protocol", AAZStrType, ".protocol", typ_kwargs={"flags": {"required": True}})
                properties.set_prop("sourceAddressPrefix", AAZStrType, ".source_address_prefix")
                properties.set_prop("sourceAddressPrefixes", AAZListType, ".source_address_prefixes")
                properties.set_prop("sourceApplicationSecurityGroups", AAZListType,
                                    ".source_application_security_groups")
                properties.set_prop("sourcePortRange", AAZStrType, ".source_port_range")
                properties.set_prop("sourcePortRanges", AAZListType, ".source_port_ranges")

            destination_address_prefixes = _builder.get(
                ".properties.subnet.properties.networkSecurityGroup.properties.securityRules[].properties.destinationAddressPrefixes")
            if destination_address_prefixes is not None:
                destination_address_prefixes.set_elements(AAZStrType, ".")

            destination_application_security_groups = _builder.get(
                ".properties.subnet.properties.networkSecurityGroup.properties.securityRules[].properties.destinationApplicationSecurityGroups")
            if destination_application_security_groups is not None:
                _UpdateHelper._build_schema_application_security_group_update(
                    destination_application_security_groups.set_elements(AAZObjectType, "."))

            destination_port_ranges = _builder.get(
                ".properties.subnet.properties.networkSecurityGroup.properties.securityRules[].properties.destinationPortRanges")
            if destination_port_ranges is not None:
                destination_port_ranges.set_elements(AAZStrType, ".")

            source_address_prefixes = _builder.get(
                ".properties.subnet.properties.networkSecurityGroup.properties.securityRules[].properties.sourceAddressPrefixes")
            if source_address_prefixes is not None:
                source_address_prefixes.set_elements(AAZStrType, ".")

            source_application_security_groups = _builder.get(
                ".properties.subnet.properties.networkSecurityGroup.properties.securityRules[].properties.sourceApplicationSecurityGroups")
            if source_application_security_groups is not None:
                _UpdateHelper._build_schema_application_security_group_update(
                    source_application_security_groups.set_elements(AAZObjectType, "."))

            source_port_ranges = _builder.get(
                ".properties.subnet.properties.networkSecurityGroup.properties.securityRules[].properties.sourcePortRanges")
            if source_port_ranges is not None:
                source_port_ranges.set_elements(AAZStrType, ".")

            tags = _builder.get(".properties.subnet.properties.networkSecurityGroup.tags")
            if tags is not None:
                tags.set_elements(AAZStrType, ".")

            route_table = _builder.get(".properties.subnet.properties.routeTable")
            if route_table is not None:
                route_table.set_prop("id", AAZStrType, ".id")
                route_table.set_prop("location", AAZStrType, ".location")
                route_table.set_prop("properties", AAZObjectType, typ_kwargs={"flags": {"client_flatten": True}})
                route_table.set_prop("tags", AAZDictType, ".tags")

            properties = _builder.get(".properties.subnet.properties.routeTable.properties")
            if properties is not None:
                properties.set_prop("disableBgpRoutePropagation", AAZBoolType, ".disable_bgp_route_propagation")
                properties.set_prop("routes", AAZListType, ".routes")

            routes = _builder.get(".properties.subnet.properties.routeTable.properties.routes")
            if routes is not None:
                routes.set_elements(AAZObjectType, ".")

            _elements = _builder.get(".properties.subnet.properties.routeTable.properties.routes[]")
            if _elements is not None:
                _elements.set_prop("id", AAZStrType, ".id")
                _elements.set_prop("name", AAZStrType, ".name")
                _elements.set_prop("properties", AAZObjectType, typ_kwargs={"flags": {"client_flatten": True}})
                _elements.set_prop("type", AAZStrType, ".type")

            properties = _builder.get(".properties.subnet.properties.routeTable.properties.routes[].properties")
            if properties is not None:
                properties.set_prop("addressPrefix", AAZStrType, ".address_prefix")
                properties.set_prop("nextHopIpAddress", AAZStrType, ".next_hop_ip_address")
                properties.set_prop("nextHopType", AAZStrType, ".next_hop_type",
                                    typ_kwargs={"flags": {"required": True}})

            tags = _builder.get(".properties.subnet.properties.routeTable.tags")
            if tags is not None:
                tags.set_elements(AAZStrType, ".")

            service_endpoint_policies = _builder.get(".properties.subnet.properties.serviceEndpointPolicies")
            if service_endpoint_policies is not None:
                service_endpoint_policies.set_elements(AAZObjectType, ".")

            _elements = _builder.get(".properties.subnet.properties.serviceEndpointPolicies[]")
            if _elements is not None:
                _elements.set_prop("id", AAZStrType, ".id")
                _elements.set_prop("location", AAZStrType, ".location")
                _elements.set_prop("properties", AAZObjectType, typ_kwargs={"flags": {"client_flatten": True}})
                _elements.set_prop("tags", AAZDictType, ".tags")

            properties = _builder.get(".properties.subnet.properties.serviceEndpointPolicies[].properties")
            if properties is not None:
                properties.set_prop("contextualServiceEndpointPolicies", AAZListType,
                                    ".contextual_service_endpoint_policies")
                properties.set_prop("serviceAlias", AAZStrType, ".service_alias")
                properties.set_prop("serviceEndpointPolicyDefinitions", AAZListType,
                                    ".service_endpoint_policy_definitions")

            contextual_service_endpoint_policies = _builder.get(
                ".properties.subnet.properties.serviceEndpointPolicies[].properties.contextualServiceEndpointPolicies")
            if contextual_service_endpoint_policies is not None:
                contextual_service_endpoint_policies.set_elements(AAZStrType, ".")

            service_endpoint_policy_definitions = _builder.get(
                ".properties.subnet.properties.serviceEndpointPolicies[].properties.serviceEndpointPolicyDefinitions")
            if service_endpoint_policy_definitions is not None:
                service_endpoint_policy_definitions.set_elements(AAZObjectType, ".")

            _elements = _builder.get(
                ".properties.subnet.properties.serviceEndpointPolicies[].properties.serviceEndpointPolicyDefinitions[]")
            if _elements is not None:
                _elements.set_prop("id", AAZStrType, ".id")
                _elements.set_prop("name", AAZStrType, ".name")
                _elements.set_prop("properties", AAZObjectType, typ_kwargs={"flags": {"client_flatten": True}})
                _elements.set_prop("type", AAZStrType, ".type")

            properties = _builder.get(
                ".properties.subnet.properties.serviceEndpointPolicies[].properties.serviceEndpointPolicyDefinitions[].properties")
            if properties is not None:
                properties.set_prop("description", AAZStrType, ".description")
                properties.set_prop("service", AAZStrType, ".service")
                properties.set_prop("serviceResources", AAZListType, ".service_resources")

            service_resources = _builder.get(
                ".properties.subnet.properties.serviceEndpointPolicies[].properties.serviceEndpointPolicyDefinitions[].properties.serviceResources")
            if service_resources is not None:
                service_resources.set_elements(AAZStrType, ".")

            tags = _builder.get(".properties.subnet.properties.serviceEndpointPolicies[].tags")
            if tags is not None:
                tags.set_elements(AAZStrType, ".")

            service_endpoints = _builder.get(".properties.subnet.properties.serviceEndpoints")
            if service_endpoints is not None:
                service_endpoints.set_elements(AAZObjectType, ".")

            _elements = _builder.get(".properties.subnet.properties.serviceEndpoints[]")
            if _elements is not None:
                _elements.set_prop("locations", AAZListType, ".locations")
                _UpdateHelper._build_schema_sub_resource_update(
                    _elements.set_prop("networkIdentifier", AAZObjectType, ".network_identifier"))
                _elements.set_prop("service", AAZStrType, ".service")

            locations = _builder.get(".properties.subnet.properties.serviceEndpoints[].locations")
            if locations is not None:
                locations.set_elements(AAZStrType, ".")

            tags = _builder.get(".tags")
            if tags is not None:
                tags.set_elements(AAZStrType, ".")

            return _instance_value


class _UpdateHelper:
    """Helper class for Update"""

    @classmethod
    def _build_schema_application_security_group_update(cls, _builder):
        if _builder is None:
            return
        _builder.set_prop("location", AAZStrType, ".location")
        _builder.set_prop("tags", AAZDictType, ".tags")

        tags = _builder.get(".tags")
        if tags is not None:
            tags.set_elements(AAZStrType, ".")

    @classmethod
    def _build_schema_sub_resource_update(cls, _builder):
        if _builder is None:
            return
        _builder.set_prop("id", AAZStrType, ".id")
