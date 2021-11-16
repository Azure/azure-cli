# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}

from azure.cli.core.aaz import AAZCommand, register_command


@register_command("network vnet create")
class Create(AAZCommand):
    """ Create a virtual network.

    You may also create a subnet at the same time by specifying a subnet name and (optionally) an address prefix.
    To learn about how to create a virtual network visit https://docs.microsoft.com/azure/virtual-network/manage-virtual-network#create-a-virtual-network
    """
    pass
