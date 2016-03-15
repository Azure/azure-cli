import sys
import textwrap
from collections import OrderedDict

from yaml import load, dump

from ._output import OutputProducer, TableOutput, format_table, format_list, format_unordered_list

def print_detailed_help(help_file, out=sys.stdout):  # TODO: wire up out to print statements
    indent = 0
    print('')
    _printIndent('{0}: {1}'.format(help_file.command, help_file.short_summary), indent)

    indent = 1
    _printIndent('{0}'.format(help_file.long_summary), indent)
    print('')

    indent = 0
    _printIndent('Arguments', indent)

    if help_file.type == 'command':
        for p in help_file.parameters:
            indent = 1
            _printIndent('{0}: {1}'.format(p.name, p.short_summary), indent)

            indent = 2
            _printIndent('{0}'.format(p.long_summary), indent)

            if p.value_sources:
                _printIndent("Values from: {0}".format(', '.join(p.value_sources)), indent)
            print('')

    if help_file.type == 'group':
        indent = 1
        for c in help_file.children:
            _printIndent('{0}: {1}'.format(c.name, c.short_summary), indent)


class HelpFile(object):
    def __init__(self, delimiters):
        self.delimiters = delimiters
        self.name = delimiters.split('.')[-1]
        self.command = delimiters.replace('.', ' ')
        self.type = ''
        self.short_summary = ''
        self.long_summary = ''

    def load_from_file(self):
        _load_from_data(_load_help_file(self.delimiters))

    @classmethod
    def _load_from_data(cls, data):
        self.type = data['type']
        self.short_summary = data['short-summary']
        self.long_summary = data['long-summary']


class GroupHelpFile(HelpFile):
    def __init__(self, delimiters, child_names):
        super(GroupHelpFile, self).__init__(delimiters)
        self.type = 'group'
        self.children = [HelpFile('{0}.{1}'.format(self.delimiters, n)) for n in child_names]

    @classmethod
    def load_from_data(cls, data):
        super()._load_from_data(data)

        child_helps = [GroupHelpFile(child.delimiters, []) for child in cls.children]
        loaded_children = []
        for child in cls.children:
            file = [h for h in child_helps if h.name == child.name]
            loaded_children.append(file[0] if len(file) > 0 else child)
        cls.children = loaded_children


class CommandHelpFile(HelpFile):
    def __init__(self, delimiters, argdoc):
        super(CommandHelpFile, self).__init__(delimiters)
        self.type = 'command'
        self.parameters = [HelpParameter(a, r) for a, _, r in argdoc]

    @classmethod
    def load_from_data(cls, data):
        super()._load_from_data(data)

        loaded_params = []
        for param in cls.parameters:
            if data.get(param.name):
                loaded_params.append(data[param.name])
            else:
                raise HelpAuthoringException('Missing param help for {0}'.format(param.name))
        cls.parameters = loaded_params

    #def load_saved_data(self):
    #    data = _load_help_file(self.delimiters)
    #    self.name = _get_data_value(data, 'name')
    #    self.type = _get_data_value(data, 'type')
    #    self.short_summary = _get_data_value(data, 'short-summary')
    #    self.long_summary = _get_data_value(data, 'long-summary')
    #    self.command = self.name.replace('.', ' ')

    #    file_params = {HelpParameter(x).name: HelpParameter(x) for x in data.get('parameters')}
    #    for param in self.parameters:
    #        if file_params.get(param.name):
    #            param.copy_from(file_params.pop(param.name))
    #    if len(file_params) != 0:
    #        raise HelpAuthoringException('unmatched parameters in help file: ' + ', '.join(file_params.keys))

    #    file_children = {HelpFile(d).name: HelpFile(d) for d in _load_child_delimiters(self._delimiters)}
    #    for child in file_children:
    #        if file_children.get(child.name):
    #            child.copy_from(file_children.pop(child.name))
    #    if len(file_children


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

        if self.name != data.get('required'):
            raise HelpAuthoringException("mismatched required {0} vs. {1}".format(self.required, data.get('required')))

        self.type = _data.get('type')
        self.short_summary = _data.get('short-summary')
        self.long_summary = _data.get('long-summary')
        self.value_sources = _data.get('populator-commands')


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
        - name: prm1longlonglong
          type: enum
          required: true
          short-summary: one line partial sentence
          long-summary: text, markdown, etc.
          populator-commands: 
              - az vm list
              - default
        - name: prm2
          type: flag
          short-summary: one line partial sentence
          long-summary: paragraph(s)


    """

    return load(s)

def _load_child_delimiters(delimiters):
    return [delimiters + '.foo', delimiters + '.bar']

class HelpAuthoringException(Exception):
    pass