# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/locations/{}/availableDelegations
#   - /subscriptions/{}/providers/Microsoft.Network/locations/{}/availableDelegations
from azure.cli.core.aaz import AAZCommand, register_command


@register_command("network vnet subnet list-available-delegations")
class ListAvailableDelegations(AAZCommand):
    pass
