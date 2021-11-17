# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}

from azure.cli.core.aaz import AAZCommand, register_command


@register_command("network vnet subnet show")
class Show(AAZCommand):
    """ Show details of a subnet.

    :example: Show the details of a subnet associated with a virtual network.
        az network vnet subnet show -g MyResourceGroup -n MySubnet --vnet-name MyVNet

    """
    pass
