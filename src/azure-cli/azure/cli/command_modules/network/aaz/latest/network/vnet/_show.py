# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}

from azure.cli.core.aaz import AAZCommand, register_command, AAZStrArg, AAZHttpOperation, AAZResourceGroupNameArg


@register_command("network vnet show")
class Show(AAZCommand):
    """ Get the details of a virtual network.

    :example: Get details for MyVNet.
        az network vnet show -g MyResourceGroup -n MyVNet

    """

    class VirtualNetworkGet(AAZHttpOperation):
        CLIENT_TYPE = "MgmtClient"

        @property
        def url(self):
            parameters = {
                **self.serialize_url_param('subscriptionId', self.ctx.subscription_id),
                **self.serialize_url_param('resourceGroupName', self.ctx.args.resource_group_name),
                **self.serialize_url_param('virtualNetworkName', self.ctx.args.virtual_network_name),
            }
            return self.client.format_url(
                '/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Network/virtualNetworks/{virtualNetworkName}',
                **parameters
            )

        @property
        def query_parameters(self):
            parameters = {
                **self.serialize_query_param('api-version', '2021-05-01'),
            }
            return parameters

        @property
        def header_parameters(self):
            parameters = {
                **self.serialize_query_param('Accept', "application/json"),
            }
            return parameters

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        schema = super()._build_arguments_schema(*args, **kwargs)
        schema.resource_group_name = AAZResourceGroupNameArg()
        schema.virtual_network_name = AAZStrArg(
            options=["--virtual-network-name", "--name", "-n"], required=True,
            id_part="name",
            help="The name of the virtual network.",
        )
        schema.expand = AAZStrArg(
            options=["--expand"],
            help="Expands referenced resources."
        )
        return schema

    def _handler(self, command_args):
        super()._handler(command_args)
        operation = self.VirtualNetworkGet(self.ctx)


    # def _virtual_networks_get_operation(self):
    #     pass
