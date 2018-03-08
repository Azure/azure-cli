# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import absolute_import, division, print_function, unicode_literals

from prompt_toolkit.completion import Completer, Completion
from azure.cli.core.parser import AzCliCommandParser
from . import configuration
from .argfinder import ArgsFinder
from .command_tree import in_tree
from .util import parse_quotes

SELECT_SYMBOL = configuration.SELECT_SYMBOL


def initialize_command_table_attributes(completer):
    from ._dump_commands import FreshTable
    completer.cmdtab = FreshTable(completer.shell_ctx).command_table
    if completer.cmdtab:
        completer.parser.load_command_table(completer.cmdtab)
        completer.argsfinder = ArgsFinder(completer.parser)


def error_pass(_, message):  # pylint: disable=unused-argument
    return


def dynamic_param_logic(text):
    """ validates parameter values for dynamic completion """
    is_param = False
    started_param = False
    prefix = ""
    param = ""
    txtspt = text.split()
    if txtspt:
        param = txtspt[-1]
        if param.startswith("-"):
            is_param = True
        elif len(txtspt) > 2 and txtspt[-2]\
                and txtspt[-2].startswith('-'):
            is_param = True
            param = txtspt[-2]
            started_param = True
            prefix = txtspt[-1]
    return is_param, started_param, prefix, param


def verify_dynamic_completion(comp, started_param, prefix, text):
    """ how to validate and generate completion for dynamic params """
    if len(comp.split()) > 1:
        completion = '\"' + comp + '\"'
    else:
        completion = comp
    if started_param:
        if comp.lower().startswith(prefix.lower()) and comp not in text.split():
            yield Completion(completion, -len(prefix))
    else:
        yield Completion(completion, -len(prefix))


def sort_completions(completions_gen):
    """ sorts the completions """

    def _get_weight(val):
        """ weights the completions with required things first the lexicographically"""
        priority = ''
        if val.display_meta and val.display_meta.startswith('[REQUIRED]'):
            priority = ' '  # a space has the lowest ordinance
        return priority + val.text

    return sorted(completions_gen, key=_get_weight)


# pylint: disable=too-many-instance-attributes
class AzCompleter(Completer):
    """ Completes Azure CLI commands """

    def __init__(self, shell_ctx, commands, global_params=True):
        self.shell_ctx = shell_ctx
        # dictionary of command to descriptions
        self.command_description = commands.descrip
        # from a command to a list of parameters
        self.command_parameters = commands.command_param
        # a list of all the possible parameters
        self.completable_param = commands.completable_param
        # the command tree
        self.command_tree = commands.command_tree
        # a dictionary of parameter (which is command + " " + parameter name)
        # to a description of what it does
        self.param_description = commands.param_descript
        # a dictionary of command to examples of how to use it
        self.command_examples = commands.command_example
        # a dictionary of commands with parameters with multiple names (e.g. {'vm create':{-n: --name}})
        self.same_param_doubles = commands.same_param_doubles or {}

        self._is_command = True

        self.branch = self.command_tree
        self.curr_command = ""

        self.global_param = commands.global_param if global_params else []
        self.output_choices = commands.output_choices if global_params else []
        self.output_options = commands.output_options if global_params else []
        self.global_param_descriptions = commands.global_param_descriptions if global_params else []

        self.global_parser = AzCliCommandParser(add_help=False)
        self.global_parser.add_argument_group('global', 'Global Arguments')
        self.parser = AzCliCommandParser(parents=[self.global_parser])
        self.argsfinder = ArgsFinder(self.parser)
        self.cmdtab = {}

    def validate_completion(self, param, words, text_before_cursor, check_double=True):
        """ validates that a param should be completed """
        # validates the position of the parameter
        position = param.lower().startswith(words.lower()) and not text_before_cursor[-1].isspace()
        # cancels parameters that are already in the in line
        canceling_positions = param.lower() != words.lower() and param not in text_before_cursor.split()

        found_double = True
        # checks for aliasing of parameters

        if check_double:
            for double_sets in self.same_param_doubles.get(self.curr_command, []):
                # if the parameter is in any of the sets
                if param in double_sets:
                    # if any of the other aliases are in the line already
                    found_double = not any(
                        alias in text_before_cursor.split() and alias != param for alias in double_sets)

        return position and canceling_positions and found_double

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        self.branch = self.command_tree
        self.curr_command = ''
        self._is_command = True
        text = self.reformat_cmd(text)
        if text.split():

            for comp in sort_completions(self.gen_cmd_and_param_completions(text)):
                yield comp

        for cmd in sort_completions(self.gen_cmd_completions(text)):
            yield cmd

        if self.cmdtab:
            for val in sort_completions(self.gen_dynamic_completions(text)):
                yield val

        for param in sort_completions(self.gen_global_param_completions(text)):
            yield param

    def gen_enum_completions(self, arg_name, text, started_param, prefix):
        """ generates dynamic enumeration completions """
        try:  # if enum completion
            for choice in self.cmdtab[
                    self.curr_command].arguments[arg_name].choices:
                if started_param:
                    if choice.lower().startswith(prefix.lower()) and choice not in text.split():
                        yield Completion(choice, -len(prefix))
                else:
                    yield Completion(choice, -len(prefix))

        except TypeError:  # there is no choices option
            pass

    def get_arg_name(self, is_param, param):
        """ gets the argument name used in the command table for a parameter """
        if self.curr_command in self.cmdtab and is_param:
            for arg in self.cmdtab[self.curr_command].arguments:

                for name in self.cmdtab[self.curr_command].arguments[arg].options_list:
                    if name == param:
                        return arg
        return None

    def mute_parse_args(self, text):
        """ mutes the parser error when parsing, then puts it back """
        error = AzCliCommandParser.error
        AzCliCommandParser.error = error_pass

        parse_args = self.argsfinder.get_parsed_args(
            parse_quotes(text, quotes=False, string=False))

        AzCliCommandParser.error = error
        return parse_args

    # pylint: disable=too-many-branches
    def gen_dynamic_completions(self, text):
        """ generates the dynamic values, like the names of resource groups """
        try:  # pylint: disable=too-many-nested-blocks

            is_param, started_param, prefix, param = dynamic_param_logic(text)

            # command table specific name
            arg_name = self.get_arg_name(is_param, param)

            if arg_name and ((text.split()[-1].startswith('-') and text[-1].isspace()) or
                             text.split()[-2].startswith('-')):

                for comp in self.gen_enum_completions(arg_name, text, started_param, prefix):
                    yield comp

                parse_args = self.mute_parse_args(text)

                # there are 3 formats for completers the cli uses
                # this try catches which format it is
                if self.cmdtab[self.curr_command].arguments[arg_name].completer:
                    try:
                        for comp in self.cmdtab[self.curr_command].arguments[arg_name].completer(
                                prefix=prefix, action=None, parsed_args=parse_args):
                            for completion in verify_dynamic_completion(
                                    comp, started_param, prefix, text):
                                yield completion
                    except TypeError:
                        try:
                            for comp in self.cmdtab[self.curr_command].\
                                    arguments[arg_name].completer(prefix=prefix):

                                for completion in verify_dynamic_completion(
                                        comp, started_param, prefix, text):
                                    yield completion
                        except TypeError:
                            try:
                                for comp in self.cmdtab[self.curr_command].\
                                        arguments[arg_name].completer():

                                    for completion in verify_dynamic_completion(
                                            comp, started_param, prefix, text):
                                        yield completion

                            except TypeError:
                                pass  # other completion method used

        # if the user isn't logged in
        except Exception:  # pylint: disable=broad-except
            pass

    def gen_cmd_completions(self, text):
        """ whether is a space or no text typed, send the current branch """
        # if nothing, so first level commands
        if not text.split() and self._is_command:
            if self.branch.children is not None:
                for com in self.branch.children:
                    yield Completion(com.data)

        # if space show current level commands
        elif text.split() and text[-1].isspace() and self._is_command:
            if self.branch is not self.command_tree:
                for com in self.branch.children:
                    yield Completion(com.data)

    def yield_param_completion(self, param, last_word):
        """ yields a parameter """
        return Completion(param, -len(last_word), display_meta=self.param_description.get(
            self.curr_command + " " + str(param), '').replace('\n', ''))

    def gen_cmd_and_param_completions(self, text):
        """ generates command and parameter completions """
        temp_command = str('')
        txtspt = text.split()

        for word in txtspt:
            if word.startswith("-"):
                self._is_command = False

            # building what the command is
            elif self._is_command:
                temp_command += ' ' + str(word) if temp_command else str(word)

            mid_val = text.find(word) + len(word)
            # moving down command tree
            if self.branch.has_child(word) and len(text) > mid_val and text[mid_val].isspace():
                self.branch = self.branch.get_child(word, self.branch.children)

        if text and text[-1].isspace():
            if in_tree(self.command_tree, temp_command):
                self.curr_command = temp_command
            else:
                self._is_command = False
        else:
            self.curr_command = temp_command

        last_word = txtspt[-1]
        # this is for single char parameters
        if last_word.startswith("-") and not last_word.startswith("--"):
            self._is_command = False
            if self.curr_command in self.command_parameters:
                for param in self.command_parameters[self.curr_command]:
                    if self.validate_completion(param, last_word, text) and\
                            not param.startswith("--"):
                        yield self.yield_param_completion(param, last_word)

        elif last_word.startswith("--"):  # for regular parameters
            self._is_command = False

            if self.curr_command in self.command_parameters:  # Everything should, map to empty list
                for param in self.command_parameters[self.curr_command]:
                    if self.validate_completion(param, last_word, text):
                        yield self.yield_param_completion(param, last_word)

        if self.branch.children and self._is_command:  # all underneath commands
            for kid in self.branch.children:
                if self.validate_completion(kid.data, txtspt[-1], text, False):
                    yield Completion(
                        str(kid.data), -len(txtspt[-1]))
        elif self._is_command and self.curr_command.strip() in self.command_parameters:
            for param in self.command_parameters[self.curr_command.strip()]:
                if param.startswith('--'):
                    yield self.yield_param_completion(param, '')

    def gen_global_param_completions(self, text):
        """ Global parameter stuff hard-coded in """
        txtspt = text.split()
        if txtspt and txtspt:
            for param in self.global_param:
                # for single dash global parameters
                if txtspt[-1].startswith('-') \
                        and not txtspt[-1].startswith('--') and \
                        param.startswith('-') and not param.startswith('--') and\
                        self.validate_completion(param, txtspt[-1], text, check_double=False):
                    yield Completion(
                        param, -len(txtspt[-1]),
                        display_meta=self.global_param_descriptions[param])
                # for double dash global parameters
                elif txtspt[-1].startswith('--') and \
                        self.validate_completion(param, txtspt[-1], text, check_double=False):
                    yield Completion(
                        param, -len(txtspt[-1]),
                        display_meta=self.global_param_descriptions[param])
            # if there is an output, gets the options without user typing
            if txtspt[-1] in self.output_options:
                for opt in self.output_choices:
                    yield Completion(opt)
            # if there is an output option, if they have started typing
            if len(txtspt) > 1 and\
                    txtspt[-2] in self.output_options:
                for opt in self.output_choices:
                    if self.validate_completion(opt, txtspt[-1], text, check_double=False):
                        yield Completion(opt, -len(txtspt[-1]))

    def is_completable(self, symbol):
        """ whether the word can be completed as a command or parameter """
        return symbol in self.command_parameters or symbol in self.param_description.keys()

    def has_description(self, param):
        """ if a parameter has a description """
        return param in self.param_description.keys() and \
            not self.param_description[param].isspace()

    def reformat_cmd(self, text):
        """ reformat the text to be stripped of noise """
        # remove az if there
        text = text.replace('az', '')
        # disregard defaulting symbols
        if text and SELECT_SYMBOL['scope'] == text[0:2]:
            text = text.replace(SELECT_SYMBOL['scope'], "")

        if self.shell_ctx.default_command:
            text = self.shell_ctx.default_command + ' ' + text
        return text
