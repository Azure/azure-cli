# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.core.aaz.utils import assign_aaz_list_arg
from azure.cli.command_modules.network.aaz.latest.network.application_gateway.ssl_profile._add import Add as _SSLProfileAdd


class SSLProfileAdd(_SSLProfileAdd):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZBoolArg, AAZListArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.client_auth_config = AAZBoolArg(
            options=["--client-auth-configuration", "--client-auth-config"],
            help="Client authentication configuration of the application gateway resource.",
        )
        args_schema.trusted_client_certs = AAZListArg(
            options=["--trusted-client-certificates", "--trusted-client-cert"],
            help="Array of references to application gateway trusted client certificates.",
        )
        args_schema.trusted_client_certs.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/trustedClientCertificates/{}",
            ),
        )
        args_schema.auth_configuration._registered = False
        args_schema.client_certificates._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.client_auth_config):
            args.auth_configuration.verify_client_cert_issuer_dn = args.client_auth_config
        args.client_certificates = assign_aaz_list_arg(
            args.client_certificates,
            args.trusted_client_certs,
            element_transformer=lambda _, cert_id: {"id": cert_id}
        )

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result
