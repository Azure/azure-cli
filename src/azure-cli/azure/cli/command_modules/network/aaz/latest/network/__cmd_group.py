from azure.cli.core.aaz._command import AAZCommandGroup, register_command_group


@register_command_group("network")
class __CMDGroup(AAZCommandGroup):
    """ Manage Azure Network resources.
    """
    pass
