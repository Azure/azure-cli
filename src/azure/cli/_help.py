import sys
import textwrap
from collections import OrderedDict

from yaml import load, dump

from ._output import OutputProducer, TableOutput, format_table, format_list, format_unordered_list

def print_detailed_help(help_file, out=sys.stdout):  # TODO: wire up out to print statements
    indent = 0
    print('')
    _printIndent('{0}{1}'.format(help_file.command, ': ' + help_file.short_summary if help_file.short_summary else ''), indent)

    indent = 1
    _printIndent('{0}'.format(help_file.long_summary), indent)
    print('')

    indent = 0
    _printIndent('Arguments' if help_file.type == 'command' else 'Sub-Commands', indent) 

    if help_file.type == 'command':
        if len(help_file.parameters) == 0:
            _printIndent('none', indent)
        for p in help_file.parameters:
            indent = 1
            _printIndent('{0}{1}'.format(p.name, ': ' + p.short_summary if p.short_summary else ''), indent)

            indent = 2
            _printIndent('{0}'.format(p.long_summary), indent)

            if p.value_sources:
                _printIndent("Values from: {0}".format(', '.join(p.value_sources)), indent)
            print('')

    if help_file.type == 'group':
        indent = 1
        for c in help_file.children:
            _printIndent('{0}{1}'.format(c.name, ': ' + c.short_summary if c.short_summary else ''), indent)
        print('')

    if len(help_file.examples) > 0:
        indent = 0
        _printIndent('Examples', indent)

        for e in help_file.examples:
            indent = 1
            _printIndent('{0}'.format(e.name), indent)

            indent = 2
            _printIndent('{0}'.format(e.text), indent)


class HelpFile(object):
    def __init__(self, delimiters):
        self.delimiters = delimiters
        self.name = delimiters.split('.')[-1]
        self.command = delimiters.replace('.', ' ')
        self.type = ''
        self.short_summary = ''
        self.long_summary = ''
        self.examples = ''

    def load_from_file(self):
        file_data = _load_help_file(self.delimiters)
        if file_data:
            self._load_from_data(file_data)

    def _load_from_data(self, data):
        self.type = data['type']
        self.short_summary = data['short-summary']
        self.long_summary = data['long-summary']
        self.examples = [HelpExample(d) for d in data['examples']]


class GroupHelpFile(HelpFile):
    def __init__(self, delimiters, child_names):
        super(GroupHelpFile, self).__init__(delimiters)
        self.type = 'group'
        self.children = [HelpFile('{0}.{1}'.format(self.delimiters, n)) for n in child_names]

    def _load_from_data(self, data):
        super(GroupHelpFile, self)._load_from_data(data)

        child_helps = [GroupHelpFile(child.delimiters, []) for child in self.children]
        loaded_children = []
        for child in self.children:
            file = [h for h in child_helps if h.name == child.name]
            loaded_children.append(file[0] if len(file) > 0 else child)
        self.children = loaded_children


class CommandHelpFile(HelpFile):
    def __init__(self, delimiters, argdoc):
        super(CommandHelpFile, self).__init__(delimiters)
        self.type = 'command'
        self.parameters = [HelpParameter(a, r) for a, _, r in argdoc]

    def _load_from_data(self, data):
        super(CommandHelpFile, self)._load_from_data(data)

        loaded_params = []
        loaded_param = {}
        for param in self.parameters:
            loaded_param = next((n for n in data['parameters'] if n['name'] == param.name), None)
            if loaded_param:
                param.update_from_data(loaded_param)
                loaded_params.append(param)
            else:
                raise HelpAuthoringException('Missing param help for {0}'.format(param.name))
        self.parameters = loaded_params


class HelpParameter(object):
    def __init__(self, param_name, required):
        self.name = param_name
        self.required = required
        self.type = ''
        self.short_summary = ''
        self.long_summary = ''
        self.value_sources = ''

    def update_from_data(self, data):
        if self.name != data.get('name'):
            raise HelpAuthoringException("mismatched name {0} vs. {1}".format(self.name, data.get('name')))

        if self.required != data.get('required', False):
            raise HelpAuthoringException("mismatched required {0} vs. {1}, {2}".format(self.required, data.get('required'), data.get('name')))

        self.type = data.get('type')
        self.short_summary = data.get('short-summary')
        self.long_summary = data.get('long-summary')
        self.value_sources = data.get('populator-commands')

class HelpExample(object):
    def __init__(self, _data):
        self.name = _data['name']
        self.text = _data['text']

def _printIndent(str, indent=0):
    tw = textwrap.TextWrapper(initial_indent = "    "*indent, subsequent_indent = "    "*indent)
    print(tw.fill(str))

def _load_help_file(delimiters):
    s = """
    type: command
    short-summary: this module does xyz one-line or so
    long-summary: |
        this module.... kjsdflkj... klsfkj paragraph1
        this module.... kjsdflkj... klsfkj paragraph2
    parameters: 
        - name: --username/-u
          type: string
          required: false
          short-summary: one line partial sentence
          long-summary: text, markdown, etc.
          populator-commands: 
              - az vm list
              - default
        - name: --password/-p
          type: string
          short-summary: one line partial sentence
          long-summary: paragraph(s)
        - name: --service-principal
          type: string
          short-summary: one line partial sentence
          long-summary: paragraph(s)
        - name: --tenant/-t
          type: string
          short-summary: one line partial sentence
          long-summary: paragraph(s)
    examples:
        - name: foo example
          text: example details

    """ if delimiters == 'login' \
    else ''

    if s == '' and delimiters == 'account':
        s = """
        type: group
        short-summary: this module does xyz one-line or so
        long-summary: |
            this module.... kjsdflkj... klsfkj paragraph1
            this module.... kjsdflkj... klsfkj paragraph2
        parameters: 
            - name: --username/-u
              type: string
              required: false
              short-summary: one line partial sentence
              long-summary: text, markdown, etc.
              populator-commands: 
                  - az vm list
                  - default
            - name: --password/-p
              type: string
              short-summary: one line partial sentence
              long-summary: paragraph(s)
            - name: --service-principal
              type: string
              short-summary: one line partial sentence
              long-summary: paragraph(s)
            - name: --tenant/-t
              type: string
              short-summary: one line partial sentence
              long-summary: paragraph(s)
        examples:
            - name: foo example
              text: example details
    """

    return load(s)

class HelpAuthoringException(Exception):
    pass