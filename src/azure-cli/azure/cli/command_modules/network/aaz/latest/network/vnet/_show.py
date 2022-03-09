# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}

from azure.cli.core.aaz import *


@register_command("network vnet show")
class Show(AAZCommand):
    """ Get the details of a virtual network.

    :example: Get details for MyVNet.
        az network vnet show -g MyResourceGroup -n MyVNet
        az network vnet show -g MyResourceGroup -n MyVNet

    """

    def _handler(self, command_args):
        super()._handler(command_args)
        self._execute_operations()
        return self._output()

    def _execute_operations(self):
        self.VirtualNetworkGet(ctx=self.ctx)()

    def _output(self, *args, **kwargs):
        return self.deserialize_output(self.ctx.vars.instance, client_flatten=True)

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        _schema = super()._build_arguments_schema(*args, **kwargs)
        _schema.resource_group_name = AAZResourceGroupNameArg()
        _schema.virtual_network_name = AAZStrArg(
            options=["--virtual-network-name", "--name", "-n"], required=True,
            id_part="name",
            help="The name of the virtual network.",
        )
        _schema.expand = AAZStrArg(
            options=["--expand"],
            help="Expands referenced resources."
        )
        return _schema

    class VirtualNetworkGet(AAZHttpOperation):
        CLIENT_TYPE = "MgmtClient"
        ERROR_FORMAT = "MgmtErrorFormat"

        def __call__(self, *args, **kwargs):
            request = self.make_request()
            session = self.client.send_request(request=request, stream=False, **kwargs)
            if session.http_response.status_code in [200]:
                return self.on_200(session)
            return self.on_error(session)

        @property
        def url(self):
            return self.client.format_url(
                '/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Network/virtualNetworks/{virtualNetworkName}',
                **self.url_parameters
            )

        @property
        def method(self):
            return "GET"

        @property
        def url_parameters(self):
            parameters = {
                **self.serialize_url_param(
                    'subscriptionId', self.ctx.subscription_id,
                ),
                **self.serialize_url_param('resourceGroupName', self.ctx.args.resource_group_name),
                **self.serialize_url_param('virtualNetworkName', self.ctx.args.virtual_network_name),
            }
            return parameters

        @property
        def query_parameters(self):
            parameters = {
                **self.serialize_query_param('api-version', '2021-05-01'),
            }
            return parameters

        @property
        def header_parameters(self):
            parameters = {
                **self.serialize_header_param('Accept', "application/json"),
            }
            return parameters

        def on_200(self, session):
            data = self.deserialize_http_content(session)
            self.ctx.set_var('instance', data, schema_builder=self._build_instance_schema)

        @classmethod
        def _build_instance_schema(cls):
            _schema = AAZObjectType()
            _schema.id = AAZStrType()
            _schema.name = AAZStrType(flags={'read_only': True})
            _schema.type = AAZStrType(flags={'read_only': True})
            _schema.location = AAZStrType()
            _schema.tags = AAZDictType()
            _schema.tags.Element = AAZStrType()
            _schema.extended_location = AAZObjectType(serialized_name="extendedLocation")
            _schema.properties = AAZObjectType(flags={'client_flatten': True})
            _schema.etag = AAZStrType(flags={'read_only': True})

            extended_location = _schema.extended_location
            extended_location.name = AAZStrType()
            extended_location.type = AAZStrType()

            properties = _schema.properties
            properties.address_space = AAZObjectType(serialized_name='addressSpace')
            properties.dhcp_options = AAZObjectType(serialized_name='dhcpOptions')
            properties.flow_timeout_in_minutes = AAZIntType(serialized_name='flowTimeoutInMinutes')
            properties.subnets = AAZListType()
            properties.subnets.Element = AAZObjectType()
            properties.virtual_network_peerings = AAZListType(serialized_name='virtualNetworkPeerings')
            properties.virtual_network_peerings.Element = AAZObjectType()
            properties.resource_guid = AAZStrType(serialized_name='resourceGuid', flags={'read_only': True})
            properties.provisioning_state = AAZStrType(serialized_name='provisioningState', flags={'read_only': True})
            properties.enable_ddos_protection = AAZBoolType(serialized_name='enableDdosProtection')
            properties.enable_vm_protection = AAZBoolType(serialized_name='enableVmProtection')
            properties.ddos_protection_plan = AAZObjectType(serialized_name='ddosProtectionPlan')
            properties.bgp_communities = AAZObjectType(serialized_name='bgpCommunities')
            properties.encryption = AAZObjectType(serialized_name='encryption')
            properties.ip_allocations = AAZListType(serialized_name='ipAllocations')
            properties.ip_allocations.Element = AAZObjectType()

            address_space = _schema.properties.address_space
            address_space.address_prefixes = AAZListType(serialized_name='addressPrefixes')
            address_space.address_prefixes.Element = AAZStrType()

            dhcp_options = _schema.properties.dhcp_options
            dhcp_options.dns_servers = AAZListType(serialized_name='dnsServers')
            dhcp_options.dns_servers.Element = AAZStrType()

            element = _schema.properties.subnets.Element
            # TODO:

            element = _schema.properties.virtual_network_peerings.Element
            # TODO:

            ddos_protection_plan = _schema.properties.ddos_protection_plan
            ddos_protection_plan.id = AAZStrType()

            bgp_communities = _schema.properties.bgp_communities
            bgp_communities.virtual_network_community = AAZStrType(serialized_name='virtualNetworkCommunity')
            bgp_communities.regional_community = AAZStrType(serialized_name='regionalCommunity', flags={'read_only': True})

            encryption = _schema.properties.encryption
            encryption.enabled = AAZBoolType()
            encryption.enforcement = AAZStrType()

            element = _schema.properties.ip_allocations.Element
            element.id = AAZStrType()

            return _schema


__all__ = ["Show"]
