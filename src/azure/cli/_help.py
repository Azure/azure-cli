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
        self._delimiters = delimiters
        self._data = {}

    @property
    def name(self):
        return self._delimiters.split('.')[-1]

    @property
    def command(self):
        return self._delimiters.replace('.', ' ')

    @property
    def type(self):
        t = self._data.get('type')
        if t != 'command' and t != 'group':
            raise HelpAuthoringException('help file type must be "command" or "group"')
        return t

    @property
    def short_summary(self):
        return self._data.get('short-summary')

    @property
    def long_summary(self):
        return self._data.get('long-summary')

    @property
    def parameters(self):
        return [HelpParameter(x) for x in self._data.get('parameters')]

    @property
    def children(self):
        return [HelpFile(d) for d in _load_child_delimiters(self._delimiters)]

    def load_saved_data(self):
        self._data = _load_help_file(delimiters)

class HelpParameter(object):
    def __init__(self, _data):
        self._data = _data

    @property
    def name(self):
        return self._data.get('name')

    @property
    def required(self):
        return bool(self._data.get('required'))

    @property
    def short_summary(self):
        return self._data.get('short-summary')

    @property
    def long_summary(self):
        return self._data.get('long-summary')

    @property
    def type(self):
        return self._data.get('type')

    @property
    def value_sources(self):
        return self._data.get('populator-commands')


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