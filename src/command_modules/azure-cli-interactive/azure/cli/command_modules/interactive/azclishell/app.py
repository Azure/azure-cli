# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from __future__ import unicode_literals, print_function

import datetime
import json
import math
import os
import re
import subprocess
import sys
from threading import Thread

import jmespath
from six.moves import configparser

from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.filters import Always
from prompt_toolkit.history import FileHistory
from prompt_toolkit.interface import Application
from prompt_toolkit.shortcuts import create_eventloop

from knack.log import get_logger
from knack.util import CLIError

from azure.cli.core.commands.client_factory import ENV_ADDITIONAL_USER_AGENT
from azure.cli.core._config import DEFAULTS_SECTION
from azure.cli.core._profile import _SUBSCRIPTION_NAME, Profile
from azure.cli.core._session import ACCOUNT, CONFIG, SESSION
from azure.cli.core.api import get_config_dir
from azure.cli.core.util import handle_exception

from . import __version__
from .az_completer import AzCompleter
from .az_lexer import get_az_lexer, ExampleLexer, ToolbarLexer
from .configuration import Configuration, SELECT_SYMBOL
from .frequency_heuristic import DISPLAY_TIME, frequency_heuristic
from .gather_commands import add_new_lines, GatherCommands
from .key_bindings import InteractiveKeyBindings
from .layout import LayoutManager
from .progress import progress_view
from . import telemetry
from .threads import LoadCommandTableThread
from .util import get_window_dim, parse_quotes, get_os_clear_screen_word


NOTIFICATIONS = ""
PART_SCREEN_EXAMPLE = .3
START_TIME = datetime.datetime.utcnow()
CLEAR_WORD = get_os_clear_screen_word()

logger = get_logger(__name__)


def space_toolbar(settings_items, empty_space):
    """ formats the toolbar """
    counter = 0
    for part in settings_items:
        counter += len(part)

    if len(settings_items) == 1:
        spacing = ''
    else:
        spacing = empty_space[
            :int(math.floor((len(empty_space) - counter) / (len(settings_items) - 1)))]

    settings = spacing.join(settings_items)

    empty_space = empty_space[len(NOTIFICATIONS) + len(settings) + 1:]
    return settings, empty_space


# pylint: disable=too-many-instance-attributes
class AzInteractiveShell(object):

    def __init__(self, cli_ctx, style=None, completer=None,
                 lexer=None, history=None,
                 input_custom=sys.stdin, output_custom=None,
                 user_feedback=False, intermediate_sleep=.25, final_sleep=4):

        from .color_styles import style_factory

        self.cli_ctx = cli_ctx
        self.config = Configuration(cli_ctx.config, style=style)
        self.config.set_style(style)
        self.style = style_factory(self.config.get_style())
        try:
            gathered_commands = GatherCommands(self.config)
            self.completer = completer or AzCompleter(self, gathered_commands)
            self.completer.initialize_command_table_attributes()
            self.lexer = lexer or get_az_lexer(gathered_commands)
        except IOError:  # if there is no cache
            self.completer = AzCompleter(self, None)
            self.lexer = None
        self.history = history or FileHistory(os.path.join(self.config.get_config_dir(), self.config.get_history()))
        os.environ[ENV_ADDITIONAL_USER_AGENT] = 'AZURECLISHELL/' + __version__

        # OH WHAT FUN TO FIGURE OUT WHAT THESE ARE!
        self._cli = None
        self.layout = None
        self.description_docs = u''
        self.param_docs = u''
        self.example_docs = u''
        self.last = None
        self.last_exit = 0
        self.user_feedback = user_feedback
        self.input = input_custom
        self.output = output_custom
        self.config_default = ""
        self.default_command = ""
        self.threads = []
        self.curr_thread = None
        self.spin_val = -1
        self.intermediate_sleep = intermediate_sleep
        self.final_sleep = final_sleep
        self.command_table_thread = None

        # try to consolidate state information here...
        # Used by key bindings and layout
        self.example_page = 1
        self.is_prompting = False
        self.is_example_repl = False
        self.is_showing_default = False
        self.is_symbols = True

    def __call__(self):

        if self.cli_ctx.data["az_interactive_active"]:
            logger.warning("You're in the interactive shell already.")
            return

        if self.config.BOOLEAN_STATES[self.config.config.get('DEFAULT', 'firsttime')]:
            self.config.firsttime()

        if not self.config.has_feedback() and frequency_heuristic(self):
            print("\n\nAny comments or concerns? You can use the \'feedback\' command!" +
                  " We would greatly appreciate it.\n")

        self.cli_ctx.data["az_interactive_active"] = True
        self.run()
        self.cli_ctx.data["az_interactive_active"] = False

    @property
    def cli(self):
        """ Makes the interface or refreshes it """
        if self._cli is None:
            self._cli = self.create_interface()
        return self._cli

    def handle_cd(self, cmd):
        """changes dir """
        if len(cmd) != 2:
            print("Invalid syntax: cd path", file=self.output)
            return
        path = os.path.expandvars(os.path.expanduser(cmd[1]))
        try:
            os.chdir(path)
        except OSError as ex:
            print("cd: %s\n" % ex, file=self.output)

    def on_input_timeout(self, cli):
        """
        brings up the metadata for the command if there is a valid command already typed
        """
        document = cli.current_buffer.document
        text = document.text

        text = text.replace('az ', '')
        if self.default_command:
            text = self.default_command + ' ' + text

        param_info, example = self.generate_help_text()

        self.param_docs = u'{}'.format(param_info)
        self.example_docs = u'{}'.format(example)

        self._update_default_info()

        cli.buffers['description'].reset(
            initial_document=Document(self.description_docs, cursor_position=0))
        cli.buffers['parameter'].reset(
            initial_document=Document(self.param_docs))
        cli.buffers['examples'].reset(
            initial_document=Document(self.example_docs))
        cli.buffers['default_values'].reset(
            initial_document=Document(
                u'{}'.format(self.config_default if self.config_default else 'No Default Values')))
        self._update_toolbar()
        cli.request_redraw()

    def restart_completer(self):
        command_info = GatherCommands(self.config)
        if not self.completer:
            self.completer.start(command_info)
        self.completer.initialize_command_table_attributes()
        if not self.lexer:
            self.lexer = get_az_lexer(command_info)
        self._cli = None

    def _space_examples(self, list_examples, rows, section_value):
        """ makes the example text """
        examples_with_index = []

        for i, _ in list(enumerate(list_examples)):
            if len(list_examples[i]) > 1:
                examples_with_index.append("[" + str(i + 1) + "] " + list_examples[i][0] +
                                           list_examples[i][1])

        example = "".join(exam for exam in examples_with_index)
        num_newline = example.count('\n')

        page_number = ''
        if num_newline > rows * PART_SCREEN_EXAMPLE and rows > PART_SCREEN_EXAMPLE * 10:
            len_of_excerpt = math.floor(float(rows) * PART_SCREEN_EXAMPLE)

            group = example.split('\n')
            end = int(section_value * len_of_excerpt)
            begin = int((section_value - 1) * len_of_excerpt)

            if end < num_newline:
                example = '\n'.join(group[begin:end]) + "\n"
            else:
                # default chops top off
                example = '\n'.join(group[begin:]) + "\n"
                while ((section_value - 1) * len_of_excerpt) > num_newline:
                    self.example_page -= 1
            page_number = '\n' + str(section_value) + "/" + str(int(math.ceil(num_newline / len_of_excerpt)))

        return example + page_number + ' CTRL+Y (^) CTRL+N (v)'

    def _update_toolbar(self):
        cli = self.cli
        _, cols = get_window_dim()
        cols = int(cols)

        empty_space = " " * cols

        delta = datetime.datetime.utcnow() - START_TIME
        if self.user_feedback and delta.seconds < DISPLAY_TIME:
            toolbar = [
                ' Try out the \'feedback\' command',
                'If refreshed disappear in: {}'.format(str(DISPLAY_TIME - delta.seconds))]
        elif self.command_table_thread.is_alive():
            toolbar = [
                ' Loading...',
                'Hit [enter] to refresh'
            ]
        else:
            toolbar = self._toolbar_info()

        toolbar, empty_space = space_toolbar(toolbar, empty_space)
        cli.buffers['bottom_toolbar'].reset(
            initial_document=Document(u'{}{}{}'.format(NOTIFICATIONS, toolbar, empty_space)))

    def _toolbar_info(self):
        sub_name = ""
        try:
            profile = Profile(cli_ctx=self.cli_ctx)
            sub_name = profile.get_subscription()[_SUBSCRIPTION_NAME]
        except CLIError:
            pass

        curr_cloud = "Cloud: {}".format(self.cli_ctx.cloud.name)

        tool_val = 'Subscription: {}'.format(sub_name) if sub_name else curr_cloud

        settings_items = [
            " [F1]Layout",
            "[F2]Defaults",
            "[F3]Keys",
            "[Ctrl+D]Quit",
            tool_val
        ]
        return settings_items

    def generate_help_text(self):
        """ generates the help text based on commands typed """
        param_descrip = example = ""
        self.description_docs = u''

        rows, _ = get_window_dim()
        rows = int(rows)

        param_args = self.completer.leftover_args
        last_word = self.completer.unfinished_word
        command = self.completer.current_command
        new_command = ' '.join([command, last_word]).strip()

        if not self.completer.complete_command and new_command in self.completer.command_description:
            command = new_command

        # get command/group help
        if self.completer and command in self.completer.command_description:
            self.description_docs = u'{}'.format(self.completer.command_description[command])

        # get parameter help if full command
        if self.completer and command in self.completer.command_param_info:
            param = param_args[-1] if param_args else ''
            param = last_word if last_word.startswith('-') else param

            if param in self.completer.command_param_info[command] and self.completer.has_description(
                    command + " " + param):
                param_descrip = ''.join([
                    param, ":", '\n', self.completer.param_description.get(command + " " + param, '')])

            if command in self.completer.command_examples:
                string_example = []
                for example in self.completer.command_examples[command]:
                    for part in example:
                        string_example.append(part)
                ''.join(string_example)
                example = self._space_examples(
                    self.completer.command_examples[command], rows, self.example_page)

        return param_descrip, example

    def _update_default_info(self):
        try:
            options = self.cli_ctx.config.config_parser.options(DEFAULTS_SECTION)
            self.config_default = ""
            for opt in options:
                self.config_default += opt + ": " + self.cli_ctx.config.get(DEFAULTS_SECTION, opt) + "  "
        except configparser.NoSectionError:
            self.config_default = ""

    def create_application(self, full_layout=True):
        """ makes the application object and the buffers """
        layout_manager = LayoutManager(self)
        if full_layout:
            layout = layout_manager.create_layout(ExampleLexer, ToolbarLexer)
        else:
            layout = layout_manager.create_tutorial_layout()

        buffers = {
            DEFAULT_BUFFER: Buffer(is_multiline=True),
            'description': Buffer(is_multiline=True, read_only=True),
            'parameter': Buffer(is_multiline=True, read_only=True),
            'examples': Buffer(is_multiline=True, read_only=True),
            'bottom_toolbar': Buffer(is_multiline=True),
            'example_line': Buffer(is_multiline=True),
            'default_values': Buffer(),
            'symbols': Buffer(),
            'progress': Buffer(is_multiline=False)
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
            style=self.style,
            buffer=writing_buffer,
            on_input_timeout=self.on_input_timeout,
            key_bindings_registry=InteractiveKeyBindings(self).registry,
            layout=layout,
            buffers=buffers,
        )

    def create_interface(self):
        """ instantiates the interface """
        from prompt_toolkit.interface import CommandLineInterface
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
            print("An Integer should follow the colon", file=self.output)
            return ""
        if cmd in self.completer.command_examples:
            if num >= 0 and num < len(self.completer.command_examples[cmd]):
                example = self.completer.command_examples[cmd][num][1]
                example = example.replace('\n', '')
            else:
                print('Invalid example number', file=self.output)
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
        from prompt_toolkit.interface import CommandLineInterface

        if start_index:
            start_index = start_index + 1
            cmd = ' '.join(text.split()[:start_index])
            example_cli = CommandLineInterface(
                application=self.create_application(
                    full_layout=False),
                eventloop=create_eventloop())
            example_cli.buffers['example_line'].reset(
                initial_document=Document(u'{}\n'.format(
                    add_new_lines(example)))
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

    # pylint: disable=too-many-statements
    def _special_cases(self, cmd, outside):
        break_flag = False
        continue_flag = False
        args = parse_quotes(cmd)
        cmd_stripped = cmd.strip()

        if not cmd_stripped and cmd:
            # add scope if there are only spaces
            cmd = self.default_command + " " + cmd
        elif cmd_stripped == "quit" or cmd_stripped == "exit":
            break_flag = True
        elif cmd_stripped == "clear-history":
            continue_flag = True
            self.reset_history()
        elif cmd_stripped == CLEAR_WORD:
            outside = True
            cmd = CLEAR_WORD
        elif cmd_stripped[0] == SELECT_SYMBOL['outside']:
            cmd = cmd_stripped[1:]
            outside = True
            if cmd.strip() and cmd.split()[0] == 'cd':
                self.handle_cd(parse_quotes(cmd))
                continue_flag = True
            telemetry.track_outside_gesture()

        elif cmd_stripped[0] == SELECT_SYMBOL['exit_code']:
            meaning = "Success" if self.last_exit == 0 else "Failure"

            print(meaning + ": " + str(self.last_exit), file=self.output)
            continue_flag = True
            telemetry.track_exit_code_gesture()
        elif SELECT_SYMBOL['query'] in cmd_stripped and self.last and self.last.result:
            continue_flag = self.handle_jmespath_query(args)
            telemetry.track_query_gesture()
        elif not args:
            continue_flag = True
        elif args[0] == '--version' or args[0] == '-v':
            try:
                continue_flag = True
                self.cli_ctx.show_version()
            except SystemExit:
                pass
        elif SELECT_SYMBOL['example'] in cmd:
            cmd, continue_flag = self.handle_example(cmd, continue_flag)
            telemetry.track_ran_tutorial()
        elif SELECT_SYMBOL['scope'] == cmd_stripped[0:2]:
            continue_flag, cmd = self.handle_scoping_input(continue_flag, cmd, cmd_stripped)
            telemetry.track_scope_changes()
        else:
            # not a special character; add scope and remove 'az'
            if self.default_command:
                cmd = self.default_command + " " + cmd
            elif cmd.split(' ', 1)[0].lower() == 'az':
                cmd = ' '.join(cmd.split()[1:])
            if "|" in cmd or ">" in cmd:
                # anything I don't parse, send off
                outside = True
                cmd = "az " + cmd
            telemetry.track_cli_commands_used()

        return break_flag, continue_flag, outside, cmd

    def handle_jmespath_query(self, args):
        """ handles the jmespath query for injection or printing """
        continue_flag = False
        query_symbol = SELECT_SYMBOL['query']
        symbol_len = len(query_symbol)
        try:
            if len(args) == 1:
                # if arguments start with query_symbol, just print query result
                if args[0] == query_symbol:
                    result = self.last.result
                elif args[0].startswith(query_symbol):
                    result = jmespath.search(args[0][symbol_len:], self.last.result)
                print(json.dumps(result, sort_keys=True, indent=2), file=self.output)
            elif args[0].startswith(query_symbol):
                # print error message, user unsure of query shortcut usage
                print(("Usage Error: " + os.linesep +
                       "1. Use {0} stand-alone to display previous result with optional filtering "
                       "(Ex: {0}[jmespath query])" +
                       os.linesep + "OR:" + os.linesep +
                       "2. Use {0} to query the previous result for argument values "
                       "(Ex: group show --name {0}[jmespath query])").format(query_symbol), file=self.output)
            else:
                # query, inject into cmd
                def jmespath_query(match):
                    if match.group(0) == query_symbol:
                        return str(self.last.result)
                    query_result = jmespath.search(match.group(0)[symbol_len:], self.last.result)
                    return str(query_result)

                def sub_result(arg):
                    escaped_symbol = re.escape(query_symbol)
                    # regex captures query symbol and all characters following it in the argument
                    return json.dumps(re.sub(r'%s.*' % escaped_symbol, jmespath_query, arg))
                cmd_base = ' '.join(map(sub_result, args))
                self.cli_execute(cmd_base)
            continue_flag = True
        except (jmespath.exceptions.ParseError, CLIError) as e:
            print("Invalid Query Input: " + str(e), file=self.output)
            continue_flag = True
        return continue_flag

    def handle_scoping_input(self, continue_flag, cmd, text):
        """ handles what to do with a scoping gesture """
        default_split = text.partition(SELECT_SYMBOL['scope'])[2].split()
        cmd = cmd.replace(SELECT_SYMBOL['scope'], '')

        continue_flag = True

        if not default_split:
            self.default_command = ""
            print('unscoping all', file=self.output)

            return continue_flag, cmd

        while default_split:
            if not text:
                value = ''
            else:
                value = default_split[0]

            tree_path = self.default_command.split()
            tree_path.append(value)

            if self.completer.command_tree.in_tree(tree_path):
                self.set_scope(value)
                print("defaulting: " + value, file=self.output)
                cmd = cmd.replace(SELECT_SYMBOL['scope'], '')
            elif SELECT_SYMBOL['unscope'] == default_split[0] and self.default_command.split():

                value = self.default_command.split()[-1]
                self.default_command = ' ' + ' '.join(self.default_command.split()[:-1])

                if not self.default_command.strip():
                    self.default_command = self.default_command.strip()
                print('unscoping: ' + value, file=self.output)

            elif SELECT_SYMBOL['unscope'] not in text:
                print("Scope must be a valid command", file=self.output)

            default_split = default_split[1:]
        return continue_flag, cmd

    def reset_history(self):
        history_file_path = os.path.join(self.config.get_config_dir(), self.config.get_history())
        os.remove(history_file_path)
        self.history = FileHistory(history_file_path)
        self.cli.buffers[DEFAULT_BUFFER].history = self.history

    def cli_execute(self, cmd):
        """ sends the command to the CLI to be executed """

        try:
            args = parse_quotes(cmd)

            if args and args[0] == 'feedback':
                self.config.set_feedback('yes')
                self.user_feedback = False

            azure_folder = get_config_dir()
            if not os.path.exists(azure_folder):
                os.makedirs(azure_folder)
            ACCOUNT.load(os.path.join(azure_folder, 'azureProfile.json'))
            CONFIG.load(os.path.join(azure_folder, 'az.json'))
            SESSION.load(os.path.join(azure_folder, 'az.sess'), max_age=3600)

            invocation = self.cli_ctx.invocation_cls(cli_ctx=self.cli_ctx,
                                                     parser_cls=self.cli_ctx.parser_cls,
                                                     commands_loader_cls=self.cli_ctx.commands_loader_cls,
                                                     help_cls=self.cli_ctx.help_cls)

            if '--progress' in args:
                args.remove('--progress')
                execute_args = [args]
                thread = Thread(target=invocation.execute, args=execute_args)
                thread.daemon = True
                thread.start()
                self.threads.append(thread)
                self.curr_thread = thread

                progress_args = [self]
                thread = Thread(target=progress_view, args=progress_args)
                thread.daemon = True
                thread.start()
                self.threads.append(thread)
                result = None
            else:
                result = invocation.execute(args)

            self.last_exit = 0
            if result and result.result is not None:
                from azure.cli.core._output import OutputProducer
                if self.output:
                    self.output.write(result)
                    self.output.flush()
                else:
                    formatter = OutputProducer.get_formatter(self.cli_ctx.invocation.data['output'])
                    OutputProducer(formatter=formatter).out(result)
                    self.last = result

        except Exception as ex:  # pylint: disable=broad-except
            self.last_exit = handle_exception(ex)
        except SystemExit as ex:
            self.last_exit = int(ex.code)

    def progress_patch(self, _=False):
        """ forces to use the Shell Progress """
        from .progress import ShellProgressView
        self.cli_ctx.progress_controller.init_progress(ShellProgressView())
        return self.cli_ctx.progress_controller

    def run(self):
        """ starts the REPL """
        from .progress import ShellProgressView
        self.cli_ctx.get_progress_controller().init_progress(ShellProgressView())
        self.cli_ctx.get_progress_controller = self.progress_patch

        self.command_table_thread = LoadCommandTableThread(self.restart_completer, self)
        self.command_table_thread.start()

        from .configuration import SHELL_HELP
        self.cli.buffers['symbols'].reset(
            initial_document=Document(u'{}'.format(SHELL_HELP)))
        # flush telemetry for new commands and send successful interactive mode entry event
        telemetry.set_success()
        telemetry.flush()
        while True:
            try:
                document = self.cli.run(reset_current_buffer=True)
                text = document.text
                if not text:
                    # not input
                    self.set_prompt()
                    continue
                cmd = text
                outside = False

            except AttributeError:
                # when the user pressed Control D
                break
            except (KeyboardInterrupt, ValueError):
                # CTRL C
                self.set_prompt()
                continue
            else:
                self.history.append(text)
                b_flag, c_flag, outside, cmd = self._special_cases(cmd, outside)

                if b_flag:
                    break
                if c_flag:
                    self.set_prompt()
                    continue

                self.set_prompt()

                if outside:
                    subprocess.Popen(cmd, shell=True).communicate()
                else:
                    telemetry.start()
                    self.cli_execute(cmd)
                    if self.last_exit and self.last_exit != 0:
                        telemetry.set_failure()
                    else:
                        telemetry.set_success()
                    telemetry.flush()
        telemetry.conclude()
