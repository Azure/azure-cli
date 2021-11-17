# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets
from azure.cli.core.aaz import AAZCommand, register_command


@register_command("network vnet subnet list")
class List(AAZCommand):
    """ List the subnets in a virtual network.

    :example: List the subnets in a virtual network.
        az network vnet subnet list -g MyResourceGroup --vnet-name MyVNet

    """
    pass
