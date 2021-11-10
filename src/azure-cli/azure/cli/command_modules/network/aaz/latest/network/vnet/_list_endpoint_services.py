
# Resources:
#   - /subscriptions/{}/providers/Microsoft.Network/locations/{}/virtualNetworkAvailableEndpointServices


from azure.cli.core.aaz import AAZCommand, register_command


@register_command("network vnet list-endpoint-services")
class ListEndpointServices(AAZCommand):
    pass
