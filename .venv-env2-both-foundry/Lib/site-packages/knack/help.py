# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import sys
import textwrap

from .deprecation import ImplicitDeprecated, resolve_deprecate_info
from .log import get_logger
from .preview import ImplicitPreviewItem, resolve_preview_info
from .experimental import ImplicitExperimentalItem, resolve_experimental_info
from .util import CtxTypeError
from .help_files import _load_help_file


logger = get_logger(__name__)


FIRST_LINE_PREFIX = ' : '
REQUIRED_TAG = '[Required]'


def _get_hanging_indent(max_length, indent):
    return max_length + (indent * 4) + len(FIRST_LINE_PREFIX) - 1


def _get_padding_len(max_len, layout):
    if layout['tags']:
        pad_len = max_len - layout['line_len'] + 1
    else:
        pad_len = max_len - layout['line_len']
    return pad_len


def _get_line_len(name, tags_len):
    return len(name) + tags_len + (2 if tags_len else 1)


def _print_indent(s, indent=0, subsequent_spaces=-1, width=100):
    tw = textwrap.TextWrapper(initial_indent='    ' * indent,
                              subsequent_indent=('    ' * indent
                                                 if subsequent_spaces == -1
                                                 else ' ' * subsequent_spaces),
                              replace_whitespace=False,
                              width=width)
    paragraphs = s.split('\n')
    for p in paragraphs:
        try:
            print(tw.fill(p), file=sys.stdout)
        except UnicodeEncodeError:
            print(tw.fill(p).encode('ascii', 'ignore').decode('utf-8', 'ignore'), file=sys.stdout)


class HelpAuthoringException(Exception):
    pass


class ArgumentGroupRegistry(object):  # pylint: disable=too-few-public-methods

    def __init__(self, group_list):

        self.priorities = {
            None: 0,
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


class HelpObject(object):

    @staticmethod
    def _normalize_text(s):
        if not s or len(s) < 2:
            return s or ''
        s = s.strip()
        initial_upper = s[0].upper() + s[1:]
        trailing_period = '' if s[-1] in '.!?' else '.'
        return initial_upper + trailing_period

    def __init__(self, **kwargs):
        self._short_summary = ''
        self._long_summary = ''
        super().__init__(**kwargs)

    @property
    def short_summary(self):
        return self._short_summary

    @short_summary.setter
    def short_summary(self, value):
        self._short_summary = self._normalize_text(value)

    @property
    def long_summary(self):
        return self._long_summary

    @long_summary.setter
    def long_summary(self, value):
        self._long_summary = self._normalize_text(value)


# pylint: disable=too-many-instance-attributes
class HelpFile(HelpObject):

    @staticmethod
    def _load_help_file_from_string(text):
        import yaml
        try:
            return yaml.safe_load(text) if text else None
        except Exception:  # pylint: disable=broad-except
            return text

    def __init__(self, help_ctx, delimiters):  # pylint: disable=too-many-statements
        super().__init__()
        self.help_ctx = help_ctx
        self.delimiters = delimiters
        self.name = delimiters.split()[-1] if delimiters else delimiters
        self.command = delimiters
        self.type = ''
        self.short_summary = ''
        self.long_summary = ''
        self.examples = []
        self.deprecate_info = None
        self.preview_info = None
        self.experimental_info = None

        direct_deprecate_info = resolve_deprecate_info(help_ctx.cli_ctx, delimiters)
        if direct_deprecate_info:
            self.deprecate_info = direct_deprecate_info

        # search for implicit deprecation
        path_comps = delimiters.split()[:-1]
        implicit_deprecate_info = None
        while path_comps and not implicit_deprecate_info:
            implicit_deprecate_info = resolve_deprecate_info(help_ctx.cli_ctx, ' '.join(path_comps))
            del path_comps[-1]

        if implicit_deprecate_info:
            deprecate_kwargs = implicit_deprecate_info.__dict__.copy()
            deprecate_kwargs['object_type'] = 'command' if delimiters in \
                help_ctx.cli_ctx.invocation.commands_loader.command_table else 'command group'
            del deprecate_kwargs['_get_tag']
            del deprecate_kwargs['_get_message']
            self.deprecate_info = ImplicitDeprecated(cli_ctx=help_ctx.cli_ctx, **deprecate_kwargs)

        # resolve preview info
        direct_preview_info = resolve_preview_info(help_ctx.cli_ctx, delimiters)
        if direct_preview_info:
            self.preview_info = direct_preview_info

        # search for implicit preview
        path_comps = delimiters.split()[:-1]
        implicit_preview_info = None
        while path_comps and not implicit_preview_info:
            implicit_preview_info = resolve_preview_info(help_ctx.cli_ctx, ' '.join(path_comps))
            del path_comps[-1]

        if implicit_preview_info:
            preview_kwargs = implicit_preview_info.__dict__.copy()
            if delimiters in help_ctx.cli_ctx.invocation.commands_loader.command_table:
                preview_kwargs['object_type'] = 'command'
            else:
                preview_kwargs['object_type'] = 'command group'
            self.preview_info = ImplicitPreviewItem(cli_ctx=help_ctx.cli_ctx, **preview_kwargs)

        # resolve experimental info
        direct_experimental_info = resolve_experimental_info(help_ctx.cli_ctx, delimiters)
        if direct_experimental_info:
            self.experimental_info = direct_experimental_info

        # search for implicit experimental
        path_comps = delimiters.split()[:-1]
        implicit_experimental_info = None
        while path_comps and not implicit_experimental_info:
            implicit_experimental_info = resolve_experimental_info(help_ctx.cli_ctx, ' '.join(path_comps))
            del path_comps[-1]

        if implicit_experimental_info:
            experimental_kwargs = implicit_experimental_info.__dict__.copy()
            if delimiters in help_ctx.cli_ctx.invocation.commands_loader.command_table:
                experimental_kwargs['object_type'] = 'command'
            else:
                experimental_kwargs['object_type'] = 'command group'
            self.experimental_info = ImplicitExperimentalItem(cli_ctx=help_ctx.cli_ctx, **experimental_kwargs)

    def load(self, options):
        description = getattr(options, 'description', None)
        try:
            self.short_summary = description[:description.index('.')]
            long_summary = description[description.index('.') + 1:].lstrip()
            self.long_summary = ' '.join(long_summary.splitlines())
        except (ValueError, AttributeError):
            self.short_summary = description

        file_data = (self._load_help_file_from_string(options.help_file)
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
            self.examples = [HelpExample(d) for d in data['examples']]


class GroupHelpFile(HelpFile):

    def __init__(self, help_ctx, delimiters, parser):

        super().__init__(help_ctx, delimiters)
        self.type = 'group'

        self.children = []
        if getattr(parser, 'choices', None):
            for options in parser.choices.values():
                delimiters = ' '.join(options.prog.split()[1:])
                child = (help_ctx.group_help_cls(self.help_ctx, delimiters, options) if options.is_group()
                         else help_ctx.help_cls(self.help_ctx, delimiters))
                child.load(options)
                try:
                    # don't hide implicitly deprecated commands
                    if not isinstance(child.deprecate_info, ImplicitDeprecated) and \
                            not child.deprecate_info.show_in_help():
                        continue
                except AttributeError:
                    pass
                self.children.append(child)


class CommandHelpFile(HelpFile):

    def __init__(self, help_ctx, delimiters, parser):

        super().__init__(help_ctx, delimiters)
        self.type = 'command'

        self.parameters = []

        for action in [a for a in parser._actions if a.help != argparse.SUPPRESS]:  # pylint: disable=protected-access
            if action.option_strings:
                self._add_parameter_help(action)
            else:
                # use metavar for positional parameters
                param_kwargs = {
                    'name_source': [action.metavar or action.dest],
                    'deprecate_info': getattr(action, 'deprecate_info', None),
                    'preview_info': getattr(action, 'preview_info', None),
                    'experimental_info': getattr(action, 'experimental_info', None),
                    'description': action.help,
                    'choices': action.choices,
                    'required': False,
                    'default': None,
                    'group_name': 'Positional'
                }
                self.parameters.append(HelpParameter(**param_kwargs))

        help_param = next(p for p in self.parameters if p.name == '--help -h')
        help_param.group_name = 'Global Arguments'

    def _add_parameter_help(self, param):
        param_kwargs = {
            'description': param.help,
            'choices': param.choices,
            'required': param.required,
            'default': param.default,
            'group_name': param.container.description
        }
        normal_options = []
        deprecated_options = []
        for item in param.option_strings:
            deprecated_info = getattr(item, 'deprecate_info', None)
            if deprecated_info:
                if deprecated_info.show_in_help():
                    deprecated_options.append(item)
            else:
                normal_options.append(item)
        if deprecated_options:
            param_kwargs.update({
                'name_source': deprecated_options,
                'deprecate_info': deprecated_options[0].deprecate_info
            })
            self.parameters.append(HelpParameter(**param_kwargs))
        param_kwargs.update({
            'name_source': normal_options,
            'deprecate_info': getattr(param, 'deprecate_info', None),
            'preview_info': getattr(param, 'preview_info', None),
            'experimental_info': getattr(param, 'experimental_info', None),
            'default_value_source': getattr(param, 'default_value_source', None)
        })
        self.parameters.append(HelpParameter(**param_kwargs))

    def _load_from_data(self, data):
        super()._load_from_data(data)

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


class HelpParameter(HelpObject):  # pylint: disable=too-many-instance-attributes

    def __init__(self, name_source, description, required, choices=None, default=None, group_name=None,
                 deprecate_info=None, preview_info=None, experimental_info=None, default_value_source=None):
        super().__init__()
        self.name_source = name_source
        self.name = ' '.join(sorted(name_source))
        self.required = required
        self.type = 'string'
        self.short_summary = description
        self.long_summary = ''
        self.value_sources = []
        self.choices = choices
        self.default = default
        self.group_name = group_name
        self.deprecate_info = deprecate_info
        self.preview_info = preview_info
        self.experimental_info = experimental_info
        self.default_value_source = default_value_source

    def update_from_data(self, data):
        if self.name != data.get('name'):
            raise HelpAuthoringException("mismatched name {} vs. {}"
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


class CLIHelp(object):

    def _print_header(self, cli_name, help_file):
        indent = 0
        _print_indent('')
        _print_indent('Command' if help_file.type == 'command' else 'Group', indent)

        indent += 1
        LINE_FORMAT = '{cli}{name}{separator}{summary}'
        line = LINE_FORMAT.format(
            cli=cli_name,
            name=' ' + help_file.command if help_file.command else '',
            separator=FIRST_LINE_PREFIX if help_file.short_summary else '',
            summary=help_file.short_summary if help_file.short_summary else ''
        )
        _print_indent(line, indent, width=self.textwrap_width)

        def _build_long_summary(item):
            lines = []
            if item.long_summary:
                lines.append(item.long_summary)
            if item.deprecate_info:
                lines.append(str(item.deprecate_info.message))
            if item.preview_info:
                lines.append(str(item.preview_info.message))
            if item.experimental_info:
                lines.append(str(item.experimental_info.message))
            return '\n'.join(lines)

        indent += 1
        long_sum = _build_long_summary(help_file)
        _print_indent(long_sum, indent, width=self.textwrap_width)

    def _print_groups(self, help_file):

        LINE_FORMAT = '{name}{padding}{tags}{separator}{summary}'
        indent = 1

        self.max_line_len = 0

        def _build_tags_string(item):

            preview_info = getattr(item, 'preview_info', None)
            preview = preview_info.tag if preview_info else ''

            experimental_info = getattr(item, 'experimental_info', None)
            experimental = experimental_info.tag if experimental_info else ''

            deprecate_info = getattr(item, 'deprecate_info', None)
            deprecated = deprecate_info.tag if deprecate_info else ''

            required = REQUIRED_TAG if getattr(item, 'required', None) else ''
            tags = ' '.join([x for x in [str(deprecated), str(preview), str(experimental), required] if x])
            tags_len = sum([
                len(deprecated),
                len(preview),
                len(experimental),
                len(required),
                tags.count(' ')
            ])
            if not tags_len:
                tags = ''
            return tags, tags_len

        def _layout_items(items):

            layouts = []
            for c in sorted(items, key=lambda h: h.name):
                tags, tags_len = _build_tags_string(c)
                line_len = _get_line_len(c.name, tags_len)
                layout = {
                    'name': c.name,
                    'tags': tags,
                    'separator': FIRST_LINE_PREFIX if c.short_summary else '',
                    'summary': c.short_summary or '',
                    'line_len': line_len
                }
                layout['summary'] = layout['summary'].replace('\n', ' ')
                if line_len > self.max_line_len:
                    self.max_line_len = line_len
                layouts.append(layout)
            return layouts

        def _print_items(layouts):
            for layout in layouts:
                layout['padding'] = ' ' * _get_padding_len(self.max_line_len, layout)
                _print_indent(
                    LINE_FORMAT.format(**layout),
                    indent,
                    _get_hanging_indent(self.max_line_len, indent),
                    width=self.textwrap_width,
                )
            _print_indent('')

        groups = [c for c in help_file.children if isinstance(c, self.group_help_cls)]
        group_layouts = _layout_items(groups)

        commands = [c for c in help_file.children if c not in groups]
        command_layouts = _layout_items(commands)

        if groups:
            _print_indent('Subgroups:')
            _print_items(group_layouts)

        if commands:
            _print_indent('Commands:')
            _print_items(command_layouts)

    @staticmethod
    def _get_choices_defaults_sources_str(p):
        choice_str = '  Allowed values: {}.'.format(', '.join(sorted([str(x) for x in p.choices]))) \
            if p.choices else ''
        default_str = '  Default: {}.'.format(p.default) \
            if p.default and p.default != argparse.SUPPRESS else ''
        value_sources_str = '  Values from: {}.'.format(', '.join(p.value_sources)) \
            if p.value_sources else ''
        return '{}{}{}'.format(choice_str, default_str, value_sources_str)

    @staticmethod
    def print_description_list(help_files):
        indent = 1
        max_length = max(len(f.name) for f in help_files) if help_files else 0
        for help_file in sorted(help_files, key=lambda h: h.name):
            column_indent = max_length - len(help_file.name)
            _print_indent('{}{}{}'.format(help_file.name,
                                          ' ' * column_indent,
                                          FIRST_LINE_PREFIX + help_file.short_summary
                                          if help_file.short_summary
                                          else ''),
                          indent,
                          _get_hanging_indent(max_length, indent))

    @staticmethod
    def _print_examples(help_file):
        indent = 0
        _print_indent('Examples', indent)
        for e in help_file.examples:
            indent = 1
            _print_indent('{0}'.format(e.name), indent)
            indent = 2
            _print_indent('{0}'.format(e.text), indent)
            print('')

    def _print_arguments(self, help_file):  # pylint: disable=too-many-statements

        LINE_FORMAT = '{name}{padding}{tags}{separator}{short_summary}'
        indent = 1
        self.max_line_len = 0

        if not help_file.parameters:
            _print_indent('None', indent)
            _print_indent('')
            return None

        def _build_tags_string(item):

            preview_info = getattr(item, 'preview_info', None)
            preview = preview_info.tag if preview_info else ''

            experimental_info = getattr(item, 'experimental_info', None)
            experimental = experimental_info.tag if experimental_info else ''

            deprecate_info = getattr(item, 'deprecate_info', None)
            deprecated = deprecate_info.tag if deprecate_info else ''

            required = REQUIRED_TAG if getattr(item, 'required', None) else ''
            tags = ' '.join([x for x in [str(deprecated), str(preview), str(experimental), required] if x])
            tags_len = sum([
                len(deprecated),
                len(preview),
                len(experimental),
                len(required),
                tags.count(' ')
            ])
            if not tags_len:
                tags = ''
            return tags, tags_len

        def _layout_items(items):

            layouts = []
            for c in sorted(items, key=_get_parameter_key):

                deprecate_info = getattr(c, 'deprecate_info', None)
                if deprecate_info and not deprecate_info.show_in_help():
                    continue

                tags, tags_len = _build_tags_string(c)
                short_summary = _build_short_summary(c)
                long_summary = _build_long_summary(c)
                line_len = _get_line_len(c.name, tags_len)
                layout = {
                    'name': c.name,
                    'tags': tags,
                    'separator': FIRST_LINE_PREFIX if short_summary else '',
                    'short_summary': short_summary,
                    'long_summary': long_summary,
                    'group_name': c.group_name,
                    'line_len': line_len
                }
                if line_len > self.max_line_len:
                    self.max_line_len = line_len
                layouts.append(layout)
            return layouts

        def _print_items(layouts):
            last_group_name = ''

            for layout in layouts:
                indent = 1
                if layout['group_name'] != last_group_name:
                    if layout['group_name']:
                        print('')
                        print(layout['group_name'])
                    last_group_name = layout['group_name']

                layout['padding'] = ' ' * _get_padding_len(self.max_line_len, layout)
                _print_indent(
                    LINE_FORMAT.format(**layout),
                    indent,
                    _get_hanging_indent(self.max_line_len, indent),
                    width=self.textwrap_width,
                )

                indent = 2
                long_summary = layout.get('long_summary', None)
                if long_summary:
                    _print_indent(long_summary, indent, width=self.textwrap_width)

            _print_indent('')

        def _build_short_summary(item):
            short_summary = item.short_summary
            possible_values_index = short_summary.find(' Possible values include')
            short_summary = short_summary[0:possible_values_index
                                          if possible_values_index >= 0 else len(short_summary)]
            short_summary += self._get_choices_defaults_sources_str(item)
            short_summary = short_summary.strip()
            return short_summary

        def _build_long_summary(item):
            lines = []
            if item.long_summary:
                lines.append(item.long_summary)
            deprecate_info = getattr(item, 'deprecate_info', None)
            if deprecate_info:
                lines.append(str(item.deprecate_info.message))
            preview_info = getattr(item, 'preview_info', None)
            if preview_info:
                lines.append(str(item.preview_info.message))
            experimental_info = getattr(item, 'experimental_info', None)
            if experimental_info:
                lines.append(str(item.experimental_info.message))
            return ' '.join(lines)

        group_registry = ArgumentGroupRegistry([p.group_name for p in help_file.parameters if p.group_name])

        def _get_parameter_key(parameter):
            return '{}{}{}'.format(group_registry.get_group_priority(parameter.group_name),
                                   str(not parameter.required),
                                   parameter.name)

        parameter_layouts = _layout_items(help_file.parameters)
        _print_items(parameter_layouts)

        return indent

    def _print_detailed_help(self, cli_name, help_file):
        self._print_header(cli_name, help_file)
        if help_file.long_summary or getattr(help_file, 'deprecate_info', None):
            _print_indent('')

        # fix incorrect groupings instead of crashing
        if help_file.type == 'command' and not isinstance(help_file, CommandHelpFile):
            help_file.type = 'group'
            logger.info("'%s' is labeled a command but is actually a group!", help_file.delimiters)
        elif help_file.type == 'group' and not isinstance(help_file, GroupHelpFile):
            help_file.type = 'command'
            logger.info("'%s' is labeled a group but is actually a command!", help_file.delimiters)

        if help_file.type == 'command':
            _print_indent('Arguments')
            self._print_arguments(help_file)
        elif help_file.type == 'group':
            self._print_groups(help_file)
        if help_file.examples:
            self._print_examples(help_file)

    def __init__(self, cli_ctx=None, privacy_statement='', welcome_message='',
                 group_help_cls=GroupHelpFile, command_help_cls=CommandHelpFile,
                 help_cls=HelpFile, textwrap_width=100):
        """ Manages the generation and production of help in the CLI

        :param cli_ctx: CLI Context
        :type cli_ctx: knack.cli.CLI
        :param privacy_statement: Privacy statement for the CLI
        :type privacy_statement: str
        :param welcome_message: A welcome message for the CLI
        :type welcome_message: str
        :param group_help_cls: Class to use for formatting group help.
        :type group_help_cls: HelpFile
        :param command_help_cls: Class to use for formatting command help.
        :type command_help_cls: HelpFile
        :param command_help_cls: Class to use for formatting generic help.
        :type command_help_cls: HelpFile
        :param textwrap_width: Line length to which text will be wrapped.
        :type textwrap_width: int
        """
        from .cli import CLI
        if cli_ctx is not None and not isinstance(cli_ctx, CLI):
            raise CtxTypeError(cli_ctx)
        self.cli_ctx = cli_ctx
        self.privacy_statement = privacy_statement
        self.welcome_message = welcome_message
        self.max_line_len = 0
        self.group_help_cls = group_help_cls
        self.command_help_cls = command_help_cls
        self.help_cls = help_cls
        self.textwrap_width = textwrap_width

    def show_privacy_statement(self):
        ran_before = self.cli_ctx.config.getboolean('core', 'first_run', fallback=False)
        if not ran_before:
            if self.privacy_statement:
                print(self.privacy_statement, file=self.cli_ctx.out_file)
            self.cli_ctx.config.set_value('core', 'first_run', 'yes')

    def show_welcome_message(self):
        _print_indent(self.welcome_message, width=self.textwrap_width)

    def show_welcome(self, parser):
        self.show_privacy_statement()
        self.show_welcome_message()
        help_file = self.group_help_cls(self, '', parser)
        self.print_description_list(help_file.children)

    def show_help(self, cli_name, nouns, parser, is_group):
        delimiters = ' '.join(nouns)
        help_file = self.command_help_cls(self, delimiters, parser) if not is_group \
            else self.group_help_cls(self, delimiters, parser)
        help_file.load(parser)
        if not nouns:
            help_file.command = ''
        self._print_detailed_help(cli_name, help_file)
