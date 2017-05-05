# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import unicode_literals, print_function

import json
import math
import os
import subprocess
import sys

import jmespath
from six.moves import configparser

from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.filters import Always
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.interface import CommandLineInterface, Application
from prompt_toolkit.shortcuts import create_eventloop

import azclishell.configuration
from azclishell.az_lexer import AzLexer, ExampleLexer, ToolbarLexer
from azclishell.command_tree import in_tree
from azclishell.gather_commands import add_random_new_lines
from azclishell.key_bindings import registry, get_section, sub_section
from azclishell.layout import create_layout, create_tutorial_layout, set_scope
from azclishell.telemetry import TC as telemetry
from azclishell.util import get_window_dim, parse_quotes, get_os_clear_screen_word

import azure.cli.core.azlogging as azlogging
from azure.cli.core.application import Configuration
from azure.cli.core.cloud import get_active_cloud_name
from azure.cli.core._config import az_config, DEFAULTS_SECTION
from azure.cli.core._environment import get_config_dir
from azure.cli.core._profile import _SUBSCRIPTION_NAME, Profile
from azure.cli.core._session import ACCOUNT, CONFIG, SESSION
from azure.cli.core.util import (show_version_info_exit, handle_exception)
from azure.cli.core.util import CLIError


SHELL_CONFIGURATION = azclishell.configuration.CONFIGURATION
SHELL_CONFIG_DIR = azclishell.configuration.get_config_dir

NOTIFICATIONS = ""
PROFILE = Profile()
SELECT_SYMBOL = azclishell.configuration.SELECT_SYMBOL
PART_SCREEN_EXAMPLE = .3
CLEAR_WORD = get_os_clear_screen_word()


def handle_cd(cmd):
    """changes dir """
    if len(cmd) != 2:
        print("Invalid syntax: cd path")
        return
    path = os.path.expandvars(os.path.expanduser(cmd[1]))
    try:
        os.chdir(path)
    except OSError as ex:
        print("cd: %s\n" % ex)


def space_examples(list_examples, rows):
    """ makes the example text """
    examples_with_index = []

    for i, _ in list(enumerate(list_examples)):
        examples_with_index.append("[" + str(i + 1) + "] " + list_examples[i][0] +
                                   list_examples[i][1])

    example = "".join(exam for exam in examples_with_index)
    num_newline = example.count('\n')

    page_number = ''
    if num_newline > rows * PART_SCREEN_EXAMPLE:
        len_of_excerpt = math.floor(float(rows) * PART_SCREEN_EXAMPLE)

        group = example.split('\n')
        end = int(get_section() * len_of_excerpt)
        begin = int((get_section() - 1) * len_of_excerpt)

        if get_section() * len_of_excerpt < num_newline:
            example = '\n'.join(group[begin:end]) + "\n"
        else:  # default chops top off
            example = '\n'.join(group[begin:]) + "\n"
            while ((get_section() - 1) * len_of_excerpt) > num_newline:
                sub_section()
        page_number = '\n' + str(get_section()) + "/" + str(math.ceil(num_newline / len_of_excerpt))

    return example + page_number


def _toolbar_info():
    sub_name = ""
    try:
        sub_name = PROFILE.get_subscription()[_SUBSCRIPTION_NAME]
    except CLIError:
        pass

    curr_cloud = "Cloud: {}".format(get_active_cloud_name())
    tool_val = '{}'.format('Subscription: {}'.format(sub_name) if sub_name else curr_cloud)

    settings_items = [
        " [F1]Layout",
        "[F2]Defaults",
        "[F3]Keys",
        "[Ctrl+D]Quit",
        tool_val
    ]
    return settings_items


def space_toolbar(settings_items, cols, empty_space):
    """ formats the toolbar """
    counter = 0
    for part in settings_items:
        counter += len(part)
    spacing = empty_space[:int(math.floor((cols - counter) / (len(settings_items) - 1)))]

    settings = spacing.join(settings_items)

    empty_space = empty_space[len(NOTIFICATIONS) + len(settings) + 1:]
    return settings, empty_space


# pylint: disable=too-many-instance-attributes
class Shell(object):
    """ represents the shell """

    # pylint: disable=too-many-arguments
    def __init__(self, completer=None, styles=None,
                 lexer=None, history=InMemoryHistory(),
                 app=None, input_custom=sys.stdout, output_custom=None):
        self.styles = styles
        if styles:
            self.lexer = lexer or AzLexer
        else:
            self.lexer = None
        self.app = app
        self.completer = completer
        self.history = history
        self._cli = None
        self.refresh_cli = False
        self.layout = None
        self.description_docs = u''
        self.param_docs = u''
        self.example_docs = u''
        self._env = os.environ
        self.last = None
        self.last_exit = 0
        self.input = input_custom
        self.output = output_custom
        self.config_default = ""
        self.default_command = ""

    @property
    def cli(self):
        """ Makes the interface or refreshes it """
        if self._cli is None or self.refresh_cli:
            self._cli = self.create_interface()
            self.refresh_cli = False
        return self._cli

    def on_input_timeout(self, cli):
        """
        brings up the metadata for the command if there is a valid command already typed
        """
        _, cols = get_window_dim()
        cols = int(cols)
        document = cli.current_buffer.document
        text = document.text
        empty_space = ""
        for i in range(cols):  # pylint: disable=unused-variable
            empty_space += " "

        text = text.replace('az', '')
        if self.default_command:
            text = self.default_command + ' ' + text

        param_info, example = self.generate_help_text(text)

        self.param_docs = u'{}'.format(param_info)
        self.example_docs = u'{}'.format(example)

        self._update_default_info()

        settings, empty_space = space_toolbar(_toolbar_info(), cols, empty_space)

        cli.buffers['description'].reset(
            initial_document=Document(self.description_docs, cursor_position=0))
        cli.buffers['parameter'].reset(
            initial_document=Document(self.param_docs))
        cli.buffers['examples'].reset(
            initial_document=Document(self.example_docs))
        cli.buffers['bottom_toolbar'].reset(
            initial_document=Document(u'{}{}{}'.format(NOTIFICATIONS, settings, empty_space)))
        cli.buffers['default_values'].reset(
            initial_document=Document(
                u'{}'.format(self.config_default if self.config_default else 'No Default Values')))
        cli.request_redraw()

    def generate_help_text(self, text):
        """ generates the help text based on commands typed """
        command = param_descrip = example = ""
        any_documentation = False
        is_command = True
        rows, _ = get_window_dim()
        rows = int(rows)

        for word in text.split():
            if word.startswith("-"):  # any parameter
                is_command = False
            if is_command:
                command += str(word) + " "

            if self.completer.is_completable(command.rstrip()):
                cmdstp = command.rstrip()
                any_documentation = True

                if word in self.completer.command_parameters[cmdstp] and \
                   self.completer.has_description(cmdstp + " " + word):
                    param_descrip = word + ":\n" + \
                        self.completer.get_param_description(
                            cmdstp + " " + word)

                self.description_docs = u'{}'.format(
                    self.completer.command_description[cmdstp])

                if cmdstp in self.completer.command_examples:
                    string_example = ""
                    for example in self.completer.command_examples[cmdstp]:
                        for part in example:
                            string_example += part
                    example = space_examples(
                        self.completer.command_examples[cmdstp], rows)

        if not any_documentation:
            self.description_docs = u''
        return param_descrip, example

    def _update_default_info(self):
        try:
            options = az_config.config_parser.options(DEFAULTS_SECTION)
            self.config_default = ""
            for opt in options:
                self.config_default += opt + ": " + az_config.get(DEFAULTS_SECTION, opt) + "  "
        except configparser.NoSectionError:
            self.config_default = ""

    def create_application(self, full_layout=True):
        """ makes the application object and the buffers """
        if full_layout:
            layout = create_layout(self.lexer, ExampleLexer, ToolbarLexer)
        else:
            layout = create_tutorial_layout(self.lexer)

        buffers = {
            DEFAULT_BUFFER: Buffer(is_multiline=True),
            'description': Buffer(is_multiline=True, read_only=True),
            'parameter': Buffer(is_multiline=True, read_only=True),
            'examples': Buffer(is_multiline=True, read_only=True),
            'bottom_toolbar': Buffer(is_multiline=True),
            'example_line': Buffer(is_multiline=True),
            'default_values': Buffer(),
            'symbols': Buffer()
        }

        writing_buffer = Buffer(
            history=self.history,
            auto_suggest=AutoSuggestFromHistory(),
            enable_history_search=True,
            completer=self.completer,
            complete_while_typing=Always()
        )

        return Application(
            mouse_support=False,
            style=self.styles,
            buffer=writing_buffer,
            on_input_timeout=self.on_input_timeout,
            key_bindings_registry=registry,
            layout=layout,
            buffers=buffers,
        )

    def create_interface(self):
        """ instantiates the intereface """
        return CommandLineInterface(
            application=self.create_application(),
            eventloop=create_eventloop())

    def set_prompt(self, prompt_command="", position=0):
        """ writes the prompt line """
        self.description_docs = u'{}'.format(prompt_command)
        self.cli.current_buffer.reset(
            initial_document=Document(
                self.description_docs,
                cursor_position=position))
        self.cli.request_redraw()

    def set_scope(self, value):
        """ narrows the scopes the commands """

        set_scope(value)
        if self.default_command:
            self.default_command += ' ' + value
        else:
            self.default_command += value
        return value

    def handle_example(self, text, continue_flag):
        """ parses for the tutorial """
        cmd = text.partition(SELECT_SYMBOL['example'])[0].rstrip()
        num = text.partition(SELECT_SYMBOL['example'])[2].strip()
        example = ""
        try:
            num = int(num) - 1
        except ValueError:
            print("An Integer should follow the colon")
            return ""
        if cmd in self.completer.command_examples:
            if num >= 0 and num < len(self.completer.command_examples[cmd]):
                example = self.completer.command_examples[cmd][num][1]
                example = example.replace('\n', '')
            else:
                print('Invalid example number')
                return '', True

        example = example.replace('az', '')

        starting_index = None
        counter = 0
        example_no_fill = ""
        flag_fill = True
        for word in example.split():
            if flag_fill:
                example_no_fill += word + " "
            if word.startswith('-'):
                example_no_fill += word + " "
                if not starting_index:
                    starting_index = counter
                flag_fill = False
            counter += 1

        return self.example_repl(example_no_fill, example, starting_index, continue_flag)

    def example_repl(self, text, example, start_index, continue_flag):
        """ REPL for interactive tutorials """

        if start_index:
            start_index = start_index + 1
            cmd = ' '.join(text.split()[:start_index])
            example_cli = CommandLineInterface(
                application=self.create_application(
                    full_layout=False),
                eventloop=create_eventloop())
            example_cli.buffers['example_line'].reset(
                initial_document=Document(u'{}\n'.format(
                    add_random_new_lines(example)))
            )
            while start_index < len(text.split()):
                if self.default_command:
                    cmd = cmd.replace(self.default_command + ' ', '')
                example_cli.buffers[DEFAULT_BUFFER].reset(
                    initial_document=Document(
                        u'{}'.format(cmd),
                        cursor_position=len(cmd)))
                example_cli.request_redraw()
                answer = example_cli.run()
                if not answer:
                    return "", True
                answer = answer.text
                if answer.strip('\n') == cmd.strip('\n'):
                    continue
                else:
                    if len(answer.split()) > 1:
                        start_index += 1
                        cmd += " " + answer.split()[-1] + " " +\
                               u' '.join(text.split()[start_index:start_index + 1])
            example_cli.exit()
            del example_cli
        else:
            cmd = text

        return cmd, continue_flag

    # pylint: disable=too-many-branches
    def _special_cases(self, text, cmd, outside):
        break_flag = False
        continue_flag = False

        if text and len(text.split()) > 0 and text.split()[0].lower() == 'az':
            telemetry.track_ssg('az', text)
            cmd = ' '.join(text.split()[1:])
        if self.default_command:
            cmd = self.default_command + " " + cmd

        if text.strip() == "quit" or text.strip() == "exit":
            break_flag = True
        elif text.strip() == "clear-history":  # clears the history, but only when you restart
            outside = True
            cmd = 'echo -n "" >' +\
                os.path.join(
                    SHELL_CONFIG_DIR(),
                    SHELL_CONFIGURATION.get_history())
        elif text.strip() == CLEAR_WORD:
            outside = True
            cmd = CLEAR_WORD
        if '--version' in text:
            try:
                continue_flag = True
                show_version_info_exit(sys.stdout)
            except SystemExit:
                pass
        if text:
            if text[0] == SELECT_SYMBOL['outside']:
                cmd = text[1:]
                outside = True
                if cmd.strip() and cmd.split()[0] == 'cd':
                    handle_cd(parse_quotes(cmd))
                    continue_flag = True
                telemetry.track_ssg('outside', cmd)

            elif text[0] == SELECT_SYMBOL['exit_code']:
                meaning = "Success" if self.last_exit == 0 else "Failure"

                print(meaning + ": " + str(self.last_exit))
                continue_flag = True
                telemetry.track_ssg('exit code', cmd)

            elif text[0] == SELECT_SYMBOL['query']:  # query previous output
                continue_flag = self.handle_jmespath_query(text, continue_flag)

            elif "|" in text or ">" in text:  # anything I don't parse, send off
                outside = True
                cmd = "az " + cmd

            elif SELECT_SYMBOL['example'] in text:
                cmd, continue_flag = self.handle_example(cmd, continue_flag)
                telemetry.track_ssg('tutorial', text)

        continue_flag, cmd = self.handle_scoping_input(continue_flag, cmd, text)

        return break_flag, continue_flag, outside, cmd

    def handle_jmespath_query(self, text, continue_flag):
        if self.last and self.last.result:
            if hasattr(self.last.result, '__dict__'):
                input_dict = dict(self.last.result)
            else:
                input_dict = self.last.result
            try:
                query_text = text.partition(SELECT_SYMBOL['query'])[2]
                result = ""
                if query_text:
                    result = jmespath.search(
                        query_text, input_dict)
                if isinstance(result, str):
                    print(result)
                else:
                    print(json.dumps(result, sort_keys=True, indent=2))
            except jmespath.exceptions.ParseError:
                print("Invalid Query")
        continue_flag = True
        telemetry.track_ssg('query', text)
        return continue_flag

    def handle_scoping_input(self, continue_flag, cmd, text):
        default_split = text.partition(SELECT_SYMBOL['scope'])[2].split()
        cmd = cmd.replace(SELECT_SYMBOL['scope'], '')

        if text and SELECT_SYMBOL['scope'] == text[0:2]:
            continue_flag = True

            if not default_split:
                self.default_command = ""
                set_scope("", add=False)
                print('unscoping all')

                return continue_flag, cmd

            while default_split:
                if not text:
                    value = ''
                else:
                    value = default_split[0]

                if self.default_command:
                    tree_val = self.default_command + " " + value
                else:
                    tree_val = value

                if in_tree(self.completer.command_tree, tree_val.strip()):
                    self.set_scope(value)
                    print("defaulting: " + value)
                    cmd = cmd.replace(SELECT_SYMBOL['scope'], '')
                    telemetry.track_ssg('scope command', value)

                elif SELECT_SYMBOL['unscope'] == default_split[0] and \
                        len(self.default_command.split()) > 0:

                    value = self.default_command.split()[-1]
                    self.default_command = ' ' + ' '.join(self.default_command.split()[:-1])

                    if not self.default_command.strip():
                        self.default_command = self.default_command.strip()
                    set_scope(self.default_command, add=False)
                    print('unscoping: ' + value)

                elif SELECT_SYMBOL['unscope'] not in text:
                    print("Scope must be a valid command")

                default_split = default_split[1:]
        else:
            return continue_flag, cmd
        return continue_flag, cmd

    def cli_execute(self, cmd):
        try:
            args = parse_quotes(cmd)
            azlogging.configure_logging(args)

            azure_folder = get_config_dir()
            if not os.path.exists(azure_folder):
                os.makedirs(azure_folder)
            ACCOUNT.load(os.path.join(azure_folder, 'azureProfile.json'))
            CONFIG.load(os.path.join(azure_folder, 'az.json'))
            SESSION.load(os.path.join(azure_folder, 'az.sess'), max_age=3600)

            config = Configuration()
            self.app.initialize(config)
            result = self.app.execute(args)
            self.last_exit = 0
            if result and result.result is not None:
                from azure.cli.core._output import OutputProducer
                if self.output:
                    self.output.out(result)
                else:
                    formatter = OutputProducer.get_formatter(
                        self.app.configuration.output_format)
                    OutputProducer(formatter=formatter, file=sys.stdout).out(result)
                    self.last = result

        except Exception as ex:  # pylint: disable=broad-except
            self.last_exit = handle_exception(ex)
        except SystemExit as ex:
            self.last_exit = int(ex.code)

    def run(self):

        telemetry.start()

        from azclishell.configuration import SHELL_HELP
        self.cli.buffers['symbols'].reset(
            initial_document=Document(u'{}'.format(SHELL_HELP)))

        while True:
            try:
                try:
                    document = self.cli.run(reset_current_buffer=True)
                    text = document.text
                    if not text:  # not input
                        self.set_prompt()
                        continue
                    cmd = text
                    outside = False

                except AttributeError:  # when the user pressed Control D
                    break
                else:
                    b_flag, c_flag, outside, cmd = self._special_cases(text, cmd, outside)

                    if b_flag:
                        break
                    if c_flag:
                        self.set_prompt()
                        continue

                    if not self.default_command:
                        self.history.append(text)

                    self.set_prompt()

                    if outside:
                        subprocess.Popen(cmd, shell=True).communicate()
                    else:
                        self.cli_execute(cmd)
            except KeyboardInterrupt:  # CTRL C
                self.set_prompt()
                continue

        print('Have a lovely day!!')
        telemetry.conclude()
