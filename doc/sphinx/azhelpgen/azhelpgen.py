# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import json
from unittest.mock import patch
from os.path import expanduser
from docutils import nodes
from docutils.statemachine import ViewList
try:
    # Deprecated in 1.6 and removed in 1.7
    from sphinx.util.compat import Directive
except ImportError:
    from docutils.parsers.rst import Directive  # pylint: disable=import-error
from sphinx.util.nodes import nested_parse_with_titles


from azure.cli.core import MainCommandsLoader, AzCli
from azure.cli.core.commands import AzCliCommandInvoker
from azure.cli.core.parser import AzCliCommandParser
from azure.cli.core.file_util import create_invoker_and_load_cmds_and_args, get_all_help
from azure.cli.core._help import AzCliHelp, CliCommandHelpFile, ArgumentGroupRegistry

USER_HOME = expanduser('~')


class AzHelpGenDirective(Directive):
    def make_rst(self):
        INDENT = '   '
        DOUBLEINDENT = INDENT * 2

        az_cli = AzCli(cli_name='az',
               commands_loader_cls=MainCommandsLoader,
               invocation_cls=AzCliCommandInvoker,
               parser_cls=AzCliCommandParser,
               help_cls=AzCliHelp)
        with patch('getpass.getuser', return_value='your_system_user_login_name'):
            create_invoker_and_load_cmds_and_args(az_cli)
        help_files = get_all_help(az_cli)

        doc_source_map = _load_doc_source_map()

        for help_file in help_files:
            is_command = isinstance(help_file, CliCommandHelpFile)
            yield '.. cli{}:: {}'.format('command' if is_command else 'group', help_file.command if help_file.command else 'az') #it is top level group az if command is empty
            yield ''
            yield '{}:summary: {}'.format(INDENT, help_file.short_summary)
            yield '{}:description: {}'.format(INDENT, help_file.long_summary)
            if help_file.deprecate_info:
                yield '{}:deprecated: {}'.format(INDENT, help_file.deprecate_info._get_message(help_file.deprecate_info))
            if not is_command:
                top_group_name = help_file.command.split()[0] if help_file.command else 'az'
                yield '{}:docsource: {}'.format(INDENT, doc_source_map[top_group_name] if top_group_name in doc_source_map else '')
            else:
                top_command_name = help_file.command.split()[0] if help_file.command else ''
                if top_command_name in doc_source_map:
                    yield '{}:docsource: {}'.format(INDENT, doc_source_map[top_command_name])
            yield ''

            if is_command and help_file.parameters:
               group_registry = ArgumentGroupRegistry(
                  [p.group_name for p in help_file.parameters if p.group_name])

               for arg in sorted(help_file.parameters,
                                key=lambda p: group_registry.get_group_priority(p.group_name)
                                + str(not p.required) + p.name):
                    yield '{}.. cliarg:: {}'.format(INDENT, arg.name)
                    yield ''
                    yield '{}:required: {}'.format(DOUBLEINDENT, arg.required)
                    if arg.deprecate_info:
                        yield '{}:deprecated: {}'.format(DOUBLEINDENT, arg.deprecate_info._get_message(arg.deprecate_info))
                    short_summary = arg.short_summary or ''
                    possible_values_index = short_summary.find(' Possible values include')
                    short_summary = short_summary[0:possible_values_index
                                                    if possible_values_index >= 0 else len(short_summary)]
                    short_summary = short_summary.strip()
                    yield '{}:summary: {}'.format(DOUBLEINDENT, short_summary)
                    yield '{}:description: {}'.format(DOUBLEINDENT, arg.long_summary)
                    if arg.choices:
                        yield '{}:values: {}'.format(DOUBLEINDENT, ', '.join(sorted([str(x) for x in arg.choices])))
                    if arg.default and arg.default != argparse.SUPPRESS:
                        try:
                            if arg.default.startswith(USER_HOME):
                                arg.default = arg.default.replace(USER_HOME, '~').replace('\\', '/')
                        except Exception:
                            pass
                        try:
                            arg.default = arg.default.replace("\\", "\\\\")
                        except Exception:
                            pass
                        yield '{}:default: {}'.format(DOUBLEINDENT, arg.default)
                    if arg.value_sources:
                        yield '{}:source: {}'.format(DOUBLEINDENT, ', '.join(_get_populator_commands(arg)))
                    yield ''
            yield ''
            if len(help_file.examples) > 0:
               for e in help_file.examples:
                  yield '{}.. cliexample:: {}'.format(INDENT, e.short_summary)
                  yield ''
                  yield DOUBLEINDENT + e.command.replace("\\", "\\\\")
                  yield ''

    def run(self):
        node = nodes.section()
        node.document = self.state.document
        result = ViewList()
        for line in self.make_rst():
            result.append(line, '<azhelpgen>')

        nested_parse_with_titles(self.state, result, node)
        return node.children

def setup(app):
    app.add_directive('azhelpgen', AzHelpGenDirective)


def _store_parsers(parser, parser_keys, parser_values, sub_parser_keys, sub_parser_values):
    for s in parser.subparsers.values():
        parser_keys.append(_get_parser_name(s))
        parser_values.append(s)
        if _is_group(s):
            for c in s.choices.values():
                sub_parser_keys.append(_get_parser_name(c))
                sub_parser_values.append(c)
                _store_parsers(c, parser_keys, parser_values, sub_parser_keys, sub_parser_values)

def _load_doc_source_map():
    with open('azhelpgen/doc_source_map.json') as open_file:
        return json.load(open_file)

def _is_group(parser):
    return getattr(parser, '_subparsers', None) is not None \
        or getattr(parser, 'choices', None) is not None

def _get_parser_name(s):
    return (s._prog_prefix if hasattr(s, '_prog_prefix') else s.prog)[3:]


def _get_populator_commands(param):
    commands = []
    for value_source in param.value_sources:
        try:
            commands.append(value_source["link"]["command"])
        except KeyError:
            continue
    return commands
