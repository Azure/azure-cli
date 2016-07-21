#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import argparse
from docutils import nodes
from docutils.statemachine import ViewList
from sphinx.util.compat import Directive
from sphinx.util.nodes import nested_parse_with_titles

from azure.cli.application import Application, Configuration
import azure.cli._help as _help

app = Application(Configuration([]))
try:
    app.execute(['-h'])
except:
    pass

class AzHelpGenDirective(Directive):
    def make_rst(self):
        INDENT = ''
        parser_dict = {}
        _store_parsers(app.parser, parser_dict)
        parser_dict.pop('')

        help_files = []
        for cmd, parser in parser_dict.items():
            help_file = _help.GroupHelpFile(cmd, parser) if _is_group(parser) else _help.CommandHelpFile(cmd, parser) 
            help_file.load(parser)
            help_files.append(help_file)
        help_files = sorted(help_files, key=lambda x: x.command)

        for help_file in help_files:
            title= '{}: {}'.format('Command' if isinstance(help_file, _help.CommandHelpFile)
                                 else 'Group', help_file.command)
            yield title
            yield '=' * len(title)
            yield help_file.short_summary
            yield ''
            yield help_file.long_summary
            yield ''
            if isinstance(help_file, _help.CommandHelpFile):
                yield '**Arguments**'
                yield ''
                if not help_file.parameters:
                    yield INDENT + 'None'
                    yield ''
                else:
                    for arg in sorted(help_file.parameters,
                                      key=lambda p: str(p.group_name or 'A')
                                      + str(not p.required) + p.name):
                        yield '{} {}'.format(arg.name, '[Required]' if arg.required else '')
                        yield ''
                        yield ''

                        short_summary = arg.short_summary or ''
                        possible_values_index = short_summary.find(' Possible values include')
                        short_summary = short_summary[0:possible_values_index
                                                      if possible_values_index >= 0 else len(short_summary)]
                        short_summary += _get_choices_defaults_str(arg)
                        short_summary = short_summary.strip()
                        yield INDENT + short_summary
                        yield ''

                        yield INDENT + arg.long_summary
                        yield ''

                        if arg.value_sources:
                            yield "Values from: {0}.".format(', '.join(arg.value_sources))
                            yield ''
            yield ''

            if len(help_file.examples) > 0:
                yield '**Examples**'
                yield ''
                for e in help_file.examples:
                    yield '--' + e.name
                    yield ''
                    yield e.text
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

def _get_choices_defaults_str(p):
    choice_str = '  Allowed values: {0}.'.format(', '.join(p.choices)) \
        if p.choices else ''
    default_str = '  Default: {0}.'.format(p.default) \
        if p.default and p.default != argparse.SUPPRESS else ''
    return '{0}{1}'.format(choice_str, default_str)

def _store_parsers(parser, d):
    for s in parser.subparsers.values():
        d[_get_parser_name(s)] = s
        if _is_group(s):
            for c in s.choices.values():
                d[_get_parser_name(c)] = c
                _store_parsers(c, d)

def _is_group(parser):
    return getattr(parser, '_subparsers', None) is not None \
        or getattr(parser, 'choices', None) is not None

def _get_parser_name(s):
    return (s._prog_prefix if hasattr(s, '_prog_prefix') else s.prog)[3:]
