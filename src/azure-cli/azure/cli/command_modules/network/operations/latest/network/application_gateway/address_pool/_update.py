# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

import socket
from azure.cli.core.aaz.utils import assign_aaz_list_arg
from azure.cli.command_modules.network.aaz.latest.network.application_gateway.address_pool._update import Update as _AddressPoolUpdate


class AddressPoolUpdate(_AddressPoolUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.servers = AAZListArg(
            options=["--servers"],
            help="Space-separated list of IP addresses or DNS names corresponding to backend servers.",
            nullable=True,
        )
        args_schema.servers.Element = AAZStrArg(
            nullable=True,
        )
        args_schema.backend_addresses._registered = False
        return args_schema

    class NonRetryableCreateOrUpdate(_AddressPoolUpdate.ApplicationGatewaysCreateOrUpdate):
        CLIENT_TYPE = "NonRetryableClient"

    def _execute_operations(self):
        self.pre_operations()
        self.ApplicationGatewaysGet(ctx=self.ctx)()
        self.pre_instance_update(self.ctx.selectors.subresource.required())
        self.InstanceUpdateByJson(ctx=self.ctx)()
        self.InstanceUpdateByGeneric(ctx=self.ctx)()
        self.post_instance_update(self.ctx.selectors.subresource.required())
        yield self.NonRetryableCreateOrUpdate(ctx=self.ctx)()
        self.post_operations()

    def pre_operations(self):
        args = self.ctx.args

        def server_trans(_, server):
            try:
                socket.inet_aton(str(server))  # pylint:disable=no-member
                return {"ip_address": server}
            except OSError:  # pylint:disable=no-member
                return {"fqdn": server}

        args.backend_addresses = assign_aaz_list_arg(
            args.backend_addresses,
            args.servers,
            element_transformer=server_trans
        )
