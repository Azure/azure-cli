# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, protected-access
from azure.cli.core.aaz import has_value, register_command
from azure.cli.core.azclierror import ArgumentUsageError
from azure.cli.core.util import parse_proxy_resource_id

from ..aaz.latest.monitor.private_link_scope import Create as _PrivateLinkScopeCreate
from ..aaz.latest.monitor.private_link_scope.private_endpoint_connection import Delete as _ConnectionDelete, \
    Show as _ConnectionShow, Update


def validate_private_endpoint_connection_id(args):
    if has_value(args.id):
        data = parse_proxy_resource_id(args.id.to_serialized_data())
        args.name = data["child_name_1"]
        args.resource_group = data["resource_group"]
        args.scope_name = data["name"]

    if not all([has_value(args.name), has_value(args.resource_group), has_value(args.scope_name)]):
        err_msg = "Incorrect usage. Please provide [--id ID] or [--n NAME -g NAME --scope-name NAME]."
        raise ArgumentUsageError(error_msg=err_msg)


class PrivateLinkScopeCreate(_PrivateLinkScopeCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.location._required = False
        args_schema.location._registered = False

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.location = "global"


class ConnectionDelete(_ConnectionDelete):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg
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


class ConnectionShow(_ConnectionShow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg
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


@register_command("monitor private-link-scope private-endpoint-connection approve")
class ConnectionApprove(Update):
    """ Approve a private endpoint connection of a private link scope resource.

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
        args = self.ctx.args
        args.status = "Approved"
        validate_private_endpoint_connection_id(args)


@register_command("monitor private-link-scope private-endpoint-connection reject")
class ConnectionReject(Update):
    """ Reject a private endpoint connection of a private link scope resource.

    :example: Reject a private endpoint connection of a private link scope resource.
        az monitor private-link-scope private-endpoint-connection reject --name MyPrivateEndpointConnection --resource-group MyResourceGroup --scope-name MyScope
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
        args = self.ctx.args
        args.status = "Rejected"
        validate_private_endpoint_connection_id(args)
