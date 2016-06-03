from __future__ import print_function
import os
import sys

from ._help import GroupHelpFile, CommandHelpFile

_help_location = os.path.join(os.path.expanduser('~'), 'azurecli', 'help')

def generate_help(noun_map):
    if not os.path.exists(_help_location):
        os.makedirs(_help_location)
    _generate_help(noun_map)

def _generate_help(noun_map):
    if noun_map is None or len(noun_map) == 0:
        return

    old_stdout = sys.stdout

    try:
        for noun in [n for n in noun_map if not n.startswith('$')]:
            properties = noun_map[noun]

            delimiters = properties['$full_name']
            file_path = os.path.join(_help_location, delimiters + '.rst')
            mode = 'w+' if not os.path.exists(file_path) else 'w'
            sys.stdout = open(file_path, mode)

            if '$kwargs' in properties:
                cmd_file = CommandHelpFile(delimiters, properties['$argdoc'])
                cmd_file.load(properties)
                _handle_command(cmd_file)
            else:
                subnouns = [n for n in properties if not n.startswith('$')]
                grp_file = GroupHelpFile(delimiters, subnouns)
                grp_file.load(properties)
                _handle_group(grp_file)

                for n in properties:
                    _generate_help({n: properties[n]})

            sys.stdout.close()
    finally:
        sys.stdout = old_stdout

    print('Help generated at {}'.format(_help_location))

def _handle_command(doc):
    _print_summary(doc)

    _h2('Arguments')
    print('')

    for p in doc.parameters:
        _h3(p.name)
        print('[{0}] {1}'.format(p.type, p.short_summary or ''))
        print('')
        print(p.long_summary)
        print('')

        if p.value_sources and len(p.value_sources) > 0:
            print('To get values:')
            print('')
            print('')
            for v in p.value_sources:
                _list_item(v)
            print('')

    _print_examples(doc)

def _handle_group(doc):
    _print_summary(doc)

    _h2('Child Commands')
    print('')

    for c in doc.children:
        _h3(c.name)
        print(c.short_summary)

    _print_examples(doc)

def _print_summary(doc):
    _h1('{0}: {1}'.format(doc.type.title(), doc.delimiters))
    _h2('Summary')
    print('')
    print(doc.short_summary or '')
    print('')
    print(doc.long_summary.replace('\n', '\n\n'))
    print('')

def _print_examples(doc):
    if len(doc.examples) > 0:
        _h2('Examples')
        for e in doc.examples:
            _h3(e.name)
            print(e.text)
            print('')

def _h1(s):
    heading = '='*len(s)
    print(heading)
    print(s)
    print(heading)

def _h2(s):
    heading = '*'*len(s)
    print(heading)
    print(s)
    print(heading)

def _h3(s):
    heading = '='*len(s)
    print(s)
    print(heading)

def _list_item(s):
    print('- {0}'.format(s))
