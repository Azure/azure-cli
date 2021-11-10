# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/CheckIPAddressAvailability

from azure.cli.core.aaz import AAZCommand, register_command


@register_command("network vnet check-ip-address-availablity")
class CheckIPAddressAvailability(AAZCommand):
    pass

