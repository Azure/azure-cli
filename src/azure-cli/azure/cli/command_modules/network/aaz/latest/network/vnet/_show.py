# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}


from azure.cli.core.aaz import AAZCommand, register_command


@register_command("network vnet show")
class Show(AAZCommand):
    """ Get the details of a virtual network.

    :example: Get details for MyVNet.
        az network vnet show -g MyResourceGroup -n MyVNet

    """
    pass
