# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import absolute_import, division, print_function, unicode_literals
import sys

from prompt_toolkit.completion import Completer, Completion

import azclishell.configuration
from azclishell.argfinder import ArgsFinder
from azclishell.command_tree import in_tree
from azclishell.layout import get_scope
from azclishell.util import parse_quotes

from azure.cli.core.parser import AzCliCommandParser

SELECT_SYMBOL = azclishell.configuration.SELECT_SYMBOL

BLACKLISTED_COMPLETIONS = ['interactive']


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


def reformat_cmd(text):
    """ reformat the text to be stripped of noise """
    # remove az if there
    text = text.replace('az', '')
    # disregard defaulting symbols
    if text and SELECT_SYMBOL['scope'] == text[0:2]:
        text = text.replace(SELECT_SYMBOL['scope'], "")

    if get_scope():
        text = get_scope() + ' ' + text
    return text


def gen_dyn_completion(comp, started_param, prefix, text):
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


def sort_completions(gen):
    """ sorts the completions """

    def _get_weight(val):
        """ weights the completions with required things first the lexicographically"""
        priority = ''
        if val.display_meta and val.display_meta.startswith('[REQUIRED]'):
            priority = ' '  # a space has the lowest ordinance
        return priority + val.text

    completions = []
    for comp in gen:
        if comp.text not in BLACKLISTED_COMPLETIONS:
            completions.append(comp)
    return sorted(completions, key=_get_weight)


# pylint: disable=too-many-instance-attributes
class AzCompleter(Completer):
    """ Completes Azure CLI commands """

    def __init__(self, commands, global_params=True, outstream=sys.stderr):
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
        # a dictionary of which parameters mean the same thing
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

        from azclishell._dump_commands import CMD_TABLE
        self.cmdtab = CMD_TABLE
        self.parser.load_command_table(CMD_TABLE)
        self.argsfinder = ArgsFinder(self.parser, outstream)

    def validate_completion(self, param, words, text_before_cursor, double=True):
        """ validates that a param should be completed """
        return param.lower().startswith(words.lower()) and param.lower() != words.lower() and\
            param not in text_before_cursor.split() and not \
            text_before_cursor[-1].isspace() and\
            (not (double and param in self.same_param_doubles) or
             self.same_param_doubles[param] not in text_before_cursor.split())

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        self.branch = self.command_tree
        self.curr_command = ''
        self._is_command = True

        text = reformat_cmd(text)
        if text.split():

            for comp in sort_completions(self.gen_cmd_and_param_completions(text)):
                yield comp

        for cmd in sort_completions(self.gen_cmd_completions(text)):
            yield cmd

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
                    if choice.lower().startswith(prefix.lower())\
                       and choice not in text.split():
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

    def mute_parse_args(self, text):
        """ mutes the parser error when parsing, the puts it back """
        error = AzCliCommandParser.error
        AzCliCommandParser.error = error_pass

        parse_args = self.argsfinder.get_parsed_args(
            parse_quotes(text, quotes=False, string=False))

        AzCliCommandParser.error = error
        return parse_args

    # pylint: disable=too-many-branches
    def gen_dynamic_completions(self, text):
        """ generates the dynamic values, like the names of resource groups """
        try:
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

                            for comp in gen_dyn_completion(
                                    comp, started_param, prefix, text):
                                yield comp
                    except TypeError:
                        try:
                            for comp in self.cmdtab[self.curr_command].\
                                    arguments[arg_name].completer(prefix=prefix):

                                for comp in gen_dyn_completion(
                                        comp, started_param, prefix, text):
                                    yield comp
                        except TypeError:
                            try:
                                for comp in self.cmdtab[self.curr_command].\
                                        arguments[arg_name].completer():

                                    for comp in gen_dyn_completion(
                                            comp, started_param, prefix, text):
                                        yield comp

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
        elif len(text.split()) > 0 and text[-1].isspace() and self._is_command:
            if self.branch is not self.command_tree:
                for com in self.branch.children:
                    yield Completion(com.data)

    def yield_param_completion(self, param, last_word):
        """ yields a parameter """
        return Completion(param, -len(last_word), display_meta=self.get_param_description(
            self.curr_command + " " + str(param)).replace('\n', ''))

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

        if len(text) > 0 and text[-1].isspace():
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
            if self.has_parameters(self.curr_command):
                for param in self.command_parameters[self.curr_command]:
                    if self.validate_completion(param, last_word, text) and\
                            not param.startswith("--"):
                        yield self.yield_param_completion(param, last_word)

        elif last_word.startswith("--"):  # for regular parameters
            self._is_command = False

            if self.has_parameters(self.curr_command):  # Everything should, map to empty list
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
        if txtspt and len(txtspt) > 0:
            for param in self.global_param:
                # for single dash global parameters
                if txtspt[-1].startswith('-') \
                        and not txtspt[-1].startswith('--') and \
                        param.startswith('-') and not param.startswith('--') and\
                        self.validate_completion(param, txtspt[-1], text, double=False):
                    yield Completion(
                        param, -len(txtspt[-1]),
                        display_meta=self.global_param_descriptions[param])
                # for double dash global parameters
                elif txtspt[-1].startswith('--') and \
                        self.validate_completion(param, txtspt[-1], text, double=False):
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
                    if self.validate_completion(opt, txtspt[-1], text, double=False):
                        yield Completion(opt, -len(txtspt[-1]))

    def is_completable(self, symbol):
        """ whether the word can be completed as a command or parameter """
        return self.has_parameters(symbol) or symbol in self.param_description.keys()

    def get_param_description(self, param):
        """ gets a description of an empty string """
        if param in self.param_description:
            return self.param_description[param]
        else:
            return ""

    def has_parameters(self, command):
        """ returns whether given command is valid """
        return command in self.command_parameters.keys()

    def has_description(self, param):
        """ if a parameter has a description """
        return param in self.param_description.keys() and \
            not self.param_description[param].isspace()
