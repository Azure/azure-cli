# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys
import shlex
from collections import defaultdict
from importlib import import_module

import yaml
from setuptools import find_packages
from pprint import pprint


# disable deprecation warning
yaml.warnings({'YAMLLoadWarning': False})

BASE_PATH = os.path.abspath(os.path.curdir)


def load_aladdin_helps():
    import aladdin
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

        parameter_names = [p.strip() for p in parameter_section if p.startswith('-')]
        parameter_names.sort()

        formatted[tuple(parameter_names)].append(example)

    return formatted


def calculate_preceding_indent(raw_cli_help):
    yaml_indent_key = raw_cli_help[0]
    yaml_indent_idx = 0

    for idx, s in enumerate(raw_cli_help):
        if s.strip().startswith('examples'):
            yaml_indent_key = s
            yaml_indent_idx = idx
            break

    for c in yaml_indent_key:
        if c != ' ':
            break
    
    preceding_indent = yaml_indent_key[:yaml_indent_key.index(c)]

    if 'examples' in yaml_indent_key:
        yaml_indent_key = raw_cli_help[yaml_indent_idx + 1]
        for c in yaml_indent_key:
            if c != ' ':
                break
        example_inner_indent = yaml_indent_key[:yaml_indent_key.index(c)]
    else:
        example_inner_indent = preceding_indent + ' ' * 2

    return preceding_indent, example_inner_indent


def write_examples(cmd, examples, buffer, example_inner_indent):
    two_space = '  '
    name_tpl = example_inner_indent + '- name: {}\n'
    text_tpl = example_inner_indent+ two_space + 'text: |\n'
    crafted_tpl = '\n' + example_inner_indent + two_space + 'crafted: true'
    cmd_tpl = example_inner_indent + two_space * 3 + 'az {}'
    opt_tpl = ' \\\\\n' + example_inner_indent + two_space * 3 + '{} '

    for ex in examples:
        buffer.append(name_tpl.format(ex['name']))
        buffer.append(text_tpl)
        buffer.append(cmd_tpl.format(cmd))

        parameters = ex['text']
        parameters = parameters[parameters.index(cmd) + len(cmd):].strip()
        if len(parameters) + len(example_inner_indent) < 80:
            buffer.append(' ' + parameters)
        else:            
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

    # get preceding indent
    preceding_indent, example_inner_indent = calculate_preceding_indent(raw_cli_help)
    # print('preceding_indent =', len(preceding_indent))
    # print('example_inner_indent =', len(example_inner_indent))

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
            buffer.append(preceding_indent + 'examples:\n')
            yaml_example_key_written = True

        write_examples(cmd, examples, buffer, example_inner_indent)


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
    #     if 'ams' in mod.__file__:
    #         test_mod = mod
    #         break
    # merge(aladdin_helps, test_mod)

    for mod in modules:
        merge(aladdin_helps, mod)
