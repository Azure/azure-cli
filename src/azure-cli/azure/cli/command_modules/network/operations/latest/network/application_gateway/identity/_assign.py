# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.command_modules.network.aaz.latest.network.application_gateway.identity._assign import Assign as _IdentityAssign


class IdentityAssign(_IdentityAssign):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.identity = AAZResourceIdArg(
            options=["--identity"],
            help="Name or ID of the ManagedIdentity Resource.",
            required=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.ManagedIdentity"
                         "/userAssignedIdentities/{}",
            ),
        )
        args_schema.type._registered = False
        args_schema.user_assigned_identities._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.type = "UserAssigned"
        args.user_assigned_identities = {args.identity.to_serialized_data(): {}}

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result
