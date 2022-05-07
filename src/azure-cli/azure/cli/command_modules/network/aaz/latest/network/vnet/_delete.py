# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}

from azure.cli.core.aaz import *


@register_command("network vnet delete", is_preview=True)
class Delete(AAZCommand):
    """ Delete a virtual network.

    :example: Delete a virtual network.
        az network vnet delete -g MyResourceGroup -n myVNet

    """

    AZ_SUPPORT_NO_WAIT = True

    def _handler(self, command_args):
        super()._handler(command_args)
        return self.build_lro_poller(self._execute_operations(), result_callback=None)

    def _execute_operations(self):
        yield self.VirtualNetworksDelete(ctx=self.ctx)()

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        _schema = super()._build_arguments_schema(*args, **kwargs)
        _schema.subscription_id = AAZSubscriptionIdArg()
        _schema.resource_group_name = AAZResourceGroupNameArg()
        _schema.virtual_network_name = AAZStrArg(
            options=["--virtual-network-name", "--name", "-n"], required=True,
            id_part="name",
            help="The name of the virtual network.",
        )
        _schema.no_wait = AAZBoolArg(
            options=["--no-wait"],
            help='Do not wait for the long-running operation to finish.',
            default=False,
        )
        return _schema

    class VirtualNetworksDelete(AAZHttpOperation):
        CLIENT_TYPE = "MgmtClient"
        ERROR_FORMAT = "MgmtErrorFormat"

        def __call__(self, *args, **kwargs):
            request = self.make_request()
            session = self.client.send_request(request=request, stream=False, **kwargs)
            if session.http_response.status_code in [200, 202, 204]:
                return self.client.build_lro_polling(
                    self.ctx.args.no_wait, session,
                    deserialization_callback=self.on_200_202_204,
                    lro_options={'final-state-via': 'azure-async-operation'},
                    path_format_arguments=self.url_parameters,
                )
            return self.on_error(session)

        @property
        def url(self):
            return self.client.format_url(
                '/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Network/virtualNetworks/{virtualNetworkName}',
                **self.url_parameters
            )

        @property
        def method(self):
            return "DELETE"

        @property
        def url_parameters(self):
            parameters = {
                **self.serialize_url_param('subscriptionId', self.ctx.args.subscription_id),
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

        def on_200_202_204(self, session):
            return None


__all__ = ["Delete"]
