# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import absolute_import, division, print_function, unicode_literals

import os
from prompt_toolkit.completion import Completer, Completion
from azure.cli.core.parser import AzCliCommandParser
from azure.cli.command_modules.interactive.events import (
    EVENT_INTERACTIVE_PRE_COMPLETER_TEXT_PARSING,
    EVENT_INTERACTIVE_POST_SUB_TREE_CREATE
)
from . import configuration
from .argfinder import ArgsFinder
from .util import parse_quotes

SELECT_SYMBOL = configuration.SELECT_SYMBOL


def error_pass(_, message):  # pylint: disable=unused-argument
    return


def _check_value_muted(_, action, value):
    # patch for AzCliCommandParser that does no logging
    if action.choices is not None and value not in action.choices:
        import argparse
        msg = 'invalid choice: {}'.format(value)
        raise argparse.ArgumentError(action, msg)


def sort_completions(completions_gen):
    """ sorts the completions """
    from knack.help import REQUIRED_TAG

    def _get_weight(val):
        """ weights the completions with required things first the lexicographically"""
        priority = ''
        if val.display_meta and val.display_meta.startswith(REQUIRED_TAG):
            priority = ' '  # a space has the lowest ordinance
        return priority + val.text

    return sorted(completions_gen, key=_get_weight)


# pylint: disable=too-many-instance-attributes
class AzCompleter(Completer):
    """ Completes Azure CLI commands """

    def __init__(self, shell_ctx, commands, global_params=True):
        self.shell_ctx = shell_ctx
        self.started = False

        # dictionary of command to descriptions
        self.command_description = {}
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

        # information about what completions to generate
        self.current_command = ''
        self.unfinished_word = ''
        self.subtree = None
        self.leftover_args = None
        self.complete_command = False

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
            self.start(commands, global_params=global_params)

    def __bool__(self):
        return self.started

    def start(self, commands, global_params=True):
        self.started = True
        self.command_description = commands.descrip
        self.completable_param = commands.completable_param
        self.command_tree = commands.command_tree
        self.param_description = commands.param_descript
        self.command_examples = commands.command_example
        self.command_param_info = commands.command_param_info or self.command_param_info

        if global_params:
            self.global_param = commands.global_param
            self.output_choices = commands.output_choices
            self.output_options = commands.output_options
            self.global_param_descriptions = commands.global_param_descriptions

    def initialize_command_table_attributes(self):
        from ._dump_commands import FreshTable
        loader = FreshTable(self.shell_ctx).loader
        if loader and loader.command_table:
            self.cmdtab = loader.command_table
            self.parser.load_command_table(loader)
            self.argsfinder = ArgsFinder(self.parser)

    def validate_param_completion(self, param, leftover_args):
        """ validates that a param should be completed """
        # validates param starts with unfinished word
        completes = self.validate_completion(param)

        # show parameter completions when started
        full_param = self.unfinished_word.startswith("--") and param.startswith("--")
        char_param = self.unfinished_word.startswith("-") and not param.startswith("--")

        # show full parameters before any are used
        new_param = not self.unfinished_word and not leftover_args and param.startswith("--")

        # checks for parameters already in the line as well as aliases
        no_doubles = True
        command_doubles = self.command_param_info.get(self.current_command, {})
        for alias in command_doubles.get(param, []):
            if alias in leftover_args:
                no_doubles = False

        return completes and no_doubles and any((full_param, char_param, new_param))

    def validate_completion(self, completion):
        return completion.lower().startswith(self.unfinished_word.lower())

    def process_dynamic_completion(self, completion):
        """ how to validate and generate completion for dynamic params """
        if len(completion.split()) > 1:
            completion = '\"' + completion + '\"'

        if self.validate_completion(completion):
            yield Completion(completion, -len(self.unfinished_word))

    def get_completions(self, document, complete_event):
        if not self.started:
            return

        text = self.reformat_cmd(document.text_before_cursor)
        event_payload = {
            'text': text
        }
        self.shell_ctx.cli_ctx.raise_event(EVENT_INTERACTIVE_PRE_COMPLETER_TEXT_PARSING, event_payload=event_payload)
        # Reload various attributes from event_payload
        text = event_payload.get('text', text)
        text_split = text.split()
        self.unfinished_word = ''
        new_word = text and text[-1].isspace()
        if not new_word and text_split:
            self.unfinished_word = text_split[-1]
            text_split = text_split[:-1]

        self.subtree, self.current_command, self.leftover_args = self.command_tree.get_sub_tree(text_split)
        self.shell_ctx.cli_ctx.raise_event(EVENT_INTERACTIVE_POST_SUB_TREE_CREATE, subtree=self.subtree)
        self.complete_command = not self.subtree.children

        for comp in sort_completions(self.gen_cmd_and_param_completions()):
            yield comp

        for comp in sort_completions(self.gen_global_params_and_arg_completions()):
            yield comp

        if self.complete_command and self.cmdtab and self.leftover_args and self.leftover_args[-1].startswith('-'):
            for comp in sort_completions(self.gen_dynamic_completions(text)):
                yield comp

    def gen_enum_completions(self, arg_name):
        """ generates dynamic enumeration completions """
        try:  # if enum completion
            for choice in self.cmdtab[self.current_command].arguments[arg_name].choices:
                if self.validate_completion(choice):
                    yield Completion(choice, -len(self.unfinished_word))

        except TypeError:  # there is no choices option
            pass

    def get_arg_name(self, param):
        """ gets the argument name used in the command table for a parameter """
        if self.current_command in self.cmdtab:
            for arg in self.cmdtab[self.current_command].arguments:

                for name in self.cmdtab[self.current_command].arguments[arg].options_list:
                    if name == param:
                        return arg
        return None

    # pylint: disable=protected-access
    def mute_parse_args(self, text):
        """ mutes the parser error when parsing, then puts it back """
        error = AzCliCommandParser.error
        _check_value = AzCliCommandParser._check_value

        AzCliCommandParser.error = error_pass
        AzCliCommandParser._check_value = _check_value_muted

        # No exception is expected. However, we add this try-catch block, as this may have far-reaching effects.
        try:
            parse_args = self.argsfinder.get_parsed_args(parse_quotes(text, quotes=False, string=False))
        except Exception:  # pylint: disable=broad-except
            pass

        AzCliCommandParser.error = error
        AzCliCommandParser._check_value = _check_value
        return parse_args

    # pylint: disable=too-many-branches
    def gen_dynamic_completions(self, text):
        """ generates the dynamic values, like the names of resource groups """
        try:  # pylint: disable=too-many-nested-blocks
            param = self.leftover_args[-1]

            # command table specific name
            arg_name = self.get_arg_name(param)

            for comp in self.gen_enum_completions(arg_name):
                yield comp

            parsed_args = self.mute_parse_args(text)

            # there are 3 formats for completers the cli uses
            # this try catches which format it is
            if self.cmdtab[self.current_command].arguments[arg_name].completer:
                completions = []
                try:
                    completions = self.cmdtab[self.current_command].arguments[arg_name].completer(
                        prefix=self.unfinished_word, action=None, parsed_args=parsed_args)
                except TypeError:
                    try:
                        completions = self.cmdtab[self.current_command].arguments[arg_name].completer(
                            prefix=self.unfinished_word)
                    except TypeError:
                        try:
                            completions = self.cmdtab[self.current_command].arguments[arg_name].completer()
                        except TypeError:
                            pass  # other completion method used

                for comp in completions:
                    for completion in self.process_dynamic_completion(comp):
                        yield completion

        # if the user isn't logged in
        except Exception:  # pylint: disable=broad-except
            pass

    def yield_param_completion(self, param, last_word):
        """ yields a parameter """
        return Completion(param, -len(last_word), display_meta=self.param_description.get(
            self.current_command + " " + str(param), '').replace(os.linesep, ''))

    def gen_cmd_and_param_completions(self):
        """ generates command and parameter completions """
        if self.complete_command:
            for param in self.command_param_info.get(self.current_command, []):
                if self.validate_param_completion(param, self.leftover_args):
                    yield self.yield_param_completion(param, self.unfinished_word)
        elif not self.leftover_args:
            for child_command in self.subtree.children:
                if self.validate_completion(child_command):
                    yield Completion(child_command, -len(self.unfinished_word))

    def gen_global_params_and_arg_completions(self):
        # global parameters
        for param in self.global_param:
            if self.validate_param_completion(param, self.leftover_args) and self.unfinished_word:
                if param in self.output_options and not self.complete_command:
                    continue
                yield Completion(param, -len(self.unfinished_word), display_meta=self.global_param_descriptions[param])

        # global parameter args
        if self.leftover_args and self.leftover_args[-1] in self.output_options:
            for opt in self.output_choices:
                if self.validate_completion(opt):
                    yield Completion(opt, -len(self.unfinished_word))

    def is_completable(self, symbol):
        """ whether the word can be completed as a command or parameter """
        return symbol in self.command_description or symbol in self.param_description

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
