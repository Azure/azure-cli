# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-few-public-methods, too-many-instance-attributes, protected-access, not-callable

from azure.cli.core._profile import Profile

from ._arg_action import AAZArgActionOperations, AAZGenericUpdateAction
from ._base import AAZUndefined
from ._field_type import AAZObjectType
from ._field_value import AAZObject


class AAZCommandCtx:

    def __init__(self, cli_ctx, schema, command_args, no_wait_arg=None):
        self._cli_ctx = cli_ctx
        self._profile = Profile(cli_ctx=cli_ctx)
        self._subscription_id = None
        self.args = schema()
        assert self.args._is_patch  # make sure self.ctx.args is patch
        for dest, cmd_arg in command_args.items():
            if hasattr(schema, dest):
                if isinstance(cmd_arg, AAZArgActionOperations):
                    cmd_arg.apply(self.args, dest)
                elif cmd_arg != AAZUndefined:
                    self.args[dest] = cmd_arg
        self._clients = {}
        self._vars_schema = AAZObjectType()
        self.vars = AAZObject(schema=self._vars_schema, data={})
        self.generic_update_args = command_args.get(AAZGenericUpdateAction.DEST, None)
        # support no wait
        self.lro_no_wait = command_args.get(no_wait_arg, False) if no_wait_arg else False
        # support paging
        self.next_link = AAZUndefined

    def format_args(self):
        # TODO: apply format for argument values
        pass

    def get_login_credential(self):
        credential, _, _ = self._profile.get_login_credentials(
            subscription_id=self.subscription_id,
            aux_subscriptions=self.aux_subscriptions,
            aux_tenants=self.aux_tenants
        )
        return credential

    def get_http_client(self, client_type):
        from ._client import registered_clients

        if client_type not in self._clients:
            # if not client instance exist, then create a client instance
            from azure.cli.core.commands.client_factory import _prepare_client_kwargs_track2
            assert client_type
            client_cls = registered_clients[client_type]
            credential = self.get_login_credential()
            client_kwargs = _prepare_client_kwargs_track2(self._cli_ctx)
            client_kwargs['user_agent'] += " (AAZ)"  # Add AAZ label in user agent
            self._clients[client_type] = client_cls(self._cli_ctx, credential, **client_kwargs)

        return self._clients[client_type]

    def set_var(self, name, data, schema_builder=None):
        if not hasattr(self._vars_schema, name):
            assert schema_builder is not None
            self._vars_schema[name] = schema_builder()
        self.vars[name] = data

    @staticmethod
    def get_error_format(name):
        if name is None:
            return None
        from ._error_format import registered_error_formats
        return registered_error_formats[name]

    @property
    def subscription_id(self):
        from azure.cli.core.commands.client_factory import get_subscription_id
        if self._subscription_id is None:
            self._subscription_id = get_subscription_id(cli_ctx=self._cli_ctx)
        return self._subscription_id

    @property
    def aux_subscriptions(self):
        # TODO: fetch aux_subscription base on args
        return None

    @property
    def aux_tenants(self):
        # TODO: fetch aux_subscription base on args
        return None
