# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import abc

from knack.util import StatusTag, color_map

NEXT_BREAKING_CHANGE_RELEASE = '2.67.0'
DEFAULT_BREAKING_CHANGE_TAG = '[BrkChange]'


class UpcomingBreakingChangeTag(StatusTag):
    def __init__(self, cli_ctx, object_type='', target=None, target_version=None, tag_func=None, message_func=None):
        def _default_get_message(bc):
            msg = f"A breaking change may occur to this {bc.object_type} "
            if isinstance(target_version, TargetVersion):
                msg += str(target_version) + '.'
            elif isinstance(target_version, str):
                msg += 'in ' + target_version + '.'
            else:
                msg += 'in future release.'
                return msg

        if isinstance(message_func, str):
            message_func = lambda _: message_func

        self.target_version = target_version
        super().__init__(
            cli_ctx=cli_ctx,
            object_type=object_type,
            target=target,
            color=color_map['deprecation'],
            tag_func=tag_func or (lambda _: DEFAULT_BREAKING_CHANGE_TAG),
            message_func=message_func or _default_get_message
        )

    def expired(self):
        return False


class MergedTag(StatusTag):

    def __init__(self, cli_ctx, *tags):
        assert len(tags) > 0
        tag = tags[0]

        def _get_merged_tag(self):
            return ''.join(set([tag._get_tag(self) for tag in tags]))

        def _get_merged_msg(self):
            return '\n'.join(set([tag._get_message(self) for tag in tags]))

        super().__init__(cli_ctx, tag.object_type, tag.target, tag_func=_get_merged_tag,
                         message_func=_get_merged_msg, color=tag._color)
        self.tags = tags

    def hidden(self):
        return any([tag.hidden() for tag in self.tags])

    def show_in_help(self):
        return any([tag.show_in_help() for tag in self.tags])

    def expired(self):
        return any([tag.expired() for tag in self.tags])

    @property
    def tag(self):
        return ''.join(set([str(tag.tag) for tag in self.tags]))

    @property
    def message(self):
        return '\n'.join(set([str(tag.message) for tag in self.tags]))


def _next_breaking_change_version():
    return NEXT_BREAKING_CHANGE_RELEASE


# pylint: disable=too-few-public-methods
class TargetVersion(abc.ABC):
    @abc.abstractmethod
    def __str__(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def version(self):
        raise NotImplementedError()


# pylint: disable=too-few-public-methods
class NextBreakingChangeWindow(TargetVersion):
    def __str__(self):
        return f'in next breaking change release({_next_breaking_change_version()})'

    def version(self):
        return _next_breaking_change_version()


# pylint: disable=too-few-public-methods
class ExactVersion(TargetVersion):
    def __init__(self, version):
        self.version = version

    def __str__(self):
        return f'in {self.version}'

    def version(self):
        return self.version()


# pylint: disable=too-few-public-methods
class UnspecificVersion(TargetVersion):
    def __str__(self):
        return 'in future'

    def version(self):
        return None


class BreakingChange(abc.ABC):
    def __init__(self, cmd, arg=None, target=None):
        self.cmd = cmd
        if isinstance(arg, str):
            self.args = [arg]
        elif isinstance(arg, list):
            self.args = arg
        else:
            self.args = []
        self.target = target if target else '/'.join(self.args) if self.args else self.cmd

    @property
    def message(self):
        return ''

    @property
    def target_version(self):
        return UnspecificVersion()

    @staticmethod
    def format_doc_link(doc_link):
        return f' To know more about the Breaking Change, please visit {doc_link}.' if doc_link else ''

    @property
    def command_name(self):
        if self.cmd.startswith('az '):
            return self.cmd[3:].strip()
        else:
            return self.cmd

    def is_command_group(self, cli_ctx):
        return self.command_name in cli_ctx.invocation.commands_loader.command_group_table

    def to_tag(self, cli_ctx):
        if self.args:
            object_type = 'argument'
        elif self.is_command_group(cli_ctx):
            object_type = 'command group'
        else:
            object_type = 'command'
        return UpcomingBreakingChangeTag(cli_ctx, object_type, target=self.target, target_version=self.target_version,
                                         message_func=lambda _: self.message)

    def apply(self, cli_ctx):
        def _handle_argument_deprecation(deprecate_info, parent_class):

            class DeprecatedArgumentAction(parent_class):

                def __call__(self, parser, namespace, values, option_string=None):
                    if not hasattr(namespace, '_argument_deprecations'):
                        setattr(namespace, '_argument_deprecations', [deprecate_info])
                    else:
                        namespace._argument_deprecations.append(deprecate_info)  # pylint: disable=protected-access
                    try:
                        super().__call__(parser, namespace, values, option_string)
                    except NotImplementedError:
                        setattr(namespace, self.dest, values)

            return DeprecatedArgumentAction

        def find_arg(arg_name, arguments):
            if arg_name in arguments:
                return arg_name, arguments[arg_name]
            for key, argument in arguments.items():
                for option in argument.options_list or []:
                    if arg_name == option:
                        return key, argument
            trimmed_arg_name = arg_name.strip('-').replace('-', '_')
            if trimmed_arg_name in arguments:
                return trimmed_arg_name, arguments[trimmed_arg_name]
            return None, None

        def iter_direct_sub_cg(cg_name):
            for key, command_group in cli_ctx.invocation.commands_loader.command_group_table.items():
                if key.rsplit(maxsplit=1)[0] == cg_name:
                    from azure.cli.core.commands import AzCommandGroup
                    if isinstance(command_group, AzCommandGroup):
                        yield command_group
                    else:
                        yield from iter_direct_sub_cg(key)

        def upsert_breaking_change(command_group, tag):
            command_group.group_kwargs['deprecate_info'] = tag

        if self.args:
            for arg_name in self.args:
                #     arg_name, arg_type = find_arg(arg)
                #     # if arg_type and 'deprecate_info' in arg_type.settings:
                #     #     arg_type.settings['deprecate_info'] = self.to_tag(cli_ctx)
                #     # else:
                #     #     arg_type.settings['upcoming_breaking_change'] = [self.to_tag(cli_ctx)]
                #     if not arg_type:
                #         continue
                #     for loader in cli_ctx.invocation.commands_loader.cmd_to_loader_map[self.command_name]:
                #         with loader.argument_context(self.command_name) as c:
                #             c.argument(arg_name, arg_type=arg_type, deprecate_info=self.to_tag(cli_ctx))
                # cli_ctx.invocation.commands_loader._update_command_definitions()
                command = cli_ctx.invocation.commands_loader.command_table.get(self.cmd)
                if not command:
                    return
                arg_name, arg = find_arg(arg_name, command.arguments)
                if not arg:
                    continue
                arg.deprecate_info = self.to_tag(cli_ctx)
                arg.action = _handle_argument_deprecation(arg.deprecate_info, arg.options['action'])
        elif self.is_command_group(cli_ctx):
            command_group = cli_ctx.invocation.commands_loader.command_group_table[self.command_name]
            if not command_group:
                for command_group in iter_direct_sub_cg(self.command_name):
                    upsert_breaking_change(command_group, self.to_tag(cli_ctx))
            else:
                upsert_breaking_change(command_group, self.to_tag(cli_ctx))
        else:
            command = cli_ctx.invocation.commands_loader.command_table.get(self.cmd)
            if not command:
                return
            command.deprecate_info = self.to_tag(cli_ctx)


class AzCLIRemoveChange(BreakingChange):
    """
    Remove the command groups, commands or arguments in a future release.

    **It is recommended to utilize `deprecate_info` instead of this class to pre-announce Breaking Change of Removal.**
    :param target: name of the removed command group, command or argument
    :param target_version: version where the breaking change is expected to happen.
    :type target_version: TargetVersion
    :param redirect: alternative way to replace the old behavior
    :param doc_link: link of the related document
    """

    def __init__(self, cmd, arg=None, target_version=NextBreakingChangeWindow(), target=None, redirect=None, doc_link=None):
        super().__init__(cmd, arg, target)
        self._target_version = target_version
        self.alter = redirect
        self.doc_link = doc_link

    @property
    def message(self):
        alter = f' Please use {self.alter} instead.' if self.alter else ''
        doc = self.format_doc_link(self.doc_link)
        return f'`{self.target}` will be removed {str(self._target_version)}.{alter}{doc}'

    @property
    def target_version(self):
        return self._target_version


class AzCLIRenameChange(BreakingChange):
    """
    Rename the command groups, commands or arguments to a new name in a future release.

    **It is recommended to utilize `deprecate_info` instead of this class to pre-announce Breaking Change of Renaming.**
    It is recommended that the old name and the new name should be reserved in few releases.
    :param target: name of the renamed command group, command or argument
    :param new_name: new name
    :param target_version: version where the breaking change is expected to happen.
    :type target_version: TargetVersion
    :param doc_link: link of the related document
    """

    def __init__(self, cmd, new_name, arg=None, target=None, target_version=NextBreakingChangeWindow(), doc_link=None):
        super().__init__(cmd, arg, target)
        self.new_name = new_name
        self._target_version = target_version
        self.doc_link = doc_link

    @property
    def message(self):
        doc = self.format_doc_link(self.doc_link)
        return f'`{self.target}` will be renamed to `{self.new_name}` {str(self._target_version)}.{doc}'

    @property
    def target_version(self):
        return self._target_version


class AzCLIOutputChange(BreakingChange):
    """
    The output of the command will be changed in a future release.
    :param description: describe the changes in output
    :param target_version: version where the breaking change is expected to happen.
    :type target_version: TargetVersion
    :param guide: how to adapt to the change
    :param doc_link: link of the related document
    """

    def __init__(self, cmd, description: str, target_version=NextBreakingChangeWindow(), guide=None, doc_link=None):
        super().__init__(cmd, None, None)
        self.desc = description
        self._target_version = target_version
        self.guide = guide
        self.doc_link = doc_link

    @property
    def message(self):
        desc = self.desc.rstrip()
        if desc and desc[-1] not in ',.;?!':
            desc = desc + '.'
        if self.guide:
            guide = self.guide.rstrip()
            if guide and guide[-1] not in ',.;?!':
                guide = guide + '.'
        else:
            guide = ''
        doc = self.format_doc_link(self.doc_link)
        return f'The output will be changed {str(self._target_version)}. {desc} {guide}{doc}'

    @property
    def target_version(self):
        return self._target_version


class AzCLILogicChange(BreakingChange):
    """
    There would be a breaking change in the logic of the command in future release.
    :param summary: a short summary about the breaking change
    :param target_version: version where the breaking change is expected to happen.
    :type target_version: TargetVersion
    :param detail: detailed information
    :param doc_link: link of the related document
    """

    def __init__(self, cmd, summary, target_version=NextBreakingChangeWindow(), detail=None, doc_link=None):
        super().__init__(cmd, None, None)
        self.summary = summary
        self._target_version = target_version
        self.detail = detail
        self.doc_link = doc_link

    @property
    def message(self):
        detail = f' {self.detail}' if self.detail else ''
        return f'{self.summary} {str(self._target_version)}.{detail}{self.format_doc_link(self.doc_link)}'

    @property
    def target_version(self):
        return self._target_version


class AzCLIDefaultChange(BreakingChange):
    """
    The default value of an argument would be changed in a future release.
    :param target: name of the related argument
    :param current_default: current default value of the argument
    :param new_default: new default value of the argument
    :param target_version: version where the breaking change is expected to happen.
    :type target_version: TargetVersion
    :param doc_link: link of the related document
    """

    def __init__(self, cmd, arg, current_default, new_default, target_version=NextBreakingChangeWindow(),
                 target=None, doc_link=None):
        super().__init__(cmd, arg, target)
        self.target = target
        self.current_default = current_default
        self.new_default = new_default
        self._target_version = target_version
        self.doc_link = doc_link

    @property
    def message(self):
        doc = self.format_doc_link(self.doc_link)
        return (f'The default value of `{self.target}` will be changed to `{self.new_default}` from '
                f'`{self.current_default}` {str(self._target_version)}.{doc}')

    @property
    def target_version(self):
        return self._target_version


class AzCLIBeRequired(BreakingChange):
    """
    The argument would become required in a future release.
    :param target: name of the related argument
    :param target_version: version where the breaking change is expected to happen.
    :type target_version: TargetVersion
    :param doc_link: link of the related document
    """

    def __init__(self, cmd, arg, target_version=NextBreakingChangeWindow(), target=None, doc_link=None):
        super().__init__(cmd, arg, target)
        self._target_version = target_version
        self.doc_link = doc_link

    @property
    def message(self):
        doc = self.format_doc_link(self.doc_link)
        return f'The argument `{self.target}` will become required {str(self._target_version)}.{doc}'

    @property
    def target_version(self):
        return self._target_version


class AzCLIOtherChange(BreakingChange):
    """
    Other custom breaking changes.
    :param message: A description of the breaking change, including the version number where it is expected to occur.
    :param target_version: version where the breaking change is expected to happen.
    :type target_version: TargetVersion
    """

    def __init__(self, cmd, message, arg=None, target=None, target_version=NextBreakingChangeWindow()):
        super().__init__(cmd, arg, target)
        self._message = message
        self._target_version = target_version

    @property
    def message(self):
        return self._message

    @property
    def target_version(self):
        return self._target_version


upcoming_breaking_changes = {}


def import_module_breaking_changes(mod):
    try:
        from importlib import import_module
        import_module('azure.cli.command_modules.' + mod + '._breaking_change')
    except ImportError:
        pass


def import_extension_breaking_changes(ext_mod):
    try:
        from importlib import import_module
        import_module(ext_mod + '._breaking_change')
    except ImportError:
        pass


def register_upcoming_breaking_change_info(cli_ctx):
    from knack import events

    def update_breaking_change_info(cli_ctx, **kwargs):
        for bc in upcoming_breaking_changes.values():
            if isinstance(bc, list):
                for bc in bc:
                    bc.apply(cli_ctx)
            else:
                bc.apply(cli_ctx)

    cli_ctx.register_event(events.EVENT_INVOKER_POST_CMD_TBL_CREATE, update_breaking_change_info)


def iter_command_breaking_changes(cmd):
    cmd_parts = cmd.split()
    if cmd_parts and cmd_parts[0] == 'az':
        cmd_parts = cmd_parts[1:]
    for parts_end in range(0, len(cmd_parts) + 1):
        bc = upcoming_breaking_changes.get(' '.join(cmd_parts[:parts_end]))
        if isinstance(bc, list):
            yield from bc
        elif bc:
            yield bc
