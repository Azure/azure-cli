# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.application_gateway.root_cert._update import Update as _RootCertUpdate


class RootCertUpdate(_RootCertUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZFileArg, AAZFileArgBase64EncodeFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.cert_file = AAZFileArg(
            options=["--cert-file"],
            help="Path to the certificate file.",
            fmt=AAZFileArgBase64EncodeFormat(),
            nullable=True,
        )
        args_schema.data._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.cert_file):
            args.data = args.cert_file
