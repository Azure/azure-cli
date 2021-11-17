# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/virtualNetworkPeerings/{}
from azure.cli.core.aaz import AAZCommand, register_command


@register_command("network vnet peering delete")
class Delete(AAZCommand):
    """ Delete a peering.

    :example: Delete a virtual network peering connection.
        az network vnet peering delete -g MyResourceGroup -n MyVnet1ToMyVnet2 --vnet-name MyVnet1

    """
    pass
