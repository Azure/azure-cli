# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.private_endpoint._update import Update as _PrivateEndpointUpdate


class PrivateEndpointUpdate(_PrivateEndpointUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.request_message = AAZStrArg(
            options=['--request-message'],
            help="A message passed to the owner of the remote resource with this connection request. Restricted to 140 chars.")

        args_schema.manual_private_link_service_connections._registered = False
        args_schema.private_link_service_connections._registered = False

        return args_schema

    def pre_instance_update(self, instance):
        args = self.ctx.args
        if has_value(args.request_message):
            if has_value(instance.properties.private_link_service_connections):
                instance.properties.private_link_service_connections[0].properties.request_message = args.request_message
            elif has_value(instance.properties.manual_private_link_service_connections):
                instance.properties.manual_private_link_service_connections[0].properties.request_message = args.request_message
