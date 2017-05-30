# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import argparse
import sys
import textwrap

from azure.cli.core.help_files import _load_help_file

__all__ = ['print_detailed_help', 'print_welcome_message', 'GroupHelpFile', 'CommandHelpFile']

FIRST_LINE_PREFIX = ': '

PRIVACY_STATEMENT = """
Welcome to Azure CLI!
---------------------
Use `az -h` to see available commands or go to https://aka.ms/cli.

Telemetry
---------
The Azure CLI collects usage data in order to improve your experience.
The data is anonymous and does not include commandline argument values.
The data is collected by Microsoft.

You can change your telemetry settings with `az configure`.
"""


def show_privacy_statement():
    from azure.cli.core._config import az_config, set_global_config_value
    first_ran = az_config.getboolean('core', 'first_run', fallback=False)
    if not first_ran:
        print(PRIVACY_STATEMENT, file=sys.stdout)
        set_global_config_value('core', 'first_run', 'yes')


def show_help(nouns, parser, is_group):
    delimiters = ' '.join(nouns)
    help_file = CommandHelpFile(delimiters, parser) \
        if not is_group \
        else GroupHelpFile(delimiters, parser)

    help_file.load(parser)

    if not nouns:
        print("\nFor version info, use 'az --version'")
        help_file.command = ''

    print_detailed_help(help_file)


def show_welcome(parser):
    show_privacy_statement()
    print_welcome_message()

    help_file = GroupHelpFile('', parser)
    print_description_list(help_file.children)


def print_welcome_message():
    _print_indent(r"""
     /\
    /  \    _____   _ _ __ ___
   / /\ \  |_  / | | | \'__/ _ \
  / ____ \  / /| |_| | | |  __/
 /_/    \_\/___|\__,_|_|  \___|
""")
    _print_indent('\nWelcome to the cool new Azure CLI!\n\nHere are the base commands:\n')


def print_detailed_help(help_file):
    _print_header(help_file)

    if help_file.type == 'command':
        _print_indent('Arguments')
        print_arguments(help_file)
    elif help_file.type == 'group':
        _print_groups(help_file)

    if help_file.examples:
        _print_examples(help_file)


def print_description_list(help_files):
    indent = 1
    max_name_length = max(len(f.name) for f in help_files) if help_files else 0
    for help_file in sorted(help_files, key=lambda h: h.name):
        _print_indent('{0}{1}{2}'.format(help_file.name,
                                         _get_column_indent(help_file.name, max_name_length),
                                         FIRST_LINE_PREFIX + help_file.short_summary
                                         if help_file.short_summary
                                         else ''),
                      indent,
                      _get_hanging_indent(max_name_length, indent))


def print_arguments(help_file):
    indent = 1
    if not help_file.parameters:
        _print_indent('None', indent)
        _print_indent('')
        return

    if not help_file.parameters:
        _print_indent('none', indent)
    required_tag = ' [Required]'
    max_name_length = max(len(p.name) + (len(required_tag) if p.required else 0)
                          for p in help_file.parameters)
    last_group_name = None

    group_registry = ArgumentGroupRegistry(
        [p.group_name for p in help_file.parameters if p.group_name])

    def _get_parameter_key(parameter):
        return '{}{}{}'.format(group_registry.get_group_priority(parameter.group_name),
                               str(not parameter.required),
                               parameter.name)

    for p in sorted(help_file.parameters, key=_get_parameter_key):
        indent = 1
        required_text = required_tag if p.required else ''

        short_summary = p.short_summary if p.short_summary else ''
        possible_values_index = short_summary.find(' Possible values include')
        short_summary = short_summary[0:possible_values_index
                                      if possible_values_index >= 0 else len(short_summary)]
        short_summary += _get_choices_defaults_sources_str(p)
        short_summary = short_summary.strip()

        if p.group_name != last_group_name:
            if p.group_name:
                print('')
                print(p.group_name)
            last_group_name = p.group_name
        _print_indent(
            '{0}{1}{2}{3}'.format(
                p.name,
                _get_column_indent(p.name + required_text, max_name_length),
                required_text,
                FIRST_LINE_PREFIX + short_summary if short_summary else ''
            ),
            indent,
            _get_hanging_indent(max_name_length, indent)
        )

        indent = 2
        if p.long_summary:
            _print_indent('{0}'.format(p.long_summary.rstrip()), indent)

    return indent


class ArgumentGroupRegistry(object):  # pylint: disable=too-few-public-methods

    def __init__(self, group_list):

        self.priorities = {
            None: 0,
            'Resource Id Arguments': 1,
            'Generic Update Arguments': 998,
            'Global Arguments': 1000,
        }
        priority = 2
        # any groups not already in the static dictionary should be prioritized alphabetically
        other_groups = [g for g in sorted(list(set(group_list))) if g not in self.priorities]
        for group in other_groups:
            self.priorities[group] = priority
            priority += 1

    def get_group_priority(self, group_name):
        key = self.priorities.get(group_name, 0)
        return "%06d" % key


def _print_header(help_file):
    indent = 0
    _print_indent('')
    _print_indent('Command' if help_file.type == 'command' else 'Group', indent)

    indent += 1
    _print_indent('{0}{1}'.format('az ' + help_file.command,
                                  FIRST_LINE_PREFIX + help_file.short_summary
                                  if help_file.short_summary
                                  else ''),
                  indent)

    indent += 1
    if help_file.long_summary:
        _print_indent('{0}'.format(help_file.long_summary.rstrip()), indent)
    _print_indent('')


def _print_groups(help_file):

    def _print_items(items):
        for c in sorted(items, key=lambda h: h.name):
            column_indent = _get_column_indent(c.name, max_name_length)
            summary = FIRST_LINE_PREFIX + c.short_summary if c.short_summary else ''
            summary = summary.replace('\n', ' ')
            hanging_indent = max_name_length + indent * 4 + 2
            _print_indent(
                '{0}{1}{2}'.format(c.name, column_indent, summary), indent, hanging_indent)
        _print_indent('')

    indent = 1
    max_name_length = max(len(c.name) for c in help_file.children) \
        if help_file.children \
        else 0
    subgroups = [c for c in help_file.children if isinstance(c, GroupHelpFile)]
    subcommands = [c for c in help_file.children if c not in subgroups]

    if subgroups:
        _print_indent('Subgroups:')
        _print_items(subgroups)

    if subcommands:
        _print_indent('Commands:')
        _print_items(subcommands)


def _get_choices_defaults_sources_str(p):
    choice_str = '  Allowed values: {0}.'.format(', '.join(sorted([str(x) for x in p.choices]))) \
        if p.choices else ''
    default_str = '  Default: {0}.'.format(p.default) \
        if p.default and p.default != argparse.SUPPRESS else ''
    value_sources_str = '  Values from: {0}.'.format(', '.join(p.value_sources)) \
        if p.value_sources else ''
    return '{0}{1}{2}'.format(choice_str, default_str, value_sources_str)


def _print_examples(help_file):
    indent = 0
    print('')
    _print_indent('Examples', indent)

    for e in help_file.examples:
        indent = 1
        _print_indent('{0}'.format(e.name), indent)

        indent = 2
        _print_indent('{0}'.format(e.text), indent)

        print('')


class HelpObject(object):  # pylint: disable=too-few-public-methods

    def __init__(self, **kwargs):
        self._short_summary = ''
        self._long_summary = ''
        super(HelpObject, self).__init__(**kwargs)

    @property
    def short_summary(self):
        return self._short_summary

    @short_summary.setter
    def short_summary(self, value):
        self._short_summary = _normalize_text(value)

    @property
    def long_summary(self):
        return self._long_summary

    @long_summary.setter
    def long_summary(self, value):
        self._long_summary = _normalize_text(value)


class HelpFile(HelpObject):  # pylint: disable=too-few-public-methods,too-many-instance-attributes

    def __init__(self, delimiters):
        super(HelpFile, self).__init__()
        self.delimiters = delimiters
        self.name = delimiters.split()[-1] if delimiters else delimiters
        self.command = delimiters
        self.type = ''
        self.short_summary = ''
        self.long_summary = ''
        self.examples = []

    def load(self, options):
        description = getattr(options, 'description', None)
        try:
            self.short_summary = description[:description.index('.')]
            long_summary = description[description.index('.') + 1:].lstrip()
            self.long_summary = ' '.join(long_summary.splitlines())
        except (ValueError, AttributeError):
            self.short_summary = description

        file_data = (_load_help_file_from_string(options.help_file)
                     if hasattr(options, '_defaults')
                     else None)

        if file_data:
            self._load_from_data(file_data)
        else:
            self._load_from_file()

    def _load_from_file(self):
        file_data = _load_help_file(self.delimiters)
        if file_data:
            self._load_from_data(file_data)

    @staticmethod
    def _should_include_example(ex):
        min_profile = ex.get('min_profile')
        max_profile = ex.get('max_profile')
        if min_profile or max_profile:
            from azure.cli.core.profiles import supported_api_version, PROFILE_TYPE
            # yaml will load this as a datetime if it's a date, we need a string.
            min_profile = str(min_profile) if min_profile else None
            max_profile = str(max_profile) if max_profile else None
            return supported_api_version(PROFILE_TYPE,
                                         min_api=min_profile,
                                         max_api=max_profile)
        return True

    def _load_from_data(self, data):
        if not data:
            return

        if isinstance(data, str):
            self.long_summary = data
            return

        if 'type' in data:
            self.type = data['type']

        if 'short-summary' in data:
            self.short_summary = data['short-summary']

        self.long_summary = data.get('long-summary')

        if 'examples' in data:
            self.examples = []
            for d in data['examples']:
                if HelpFile._should_include_example(d):
                    self.examples.append(HelpExample(d))


class GroupHelpFile(HelpFile):  # pylint: disable=too-few-public-methods

    def __init__(self, delimiters, parser):
        super(GroupHelpFile, self).__init__(delimiters)
        self.type = 'group'

        self.children = []
        if getattr(parser, 'choices', None):
            for options in parser.choices.values():
                delimiters = ' '.join(options.prog.split()[1:])
                child = (GroupHelpFile(delimiters, options) if options.is_group()
                         else HelpFile(delimiters))
                child.load(options)
                self.children.append(child)


class CommandHelpFile(HelpFile):  # pylint: disable=too-few-public-methods

    def __init__(self, delimiters, parser):
        super(CommandHelpFile, self).__init__(delimiters)
        self.type = 'command'

        self.parameters = []

        for action in [a for a in parser._actions if a.help != argparse.SUPPRESS]:  # pylint: disable=protected-access
            self.parameters.append(HelpParameter(' '.join(sorted(action.option_strings)),
                                                 action.help,
                                                 required=action.required,
                                                 choices=action.choices,
                                                 default=action.default,
                                                 group_name=action.container.description))

        help_param = next(p for p in self.parameters if p.name == '--help -h')
        help_param.group_name = 'Global Arguments'

    def _load_from_data(self, data):
        super(CommandHelpFile, self)._load_from_data(data)

        if isinstance(data, str) or not self.parameters or not data.get('parameters'):
            return

        loaded_params = []
        loaded_param = {}
        for param in self.parameters:
            loaded_param = next((n for n in data['parameters'] if n['name'] == param.name), None)
            if loaded_param:
                param.update_from_data(loaded_param)
            loaded_params.append(param)

        self.parameters = loaded_params


class HelpParameter(HelpObject):  # pylint: disable=too-few-public-methods, too-many-instance-attributes

    def __init__(self, param_name, description, required, choices=None,
                 default=None, group_name=None):
        super(HelpParameter, self).__init__()
        self.name = param_name
        self.required = required
        self.type = 'string'
        self.short_summary = description
        self.long_summary = ''
        self.value_sources = []
        self.choices = choices
        self.default = default
        self.group_name = group_name

    def update_from_data(self, data):
        if self.name != data.get('name'):
            raise HelpAuthoringException("mismatched name {0} vs. {1}"
                                         .format(self.name,
                                                 data.get('name')))

        if data.get('type'):
            self.type = data.get('type')

        if data.get('short-summary'):
            self.short_summary = data.get('short-summary')

        if data.get('long-summary'):
            self.long_summary = data.get('long-summary')

        if data.get('populator-commands'):
            self.value_sources = data.get('populator-commands')


class HelpExample(object):  # pylint: disable=too-few-public-methods

    def __init__(self, _data):
        self.name = _data['name']
        self.text = _data['text']


def _print_indent(s, indent=0, subsequent_spaces=-1):
    tw = textwrap.TextWrapper(initial_indent='    ' * indent,
                              subsequent_indent=('    ' * indent
                                                 if subsequent_spaces == -1
                                                 else ' ' * subsequent_spaces),
                              replace_whitespace=False,
                              width=100)
    paragraphs = s.split('\n')
    for p in paragraphs:
        try:
            print(tw.fill(p), file=sys.stdout)
        except UnicodeEncodeError:
            print(tw.fill(p).encode('ascii', 'ignore').decode('utf-8', 'ignore'), file=sys.stdout)


def _get_column_indent(text, max_name_length):
    return ' ' * (max_name_length - len(text))


def _get_hanging_indent(max_length, indent):
    return max_length + (indent * 4) + len(FIRST_LINE_PREFIX)


def _normalize_text(s):
    if not s or len(s) < 2:
        return s or ''
    s = s.strip()
    initial_upper = s[0].upper() + s[1:]
    trailing_period = '' if s[-1] in '.!?' else '.'
    return initial_upper + trailing_period


def _load_help_file_from_string(text):
    import yaml
    try:
        return yaml.load(text) if text else None
    except Exception:  # pylint: disable=broad-except
        return text


def _get_single_metadata(cmd_table):
    assert len(cmd_table) == 1
    return next(metadata for _, metadata in cmd_table.items())


class HelpAuthoringException(Exception):
    pass
