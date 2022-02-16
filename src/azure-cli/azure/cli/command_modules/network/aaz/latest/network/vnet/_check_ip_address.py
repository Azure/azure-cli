# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/CheckIPAddressAvailability

from azure.cli.core.aaz import AAZCommand, register_command


@register_command("network vnet check-ip-address-availablity")
class CheckIPAddressAvailability(AAZCommand):
    """ Check if a private IP address is available for use within a virtual network.

    :example: Check whether 10.0.0.4 is available within MyVnet.
        az network vnet check-ip-address -g MyResourceGroup -n MyVnet --ip-address 10.0.0.4

    """
    pass


__all__ = ["CheckIPAddressAvailability"]
