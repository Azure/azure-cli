from __future__ import print_function
import inspect
import sys
import textwrap
import yaml

from ._locale import L
from ._help_files import _load_help_file

__all__ = ['print_detailed_help', 'print_welcome_message', 'GroupHelpFile', 'CommandHelpFile']

_out = sys.stdout

def show_welcome(parser):
    print_welcome_message()

    help_file = GroupHelpFile('', parser)
    print_description_list(help_file.children)

def print_welcome_message():
    _print_indent(L(r"""
     /\                        
    /  \    _____   _ _ __ ___ 
   / /\ \  |_  / | | | \'__/ _ \
  / ____ \  / /| |_| | | |  __/
 /_/    \_\/___|\__,_|_|  \___|
"""))
    _print_indent(L('\nWelcome to the cool new Azure CLI!\n\nHere are the base commands:\n'))

def print_detailed_help(help_file, out=sys.stdout): #pylint: disable=unused-argument
    global _out #pylint: disable=global-statement
    _out = out
    _print_header(help_file)

    _print_indent(L('Arguments') if help_file.type == 'command' else L('Sub-Commands'))

    if help_file.type == 'command':
        print_arguments(help_file)
    elif help_file.type == 'group':
        _print_groups(help_file)

    if len(help_file.examples) > 0:
        _print_examples(help_file)

def print_description_list(help_files, out=sys.stdout):
    global _out #pylint: disable=global-statement
    _out = out

    indent = 1
    max_name_length = max(len(f.name) for f in help_files) if help_files else 0
    for help_file in sorted(help_files, key=lambda h: h.name):
        _print_indent('{0}{1}{2}'.format(help_file.name,
                                         _get_column_indent(help_file.name, max_name_length),
                                         ': ' + help_file.short_summary \
                                             if help_file.short_summary \
                                             else ''),
                      indent)

def print_arguments(help_file):
    indent = 1
    if not help_file.parameters:
        _print_indent('None', indent)
        _print_indent('')
        return

    if len(help_file.parameters) == 0:
        _print_indent('none', indent)
    required_tag = L(' [Required]')
    max_name_length = max(len(p.name) + 11 if p.required else 0 for p in help_file.parameters)
    for p in help_file.parameters:
        indent = 1
        required_text = required_tag if p.required else ''
        _print_indent('{0}{1}{2}{3}'.format(p.name,
                                            required_text,
                                            _get_column_indent(p.name + required_text,
                                                               max_name_length),
                                            ': ' + p.short_summary if p.short_summary else ''),
                      indent,
                      max_name_length + indent*4 + 2)

        indent = 2
        if p.long_summary:
            _print_indent('{0}'.format(p.long_summary.rstrip()), indent)

        if p.value_sources:
            _print_indent('')
            _print_indent(L("Values from: {0}").format(', '.join(p.value_sources)), indent)
        _print_indent('')
    return indent

def _print_header(help_file):
    indent = 0
    _print_indent('')
    _print_indent(L('Command') if help_file.type == 'command' else L('Group'), indent)
    _print_indent('{0}{1}'.format(help_file.command,
                                  ': ' + help_file.short_summary
                                  if help_file.short_summary
                                  else ''),
                  indent)

    indent = 1
    if help_file.long_summary:
        _print_indent('{0}'.format(help_file.long_summary.rstrip()), indent)
    _print_indent('')

def _print_groups(help_file):
    indent = 1
    for c in help_file.children:
        _print_indent('{0}{1}'.format(c.name,
                                      ': ' + c.short_summary if c.short_summary else ''),
                      indent)
    _print_indent('')

def _print_examples(help_file):
    indent = 0
    _print_indent(L('Examples'), indent)

    for e in help_file.examples:
        indent = 1
        _print_indent('{0}'.format(e.name), indent)

        indent = 2
        _print_indent('{0}'.format(e.text), indent)


class HelpFile(object): #pylint: disable=too-few-public-methods
    def __init__(self, delimiters):
        self.delimiters = delimiters
        self.name = delimiters.split('.')[-1]
        self.command = delimiters.replace('.', ' ')
        self.type = ''
        self.short_summary = ''
        self.long_summary = ''
        self.examples = ''

    def load(self, options):
        self.short_summary = options.description
        file_data = _load_help_file_from_string(inspect.getdoc(options._defaults.get('func')))
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


class GroupHelpFile(HelpFile): #pylint: disable=too-few-public-methods
    def __init__(self, delimiters, parser):
        super(GroupHelpFile, self).__init__(delimiters)
        self.type = 'group'

        self.children = []
        for cmd, options in parser.choices.items():
            child = HelpFile(cmd)
            child.load(options)
            self.children.append(child)

class CommandHelpFile(HelpFile): #pylint: disable=too-few-public-methods
    def __init__(self, delimiters, argdoc):
        super(CommandHelpFile, self).__init__(delimiters)
        self.type = 'command'
        self.parameters = [HelpParameter(a, d, r) for a, d, r in argdoc]

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

        extra_param = next((p for p in data['parameters']
                            if p['name'] not in [lp.name for lp in loaded_params]),
                           None)
        if extra_param:
            raise HelpAuthoringException('Extra help param {0}'.format(extra_param['name']))
        self.parameters = loaded_params


class HelpParameter(object): #pylint: disable=too-few-public-methods
    def __init__(self, param_name, description, required):
        self.name = param_name
        self.required = required
        self.type = 'string'
        self.short_summary = description
        self.long_summary = ''
        self.value_sources = []

    def update_from_data(self, data):
        if self.name != data.get('name'):
            raise HelpAuthoringException("mismatched name {0} vs. {1}"
                                         .format(self.name,
                                                 data.get('name')))

        if self.required != data.get('required', False):
            raise HelpAuthoringException("mismatched required {0} vs. {1}, {2}"
                                         .format(self.required,
                                                 data.get('required'),
                                                 data.get('name')))

        self.type = data.get('type')
        self.short_summary = data.get('short-summary')
        self.long_summary = data.get('long-summary')
        self.value_sources = data.get('populator-commands')


class HelpExample(object): #pylint: disable=too-few-public-methods
    def __init__(self, _data):
        self.name = _data['name']
        self.text = _data['text']

def _list_starts_with(container_list, contained_list):
    if len(contained_list) > len(container_list):
        return False
    return container_list[:len(contained_list)] == contained_list

def _print_indent(s, indent=0, subsequent_spaces=-1):
    tw = textwrap.TextWrapper(initial_indent='    '*indent,
                              subsequent_indent=('    '*indent
                                                 if subsequent_spaces == -1
                                                 else ' '*subsequent_spaces),
                              replace_whitespace=False,
                              width=100)
    paragraphs = s.split('\n')
    for p in paragraphs:
        print(tw.fill(p), file=_out)

def _get_column_indent(text, max_name_length):
    return ' '*(max_name_length - len(text))

def _load_help_file_from_string(text):
    try:
        return yaml.load(text) if text else None
    except Exception: #pylint: disable=broad-except
        return text

class HelpAuthoringException(Exception):
    pass
