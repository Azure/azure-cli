# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-few-public-methods, too-many-instance-attributes, protected-access, not-callable
import importlib
import os
import copy
from functools import partial

from knack.commands import CLICommand, PREVIEW_EXPERIMENTAL_CONFLICT_ERROR
from knack.deprecation import Deprecated
from knack.experimental import ExperimentalItem
from knack.log import get_logger
from knack.preview import PreviewItem

from azure.cli.core.azclierror import CLIInternalError
from ._arg import AAZArgumentsSchema, AAZBoolArg, \
    AAZGenericUpdateAddArg, AAZGenericUpdateSetArg, AAZGenericUpdateRemoveArg, AAZGenericUpdateForceStringArg, \
    AAZPaginationTokenArg, AAZPaginationLimitArg
from ._base import AAZUndefined, AAZBaseValue
from ._field_type import AAZObjectType
from ._paging import AAZPaged
from ._poller import AAZLROPoller
from ._command_ctx import AAZCommandCtx
from .exceptions import AAZUnknownFieldError, AAZUnregisteredArg
from .utils import get_aaz_profile_module_name


logger = get_logger(__name__)


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


class AAZCommand(CLICommand):
    """Atomic Layer Command"""
    AZ_NAME = None
    AZ_HELP = None
    AZ_SUPPORT_NO_WAIT = False
    AZ_SUPPORT_GENERIC_UPDATE = False
    AZ_SUPPORT_PAGINATION = False

    AZ_CONFIRMATION = None
    AZ_PREVIEW_INFO = None
    AZ_EXPERIMENTAL_INFO = None
    AZ_DEPRECATE_INFO = None

    @classmethod
    def get_arguments_schema(cls):
        """ Make sure _args_schema is build once.
        """
        if not hasattr(cls, "_arguments_schema") or cls._arguments_schema is None:
            cls._arguments_schema = cls._build_arguments_schema()
        return cls._arguments_schema

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        """ Build the schema of command's argument, this function should be inherited by sub classes.
        """
        schema = AAZArgumentsSchema(*args, **kwargs)
        if cls.AZ_SUPPORT_NO_WAIT:
            schema.no_wait = AAZBoolArg(
                options=['--no-wait'],
                help='Do not wait for the long-running operation to finish.'
            )
        if cls.AZ_SUPPORT_GENERIC_UPDATE:
            schema.generic_update_add = AAZGenericUpdateAddArg()
            schema.generic_update_set = AAZGenericUpdateSetArg()
            schema.generic_update_remove = AAZGenericUpdateRemoveArg()
            schema.generic_update_force_string = AAZGenericUpdateForceStringArg()
        if cls.AZ_SUPPORT_PAGINATION:
            schema.pagination_token = AAZPaginationTokenArg()
            schema.pagination_limit = AAZPaginationLimitArg()
        return schema

    def __init__(self, loader=None, cli_ctx=None, callbacks=None, **kwargs):
        """

        :param loader: it is required for command registered in the command table
        :param cli_ctx: if a command instance is not registered in the command table, only cli_ctx is required.
        :param callbacks: a dict of customized callback functions registered by @register_callback.
            common used callbacks:
                'pre_operations': This callback runs before all the operations
                    pre_operations(ctx) -> void
                'post_operations': This callback runs after all the operations
                    post_operations(ctx) -> void
                'pre_instance_update': This callback runs before all the instance update operations
                    pre_instance_update(instance, ctx) -> void
                'post_instance_update': This callback runs after all the instance update operations and before PUT
                    post_instance_update(instance, ctx) -> void
        """
        assert loader or cli_ctx, "loader or cli_ctx is required"
        self.loader = loader
        super().__init__(
            cli_ctx=cli_ctx or loader.cli_ctx,
            name=self.AZ_NAME,
            confirmation=self.AZ_CONFIRMATION,
            arguments_loader=self._cli_arguments_loader,
            handler=True,
            # knack use cmd.handler to check whether it is group or command,
            # however this property will not be used in AAZCommand. So use True value for it.
            # https://github.com/microsoft/knack/blob/e496c9590792572e680cb3ec959db175d9ba85dd/knack/parser.py#L227-L233
            **kwargs
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
        self.callbacks = callbacks or {}

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
        # command_args will be parsed by AAZCommandCtx
        self.ctx = AAZCommandCtx(
            cli_ctx=self.cli_ctx,
            schema=self.get_arguments_schema(),
            command_args=command_args,
            no_wait_arg='no_wait' if self.supports_no_wait else None,
        )
        self.ctx.format_args()

    def _cli_arguments_loader(self):
        """load arguments"""
        schema = self.get_arguments_schema()
        args = {}
        for name, field in schema._fields.items():
            # generate command arguments from argument schema.
            try:
                args[name] = field.to_cmd_arg(name, cli_ctx=self.cli_ctx)
            except AAZUnregisteredArg:
                continue
        return list(args.items())

    def update_argument(self, param_name, argtype):
        """ This function is called by core to add global arguments
        """
        schema = self.get_arguments_schema()
        if hasattr(schema, param_name):
            # not support to overwrite arguments defined in schema, use arg.type as overrides
            argtype = copy.deepcopy(self.arguments[param_name].type)
        super().update_argument(param_name, argtype)

    @staticmethod
    def deserialize_output(value, client_flatten=True, secret_hidden=True):
        """ Deserialize output of a command.
        """
        if not isinstance(value, AAZBaseValue):
            return value

        def processor(schema, result):
            """A processor used in AAZBaseValue to serialized data"""
            if result == AAZUndefined or result is None:
                return result

            if isinstance(schema, AAZObjectType):
                # handle client flatten in result
                disc_schema = schema.get_discriminator(result)
                new_result = {}
                for k, v in result.items():
                    # get schema of k
                    try:
                        k_schema = schema[k]
                    except AAZUnknownFieldError as err:
                        if not disc_schema:
                            raise err
                        # get k_schema from discriminator definition
                        k_schema = disc_schema[k]

                    if secret_hidden and k_schema._flags.get('secret', False):
                        # hidden secret properties in output
                        continue

                    if client_flatten and k_schema._flags.get('client_flatten', False):
                        # flatten k when there are client_flatten flag in its schema
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

    def build_lro_poller(self, executor, extract_result):
        """ Build AAZLROPoller instance to support long running operation
        """
        polling_generator = executor()
        if self.ctx.lro_no_wait:
            # run until yield the first polling
            _ = next(polling_generator)
            return None
        return AAZLROPoller(polling_generator=polling_generator, result_callback=extract_result)

    def build_paging(self, executor, extract_result):
        """ Build AAZPaged instance to support paging
        """
        def executor_wrapper(next_link):
            self.ctx.next_link = next_link
            executor()

        if self.AZ_SUPPORT_PAGINATION:
            args = self.ctx.args
            token = args.pagination_token.to_serialized_data()
            limit = args.pagination_limit.to_serialized_data()

            return AAZPaged(
                executor=executor_wrapper, extract_result=extract_result, cli_ctx=self.cli_ctx,
                token=token, limit=limit
            )

        return AAZPaged(executor=executor_wrapper, extract_result=extract_result, cli_ctx=self.cli_ctx)


class AAZWaitCommand(AAZCommand):
    """Support wait command"""

    def __init__(self, loader):
        from azure.cli.core.commands.command_operation import WaitCommandOperation
        super().__init__(loader)

        # add wait args in commands
        for param_name, argtype in WaitCommandOperation.wait_args().items():
            self.arguments[param_name] = argtype

    def __call__(self, *args, **kwargs):
        from azure.cli.core.commands.command_operation import WaitCommandOperation
        return WaitCommandOperation.wait(
            *args, **kwargs,
            cli_ctx=self.cli_ctx,
            getter=lambda **command_args: self._handler(command_args)
        )


def register_callback(func):
    def wrapper(self, *args, **kwargs):
        callback = self.callbacks.get(func.__name__, None)
        if callback is None:
            return func(self, *args, **kwargs)

        kwargs.setdefault("ctx", self.ctx)
        return callback(*args, **kwargs)
    return wrapper


def register_command_group(
        name, is_preview=False, is_experimental=False, hide=False, redirect=None, expiration=None):
    """This decorator is used to register an AAZCommandGroup as a cli command group.
    A registered AAZCommandGroup will be added into module's command group table.
    """
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
        short_summary, long_summary, _ = _parse_cls_doc(cls)
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
            cls.AZ_PREVIEW_INFO = staticmethod(partial(PreviewItem,
                                                       target=f'az {name}', object_type='command group'))
        if is_experimental:
            cls.AZ_EXPERIMENTAL_INFO = staticmethod(partial(ExperimentalItem,
                                                            target=f'az {name}', object_type='command group'))
        if deprecated_info:
            cls.AZ_DEPRECATE_INFO = staticmethod(partial(Deprecated,
                                                         target=f'az {name}', object_type='command group',
                                                         **deprecated_info))
        return cls

    return decorator


def register_command(
        name, is_preview=False, is_experimental=False, confirmation=None, hide=False, redirect=None, expiration=None):
    """This decorator is used to register an AAZCommand as a cli command.
    A registered AAZCommand will be added into module's command table.
    """
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
        short_summary, long_summary, examples = _parse_cls_doc(cls)
        cls.AZ_HELP = {
            "type": "command",
            "short-summary": short_summary,
            "long-summary": long_summary,
            "examples": examples
        }

        if confirmation:
            cls.AZ_CONFIRMATION = confirmation
        if is_preview:
            cls.AZ_PREVIEW_INFO = staticmethod(partial(PreviewItem, target=f'az {name}', object_type='command'))
        if is_experimental:
            cls.AZ_EXPERIMENTAL_INFO = staticmethod(partial(ExperimentalItem,
                                                            target=f'az {name}', object_type='command'))
        if deprecated_info:
            cls.AZ_DEPRECATE_INFO = staticmethod(partial(Deprecated, target=f'az {name}',
                                                         object_type='command', **deprecated_info))
        return cls

    return decorator


AAZ_PACKAGE_FULL_LOAD_ENV_NAME = 'AZURE_AAZ_FULL_LOAD'


def load_aaz_command_table(loader, aaz_pkg_name, args):
    """ This function is used in AzCommandsLoader.load_command_table.
    It will load commands in module's aaz package.
    """
    profile_pkg = _get_profile_pkg(aaz_pkg_name, loader.cli_ctx.cloud)

    command_table = {}
    command_group_table = {}
    if args is None:
        arg_str = ''
        fully_load = True
    else:
        arg_str = ' '.join(args).lower()  # Sometimes args may contain capital letters.
        fully_load = os.environ.get(AAZ_PACKAGE_FULL_LOAD_ENV_NAME, 'False').lower() == 'true'  # disable cut logic
    if profile_pkg is not None:
        _load_aaz_pkg(loader, profile_pkg, command_table, command_group_table, arg_str, fully_load)

    for group_name, command_group in command_group_table.items():
        loader.command_group_table[group_name] = command_group
    for command_name, command in command_table.items():
        loader.command_table[command_name] = command
    return command_table, command_group_table


def _get_profile_pkg(aaz_module_name, cloud):
    """ load the profile package of aaz module according to the cloud profile.
    """
    profile_module_name = get_aaz_profile_module_name(cloud.profile)
    try:
        return importlib.import_module(f'{aaz_module_name}.{profile_module_name}')
    except ModuleNotFoundError:
        return None


def _link_helper(pkg, name, mod, helper_cls_name="_Helper"):
    helper_mod = importlib.import_module(mod, pkg)
    helper = getattr(helper_mod, helper_cls_name)
    return getattr(helper, name)


def link_helper(pkg, *links):
    def _wrapper(cls):
        for link in links:
            if isinstance(link[1], str):
                func = _link_helper(pkg, *link)
            else:
                func = getattr(link[1], link[0])
            setattr(cls, link[0], partial(func, cls))
        return cls
    return _wrapper


def _load_aaz_pkg(loader, pkg, parent_command_table, command_group_table, arg_str, fully_load):
    """ Load aaz commands and aaz command groups under a package folder.
    """
    cut = False  # if cut, its sub commands and sub pkgs will not be added
    command_table = {}  # the command available for this pkg and its sub pkgs
    for value in pkg.__dict__.values():
        if not fully_load and cut and command_table:
            # when cut and command_table is not empty, stop loading more commands.
            # the command_table should not be empty.
            # Because if it's empty, the command group will be ignored in help if parent command group.
            break
        if isinstance(value, type):
            if issubclass(value, AAZCommandGroup):
                if value.AZ_NAME:
                    # AAZCommandGroup already be registered by register_command_command
                    if not arg_str.startswith(f'{value.AZ_NAME.lower()} '):
                        # when args not contain command group prefix, then cut more loading.
                        cut = True
                    # add command group into command group table
                    command_group_table[value.AZ_NAME] = value(
                        cli_ctx=loader.cli_ctx)  # add command group even it's cut
            elif issubclass(value, AAZCommand):
                if value.AZ_NAME:
                    # AAZCommand already be registered by register_command
                    command_table[value.AZ_NAME] = value(loader=loader)

    # continue load sub pkgs
    pkg_path = os.path.dirname(pkg.__file__)
    for sub_path in os.listdir(pkg_path):
        if not fully_load and cut and command_table:
            # when cut and command_table is not empty, stop loading more sub pkgs.
            break
        if sub_path.startswith('_') or not os.path.isdir(os.path.join(pkg_path, sub_path)):
            continue
        try:
            sub_pkg = importlib.import_module(f'.{sub_path}', pkg.__name__)
        except ModuleNotFoundError:
            logger.debug('Failed to load package folder in aaz: %s.', os.path.join(pkg_path, sub_path))
            continue

        if not sub_pkg.__file__:
            logger.debug('Ignore invalid package folder in aaz: %s.', os.path.join(pkg_path, sub_path))
            continue

        # recursively load sub package
        _load_aaz_pkg(loader, sub_pkg, command_table, command_group_table, arg_str, fully_load)

    parent_command_table.update(command_table)  # update the parent pkg's command table.


_DOC_EXAMPLE_FLAG = ':example:'


def _parse_cls_doc(cls):
    """ Parse the help from the doc string of aaz classes. Examples are only defined in aaz command classes.
    """
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
