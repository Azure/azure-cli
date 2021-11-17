# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/virtualNetworkPeerings
from azure.cli.core.aaz import AAZCommand, register_command


@register_command("network vnet peering list")
class List(AAZCommand):
    """ List peerings.

    :example: List all peerings of a specified virtual network.
        az network vnet peering list -g MyResourceGroup --vnet-name MyVnet1

    """
    pass
