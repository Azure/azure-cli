# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz.utils import assign_aaz_list_arg
from azure.cli.command_modules.network.aaz.latest.network.application_gateway.settings._create import Create as _SettingsCreate


class SettingsCreate(_SettingsCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.root_certs = AAZListArg(
            options=["--root-certs"],
            help="Space-separated list of trusted root certificates (Names and IDs) to associate with the HTTP settings. "
                 "`--host-name` or `--backend-pool-host-name` is required when this field is set.",
        )
        args_schema.root_certs.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/trustedRootCertificates/{}",
            ),
        )
        args_schema.probe._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/probes/{}",
        )
        args_schema.port._required = True
        args_schema.trusted_root_certificates._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.trusted_root_certificates = assign_aaz_list_arg(
            args.trusted_root_certificates,
            args.root_certs,
            element_transformer=lambda _, root_cert_id: {"id": root_cert_id}
        )

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result
