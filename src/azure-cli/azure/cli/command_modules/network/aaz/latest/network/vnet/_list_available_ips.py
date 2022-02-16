
# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/CheckIPAddressAvailability


from azure.cli.core.aaz import AAZCommand, register_command


@register_command("network vnet list-available-ips")
class ListAvailableIps(AAZCommand):
    """ List some available ips in the vnet.

    :example: List some available ips in the vnet.
        az network vnet list-available-ips -g MyResourceGroup -n MyVNet
    """
    pass


__all__ = ["ListAvailableIps"]
