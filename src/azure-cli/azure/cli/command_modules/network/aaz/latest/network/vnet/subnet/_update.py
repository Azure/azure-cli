# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}
from azure.cli.core.aaz import *


@register_command("network vnet subnet update")
class Update(AAZCommand):
    """ Update a subnet.

    :example: Associate a network security group to a subnet.
        az network vnet subnet update -g MyResourceGroup -n MySubnet --vnet-name MyVNet --network-security-group MyNsg

    :example: Update subnet with NAT gateway.
        az network vnet subnet update -n MySubnet --vnet-name MyVnet -g MyResourceGroup --nat-gateway MyNatGateway
        --address-prefixes "10.0.0.0/21"

    :example: Disable the private endpoint network policies.
        az network vnet subnet update -n MySubnet --vnet-name MyVnet -g MyResourceGroup
        --disable-private-endpoint-network-policies

    """
    pass


__all__ = ["Update"]
