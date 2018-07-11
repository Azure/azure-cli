# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import yaml

from knack.help import REQUIRED_TAG
from knack.help_files import helps
from knack.log import get_logger
from azure.cli.core import MainCommandsLoader
from azure.cli.core.commands.arm import add_id_parameters


logger = get_logger(__name__)


class AzInteractiveCommandsLoader(MainCommandsLoader):

    def __init__(self, cli_ctx=None):
        super(AzInteractiveCommandsLoader, self).__init__(cli_ctx)
        self.loaders = []

    def _update_command_definitions(self):

        for loader in self.loaders:
            loader.command_table = self.command_table
            loader._update_command_definitions()  # pylint: disable=protected-access

    def load_arguments(self, _):
        from azure.cli.core.commands.parameters import resource_group_name_type, get_location_type, deployment_name_type
        from azure.cli.core import ArgumentsContext

        from knack.arguments import ignore_type

        command_loaders = self.loaders

        if command_loaders:
            with ArgumentsContext(self, '') as c:
                c.argument('resource_group_name', resource_group_name_type)
                c.argument('location', get_location_type(self.cli_ctx))
                c.argument('deployment_name', deployment_name_type)
                c.argument('cmd', ignore_type)

            # load each command's arguments via reflection
            for _, command in self.command_table.items():
                command.load_arguments()

            for loader in command_loaders:
                loader.skip_applicability = True
                try:
                    loader.load_arguments(None)  # load each module's params file to the argument registry
                except (ValueError, ImportError) as ex:
                    logger.debug(ex)

                self.argument_registry.arguments.update(loader.argument_registry.arguments)
                self.extra_argument_registry.update(loader.extra_argument_registry)
                # _update_command_definitions needs these set
                self.cli_ctx.invocation.commands_loader.argument_registry = self.argument_registry
                self.cli_ctx.invocation.commands_loader.extra_argument_registry = self.extra_argument_registry
                loader._update_command_definitions()  # pylint: disable=protected-access


# pylint: disable=too-few-public-methods
class FreshTable(object):
    """
    this class generates and dumps the fresh command table into a file
    as well as installs all the modules
    """
    loader = None

    def __init__(self, shell_ctx):
        self.shell_ctx = shell_ctx

    def dump_command_table(self, shell_ctx=None):
        """ dumps the command table """
        import timeit

        start_time = timeit.default_timer()
        shell_ctx = shell_ctx or self.shell_ctx
        main_loader = AzInteractiveCommandsLoader(shell_ctx.cli_ctx)

        main_loader.load_command_table(None)
        main_loader.load_arguments(None)
        add_id_parameters(None, commands_loader=main_loader)
        cmd_table = main_loader.command_table

        cmd_table_data = {}
        for command_name, cmd in cmd_table.items():

            try:
                command_description = cmd.description
                if callable(command_description):
                    command_description = command_description()

                # checking all the parameters for a single command
                parameter_metadata = {}
                for arg in cmd.arguments.values():
                    options = {
                        'name': [name for name in arg.options_list],
                        'required': REQUIRED_TAG if arg.type.settings.get('required') else '',
                        'help': arg.type.settings.get('help') or ''
                    }
                    # the key is the first alias option
                    if arg.options_list:
                        parameter_metadata[arg.options_list[0]] = options

                cmd_table_data[command_name] = {
                    'parameters': parameter_metadata,
                    'help': command_description,
                    'examples': ''
                }
            except (ImportError, ValueError):
                pass

        load_help_files(cmd_table_data)
        elapsed = timeit.default_timer() - start_time
        logger.debug('Command table dumped: %s sec', elapsed)
        FreshTable.loader = main_loader

        # dump into the cache file
        command_file = shell_ctx.config.get_help_files()
        with open(os.path.join(get_cache_dir(shell_ctx), command_file), 'w') as help_file:
            json.dump(cmd_table_data, help_file)


def load_help_files(data):
    """ loads all the extra information from help files """
    for command_name, help_yaml in helps.items():

        help_entry = yaml.load(help_yaml)
        try:
            help_type = help_entry['type']
        except KeyError:
            continue

        # if there is extra help for this command but it's not reflected in the command table
        if command_name not in data and help_type == 'command':
            logger.debug('Command: %s not found in command table', command_name)
            continue

        short_summary = help_entry.get('short-summary')
        if short_summary and help_type == 'command':
            data[command_name]['help'] = short_summary
        else:
            # must be a command group or sub-group
            data[command_name] = {'help': short_summary}
            continue

        if 'parameters' in help_entry:
            for param in help_entry['parameters']:
                # this could fail if the help file and options list are not in the same order
                param_name = param['name'].split()[0]

                if param_name not in data[command_name]['parameters']:
                    logger.debug('Command %s does not have parameter: %s', command_name, param_name)
                    continue

                if 'short-summary' in param:
                    data[command_name]['parameters'][param_name]['help'] = param["short-summary"]

        if 'examples' in help_entry:
            data[command_name]['examples'] = [[example['name'], example['text']]
                                              for example in help_entry['examples']]


def get_cache_dir(shell_ctx):
    """ gets the location of the cache """
    azure_folder = shell_ctx.config.get_config_dir()
    cache_path = os.path.join(azure_folder, 'cache')
    if not os.path.exists(azure_folder):
        os.makedirs(azure_folder)
    if not os.path.exists(cache_path):
        os.makedirs(cache_path)
    return cache_path
