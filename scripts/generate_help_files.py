import yaml

from yaml import Dumper, Loader
from collections import OrderedDict
from string import Template

class HelpFile():
    # custom loader and dumper that preserve order in yaml when working with OrderedDict
    class OrderedLoader(Loader):
        pass

    class OrderedDumper(Dumper):
        pass

    def ordered_representer(dumper, data):
        return dumper.represent_mapping(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items())

    def ordered_constructor(loader, node):
        return OrderedDict(loader.construct_pairs(node))

    OrderedDumper.add_representer(OrderedDict, ordered_representer)
    OrderedLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, ordered_constructor)
    help_file_header = \
"""# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps
"""

    def __init__(self, help_file_path, module_help_docs, command_examples_dict):
        self.help_file_path = help_file_path
        self.module_help_docs = module_help_docs
        self.command_examples_dict = command_examples_dict

        self.add_command_examples()

    def add_command_examples(self):
        for command in self.module_help_docs:
            help_dict = yaml.load(self.module_help_docs[command], Loader=self.OrderedLoader)
            # remove existing examples
            help_dict.pop('examples', None)
            az_command = 'az {0}'.format(command)
            if az_command in self.command_examples_dict:
                help_dict['examples'] = []
                for example_name in self.command_examples_dict[az_command]:
                    example_text = str(self.command_examples_dict[az_command][example_name])
                    # decode escapes
                    example_name_decoded = str(bytes(example_name.encode('utf-8')).decode('unicode_escape'))
                    example_text_decoded = str(bytes(example_text.encode('utf-8')).decode('unicode_escape'))
                    help_dict['examples'].append(OrderedDict([('name', example_name_decoded),
                                                              ('text', example_text_decoded)]))

            help_doc = yaml.dump(help_dict, Dumper=self.OrderedDumper, indent=4, default_style='|', default_flow_style=False)
            self.module_help_docs[command] = help_doc

    def dump(self):
        help_str = ''
        for command in self.module_help_docs:
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
    from importlib import import_module
    from knack.help_files import helps

    cli_ctx = get_default_cli()
    invoker = cli_ctx.invocation_cls(cli_ctx=cli_ctx, commands_loader_cls=cli_ctx.commands_loader_cls,
                                    parser_cls=cli_ctx.parser_cls, help_cls=cli_ctx.help_cls)
    invoker.commands_loader.skip_applicability = True
    cli_ctx.invocation = invoker
    command_modules_package = import_module('azure.cli.command_modules')
    installed_command_modules = [modname for _, modname, _ in
                                 pkgutil.iter_modules(command_modules_package.__path__)
                                 if modname not in BLACKLISTED_MODS]

    # get helps being defined for each module
    all_module_help_docs = {}
    for module in installed_command_modules:
        _load_module_command_loader(invoker.commands_loader, None, module)
        all_module_help_docs[module] = helps.copy()
        helps.clear()

    command_examples_dict = {}
    with open(command_examples_json_path) as command_examples_json:
        command_examples_dict = json.load(command_examples_json, encoding='utf-8')

    for module_name in all_module_help_docs:
        help_file_path = "../src/command_modules/azure-cli-{0}/azure/cli/command_modules/{0}/_help.py".format(module_name)
        help_file = HelpFile(help_file_path, all_module_help_docs[module_name], command_examples_dict)
        help_file.dump()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    required_arguments = parser.add_argument_group('required arguments')
    required_arguments.add_argument('-d', '--data', action='store', required=True, dest='data', help='Path to command examples json file.')

    args = parser.parse_args()
    command_examples_json_path = args.data

    main(command_examples_json_path)
