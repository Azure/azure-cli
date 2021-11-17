# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}

from azure.cli.core.aaz import AAZCommand, register_command


@register_command("network vnet delete")
class Delete(AAZCommand):
    """ Delete a virtual network.

    :example: Delete a virtual network.
        az network vnet delete -g MyResourceGroup -n myVNet

    """
    pass
