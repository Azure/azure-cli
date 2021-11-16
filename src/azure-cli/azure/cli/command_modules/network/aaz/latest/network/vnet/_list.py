# Resources:
#   - /subscriptions/{}/providers/Microsoft.Network/virtualNetworks
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks


from azure.cli.core.aaz import AAZCommand, register_command


@register_command("network vnet list")
class List(AAZCommand):
    """ List virtual networks.
    """
    pass
