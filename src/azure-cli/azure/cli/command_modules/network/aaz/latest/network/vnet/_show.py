# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}


from azure.cli.core.aaz import AAZCommand, register_command, AAZStrArg


@register_command("network vnet show")
class Show(AAZCommand):
    """ Get the details of a virtual network.

    :example: Get details for MyVNet.
        az network vnet show -g MyResourceGroup -n MyVNet

    """

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        schema = super()._build_arguments_schema(*args, **kwargs)
        schema.virtual_network_name = AAZStrArg(
            options=["--virtual-network-name", "--name", "-n"], required=True, id_part="name",
            help="The name of the virtual network.",
        )
        schema.expand = AAZStrArg(
            options=["--expand"],
            help="Expands referenced resources."
        )

    def _handler(self, command_args):
        self.setup_command_args(command_args)
        pass

