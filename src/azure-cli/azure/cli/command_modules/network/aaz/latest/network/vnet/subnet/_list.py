# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets
from azure.cli.core.aaz import *


@register_command("network vnet subnet list")
class List(AAZCommand):
    """ List the subnets in a virtual network.

    :example: List the subnets in a virtual network.
        az network vnet subnet list -g MyResourceGroup --vnet-name MyVNet

    """
    pass


__all__ = ["List"]
