# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/virtualNetworkPeerings/{}
from azure.cli.core.aaz import AAZCommand, register_command


@register_command("network vnet peering update")
class Update(AAZCommand):
    """ Update a peering.

    :example: Change forwarded traffic configuration of a virtual network peering.
        az network vnet peering update -g MyResourceGroup -n MyVnet1ToMyVnet2 --vnet-name MyVnet1
        --set allowForwardedTraffic=true

    :example: Change virtual network access of a virtual network peering.
        az network vnet peering update -g MyResourceGroup -n MyVnet1ToMyVnet2 --vnet-name MyVnet1
        --set allowVirtualNetworkAccess=true

    :example: Change gateway transit property configuration of a virtual network peering.
        az network vnet peering update -g MyResourceGroup -n MyVnet1ToMyVnet2 --vnet-name MyVnet1
        --set allowGatewayTransit=true

    :example: Use remote gateways in virtual network peering.
        az network vnet peering update -g MyResourceGroup -n MyVnet1ToMyVnet2 --vnet-name MyVnet1
        --set useRemoteGateways=true
    """
    pass
