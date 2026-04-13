# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access

from azure.cli.core.aaz import AAZStrArg
from azure.cli.command_modules.monitor.aaz.latest.monitor.private_link_scope.private_endpoint_connection._delete \
    import Delete as _ConnectionDelete
from azure.cli.command_modules.monitor.operations.private_link_scope import validate_private_endpoint_connection_id


class ConnectionDelete(_ConnectionDelete):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.id = AAZStrArg(
            options=["--id"],
            help="ID of the private endpoint connection associated with the private link scope. "
                 "Values from `az monitor private-link-scope show`."
        )
        args_schema.name._required = False
        args_schema.resource_group._required = False
        args_schema.scope_name._required = False

        return args_schema

    def pre_operations(self):
        validate_private_endpoint_connection_id(self.ctx.args)
