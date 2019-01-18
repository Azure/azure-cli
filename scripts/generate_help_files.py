import ruamel.yaml as yaml

from ruamel.ordereddict import ordereddict as OrderedDict
from ruamel.yaml.comments import CommentedMap
from string import Template

class HelpFileWriter():
    help_file_header = \
"""# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps
"""
    def __init__(self, help_file_path, module_help_docs, command_examples_dict, help_files):
        self.help_file_path = help_file_path
        self.module_help_docs = module_help_docs
        self.command_examples_dict = command_examples_dict
        self.help_files = help_files

        self.add_command_examples()

    def add_command_examples(self):
        for command in self.module_help_docs:
            help_dict = yaml.round_trip_load(self.module_help_docs[command])
            # only add examples to commands
            if help_dict['type'] == 'command':
                az_command = 'az {0}'.format(command)
                crafted_examples = [key for key in self.command_examples_dict if key.startswith(az_command)]
                if len(crafted_examples) != 0:
                    if 'examples' not in help_dict:
                        help_dict['examples'] = []

                    command_parameters = set()
                    if command in self.help_files:
                        for parameter in self.help_files[command].parameters:
                            command_parameters = command_parameters.union(set(parameter.name_source))

                    examples_to_add = set(crafted_examples)
                    examples_to_remove = set()
                    for crafted_example in crafted_examples:
                        if command in self.help_files:
                            # check if this example will replace any existing examples
                            crafted_example_params = set(crafted_example.split()).intersection(command_parameters)
                            for existing_example in help_dict['examples']:
                                # leave non-crafted examples alone
                                if 'crafted' not in existing_example or existing_example['crafted'] != 'True' or existing_example['text'] in examples_to_remove:
                                    continue

                                # check if params of an existing crafted example form a subset of params of a new crafted example
                                existing_example_params = set(existing_example['text'].split()).intersection(command_parameters)
                                if existing_example_params.issubset(crafted_example_params):
                                    examples_to_remove.add(existing_example['text'])

                    # remove bad crafted examples
                    help_dict['examples'] = [example_dict for example_dict in help_dict['examples'] if example_dict['text'] not in examples_to_remove]

                    # add new crafted examples
                    for crafted_example_text in examples_to_add:
                        example_text_decoded = str(bytes(crafted_example_text.decode('utf-8')).decode('unicode_escape'))
                        example_name_decoded = self.command_examples_dict[crafted_example_text]#str(bytes(self.command_examples_dict[crafted_example_text].decode('utf-8')).decode('unicode_escape'))
                        help_dict['examples'].append(CommentedMap([('name', example_name_decoded),
                                                                   ('text', crafted_example_text),
                                                                   ('crafted', 'True')]))
                        self.command_examples_dict.pop(crafted_example_text)

                # add escape slash for future loads since it gets removed on load
                # replace angle brackets with curly braces
                if 'examples' in help_dict:
                    for example in help_dict['examples']:
                        example['text'] = example['text'].replace('\\', '\\\\').replace('<', '{').replace('>', '}')
                        example['name'] = example['name'].replace('\\', '\\\\').replace('<', '{').replace('>', '}')

            help_doc = yaml.round_trip_dump(help_dict, indent=4, default_flow_style=False, allow_unicode=True)
            self.module_help_docs[command] = help_doc

    def dump(self):
        help_str = ''
        for command in sorted(self.module_help_docs):
            command_doc_string = self.module_help_docs[command].rstrip()
            help_str += 'helps["{0}"] = \"\"\"\n{1}\n\"\"\"\n\n'.format(command, command_doc_string)

        template_substitution_dict = {'header'    : self.help_file_header,
                                      'helps'     : help_str}
        with open(self.help_file_path, 'w') as help_file:
            help_template_str = '$header\n$helps'
            help_template = Template(help_template_str)
            output = help_template.substitute(template_substitution_dict)
            help_file.write(output)

def main(command_examples_json_path):
    import json
    import pkgutil

    from azure.cli.core import get_default_cli
    from azure.cli.core.commands import (_load_module_command_loader, BLACKLISTED_MODS)
    from azure.cli.core.file_util import create_invoker_and_load_cmds_and_args, get_all_help
    from azure.cli.core._help import CliCommandHelpFile
    from importlib import import_module
    from knack.help_files import helps

    cli_ctx = get_default_cli()
    from knack import events
    from azure.cli.core.commands.arm import register_global_subscription_argument, register_ids_argument

    invoker = cli_ctx.invocation_cls(cli_ctx=cli_ctx, commands_loader_cls=cli_ctx.commands_loader_cls,
                                     parser_cls=cli_ctx.parser_cls, help_cls=cli_ctx.help_cls)
    cli_ctx.invocation = invoker
    invoker.commands_loader.skip_applicability = True
    command_modules_package = import_module('azure.cli.command_modules')
    installed_command_modules = [modname for _, modname, _ in
                                 pkgutil.iter_modules(command_modules_package.__path__)
                                 if modname not in BLACKLISTED_MODS]

    # get helps being defined for each module
    all_module_help_docs = {}
    for module in installed_command_modules:
        _load_module_command_loader(cli_ctx.invocation.commands_loader, None, module)
        all_module_help_docs[module] = OrderedDict([(command, helps[command]) for command in sorted(helps.keys(), reverse=True)])
        helps.clear()

    invoker.commands_loader.load_command_table(None)
    # turn off applicability check for all loaders
    for loaders in invoker.commands_loader.cmd_to_loader_map.values():
        for loader in loaders:
            loader.skip_applicability = True

    for command in invoker.commands_loader.command_table:
        invoker.commands_loader.load_arguments(command)

    register_global_subscription_argument(cli_ctx)
    register_ids_argument(cli_ctx)  # global subscription must be registered first!
    cli_ctx.raise_event(events.EVENT_INVOKER_POST_CMD_TBL_CREATE, commands_loader=invoker.commands_loader)
    invoker.parser.load_command_table(invoker.commands_loader)
    help_files = dict([(help_file.command, help_file) for help_file in get_all_help(cli_ctx) if isinstance(help_file, CliCommandHelpFile)])

    command_examples_dict = {}
    with open(command_examples_json_path) as command_examples_json:
        command_examples_dict = json.load(command_examples_json, encoding='utf-8')

    for module_name in all_module_help_docs:
        help_file_path = "../src/command_modules/azure-cli-{0}/azure/cli/command_modules/{0}/_help.py".format(module_name)
        help_file_writer = HelpFileWriter(help_file_path, all_module_help_docs[module_name], command_examples_dict, help_files)
        help_file_writer.dump()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    required_arguments = parser.add_argument_group('required arguments')
    required_arguments.add_argument('-d', '--data', action='store', required=True, dest='data', help='Path to command examples json file.')

    args = parser.parse_args()
    command_examples_json_path = args.data

    main(command_examples_json_path)
