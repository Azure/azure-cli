from azure.cli.core.aaz import *


@register_command_group(
    "network",
)
class __CMDGroup(AAZCommandGroup):
    """ Manage Azure Network resources.
    """
    pass


__all__ = ["__CMDGroup"]
