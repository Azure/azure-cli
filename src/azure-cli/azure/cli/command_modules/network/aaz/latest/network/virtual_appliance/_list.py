# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#
# Code generated by aaz-dev-tools
# --------------------------------------------------------------------------------------------

# pylint: skip-file
# flake8: noqa

from azure.cli.core.aaz import *


@register_command(
    "network virtual-appliance list",
    is_preview=True,
)
class List(AAZCommand):
    """List all Azure network virtual appliance.

    :example: List all Azure network virtual appliances.
        az network virtual-appliance list -g MyRG
    """

    _aaz_info = {
        "version": "2021-08-01",
        "resources": [
            ["mgmt-plane", "/subscriptions/{}/providers/microsoft.network/networkvirtualappliances", "2021-08-01"],
            ["mgmt-plane", "/subscriptions/{}/resourcegroups/{}/providers/microsoft.network/networkvirtualappliances", "2021-08-01"],
        ]
    }

    def _handler(self, command_args):
        super()._handler(command_args)
        return self.build_paging(self._execute_operations, self._output)

    _args_schema = None

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        if cls._args_schema is not None:
            return cls._args_schema
        cls._args_schema = super()._build_arguments_schema(*args, **kwargs)

        # define Arg Group ""

        _args_schema = cls._args_schema
        _args_schema.resource_group = AAZResourceGroupNameArg()
        return cls._args_schema

    def _execute_operations(self):
        self.pre_operations()
        condition_0 = has_value(self.ctx.args.resource_group) and has_value(self.ctx.subscription_id)
        condition_1 = has_value(self.ctx.subscription_id) and has_value(self.ctx.args.resource_group) is not True
        if condition_0:
            self.NetworkVirtualAppliancesListByResourceGroup(ctx=self.ctx)()
        if condition_1:
            self.NetworkVirtualAppliancesList(ctx=self.ctx)()
        self.post_operations()

    @register_callback
    def pre_operations(self):
        pass

    @register_callback
    def post_operations(self):
        pass

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance.value, client_flatten=True)
        next_link = self.deserialize_output(self.ctx.vars.instance.next_link)
        return result, next_link

    class NetworkVirtualAppliancesListByResourceGroup(AAZHttpOperation):
        CLIENT_TYPE = "MgmtClient"

        def __call__(self, *args, **kwargs):
            request = self.make_request()
            session = self.client.send_request(request=request, stream=False, **kwargs)
            if session.http_response.status_code in [200]:
                return self.on_200(session)

            return self.on_error(session.http_response)

        @property
        def url(self):
            return self.client.format_url(
                "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Network/networkVirtualAppliances",
                **self.url_parameters
            )

        @property
        def method(self):
            return "GET"

        @property
        def error_format(self):
            return "ODataV4Format"

        @property
        def url_parameters(self):
            parameters = {
                **self.serialize_url_param(
                    "resourceGroupName", self.ctx.args.resource_group,
                    required=True,
                ),
                **self.serialize_url_param(
                    "subscriptionId", self.ctx.subscription_id,
                    required=True,
                ),
            }
            return parameters

        @property
        def query_parameters(self):
            parameters = {
                **self.serialize_query_param(
                    "api-version", "2021-08-01",
                    required=True,
                ),
            }
            return parameters

        @property
        def header_parameters(self):
            parameters = {
                **self.serialize_header_param(
                    "Accept", "application/json",
                ),
            }
            return parameters

        def on_200(self, session):
            data = self.deserialize_http_content(session)
            self.ctx.set_var(
                "instance",
                data,
                schema_builder=self._build_schema_on_200
            )

        _schema_on_200 = None

        @classmethod
        def _build_schema_on_200(cls):
            if cls._schema_on_200 is not None:
                return cls._schema_on_200

            cls._schema_on_200 = AAZObjectType()

            _schema_on_200 = cls._schema_on_200
            _schema_on_200.next_link = AAZStrType(
                serialized_name="nextLink",
            )
            _schema_on_200.value = AAZListType()

            value = cls._schema_on_200.value
            value.Element = AAZObjectType()

            _element = cls._schema_on_200.value.Element
            _element.etag = AAZStrType(
                flags={"read_only": True},
            )
            _element.id = AAZStrType()
            _element.identity = AAZObjectType()
            _element.location = AAZStrType()
            _element.name = AAZStrType(
                flags={"read_only": True},
            )
            _element.properties = AAZObjectType(
                flags={"client_flatten": True},
            )
            _element.tags = AAZDictType()
            _element.type = AAZStrType(
                flags={"read_only": True},
            )

            identity = cls._schema_on_200.value.Element.identity
            identity.principal_id = AAZStrType(
                serialized_name="principalId",
                flags={"read_only": True},
            )
            identity.tenant_id = AAZStrType(
                serialized_name="tenantId",
                flags={"read_only": True},
            )
            identity.type = AAZStrType()
            identity.user_assigned_identities = AAZDictType(
                serialized_name="userAssignedIdentities",
            )

            user_assigned_identities = cls._schema_on_200.value.Element.identity.user_assigned_identities
            user_assigned_identities.Element = AAZObjectType()

            _element = cls._schema_on_200.value.Element.identity.user_assigned_identities.Element
            _element.client_id = AAZStrType(
                serialized_name="clientId",
                flags={"read_only": True},
            )
            _element.principal_id = AAZStrType(
                serialized_name="principalId",
                flags={"read_only": True},
            )

            properties = cls._schema_on_200.value.Element.properties
            properties.address_prefix = AAZStrType(
                serialized_name="addressPrefix",
                flags={"read_only": True},
            )
            properties.boot_strap_configuration_blobs = AAZListType(
                serialized_name="bootStrapConfigurationBlobs",
            )
            properties.cloud_init_configuration = AAZStrType(
                serialized_name="cloudInitConfiguration",
            )
            properties.cloud_init_configuration_blobs = AAZListType(
                serialized_name="cloudInitConfigurationBlobs",
            )
            properties.inbound_security_rules = AAZListType(
                serialized_name="inboundSecurityRules",
                flags={"read_only": True},
            )
            properties.nva_sku = AAZObjectType(
                serialized_name="nvaSku",
            )
            properties.provisioning_state = AAZStrType(
                serialized_name="provisioningState",
                flags={"read_only": True},
            )
            properties.ssh_public_key = AAZStrType(
                serialized_name="sshPublicKey",
            )
            properties.virtual_appliance_asn = AAZIntType(
                serialized_name="virtualApplianceAsn",
            )
            properties.virtual_appliance_nics = AAZListType(
                serialized_name="virtualApplianceNics",
                flags={"read_only": True},
            )
            properties.virtual_appliance_sites = AAZListType(
                serialized_name="virtualApplianceSites",
                flags={"read_only": True},
            )
            properties.virtual_hub = AAZObjectType(
                serialized_name="virtualHub",
            )
            _ListHelper._build_schema_sub_resource_read(properties.virtual_hub)

            boot_strap_configuration_blobs = cls._schema_on_200.value.Element.properties.boot_strap_configuration_blobs
            boot_strap_configuration_blobs.Element = AAZStrType()

            cloud_init_configuration_blobs = cls._schema_on_200.value.Element.properties.cloud_init_configuration_blobs
            cloud_init_configuration_blobs.Element = AAZStrType()

            inbound_security_rules = cls._schema_on_200.value.Element.properties.inbound_security_rules
            inbound_security_rules.Element = AAZObjectType()
            _ListHelper._build_schema_sub_resource_read(inbound_security_rules.Element)

            nva_sku = cls._schema_on_200.value.Element.properties.nva_sku
            nva_sku.bundled_scale_unit = AAZStrType(
                serialized_name="bundledScaleUnit",
            )
            nva_sku.market_place_version = AAZStrType(
                serialized_name="marketPlaceVersion",
            )
            nva_sku.vendor = AAZStrType()

            virtual_appliance_nics = cls._schema_on_200.value.Element.properties.virtual_appliance_nics
            virtual_appliance_nics.Element = AAZObjectType(
                flags={"read_only": True},
            )

            _element = cls._schema_on_200.value.Element.properties.virtual_appliance_nics.Element
            _element.name = AAZStrType(
                flags={"read_only": True},
            )
            _element.private_ip_address = AAZStrType(
                serialized_name="privateIpAddress",
                flags={"read_only": True},
            )
            _element.public_ip_address = AAZStrType(
                serialized_name="publicIpAddress",
                flags={"read_only": True},
            )

            virtual_appliance_sites = cls._schema_on_200.value.Element.properties.virtual_appliance_sites
            virtual_appliance_sites.Element = AAZObjectType()
            _ListHelper._build_schema_sub_resource_read(virtual_appliance_sites.Element)

            tags = cls._schema_on_200.value.Element.tags
            tags.Element = AAZStrType()

            return cls._schema_on_200

    class NetworkVirtualAppliancesList(AAZHttpOperation):
        CLIENT_TYPE = "MgmtClient"

        def __call__(self, *args, **kwargs):
            request = self.make_request()
            session = self.client.send_request(request=request, stream=False, **kwargs)
            if session.http_response.status_code in [200]:
                return self.on_200(session)

            return self.on_error(session.http_response)

        @property
        def url(self):
            return self.client.format_url(
                "/subscriptions/{subscriptionId}/providers/Microsoft.Network/networkVirtualAppliances",
                **self.url_parameters
            )

        @property
        def method(self):
            return "GET"

        @property
        def error_format(self):
            return "ODataV4Format"

        @property
        def url_parameters(self):
            parameters = {
                **self.serialize_url_param(
                    "subscriptionId", self.ctx.subscription_id,
                    required=True,
                ),
            }
            return parameters

        @property
        def query_parameters(self):
            parameters = {
                **self.serialize_query_param(
                    "api-version", "2021-08-01",
                    required=True,
                ),
            }
            return parameters

        @property
        def header_parameters(self):
            parameters = {
                **self.serialize_header_param(
                    "Accept", "application/json",
                ),
            }
            return parameters

        def on_200(self, session):
            data = self.deserialize_http_content(session)
            self.ctx.set_var(
                "instance",
                data,
                schema_builder=self._build_schema_on_200
            )

        _schema_on_200 = None

        @classmethod
        def _build_schema_on_200(cls):
            if cls._schema_on_200 is not None:
                return cls._schema_on_200

            cls._schema_on_200 = AAZObjectType()

            _schema_on_200 = cls._schema_on_200
            _schema_on_200.next_link = AAZStrType(
                serialized_name="nextLink",
            )
            _schema_on_200.value = AAZListType()

            value = cls._schema_on_200.value
            value.Element = AAZObjectType()

            _element = cls._schema_on_200.value.Element
            _element.etag = AAZStrType(
                flags={"read_only": True},
            )
            _element.id = AAZStrType()
            _element.identity = AAZObjectType()
            _element.location = AAZStrType()
            _element.name = AAZStrType(
                flags={"read_only": True},
            )
            _element.properties = AAZObjectType(
                flags={"client_flatten": True},
            )
            _element.tags = AAZDictType()
            _element.type = AAZStrType(
                flags={"read_only": True},
            )

            identity = cls._schema_on_200.value.Element.identity
            identity.principal_id = AAZStrType(
                serialized_name="principalId",
                flags={"read_only": True},
            )
            identity.tenant_id = AAZStrType(
                serialized_name="tenantId",
                flags={"read_only": True},
            )
            identity.type = AAZStrType()
            identity.user_assigned_identities = AAZDictType(
                serialized_name="userAssignedIdentities",
            )

            user_assigned_identities = cls._schema_on_200.value.Element.identity.user_assigned_identities
            user_assigned_identities.Element = AAZObjectType()

            _element = cls._schema_on_200.value.Element.identity.user_assigned_identities.Element
            _element.client_id = AAZStrType(
                serialized_name="clientId",
                flags={"read_only": True},
            )
            _element.principal_id = AAZStrType(
                serialized_name="principalId",
                flags={"read_only": True},
            )

            properties = cls._schema_on_200.value.Element.properties
            properties.address_prefix = AAZStrType(
                serialized_name="addressPrefix",
                flags={"read_only": True},
            )
            properties.boot_strap_configuration_blobs = AAZListType(
                serialized_name="bootStrapConfigurationBlobs",
            )
            properties.cloud_init_configuration = AAZStrType(
                serialized_name="cloudInitConfiguration",
            )
            properties.cloud_init_configuration_blobs = AAZListType(
                serialized_name="cloudInitConfigurationBlobs",
            )
            properties.inbound_security_rules = AAZListType(
                serialized_name="inboundSecurityRules",
                flags={"read_only": True},
            )
            properties.nva_sku = AAZObjectType(
                serialized_name="nvaSku",
            )
            properties.provisioning_state = AAZStrType(
                serialized_name="provisioningState",
                flags={"read_only": True},
            )
            properties.ssh_public_key = AAZStrType(
                serialized_name="sshPublicKey",
            )
            properties.virtual_appliance_asn = AAZIntType(
                serialized_name="virtualApplianceAsn",
            )
            properties.virtual_appliance_nics = AAZListType(
                serialized_name="virtualApplianceNics",
                flags={"read_only": True},
            )
            properties.virtual_appliance_sites = AAZListType(
                serialized_name="virtualApplianceSites",
                flags={"read_only": True},
            )
            properties.virtual_hub = AAZObjectType(
                serialized_name="virtualHub",
            )
            _ListHelper._build_schema_sub_resource_read(properties.virtual_hub)

            boot_strap_configuration_blobs = cls._schema_on_200.value.Element.properties.boot_strap_configuration_blobs
            boot_strap_configuration_blobs.Element = AAZStrType()

            cloud_init_configuration_blobs = cls._schema_on_200.value.Element.properties.cloud_init_configuration_blobs
            cloud_init_configuration_blobs.Element = AAZStrType()

            inbound_security_rules = cls._schema_on_200.value.Element.properties.inbound_security_rules
            inbound_security_rules.Element = AAZObjectType()
            _ListHelper._build_schema_sub_resource_read(inbound_security_rules.Element)

            nva_sku = cls._schema_on_200.value.Element.properties.nva_sku
            nva_sku.bundled_scale_unit = AAZStrType(
                serialized_name="bundledScaleUnit",
            )
            nva_sku.market_place_version = AAZStrType(
                serialized_name="marketPlaceVersion",
            )
            nva_sku.vendor = AAZStrType()

            virtual_appliance_nics = cls._schema_on_200.value.Element.properties.virtual_appliance_nics
            virtual_appliance_nics.Element = AAZObjectType(
                flags={"read_only": True},
            )

            _element = cls._schema_on_200.value.Element.properties.virtual_appliance_nics.Element
            _element.name = AAZStrType(
                flags={"read_only": True},
            )
            _element.private_ip_address = AAZStrType(
                serialized_name="privateIpAddress",
                flags={"read_only": True},
            )
            _element.public_ip_address = AAZStrType(
                serialized_name="publicIpAddress",
                flags={"read_only": True},
            )

            virtual_appliance_sites = cls._schema_on_200.value.Element.properties.virtual_appliance_sites
            virtual_appliance_sites.Element = AAZObjectType()
            _ListHelper._build_schema_sub_resource_read(virtual_appliance_sites.Element)

            tags = cls._schema_on_200.value.Element.tags
            tags.Element = AAZStrType()

            return cls._schema_on_200


class _ListHelper:
    """Helper class for List"""

    _schema_sub_resource_read = None

    @classmethod
    def _build_schema_sub_resource_read(cls, _schema):
        if cls._schema_sub_resource_read is not None:
            _schema.id = cls._schema_sub_resource_read.id
            return

        cls._schema_sub_resource_read = _schema_sub_resource_read = AAZObjectType()

        sub_resource_read = _schema_sub_resource_read
        sub_resource_read.id = AAZStrType()

        _schema.id = cls._schema_sub_resource_read.id


__all__ = ["List"]