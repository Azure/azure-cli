# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import absolute_import, division, print_function, unicode_literals

from prompt_toolkit.completion import Completer, Completion
from azure.cli.core.parser import AzCliCommandParser
from . import configuration
from .argfinder import ArgsFinder
from .command_tree import in_tree, get_sub_tree
from .util import parse_quotes

SELECT_SYMBOL = configuration.SELECT_SYMBOL


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
        self.shell_ctx = None

        # dictionary of command to descriptions
        self.command_description = None
        # a list of all the possible parameters
        self.completable_param = None
        # the command tree
        self.command_tree = None
        # a dictionary of parameter (which is command + " " + parameter name)
        # to a description of what it does
        self.param_description = None
        # a dictionary of command to examples of how to use it
        self.command_examples = None
        # a dictionary of commands with parameters with multiple names (e.g. {'vm create':{-n: --name}})
        self.command_param_info = {}

        self._is_command = True

        self.branch = None
        self.curr_command = ""

        self.global_param = []
        self.output_choices = []
        self.output_options = []
        self.global_param_descriptions = []

        self.global_parser = AzCliCommandParser(add_help=False)
        self.global_parser.add_argument_group('global', 'Global Arguments')
        self.parser = AzCliCommandParser(parents=[self.global_parser])
        self.argsfinder = ArgsFinder(self.parser)
        self.cmdtab = {}

        if commands:
            self.start(shell_ctx, commands, global_params=global_params)

    def __bool__(self):
        return bool(self.shell_ctx)

    def start(self, shell_ctx, commands, global_params=True):
        self.shell_ctx = shell_ctx
        self.command_description = commands.descrip
        self.completable_param = commands.completable_param
        self.command_tree = commands.command_tree
        self.param_description = commands.param_descript
        self.command_examples = commands.command_example
        self.command_param_info = commands.command_param_info or self.command_param_info

        self.branch = self.command_tree

        if global_params:
            self.global_param = commands.global_param
            self.output_choices = commands.output_choices
            self.output_options = commands.output_options
            self.global_param_descriptions = commands.global_param_descriptions

    def initialize_command_table_attributes(self):
        from ._dump_commands import FreshTable
        self.cmdtab = FreshTable(self.shell_ctx).command_table
        if self.cmdtab:
            self.parser.load_command_table(self.cmdtab)
            self.argsfinder = ArgsFinder(self.parser)

    def validate_param_completion(self, param, unfinished_word, leftover_args, check_double=True):
        """ validates that a param should be completed """
        # validates param starts with unfinished word
        completes = self.validate_completion(param, unfinished_word)

        # checks for parameters already in the line as well as aliases
        no_doubles = True
        command_doubles = self.command_param_info.get(self.curr_command, {})
        for alias in command_doubles.get(param, []):
            if alias in leftover_args:
                no_doubles = False

        return completes and no_doubles

    def validate_completion(self, completion, unfinished_word):
        return completion.lower().startswith(unfinished_word.lower())

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        self.branch = self.command_tree
        self.curr_command = ''
        self._is_command = True
        text = self.reformat_cmd(text)

        for comp in sort_completions(self.gen_cmd_and_param_completions(text)):
            yield comp

        for param in sort_completions(self.gen_global_param_completions(text)):
            yield param

        if self.cmdtab:
            for val in sort_completions(self.gen_dynamic_completions(text)):
                yield val

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

    def yield_param_completion(self, param, last_word):
        """ yields a parameter """
        return Completion(param, -len(last_word), display_meta=self.param_description.get(
            self.curr_command + " " + str(param), '').replace('\n', ''))

    def gen_cmd_and_param_completions(self, text):
        """ generates command and parameter completions """
        txtspt = text.split()
        new_word = text and text[-1].isspace()
        last_word = ''
        if not new_word and txtspt:
            last_word = txtspt[-1]
            txtspt = txtspt[:-1]

        subtree, current_command, leftover_args = get_sub_tree(self.command_tree, txtspt)

        self._is_command = subtree.children

        self.curr_command = current_command

        if not self._is_command:
            for param in self.command_param_info.get(self.curr_command, []):
                if not self.validate_param_completion(param, last_word, leftover_args):
                    continue
                full_param = last_word.startswith("--") and param.startswith("--")
                char_param = last_word.startswith("-") and not param.startswith("--")
                new_param = new_word and not leftover_args and param.startswith("--")
                if full_param or char_param or new_param:
                    yield self.yield_param_completion(param, last_word)
        else:
            for kid in subtree.children:
                if self.validate_completion(kid, last_word):
                    yield Completion(kid, -len(last_word))

    def gen_global_param_completions(self, text):
        """ Global parameter stuff hard-coded in """
        txtspt = text.split()
        if txtspt and txtspt:
            for param in self.global_param:
                # for single dash global parameters
                if txtspt[-1].startswith('-') \
                        and not txtspt[-1].startswith('--') and \
                        param.startswith('-') and not param.startswith('--') and\
                        self.validate_param_completion(param, txtspt[-1], text, check_double=False):
                    yield Completion(
                        param, -len(txtspt[-1]),
                        display_meta=self.global_param_descriptions[param])
                # for double dash global parameters
                elif txtspt[-1].startswith('--') and \
                        self.validate_param_completion(param, txtspt[-1], text, check_double=False):
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
                    if self.validate_param_completion(opt, txtspt[-1], text, check_double=False):
                        yield Completion(opt, -len(txtspt[-1]))

    def is_completable(self, symbol):
        """ whether the word can be completed as a command or parameter """
        return symbol in self.command_param_info or symbol in self.param_description.keys()

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
