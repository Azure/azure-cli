# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-few-public-methods, too-many-instance-attributes, protected-access, not-callable

from azure.cli.core._profile import Profile
from azure.cli.core.azclierror import InvalidArgumentValueError
import os
import time
from urllib.parse import urlparse, urlunparse
from azure.cli.core._environment import get_config_dir
from knack.config import _ConfigFile
from knack.util import ensure_dir
import configparser

from ._arg_action import AAZArgActionOperations, AAZGenericUpdateAction
from ._base import AAZUndefined
from ._field_type import AAZObjectType
from ._field_value import AAZObject
from ._selector import AAZSelectors
from .exceptions import AAZInvalidArgValueError


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
            elif dest == "subscription":
                # support to specify the command's subscription when call AAZCommand directly in code
                if isinstance(cmd_arg, str):
                    self._subscription_id = cmd_arg

        self._clients = {}
        self._vars_schema = AAZObjectType()
        self.vars = AAZObject(schema=self._vars_schema, data={})
        self.selectors = AAZSelectors()
        self.generic_update_args = command_args.get(AAZGenericUpdateAction.DEST, None)
        # support no wait
        self.lro_no_wait = command_args.get(no_wait_arg, False) if no_wait_arg else False
        # support paging
        self.next_link = AAZUndefined

        self._aux_subscriptions = set()
        self._aux_tenants = set()
        # command config file
        self._command_config = None

    def format_args(self):
        try:
            self.args._schema._fmt(ctx=self, value=self.args)
        except AAZInvalidArgValueError as err:
            raise InvalidArgumentValueError(str(err))

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
    def profile(self):
        return self._profile

    def update_aux_subscriptions(self, subscription_id):
        if subscription_id == self._subscription_id:
            return
        self._aux_subscriptions.add(subscription_id)

    def update_aux_tenants(self, tenant_id):
        self._aux_tenants.add(tenant_id)

    @property
    def aux_subscriptions(self):
        return list(self._aux_subscriptions) or None

    @property
    def aux_tenants(self):
        return list(self._aux_tenants) or None

    def _get_command_cache_directory(self):
        return os.path.join(
            get_config_dir(),
            'command_cache',
            self._cli_ctx.cloud.name,
            self.subscription_id,
        )

    def _load_command_cache_config(self):
        config_dir = self._get_command_cache_directory()
        ensure_dir(config_dir)
        config_path = os.path.join(config_dir, "command_cache.json")
        config = _ConfigFile(config_dir=config_dir, config_path=config_path)
        # clean up expired section
        now = time.time()
        clean_sections = []
        for section in config.sections():
            if config.has_option(section, "expires_at") and config.getfloat(section, "expires_at") < now:
                clean_sections.append(section)
        for section in clean_sections:
            config.remove_section(section)
        return config

    @property
    def command_config(self):
        if not self._command_config:
            self._command_config = self._load_command_cache_config()
        return self._command_config

    def get_continuation_token(self, http_operation):
        section = self.get_command_cache_section(
            self._cli_ctx.data['command'], http_operation.method, http_operation.url
        )
        try:
            continuation_token = self.command_config.get(section, "continuation_token")
        except (configparser.NoSectionError, configparser.NoOptionError):
            raise InvalidArgumentValueError(
                "Cannot find cached continuation token for the long-running operation: --lro-continue")
        return continuation_token

    def cache_continuation_token(self, polling):
        request = polling._initial_response.http_request
        section = self.get_command_cache_section(self._cli_ctx.data['command'], request.method, request.url)
        continuation_token = polling.get_continuation_token()
        expires_at = int(time.time()) + 24*60*60
        self.command_config.set_value(section, "continuation_token", continuation_token)
        self.command_config.set_value(section, "expires_at", str(expires_at))

    def get_command_cache_section(self, command_name, method, url):
        method = method.upper()
        parsed = urlparse(url)
        url = urlunparse([parsed.scheme, parsed.netloc, parsed.path, None, None, None])
        return f"{command_name};{method};{url}"


def get_subscription_locations(ctx: AAZCommandCtx):
    from azure.cli.core.commands.parameters import get_subscription_locations as _get_subscription_locations
    return _get_subscription_locations(ctx._cli_ctx)


def get_resource_group_location(ctx: AAZCommandCtx, rg_name: str):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    from azure.core.exceptions import ResourceNotFoundError

    resource_client = get_mgmt_service_client(ctx._cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    try:
        rg = resource_client.resource_groups.get(rg_name)
    except ResourceNotFoundError:
        return AAZUndefined
    return rg.location
