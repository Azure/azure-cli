# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.vnet_gateway.root_cert._create import Create as _VnetGatewayRootCertCreate


class VnetGatewayRootCertCreate(_VnetGatewayRootCertCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZFileArg, AAZFileArgBase64EncodeFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.public_cert_data = AAZFileArg(options=['--public-cert-data'],
                                                  help="Base64 contents of the root certificate file or file path.",
                                                  required=True,
                                                  fmt=AAZFileArgBase64EncodeFormat())
        args_schema.root_cert_data._required = False
        args_schema.root_cert_data._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.public_cert_data):
            import os
            path = os.path.expanduser(args.public_cert_data.to_serialized_data())
        else:
            path = None
        args.root_cert_data = path
