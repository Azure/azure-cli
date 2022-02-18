# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/virtualNetworkPeerings/{}
from azure.cli.core.aaz import *


@register_command("network vnet peering create", hide=True)
class Create(AAZCommand):
    """ Create a virtual network peering connection.

    To successfully peer two virtual networks this command must be called twice with
    the values for --vnet-name and --remote-vnet reversed.

    :example: Create a peering connection between two virtual networks.
        az network vnet peering create -g MyResourceGroup -n MyVnet1ToMyVnet2 --vnet-name MyVnet1
        --remote-vnet MyVnet2Id --allow-vnet-access

    """
    pass


__all__ = ["Create"]
