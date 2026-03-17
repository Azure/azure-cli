# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz.utils import assign_aaz_list_arg
from azure.cli.command_modules.network.aaz.latest.network.application_gateway.http_settings._create import Create as _HTTPSettingsCreate


class HTTPSettingsCreate(_HTTPSettingsCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZIntArg, AAZIntArgFormat, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.auth_certs = AAZListArg(
            options=["--auth-certs"],
            help="Space-separated list of authentication certificates (Names and IDs) to associate with the HTTP settings.",
        )
        args_schema.auth_certs.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/authenticationCertificates/{}",
            ),
        )
        args_schema.root_certs = AAZListArg(
            options=["--root-certs"],
            help="Space-separated list of trusted root certificates (Names and IDs) to associate with the HTTP settings. "
                 "`--host-name` or `--host-name-from-backend-pool` is required when this field is set.",
        )
        args_schema.root_certs.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                         "/applicationGateways/{gateway_name}/trustedRootCertificates/{}",
            ),
        )
        args_schema.connection_draining_timeout = AAZIntArg(
            options=["--connection-draining-timeout"],
            help="Time in seconds after a backend server is removed during which on open connection remains active. "
                 "Range from 0 (Disabled) to 3600.",
            default=0,
            fmt=AAZIntArgFormat(
                maximum=3600,
                minimum=0,
            ),
        )
        args_schema.probe._fmt = AAZResourceIdArgFormat(
            template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network"
                     "/applicationGateways/{gateway_name}/probes/{}",
        )
        args_schema.cookie_based_affinity._blank = "Enabled"
        args_schema.port._required = True
        args_schema.authentication_certificates._registered = False
        args_schema.trusted_root_certificates._registered = False
        args_schema.connection_draining._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.authentication_certificates = assign_aaz_list_arg(
            args.authentication_certificates,
            args.auth_certs,
            element_transformer=lambda _, auth_cert_id: {"id": auth_cert_id}
        )
        args.trusted_root_certificates = assign_aaz_list_arg(
            args.trusted_root_certificates,
            args.root_certs,
            element_transformer=lambda _, root_cert_id: {"id": root_cert_id}
        )
        timeout = args.connection_draining_timeout.to_serialized_data()
        args.connection_draining.enabled = bool(timeout)
        args.connection_draining.drain_timeout_in_sec = timeout or 1
