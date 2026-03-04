# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.application_gateway.client_cert._add import Add as _ClientCertAdd


class ClientCertAdd(_ClientCertAdd):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZFileArg, AAZFileArgBase64EncodeFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.data = AAZFileArg(
            options=["--data"],
            help="Path to the certificate file.",
            required=True,
            fmt=AAZFileArgBase64EncodeFormat(),
        )
        args_schema.cert_data._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.data):
            args.cert_data = args.data

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result
