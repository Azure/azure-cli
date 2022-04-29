# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-few-public-methods, too-many-instance-attributes, protected-access, not-callable
import importlib
import os
from functools import partial

from azure.cli.core._profile import Profile
from azure.cli.core.azclierror import CLIInternalError
from knack.commands import CLICommand, PREVIEW_EXPERIMENTAL_CONFLICT_ERROR
from knack.deprecation import Deprecated
from knack.experimental import ExperimentalItem
from knack.preview import PreviewItem

from ._arg import AAZArgumentsSchema, AAZBoolArg
from ._arg_action import AAZArgActionOperations, AAZGenericUpdateAction
from ._base import AAZUndefined, AAZBaseValue
from ._field_type import AAZObjectType
from ._field_value import AAZObject
from ._poller import AAZLROPoller
from ._paging import AAZPaged
from ._utils import _get_profile_pkg
from .exceptions import AAZUnknownFieldError

_DOC_EXAMPLE_FLAG = ':example:'


class AAZCommandGroup:
    """Atomic Layer Command Group"""
    AZ_NAME = None
    AZ_HELP = None

    AZ_PREVIEW_INFO = None
    AZ_EXPERIMENTAL_INFO = None
    AZ_DEPRECATE_INFO = None

    def __init__(self, cli_ctx):
        self.cli_ctx = cli_ctx

        self.group_kwargs = {
            # 'deprecate_info'  # deprecate_info should be in group_kwargs
        }

        if self.AZ_PREVIEW_INFO:
            self.group_kwargs['preview_info'] = self.AZ_PREVIEW_INFO(cli_ctx=self.cli_ctx)
        if self.AZ_EXPERIMENTAL_INFO:
            self.group_kwargs['experimental_info'] = self.AZ_EXPERIMENTAL_INFO(cli_ctx=self.cli_ctx)
        if self.AZ_DEPRECATE_INFO:
            self.group_kwargs['deprecate_info'] = self.AZ_DEPRECATE_INFO(cli_ctx=self.cli_ctx)

        self.help = self.AZ_HELP  # TODO: change knack to load help directly


class AAZCommandCtx:

    def __init__(self, cli_ctx, schema, command_args):
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

        # self.next_link = AAZUndefined  # support paging

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


class AAZCommand(CLICommand):
    """Atomic Layer Command"""
    AZ_NAME = None
    AZ_HELP = None
    AZ_SUPPORT_NO_WAIT = False
    AZ_SUPPORT_GENERIC_UPDATE = False

    AZ_CONFIRMATION = None
    AZ_PREVIEW_INFO = None
    AZ_EXPERIMENTAL_INFO = None
    AZ_DEPRECATE_INFO = None

    @classmethod
    def get_arguments_schema(cls):
        if not hasattr(cls, "_arguments_schema"):
            cls._args_schema = cls._build_arguments_schema()
        return cls._args_schema

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        schema = AAZArgumentsSchema(*args, **kwargs)
        if cls.AZ_SUPPORT_NO_WAIT:
            schema.no_wait = AAZBoolArg(
                options=['--no-wait'],
                help='Do not wait for the long-running operation to finish.'
            )
        # TODO: Implement Generic Update
        # if cls.AZ_SUPPORT_GENERIC_UPDATE:
        #     schema.generic_update_add = AAZGenericUpdateAddArg()
        #     schema.generic_update_set = AAZGenericUpdateSetArg()
        #     schema.generic_update_remove = AAZGenericUpdateRemoveArg()
        #     schema.generic_update_force_string = AAZGenericUpdateForceString()
        return schema

    def __init__(self, loader):
        self.loader = loader
        super().__init__(
            cli_ctx=loader.cli_ctx,
            name=self.AZ_NAME,
            confirmation=self.AZ_CONFIRMATION,
            arguments_loader=self._cli_arguments_loader,
            handler=True,
            # knack use cmd.handler to check whether it is group or command,
            # however this property will not be used in AAZCommand. So use True value for it.
            # https://github.com/microsoft/knack/blob/e496c9590792572e680cb3ec959db175d9ba85dd/knack/parser.py#L227-L233
        )
        self.command_kwargs = {}

        if self.AZ_PREVIEW_INFO:
            self.preview_info = self.AZ_PREVIEW_INFO(cli_ctx=self.cli_ctx)
        if self.AZ_EXPERIMENTAL_INFO:
            self.experimental_info = self.AZ_EXPERIMENTAL_INFO(cli_ctx=self.cli_ctx)
        if self.AZ_DEPRECATE_INFO:
            self.deprecate_info = self.AZ_DEPRECATE_INFO(cli_ctx=self.cli_ctx)

        self.help = self.AZ_HELP

        self.ctx = None

        # help property will be assigned as help_file for command parser:
        # https://github.com/Azure/azure-cli/blob/d69eedd89bd097306b8579476ef8026b9f2ad63d/src/azure-cli-core/azure/cli/core/parser.py#L104
        # help_file will be loaded as file_data in knack:
        # https://github.com/microsoft/knack/blob/e496c9590792572e680cb3ec959db175d9ba85dd/knack/help.py#L206-L208

        # additional properties
        self.supports_no_wait = self.AZ_SUPPORT_NO_WAIT
        self.no_wait_param = None
        self.exception_handler = None

    def __call__(self, *args, **kwargs):
        return self._handler(*args, **kwargs)

    def _handler(self, command_args):
        self.ctx = AAZCommandCtx(cli_ctx=self.cli_ctx, schema=self.get_arguments_schema(), command_args=command_args)
        self.ctx.format_args()

    def _cli_arguments_loader(self):
        """load arguments"""
        schema = self.get_arguments_schema()
        args = {}
        for name, field in schema._fields.items():
            args[name] = field.to_cmd_arg(name)
        return list(args.items())

    def update_argument(self, param_name, argtype):
        # not support to overwrite arguments defined in schema
        schema = self.get_arguments_schema()
        if not hasattr(schema, param_name):
            super().update_argument(param_name, argtype)

    @staticmethod
    def deserialize_output(value, client_flatten=True):
        if not isinstance(value, AAZBaseValue):
            return value

        def processor(schema, result):
            if result == AAZUndefined:
                return result
            if client_flatten and isinstance(schema, AAZObjectType):
                disc_schema = schema.get_discriminator(result)
                new_result = {}
                for k, v in result.items():
                    try:
                        k_schema = schema[k]
                    except AAZUnknownFieldError as err:
                        if not disc_schema:
                            raise err
                        k_schema = disc_schema[k]
                    if k_schema._flags.get('client_flatten', False):
                        assert isinstance(k_schema, AAZObjectType) and isinstance(v, dict)
                        for sub_k, sub_v in v.items():
                            if sub_k in new_result:
                                raise KeyError(f"Conflict key when apply client flatten: {sub_k} in {result}")
                            new_result[sub_k] = sub_v
                    else:
                        if k in new_result:
                            raise KeyError(f"Conflict key when apply client flatten: {k} in {result}")
                        new_result[k] = v
                result = new_result
            return result

        return value.to_serialized_data(processor=processor)

    @staticmethod
    def build_lro_poller(executor, extract_result):
        # TODO:
        return AAZLROPoller(polling_generator=executor(), result_callback=extract_result)

    def build_paging(self, executor, extract_result):
        def executor_wrapper(next_link):
            self.ctx.next_link = next_link
            executor()
        return AAZPaged(executor=executor_wrapper, extract_result=extract_result)


def register_command_group(
        name, is_preview=False, is_experimental=False, hide=False, redirect=None, expiration=None):
    """register AAZCommandGroup"""
    if is_preview and is_experimental:
        raise CLIInternalError(
            PREVIEW_EXPERIMENTAL_CONFLICT_ERROR.format(name)
        )
    deprecated_info = {}
    if hide:
        deprecated_info['hide'] = hide
    if redirect:
        deprecated_info['redirect'] = f'az {redirect}'
    if expiration:
        deprecated_info['expiration'] = expiration

    def decorator(cls):
        assert issubclass(cls, AAZCommandGroup)
        cls.AZ_NAME = name
        short_summary, long_summary, _ = parse_cls_doc(cls)
        cls.AZ_HELP = {
            "type": "group",
            "short-summary": short_summary,
            "long-summary": long_summary
        }

        # the only way to load command group help in knack is by _load_from_file
        # TODO: change knack to load AZ_HELP directly
        import yaml
        from knack.help_files import helps
        helps[name] = yaml.safe_dump(cls.AZ_HELP)

        if is_preview:
            cls.AZ_PREVIEW_INFO = partial(PreviewItem, target=f'az {name}', object_type='command group')
        if is_experimental:
            cls.AZ_EXPERIMENTAL_INFO = partial(ExperimentalItem, target=f'az {name}', object_type='command group')
        if deprecated_info:
            cls.AZ_DEPRECATE_INFO = partial(Deprecated, target=f'az {name}', object_type='command group',
                                            **deprecated_info)
        return cls

    return decorator


def register_command(
        name, is_preview=False, is_experimental=False, confirmation=None, hide=False, redirect=None, expiration=None):
    """register AAZCommand"""
    if is_preview and is_experimental:
        raise CLIInternalError(
            PREVIEW_EXPERIMENTAL_CONFLICT_ERROR.format(name)
        )
    deprecated_info = {}
    if hide:
        deprecated_info['hide'] = hide
    if redirect:
        deprecated_info['redirect'] = f'az {redirect}'
    if expiration:
        deprecated_info['expiration'] = expiration

    def decorator(cls):
        assert issubclass(cls, AAZCommand)
        cls.AZ_NAME = name
        short_summary, long_summary, examples = parse_cls_doc(cls)
        cls.AZ_HELP = {
            "type": "command",
            "short-summary": short_summary,
            "long-summary": long_summary,
            "examples": examples
        }

        if confirmation:
            cls.AZ_CONFIRMATION = confirmation
        if is_preview:
            cls.AZ_PREVIEW_INFO = partial(PreviewItem, target=f'az {name}', object_type='command')
        if is_experimental:
            cls.AZ_EXPERIMENTAL_INFO = partial(ExperimentalItem, target=f'az {name}', object_type='command')
        if deprecated_info:
            cls.AZ_DEPRECATE_INFO = partial(Deprecated, target=f'az {name}', object_type='command', **deprecated_info)
        return cls

    return decorator


def load_aaz_command_table(loader, aaz_pkg_name, args):
    profile_pkg = _get_profile_pkg(aaz_pkg_name, loader.cli_ctx.cloud)
    command_table = {}
    command_group_table = {}
    arg_str = ' '.join(args)

    if profile_pkg is not None:
        _load_aaz_pkg(loader, profile_pkg, command_table, command_group_table, arg_str)

    for group_name, command_group in command_group_table.items():
        loader.command_group_table[group_name] = command_group
    for command_name, command in command_table.items():
        loader.command_table[command_name] = command
    return command_table, command_group_table


def _load_aaz_pkg(loader, pkg, parent_command_table, command_group_table, arg_str):
    cut = False  # if cut, its sub commands and sub pkgs will not be added
    command_table = {}  # the command available for this pkg and its sub pkgs
    for value in pkg.__dict__.values():
        if cut and command_table:
            # when cut and command_table is not empty, stop loading more commands.
            # the command_table should not be empty.
            # Because if it's empty, the command group will be ignored in help if parent command group.
            break
        if isinstance(value, type):
            if issubclass(value, AAZCommandGroup):
                if not arg_str.startswith(f'{value.AZ_NAME} '):
                    # when args not contain command group prefix, then cut more loading.
                    cut = True
                # add command group into command group table
                command_group_table[value.AZ_NAME] = value(
                    cli_ctx=loader.cli_ctx)  # add command group even it's cut
            elif issubclass(value, AAZCommand):
                if value.AZ_NAME:
                    command_table[value.AZ_NAME] = value(loader=loader)

    # continue load sub pkgs
    pkg_path = os.path.dirname(pkg.__file__)
    for sub_path in os.listdir(pkg_path):
        if cut and command_table:
            # when cut and command_table is not empty, stop loading more sub pkgs.
            break
        if sub_path.startswith('_') or not os.path.isdir(os.path.join(pkg_path, sub_path)):
            continue
        try:
            sub_pkg = importlib.import_module(f'.{sub_path}', pkg.__name__)
        except ModuleNotFoundError:
            continue
        _load_aaz_pkg(loader, sub_pkg, command_table, command_group_table, arg_str)

    parent_command_table.update(command_table)  # update the parent pkg's command table.


def parse_cls_doc(cls):
    doc = cls.__doc__
    short_summary = None
    long_summary = None
    lines = []
    if doc:
        for line in doc.splitlines():
            line = line.strip()
            if line:
                lines.append(line)
    examples = []
    if lines:
        short_summary = lines[0]
        assert not short_summary.startswith(':')
        idx = 1
        while idx < len(lines):
            line = lines[idx]
            if line.startswith(_DOC_EXAMPLE_FLAG):
                break
            idx += 1
        long_summary = '\n'.join(lines[1:idx]) or None
        while idx < len(lines):
            line = lines[idx]
            if line.startswith(_DOC_EXAMPLE_FLAG):
                example = {
                    "name": line[len(_DOC_EXAMPLE_FLAG):].strip()
                }
                e_idx = idx + 1
                while e_idx < len(lines) and not lines[e_idx].startswith(_DOC_EXAMPLE_FLAG):
                    e_idx += 1
                example["text"] = '\n'.join(lines[idx + 1: e_idx]) or None
                if example["text"]:
                    examples.append(example)
                idx = e_idx - 1
            idx += 1
    return short_summary, long_summary, examples
