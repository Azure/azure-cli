# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.command_modules.network.aaz.latest.network.private_endpoint.dns_zone_group._add import Add as _PrivateEndpointPrivateDnsZoneAdd


class PrivateEndpointPrivateDnsZoneAdd(_PrivateEndpointPrivateDnsZoneAdd):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.private_dns_zone = AAZResourceIdArg(
            options=['--private-dns-zone'],
            help="Name or ID of the private dns zone.",
            required=True,
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/privateDnsZones/{}"
            )
        )
        args_schema.private_dns_zone_id._registered = False

        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.private_dns_zone_id = args.private_dns_zone

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result
