# Resources:
#   - /subscriptions/{}/providers/Microsoft.Network/virtualNetworks
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks


from azure.cli.core.aaz import AAZCommand, register_command


@register_command("network vnet list")
class List(AAZCommand):
    """ List virtual networks.

    :example: List all virtual networks in a subscription.
        az network vnet list

    :example: List all virtual networks in a resource group.
        az network vnet list -g MyResourceGroup

    :example: List virtual networks in a subscription which specify a certain address prefix.
        az network vnet list --query "[?contains(addressSpace.addressPrefixes, '10.0.0.0/16')]"

    """
    pass


__all__ = [List]
