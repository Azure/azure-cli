# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import json
from docutils import nodes
from docutils.statemachine import ViewList
from sphinx.util.compat import Directive
from sphinx.util.nodes import nested_parse_with_titles

from azure.cli.core.application import Application, Configuration
import azure.cli.core._help as _help

app = Application(Configuration())
for cmd in app.configuration.get_command_table():
    try:
        app.execute(cmd.split() + ['-h'])
    except:
        pass

class AzHelpGenDirective(Directive):
    def make_rst(self):
        INDENT = '   '
        DOUBLEINDENT = INDENT * 2
        parser_dict = {}
        _store_parsers(app.parser, parser_dict)
        doc_source_map = _load_doc_source_map()

        help_files = []
        for cmd, parser in parser_dict.items():
            help_file = _help.GroupHelpFile(cmd, parser) if _is_group(parser) else _help.CommandHelpFile(cmd, parser)
            try:
                help_file.load(parser)
            except Exception as ex:
                print(ex)
            help_files.append(help_file)
        help_files = sorted(help_files, key=lambda x: x.command)

        for help_file in help_files:
            is_command = isinstance(help_file, _help.CommandHelpFile)
            yield '.. cli{}:: {}'.format('command' if is_command else 'group', help_file.command if help_file.command else 'az') #it is top level group az if command is empty
            yield ''
            yield '{}:summary: {}'.format(INDENT, help_file.short_summary)
            yield '{}:description: {}'.format(INDENT, help_file.long_summary)
            if not is_command:
                top_group_name = help_file.command.split()[0] if help_file.command else 'az' 
                yield '{}:docsource: {}'.format(INDENT, doc_source_map[top_group_name] if top_group_name in doc_source_map else '')
            else:
                top_command_name = help_file.command.split()[0] if help_file.command else ''
                if top_command_name in doc_source_map:
                    yield '{}:docsource: {}'.format(INDENT, doc_source_map[top_command_name])
            yield ''

            if is_command and help_file.parameters:
               group_registry = _help.ArgumentGroupRegistry(
                  [p.group_name for p in help_file.parameters if p.group_name]) 

               for arg in sorted(help_file.parameters,
                                key=lambda p: group_registry.get_group_priority(p.group_name)
                                + str(not p.required) + p.name):
                  yield '{}.. cliarg:: {}'.format(INDENT, arg.name)
                  yield ''
                  yield '{}:required: {}'.format(DOUBLEINDENT, arg.required)
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
                     yield '{}:default: {}'.format(DOUBLEINDENT, arg.default)
                  if arg.value_sources:
                     yield '{}:source: {}'.format(DOUBLEINDENT, ', '.join(arg.value_sources))
                  yield ''
            yield ''
            if len(help_file.examples) > 0:
               for e in help_file.examples:
                  yield '{}.. cliexample:: {}'.format(INDENT, e.name)
                  yield ''
                  yield DOUBLEINDENT + e.text
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

def _store_parsers(parser, d):
    for s in parser.subparsers.values():
        d[_get_parser_name(s)] = s
        if _is_group(s):
            for c in s.choices.values():
                d[_get_parser_name(c)] = c
                _store_parsers(c, d)

def _load_doc_source_map():
    with open('azhelpgen/doc_source_map.json') as open_file:
        return json.load(open_file)

def _is_group(parser):
    return getattr(parser, '_subparsers', None) is not None \
        or getattr(parser, 'choices', None) is not None

def _get_parser_name(s):
    return (s._prog_prefix if hasattr(s, '_prog_prefix') else s.prog)[3:]
