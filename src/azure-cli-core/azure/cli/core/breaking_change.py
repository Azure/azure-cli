# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import abc
import argparse
import re
import sys
from collections import defaultdict

from knack.log import get_logger
from knack.deprecation import Deprecated
from knack.util import StatusTag, color_map


logger = get_logger()

NEXT_BREAKING_CHANGE_RELEASE = '2.86.0'
NEXT_BREAKING_CHANGE_DATE = 'May 2026'
DEFAULT_BREAKING_CHANGE_TAG = '[Breaking Change]'


def _get_action_class(cli_ctx, action):
    action_class = argparse.Action

    # action is either a user-defined Action class or a string referring a library-defined Action
    if isinstance(action, type) and issubclass(action, argparse.Action):
        action_class = action
    elif isinstance(action, str):
        action_class = cli_ctx.invocation.parser._registries['action'][action]  # pylint: disable=protected-access
    return action_class


def _argument_breaking_change_action(cli_ctx, status_tag, action):

    action_class = _get_action_class(cli_ctx, action)

    class ArgumentBreakingChangeAction(action_class):

        def __call__(self, parser, namespace, values, option_string=None):
            if not hasattr(namespace, '_argument_deprecations'):
                setattr(namespace, '_argument_deprecations', [])
            if isinstance(status_tag, MergedStatusTag):
                for tag in status_tag.tags:
                    namespace._argument_deprecations.append(tag)
            else:
                if status_tag not in namespace._argument_deprecations:
                    namespace._argument_deprecations.append(status_tag)
            try:
                super().__call__(parser, namespace, values, option_string)
            except NotImplementedError:
                setattr(namespace, self.dest, values)

    return ArgumentBreakingChangeAction


def _find_arg(arg_name, arguments):
    if arg_name in arguments:
        return arg_name, arguments[arg_name]
    for key, argument in arguments.items():
        for option in argument.options_list or []:
            if arg_name == option or (isinstance(option, Deprecated) and arg_name == option.target):
                return key, argument
    trimmed_arg_name = arg_name.strip('-').replace('-', '_')
    if trimmed_arg_name in arguments:
        return trimmed_arg_name, arguments[trimmed_arg_name]
    return None, None


class UpcomingBreakingChangeTag(StatusTag):
    def __init__(self, cli_ctx, object_type='', target=None, target_version=None, tag_func=None, message_func=None,
                 always_display=False):
        def _default_get_message(bc):
            msg = f"A breaking change may occur to this {bc.object_type} "
            if isinstance(target_version, TargetVersion):
                msg += str(target_version) + '.'
            elif isinstance(target_version, str):
                msg += 'in ' + target_version + '.'
            else:
                msg += 'in future release.'
                return msg

        self.always_display = always_display
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


class MergedStatusTag(StatusTag):
    # This class is used to merge multiple status tags into one.
    # It is particularly useful when multiple breaking changes and deprecation information need to be recorded
    # in a single deprecate_info field.

    def __init__(self, cli_ctx, *tags):
        assert len(tags) > 0
        tag = tags[0]
        self.tags = list(tags)

        def _get_merged_tag(self):
            return ''.join({tag._get_tag(tag) for tag in self.tags})  # pylint: disable=protected-access

        def _get_merged_msg(self):
            return '\n'.join({tag._get_message(tag) for tag in self.tags})  # pylint: disable=protected-access

        super().__init__(cli_ctx, tag.object_type, tag.target, tag_func=_get_merged_tag,
                         message_func=_get_merged_msg, color=tag._color)

    def merge(self, other):
        self.tags.append(other)

    def hidden(self):
        return any(tag.hidden() for tag in self.tags)

    def show_in_help(self):
        return any(tag.show_in_help() for tag in self.tags)

    def expired(self):
        return any(tag.expired() for tag in self.tags)

    @property
    def tag(self):
        return ''.join({str(tag.tag) for tag in self.tags})

    @property
    def message(self):
        return '\n'.join({str(tag.message) for tag in self.tags})


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
        next_breaking_change_version = _next_breaking_change_version()
        message = 'in next breaking change release'
        if next_breaking_change_version:
            message += f'({next_breaking_change_version})'
        if NEXT_BREAKING_CHANGE_DATE:
            message += f' scheduled for {NEXT_BREAKING_CHANGE_DATE}'
        return message

    def version(self):
        return _next_breaking_change_version()


# pylint: disable=too-few-public-methods
class ExactVersion(TargetVersion):
    def __init__(self, version):
        self._version = version

    def __str__(self):
        return f'in {self._version}'

    def version(self):
        return self._version


# pylint: disable=too-few-public-methods
class NonVersion(TargetVersion):
    def __init__(self, msg):
        self._msg = msg

    def __str__(self):
        return f'in {self._msg}'

    def version(self):
        return None


# pylint: disable=too-few-public-methods
class UnspecificVersion(TargetVersion):
    def __str__(self):
        return 'in a future release'

    def version(self):
        return None


class BreakingChange(abc.ABC):
    def __init__(self, cmd, arg=None, target=None, target_version=None):
        self.cmd = cmd
        if isinstance(arg, str):
            self.args = [arg]
        elif isinstance(arg, list):
            self.args = arg
        else:
            self.args = []
        self.target = target if target else '/'.join(self.args) if self.args else self.cmd
        if isinstance(target_version, TargetVersion):
            self._target_version = target_version
        elif isinstance(target_version, str) and re.match(r'\d+.\d+.\d+', target_version):
            self._target_version = ExactVersion(target_version)
        elif isinstance(target_version, str):
            self._target_version = NonVersion(target_version)
        else:
            self._target_version = UnspecificVersion()

    @property
    def message(self):
        return ''

    @property
    def target_version(self):
        return self._target_version

    @staticmethod
    def format_doc_link(doc_link):
        return f' To know more about the Breaking Change, please visit {doc_link}.' if doc_link else ''

    @property
    def command_name(self):
        if self.cmd.startswith('az '):
            return self.cmd[3:].strip()
        return self.cmd

    def is_command_group(self, cli_ctx):
        return self.command_name in cli_ctx.invocation.commands_loader.command_group_table

    def to_tag(self, cli_ctx, **kwargs):
        if self.args:
            object_type = 'argument'
        elif self.is_command_group(cli_ctx):
            object_type = 'command group'
        else:
            object_type = 'command'
        tag_kwargs = {
            'object_type': object_type,
            'target': self.target,
            'target_version': self.target_version,
            'message_func': lambda _: self.message,
        }
        tag_kwargs.update(kwargs)
        return UpcomingBreakingChangeTag(cli_ctx, **tag_kwargs)

    def register(self, cli_ctx):
        if self.args:
            command = cli_ctx.invocation.commands_loader.command_table.get(self.command_name)
            if not command:
                return
            for arg_name in self.args:
                if self._register_option_deprecate(cli_ctx, command.arguments, arg_name):
                    continue
                arg_name, arg = _find_arg(arg_name, command.arguments)
                if not arg:
                    continue
                arg.deprecate_info = self.appended_status_tag(cli_ctx, arg.deprecate_info, self.to_tag(cli_ctx))
                arg.action = _argument_breaking_change_action(cli_ctx, arg.deprecate_info, arg.options.get('action'))
        elif self.is_command_group(cli_ctx):
            command_group = cli_ctx.invocation.commands_loader.command_group_table[self.command_name]
            if not command_group:
                loader = self.find_suitable_command_loader(cli_ctx)
                if not loader:
                    return
                command_group = loader.command_group(self.command_name)
                cli_ctx.invocation.commands_loader.command_group_table[self.command_name] = command_group
            if command_group:
                command_group.group_kwargs['deprecate_info'] = \
                    self.appended_status_tag(cli_ctx, command_group.group_kwargs.get('deprecate_info'),
                                             self.to_tag(cli_ctx))
        else:
            command = cli_ctx.invocation.commands_loader.command_table.get(self.cmd)
            if not command:
                return
            command.deprecate_info = self.appended_status_tag(cli_ctx, command.deprecate_info, self.to_tag(cli_ctx))

    @staticmethod
    def appended_status_tag(cli_ctx, old_status_tag, new_status_tag):
        if isinstance(old_status_tag, (Deprecated, UpcomingBreakingChangeTag)):
            return MergedStatusTag(cli_ctx, old_status_tag, new_status_tag)
        if isinstance(old_status_tag, MergedStatusTag):
            old_status_tag.merge(new_status_tag)
            return old_status_tag
        return new_status_tag

    def find_suitable_command_loader(self, cli_ctx):
        for name, loader in cli_ctx.invocation.commands_loader.cmd_to_loader_map.items():
            if name.startswith(self.command_name) and loader:
                return loader[0]
        return None

    def _register_option_deprecate(self, cli_ctx, arguments, option_name):
        for _, argument in arguments.items():
            if argument.options_list and len(argument.options_list) > 1:
                for idx, option in enumerate(argument.options_list):
                    if isinstance(option, str) and option_name == option and isinstance(self, AzCLIDeprecate):
                        if isinstance(argument.options_list, tuple):
                            # Some of the command would declare options_list as tuple
                            argument.options_list = list(argument.options_list)
                        argument.options_list[idx] = self.to_tag(cli_ctx, object_type='option')
                        argument.options_list[idx].target = option
                        argument.action = _argument_breaking_change_action(cli_ctx, argument.options_list[idx],
                                                                           argument.options['action'])
                        return True
        return False


class AzCLIDeprecate(BreakingChange):
    def __init__(self, cmd, arg=None, target_version=NextBreakingChangeWindow(), message=None, **kwargs):
        super().__init__(cmd, arg, None, target_version)
        self._message = message
        self.kwargs = kwargs

    @staticmethod
    def _build_message(object_type, target, target_version, redirect):
        if object_type in ['argument', 'option']:
            msg = "{} '{}' has been deprecated and will be removed ".format(object_type, target).capitalize()
        elif object_type:
            msg = "This {} has been deprecated and will be removed ".format(object_type)
        else:
            msg = "'{}' has been deprecated and will be removed ".format(target)
        msg += str(target_version) + '.'
        if redirect:
            msg += " Use '{}' instead.".format(redirect)
        return msg

    @property
    def message(self):
        return self._message or self._build_message(self.kwargs.get('object_type'), self.target, self.target_version,
                                                    self.kwargs.get('redirect'))

    def to_tag(self, cli_ctx, **kwargs):
        if self.args:
            object_type = 'argument'
        elif self.is_command_group(cli_ctx):
            object_type = 'command group'
        else:
            object_type = 'command'
        tag_kwargs = {
            'object_type': object_type,
            'message_func': lambda depr: self._message or self._build_message(
                depr.object_type, depr.target, self.target_version, depr.redirect),
            'target': self.target
        }
        tag_kwargs.update(self.kwargs)
        tag_kwargs.update(kwargs)
        return Deprecated(cli_ctx, **tag_kwargs)


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

    def __init__(self, cmd, arg=None, target_version=NextBreakingChangeWindow(), target=None, redirect=None,
                 doc_link=None):
        super().__init__(cmd, arg, target, target_version)
        self.alter = redirect
        self.doc_link = doc_link

    @property
    def message(self):
        alter = f" Please use '{self.alter}' instead." if self.alter else ''
        doc = self.format_doc_link(self.doc_link)
        return f"'{self.target}' will be removed {str(self._target_version)}.{alter}{doc}"


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
        super().__init__(cmd, arg, target, target_version)
        self.new_name = new_name
        self.doc_link = doc_link

    @property
    def message(self):
        doc = self.format_doc_link(self.doc_link)
        return f"'{self.target}' will be renamed to '{self.new_name}' {str(self._target_version)}.{doc}"


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
        super().__init__(cmd, None, None, target_version)
        self.desc = description
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
                guide = ' ' + guide + '.'
        else:
            guide = ''
        doc = self.format_doc_link(self.doc_link)
        return f'The output will be changed {str(self.target_version)}. {desc}{guide}{doc}'


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
        super().__init__(cmd, None, None, target_version)
        self.summary = summary
        self.detail = detail
        self.doc_link = doc_link

    @property
    def message(self):
        detail = f' {self.detail}' if self.detail else ''
        return f'{self.summary} {str(self.target_version)}.{detail}{self.format_doc_link(self.doc_link)}'


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
        super().__init__(cmd, arg, target, target_version)
        self.current_default = current_default
        self.new_default = new_default
        self.doc_link = doc_link

    @property
    def message(self):
        doc = self.format_doc_link(self.doc_link)
        return (f"The default value of '{self.target}' will be changed to '{self.new_default}' from "
                f"'{self.current_default}' {str(self._target_version)}.{doc}")

    def to_tag(self, cli_ctx, **kwargs):
        if 'always_display' not in kwargs:
            kwargs['always_display'] = True
        return super().to_tag(cli_ctx, **kwargs)


class AzCLIBeRequired(BreakingChange):
    """
    The argument would become required in a future release.
    :param target: name of the related argument
    :param target_version: version where the breaking change is expected to happen.
    :type target_version: TargetVersion
    :param doc_link: link of the related document
    """

    def __init__(self, cmd, arg, target_version=NextBreakingChangeWindow(), target=None, doc_link=None):
        super().__init__(cmd, arg, target, target_version)
        self.doc_link = doc_link

    @property
    def message(self):
        doc = self.format_doc_link(self.doc_link)
        return f"The argument '{self.target}' will become required {str(self._target_version)}.{doc}"

    def to_tag(self, cli_ctx, **kwargs):
        if 'always_display' not in kwargs:
            kwargs['always_display'] = True
        return super().to_tag(cli_ctx, **kwargs)


class AzCLIOtherChange(BreakingChange):
    """
    Other custom breaking changes.
    :param message: A description of the breaking change, including the version number where it is expected to occur.
    :param target_version: version where the breaking change is expected to happen.
    :type target_version: TargetVersion
    """

    def __init__(self, cmd, message, arg=None, target_version=NextBreakingChangeWindow()):
        super().__init__(cmd, arg, None, target_version)
        self._message = message

    @property
    def message(self):
        return self._message


upcoming_breaking_changes = defaultdict(lambda: [])


def import_core_breaking_changes():
    try:
        from importlib import import_module
        import_module('azure.cli.core._breaking_change')
    except ImportError:
        pass


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

    def update_breaking_change_info(cli_ctx, **kwargs):  # pylint: disable=unused-argument
        for key, breaking_changes in upcoming_breaking_changes.items():
            # Conditional Breaking Changes are announced with key `CommandName.Tag`. They should not be registered.
            if '.' in key:
                continue
            for breaking_change in breaking_changes:
                breaking_change.register(cli_ctx)

    cli_ctx.register_event(events.EVENT_INVOKER_POST_CMD_TBL_CREATE, update_breaking_change_info)


def register_deprecate_info(command_name, arg=None, target_version=NextBreakingChangeWindow(), message=None, **kwargs):
    upcoming_breaking_changes[command_name].append(AzCLIDeprecate(command_name, arg, target_version, message, **kwargs))


def register_output_breaking_change(command_name, description, target_version=NextBreakingChangeWindow(), guide=None,
                                    doc_link=None):
    upcoming_breaking_changes[command_name].append(
        AzCLIOutputChange(command_name, description, target_version, guide, doc_link))


def register_logic_breaking_change(command_name, summary, target_version=NextBreakingChangeWindow(), detail=None,
                                   doc_link=None):
    upcoming_breaking_changes[command_name].append(
        AzCLILogicChange(command_name, summary, target_version, detail, doc_link))


def register_default_value_breaking_change(command_name, arg, current_default, new_default,
                                           target_version=NextBreakingChangeWindow(), target=None, doc_link=None):
    upcoming_breaking_changes[command_name].append(
        AzCLIDefaultChange(command_name, arg, current_default, new_default, target_version, target, doc_link))


def register_required_flag_breaking_change(command_name, arg, target_version=NextBreakingChangeWindow(), target=None,
                                           doc_link=None):
    upcoming_breaking_changes[command_name].append(AzCLIBeRequired(command_name, arg, target_version, target, doc_link))


def register_other_breaking_change(command_name, message, arg=None, target_version=NextBreakingChangeWindow()):
    upcoming_breaking_changes[command_name].append(AzCLIOtherChange(command_name, message, arg, target_version))


def register_command_group_deprecate(command_group, redirect=None, hide=None,
                                     target_version=NextBreakingChangeWindow(), message=None, **kwargs):
    register_deprecate_info(command_group, redirect=redirect, hide=hide, target_version=target_version,
                            message=message, **kwargs)


def register_command_deprecate(command, redirect=None, hide=None,
                               target_version=NextBreakingChangeWindow(), message=None, **kwargs):
    register_deprecate_info(command, redirect=redirect, hide=hide, target_version=target_version,
                            message=message, **kwargs)


def register_argument_deprecate(command, argument, redirect=None, hide=None,
                                target_version=NextBreakingChangeWindow(), message=None, **kwargs):
    register_deprecate_info(command, argument, redirect=redirect, hide=hide, target_version=target_version,
                            message=message, **kwargs)


def register_conditional_breaking_change(tag, breaking_change, *, command_name=None):
    if command_name and command_name.startswith('az '):
        command_name = command_name[3:].strip()
    if isinstance(breaking_change, BreakingChange):
        command_name = command_name or breaking_change.command_name
        upcoming_breaking_changes[command_name + '.' + tag].append(breaking_change)
    elif isinstance(breaking_change, str):
        command_name = command_name or ''
        upcoming_breaking_changes[command_name + '.' + tag].append(AzCLIOtherChange(
            cmd=command_name,
            message=breaking_change,
        ))


def print_conditional_breaking_change(cli_ctx, tag, *, custom_logger=None, command_name=None):
    """
    Print a breaking change warning message manually.
    :param cli_ctx: By default, retrieve the command name from cli_ctx.
    :param tag: Use the tag to distinguish different warning messages to be printed in the same command.
    Please note, all breaking change items with the same tag from the parent command group will also be printed.
    :param custom_logger: Use a custom logger to replace the logger in azure.cli.core.breaking_change.
    :param command_name: Specify the command name if not pass in the cli_ctx
    """
    command = cli_ctx.invocation.commands_loader.command_name if cli_ctx else command_name
    command = command or ''
    tag_suffix = '.' + tag if tag is not None else ''

    command_comps = command.split()
    while command_comps:
        for breaking_change in upcoming_breaking_changes.get(' '.join(command_comps) + tag_suffix, []):
            if custom_logger:
                custom_logger.warning(breaking_change.message)
            else:
                print(breaking_change.message, file=sys.stderr)
        del command_comps[-1]
    for breaking_change in upcoming_breaking_changes.get(tag_suffix, []):
        if custom_logger:
            custom_logger.warning(breaking_change.message)
        else:
            print(breaking_change.message, file=sys.stderr)
