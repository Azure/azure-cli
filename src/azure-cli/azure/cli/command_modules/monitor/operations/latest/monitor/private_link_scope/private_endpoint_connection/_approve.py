# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access, line-too-long

from azure.cli.core.aaz import register_command
from azure.cli.command_modules.monitor.aaz.latest.monitor.private_link_scope.private_endpoint_connection._update \
    import Update
from azure.cli.command_modules.monitor.operations.private_link_scope import validate_private_endpoint_connection_id


@register_command("monitor private-link-scope private-endpoint-connection approve")
class ConnectionApprove(Update):
    """Approve a private endpoint connection of a private link scope resource.

    :example: Approve a private endpoint connection of a private link scope resource.
        az monitor private-link-scope private-endpoint-connection approve --name MyPrivateEndpointConnection --resource-group MyResourceGroup --scope-name MyScope
    """

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.status._registered = False
        args_schema.name._required = False
        args_schema.resource_group._required = False
        args_schema.scope_name._required = False
        return args_schema

    def pre_operations(self):
        self.ctx.args.status = "Approved"
        validate_private_endpoint_connection_id(self.ctx.args)
