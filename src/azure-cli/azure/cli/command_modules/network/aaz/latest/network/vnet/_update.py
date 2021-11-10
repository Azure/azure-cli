# Resources:
#   - /subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}


from azure.cli.core.aaz import AAZCommand, register_command


@register_command("network vnet update")
class Update(AAZCommand):
    pass
