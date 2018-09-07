# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import math
import os
import json
from knack.log import get_logger

from .command_tree import CommandBranch, CommandHead
from .util import get_window_dim


logger = get_logger(__name__)

TOLERANCE = 10

GLOBAL_PARAM_DESCRIPTIONS = {
    '--output': 'Output format',
    '-o': 'Output format',
    '--help': 'Get more information about a command',
    '-h': "Get more information about a command"
}
OUTPUT_CHOICES = ['json', 'tsv', 'table', 'jsonc']
OUTPUT_OPTIONS = ['--output', '-o']
GLOBAL_PARAM = list(GLOBAL_PARAM_DESCRIPTIONS.keys())


def _get_window_columns():
    _, col = get_window_dim()
    return col


def add_new_lines(long_phrase, line_min=None, tolerance=TOLERANCE):
    """ not everything fits on the screen, based on the size, add newlines """
    if line_min is None:
        line_min = math.floor(int(_get_window_columns()) / 2 - 15)

    if long_phrase is None:
        return long_phrase
    line_min = int(line_min)
    nl_loc = []
    skip = False
    index = 0
    if len(long_phrase) > line_min:

        for _ in range(int(math.floor(len(long_phrase) / line_min))):
            previous = index
            index += line_min
            if skip:
                index += 1
                skip = False
            while index < len(long_phrase) and \
                    not long_phrase[index].isspace() and \
                    index < tolerance + previous + line_min:
                index += 1
            if index < len(long_phrase):
                if long_phrase[index].isspace():
                    index += 1
                    skip = True
                nl_loc.append(index)

    counter = 0
    for loc in nl_loc:
        long_phrase = long_phrase[:loc + counter] + '\n' + long_phrase[loc + counter:]
        counter += 1
    return long_phrase + "\n"


# pylint: disable=too-many-instance-attributes
class GatherCommands(object):
    """ grabs all the cached commands from files """
    def __init__(self, config):
        # everything that is completable
        self.completable = []
        # a completable to the description of what is does
        self.descrip = {}
        # from a command to a list of parameters
        self.command_param = {}

        self.completable_param = []
        self.command_example = {}
        self.command_tree = CommandHead()
        self.param_descript = {}
        self.completer = None
        self.command_param_info = {}

        self.global_param_descriptions = GLOBAL_PARAM_DESCRIPTIONS
        self.output_choices = OUTPUT_CHOICES
        self.output_options = OUTPUT_OPTIONS
        self.global_param = GLOBAL_PARAM

        try:
            self._gather_from_files(config)
        except (TypeError, KeyError, ValueError):
            logger.warning('Encountered unrecognizable cache, interactive will create a new updated cache for use.')

    def add_exit(self):
        """ adds the exits from the application """
        self.completable.append("quit")
        self.completable.append("exit")

        self.descrip["quit"] = "Exits the program"
        self.descrip["exit"] = "Exits the program"

        self.command_tree.add_child(CommandBranch("quit"))
        self.command_tree.add_child(CommandBranch("exit"))

        self.command_param["quit"] = ""
        self.command_param["exit"] = ""

    def _gather_from_files(self, config):
        """ gathers from the files in a way that is convienent to use """
        command_file = config.get_help_files()
        cache_path = os.path.join(config.get_config_dir(), 'cache')
        cols = _get_window_columns()

        with open(os.path.join(cache_path, command_file), 'r') as help_file:
            data = json.load(help_file)
        self.add_exit()
        commands = data.keys()

        for command in commands:
            branch = self.command_tree
            for word in command.split():
                if word not in self.completable:
                    self.completable.append(word)
                if not branch.has_child(word):
                    branch.add_child(CommandBranch(word))
                branch = branch.get_child(word)

            description = data[command]['help']
            self.descrip[command] = add_new_lines(description, line_min=int(cols) - 2 * TOLERANCE)

            if 'examples' in data[command]:
                examples = []
                for example in data[command]['examples']:
                    examples.append([
                        add_new_lines(example[0], line_min=int(cols) - 2 * TOLERANCE),
                        add_new_lines(example[1], line_min=int(cols) - 2 * TOLERANCE)])
                self.command_example[command] = examples

            command_params = data[command].get('parameters', {})
            for param in command_params:
                if '==SUPPRESS==' not in command_params[param]['help']:
                    param_aliases = set()

                    for par in command_params[param]['name']:
                        param_aliases.add(par)

                        self.param_descript[command + " " + par] = \
                            add_new_lines(
                                command_params[param]['required'] +
                                " " + command_params[param]['help'],
                                line_min=int(cols) - 2 * TOLERANCE)
                        if par not in self.completable_param:
                            self.completable_param.append(par)

                    param_doubles = self.command_param_info.get(command, {})
                    for alias in param_aliases:
                        param_doubles[alias] = param_aliases
                    self.command_param_info[command] = param_doubles

    def get_all_subcommands(self):
        """ returns all the subcommands """
        subcommands = []
        for command in self.descrip:
            for word in command.split():
                for kid in self.command_tree.children:
                    if word != kid and word not in subcommands:
                        subcommands.append(word)
        return subcommands
