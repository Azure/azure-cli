# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}

from azure.cli.core.aaz import *


@register_command("network vnet subnet create")
class Create(AAZCommand):
    """ Create a subnet and associate an existing NSG and route table.

    :example: Create new subnet attached to an NSG with a custom route table.
        az network vnet subnet create -g MyResourceGroup --vnet-name MyVnet -n MySubnet
        --address-prefixes 10.0.0.0/24 --network-security-group MyNsg --route-table MyRouteTable

    :example: Create new subnet attached to a NAT gateway.
        az network vnet subnet create -n MySubnet --vnet-name MyVnet -g MyResourceGroup --nat-gateway MyNatGateway
        --address-prefixes "10.0.0.0/21"

    """
    pass


__all__ = ["Create"]
