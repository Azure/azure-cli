#!/usr/bin/env python

import os
import sys
import copy
import shlex
from collections import defaultdict
from importlib import import_module

import yaml
from setuptools import find_packages
from pprint import pprint

from azure.cli.command_modules import aladdin

# disable deprecation warning
yaml.warnings({'YAMLLoadWarning': False})

BASE_PATH = os.path.abspath(os.path.curdir)


def load_aladdin_helps():
    aladdin_helps = aladdin.aladdin_helps
    return {cmd: next(yaml.load_all(content)) for cmd, content in aladdin_helps.items()}


def load_command_help_modules():
    command_modules_dir = os.path.join(BASE_PATH, 'src', 'azure-cli')

    mods = []

    pkgs = find_packages(where=command_modules_dir, exclude=['*test*'])
    for pkg in pkgs:
        try:
            mod = import_module(pkg + '._help')
        except Exception as e:
            continue

        mods.append(mod)

    return mods


def format_examples(cmd, examples):
    formatted = defaultdict(list)

    for example in examples:
        text = example['text']
        command_line = text[text.index(cmd):]

        parameter_section = command_line[command_line.index(cmd) + len(cmd):]
        parameter_section = shlex.split(parameter_section)

        parameter_names = [p for p in parameter_section if p.startswith('-')]
        parameter_names.sort()

        formatted[tuple(parameter_names)].append(example)

    return formatted


def write_examples(cmd, examples, buffer):
    two_space = '  '
    name_tpl = two_space + '- name: {}\n'
    text_tpl = two_space * 2 + 'text: |\n'
    cmd_tpl = two_space * 4 + 'az {}'
    opt_tpl = ' \\\\\n' + two_space * 4 + '{} '
    crafted_tpl = '\n' + two_space * 2 + 'crafted: true'

    for ex in examples:
        buffer.append(name_tpl.format(ex['name']))
        buffer.append(text_tpl)
        buffer.append(cmd_tpl.format(cmd))

        parameters = ex['text']
        parameters = parameters[parameters.index(cmd) + len(cmd):].strip()
        for p in shlex.split(parameters):
            if p.startswith('-'):
                buffer.append(opt_tpl.format(p))
            else:
                buffer.append(p)

        if 'crafted' in ex:
            buffer.append(crafted_tpl)

        buffer.append('\n')


def merge_examples(cmd, raw_cli_help, aladdin_help, buffer):
    # print('-' * 40, cmd, '-' * 40)

    yaml_cli_help = next(yaml.load_all(''.join(raw_cli_help)))

    cli_examples = yaml_cli_help.get('examples', None)

    aladdin_examples = aladdin_help.get('examples')
    if aladdin_examples is None:
        return

    formatted_cli_examples = format_examples(cmd, cli_examples if cli_examples else [])
    formatted_aladdin_examples = format_examples(cmd, aladdin_examples)

    yaml_example_key_written = False

    # append Aladdin added examples
    for parameter_seq, examples in formatted_aladdin_examples.items():
        if parameter_seq in formatted_cli_examples:
            continue

        print("number of cli examples: {}  |  number of Aladdin examples: {}".format(
                len(formatted_cli_examples), len(examples)))

        if (
            len(formatted_aladdin_examples) > 0 and 
            len(formatted_cli_examples) == 0 and 
            yaml_example_key_written is False
        ):
            buffer.append('examples:\n')
            yaml_example_key_written = True

        write_examples(cmd, examples, buffer)


def extract_command(raw_line):
    raw_line = raw_line.strip()
    start_index, end_index = raw_line.index("['") + 2, raw_line.index("']")
    return raw_line[start_index: end_index].strip()


def merge(aladdin_helps, help_module):
    print('==================== [ Processing: {:50.50} ] ==================='.format(help_module.__name__))

    help_start_flag = "helps['"

    buffer = []

    with open(help_module.__file__, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith(help_start_flag) is False:
                buffer.append(line)
                continue

            buffer.append(line)

            cmd = extract_command(line)

            # start parseing help entries
            raw_yaml_body = []

            line = f.readline()
            while line.endswith('"""\n') is False:
                raw_yaml_body.append(line)
                line = f.readline()

            buffer.extend(raw_yaml_body)  # save the hardcode help entries first

            if cmd in aladdin_helps:
                merge_examples(cmd, raw_yaml_body, aladdin_helps[cmd], buffer)

            buffer.append(line)    # line == '""""\n'

    temp_file_name = help_module.__name__ + '.py'
    with open(temp_file_name, 'w', encoding='utf-8') as tmp:
        tmp.writelines(buffer)

    os.replace(temp_file_name, help_module.__file__)


if __name__ == '__main__':
    aladdin_helps = load_aladdin_helps()
    # pprint(aladdin_helps)

    modules = load_command_help_modules()

    # test_mod = None
    # for mod in modules:
    #     if 'botservice' in mod.__file__:
    #         test_mod = mod
    #         break
    # merge(aladdin_helps, test_mod, test_mod.__name__ + '.py')

    for mod in modules:
        merge(aladdin_helps, mod)
