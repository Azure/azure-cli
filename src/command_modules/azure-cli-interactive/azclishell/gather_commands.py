# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import math
import os
import json

import azclishell.configuration
from azclishell.command_tree import CommandBranch, CommandHead
from azclishell.util import get_window_dim

CONFIGURATION = azclishell.configuration.CONFIGURATION

ROWS, COLS = get_window_dim()

TOLERANCE = 10
LINE_MINIMUM = math.floor(int(COLS) / 2 - 15)

GLOBAL_PARAM_DESCRIPTIONS = {
    '--output': 'Output format',
    '-o': 'Output format',
    '--help': 'Get more information about a command',
    '-h': "Get more information about a command"
}
OUTPUT_CHOICES = ['json', 'tsv', 'table', 'jsonc']
OUTPUT_OPTIONS = ['--output', '-o']
GLOBAL_PARAM = list(GLOBAL_PARAM_DESCRIPTIONS.keys())


def add_random_new_lines(long_phrase, line_min=LINE_MINIMUM, tolerance=TOLERANCE):
    """ not everything fits on the screen, based on the size, add newlines """
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
    def __init__(self):
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
        self.same_param_doubles = {}

        self.global_param_descriptions = GLOBAL_PARAM_DESCRIPTIONS
        self.output_choices = OUTPUT_CHOICES
        self.output_options = OUTPUT_OPTIONS
        self.global_param = GLOBAL_PARAM

        self.gather_from_files()

    def add_exit(self):
        """ adds the exits from the application """
        self.completable.append("quit")
        self.completable.append("exit")

        self.descrip["quit"] = "Exits the program"
        self.descrip["exit"] = "Exits the program"

        self.command_tree.children.append(CommandBranch("quit"))
        self.command_tree.children.append(CommandBranch("exit"))

        self.command_param["quit"] = ""
        self.command_param["exit"] = ""

    def gather_from_files(self):
        """ gathers from the files in a way that is convienent to use """
        command_file = CONFIGURATION.get_help_files()
        cache_path = os.path.join(azclishell.configuration.get_config_dir(), 'cache')
        with open(os.path.join(cache_path, command_file), 'r') as help_file:
            data = json.load(help_file)

        self.add_exit()
        commands = data.keys()

        for command in commands:
            branch = self.command_tree
            for word in command.split():
                if word not in self.completable:
                    self.completable.append(word)
                if branch.children is None:
                    branch.children = []
                if not branch.has_child(word):
                    branch.children.append(CommandBranch(word))
                branch = branch.get_child(word, branch.children)

            description = data[command]['help']
            self.descrip[command] = add_random_new_lines(description)

            if 'examples' in data[command]:
                examples = []
                for example in data[command]['examples']:
                    examples.append([
                        add_random_new_lines(example[0], line_min=int(COLS) - 2 * TOLERANCE),
                        add_random_new_lines(example[1], line_min=int(COLS) - 2 * TOLERANCE)])
                self.command_example[command] = examples

            all_params = []
            for param in data[command]['parameters']:
                suppress = False

                if data[command]['parameters'][param]['help'] and \
                   '==SUPPRESS==' in data[command]['parameters'][param]['help']:
                    suppress = True
                if data[command]['parameters'][param]['help'] and not suppress:
                    param_double = None
                    for par in data[command]['parameters'][param]['name']:
                        if not param_double:
                            param_double = par
                        else:
                            self.same_param_doubles[par] = param_double
                            self.same_param_doubles[param_double] = par

                        self.param_descript[command + " " + par] =  \
                            add_random_new_lines(
                                data[command]['parameters'][param]['required'] +
                                " " + data[command]['parameters'][param]['help'])
                        if par not in self.completable_param:
                            self.completable_param.append(par)
                        all_params.append(par)

            self.command_param[command] = all_params

    def get_all_subcommands(self):
        """ returns all the subcommands """
        subcommands = []
        for command in self.descrip:
            for word in command.split():
                for kid in self.command_tree.children:
                    if word != kid.data and word not in subcommands:
                        subcommands.append(word)
        return subcommands
