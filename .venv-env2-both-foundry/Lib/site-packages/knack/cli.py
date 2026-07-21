# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys
from collections import defaultdict

from .invocation import CommandInvoker
from .completion import CLICompletion
from .output import OutputProducer
from .log import CLILogging, get_logger
from .util import CLIError, is_modern_terminal
from .config import CLIConfig
from .query import CLIQuery
from .events import EVENT_CLI_PRE_EXECUTE, EVENT_CLI_SUCCESSFUL_EXECUTE, EVENT_CLI_POST_EXECUTE
from .parser import CLICommandParser
from .commands import CLICommandsLoader
from .help import CLIHelp

logger = get_logger(__name__)


class CLI(object):  # pylint: disable=too-many-instance-attributes
    """ The main driver for the CLI """

    def __init__(self,
                 cli_name='cli',
                 config_dir=None,
                 config_env_var_prefix=None,
                 out_file=sys.stdout,
                 config_cls=CLIConfig,
                 logging_cls=CLILogging,
                 invocation_cls=CommandInvoker,
                 output_cls=OutputProducer,
                 completion_cls=CLICompletion,
                 query_cls=CLIQuery,
                 parser_cls=CLICommandParser,
                 commands_loader_cls=CLICommandsLoader,
                 help_cls=CLIHelp):
        """
        :param cli_name: The name of the CLI (e.g. the executable name 'az')
        :type cli_name: str
        :param config_dir: Path to store config files for this CLI
        :type config_dir: str
        :param config_env_var_prefix: The prefix for configuration environment variables
        :type config_env_var_prefix: str
        :param out_file: File to write output to
        :type out_file: file-like object
        :param config_cls: Class to handle configuration
        :type config_cls: knack.config.CLIConfig
        :param logging_cls: Class to handle logging
        :type logging_cls: knack.log.CLILogging
        :param invocation_cls: Class to handle command invocations
        :type invocation_cls: knack.invocation.CommandInvoker
        :param output_cls: Class to handle output processing of commands
        :type output_cls: knack.output.OutputProducer
        :param completion_cls: Class to handle completions
        :type completion_cls: knack.completion.CLICompletion
        :param query_cls: Class to handle command queries
        :type query_cls: knack.query.CLIQuery
        :param parser_cls: Class to handler command parsing
        :type parser_cls: knack.parser.CLICommandParser
        :param commands_loader_cls: Class to handle loading commands
        :type commands_loader_cls: knack.commands.CLICommandsLoader
        :param help_cls: Class to handle help
        :type help_cls: knack.help.CLIHelp
        """
        self.name = cli_name
        self.out_file = out_file
        self.config_cls = config_cls
        self.logging_cls = logging_cls
        self.output_cls = output_cls
        self.parser_cls = parser_cls
        self.help_cls = help_cls
        self.commands_loader_cls = commands_loader_cls
        self.invocation_cls = invocation_cls
        self.invocation = None
        self._event_handlers = defaultdict(lambda: [])
        # Data that's typically backed to persistent storage
        self.config = config_cls(
            config_dir=config_dir or os.path.expanduser(os.path.join('~', '.{}'.format(cli_name))),
            config_env_var_prefix=config_env_var_prefix or cli_name.upper()
        )
        # In memory collection of key-value data for this current cli. This persists between invocations.
        self.data = defaultdict(lambda: None)
        self.completion = completion_cls(cli_ctx=self)
        self.logging = logging_cls(self.name, cli_ctx=self)
        self.output = self.output_cls(cli_ctx=self)
        self.result = None
        self.query = query_cls(cli_ctx=self)

        # As logging is initialized in `invoke`, call `logger.debug` or `logger.info` here won't work.
        self.init_debug_log = []
        self.init_info_log = []

        self.only_show_errors = self.config.getboolean('core', 'only_show_errors', fallback=False)
        self.enable_color = self._should_enable_color()
        # Enable VT mode only in Windows legacy terminal
        self._should_enable_vt_mode = self.enable_color and sys.platform == 'win32' and not is_modern_terminal()

    @staticmethod
    def _should_show_version(args):
        return args and (args[0] == '--version' or args[0] == '-v')

    def get_cli_version(self):
        """ Get the CLI Version. Override this to define how to get the CLI version

        :return: The CLI version
        :rtype: str
        """
        return ''

    def get_runtime_version(self):
        """ Get the runtime information.

        :return: Runtime information
        :rtype: str
        """
        import platform

        version_info = '\n\n'
        version_info += 'Python ({}) {}'.format(platform.system(), sys.version)
        version_info += '\n\n'
        version_info += 'Python location \'{}\''.format(sys.executable)
        version_info += '\n'
        return version_info

    def show_version(self):
        """ Print version information to the out file. """
        version_info = self.get_cli_version()
        version_info += self.get_runtime_version()
        print(version_info, file=self.out_file)

    def register_event(self, event_name, handler):
        """ Register a callable that will be called when event is raised.
            A handler will only be registered once.

        :param event_name: The name of the event (see knack.events for in-built events)
        :type event_name: str
        :param handler: A callback to handle the event
        :type handler: function
        """
        self._event_handlers[event_name].append(handler)

    def unregister_event(self, event_name, handler):
        """ Unregister a callable that will be called when event is raised.

        :param event_name: The name of the event (see knack.events for in-built events)
        :type event_name: str
        :param handler: The callback that was used to register the event
        :type handler: function
        """
        try:
            self._event_handlers[event_name].remove(handler)
        except ValueError:
            pass

    def raise_event(self, event_name, **kwargs):
        """ Raise an event. Calls each handler in turn with kwargs

        :param event_name: The name of the event to raise
        :type event_name: str
        :param kwargs: Kwargs to be passed to all event handlers
        """
        handlers = list(self._event_handlers[event_name])
        logger.debug('Event: %s %s', event_name, handlers)
        for func in handlers:
            func(self, **kwargs)

    def exception_handler(self, ex):
        """ The default exception handler """
        if isinstance(ex, CLIError):
            logger.error(ex)
        else:
            logger.exception(ex)
        return 1

    def _print_init_log(self):
        """Print the debug/info log from CLI.__init__"""
        if self.init_debug_log:
            logger.debug('__init__ debug log:\n%s', '\n'.join(self.init_debug_log))
            self.init_debug_log.clear()
        if self.init_info_log:
            logger.info('__init__ info log:\n%s', '\n'.join(self.init_info_log))
            self.init_info_log.clear()

    def invoke(self, args, initial_invocation_data=None, out_file=None):
        """ Invoke a command.

        :param args: The arguments that represent the command
        :type args: list, tuple
        :param initial_invocation_data: Prime the in memory collection of key-value data for this invocation.
        :type initial_invocation_data: dict
        :param out_file: The file to send output to. If not used, we use out_file for knack.cli.CLI instance
        :type out_file: file-like object
        :return: The exit code of the invocation
        :rtype: int
        """
        from .util import CommandResultItem

        if not isinstance(args, (list, tuple)):
            raise TypeError('args should be a list or tuple.')
        exit_code = 0
        try:
            out_file = out_file or self.out_file

            # Enable VT mode if necessary
            if out_file is sys.stdout and self._should_enable_vt_mode:
                self.init_debug_log.append("Enable VT mode.")
                from ._win_vt import enable_vt_mode
                if not enable_vt_mode():
                    # Disable color if we can't enable it
                    self.enable_color = False

            args = self.completion.get_completion_args() or args

            self.logging.configure(args)
            logger.debug('Command arguments: %s', args)
            self._print_init_log()

            self.raise_event(EVENT_CLI_PRE_EXECUTE)
            if CLI._should_show_version(args):
                self.show_version()
                self.result = CommandResultItem(None)
            else:
                self.invocation = self.invocation_cls(cli_ctx=self,
                                                      parser_cls=self.parser_cls,
                                                      commands_loader_cls=self.commands_loader_cls,
                                                      help_cls=self.help_cls,
                                                      initial_data=initial_invocation_data)
                cmd_result = self.invocation.execute(args)
                self.result = cmd_result
                exit_code = self.result.exit_code
                output_type = self.invocation.data['output']
                if cmd_result and cmd_result.result is not None:
                    formatter = self.output.get_formatter(output_type)
                    self.output.out(cmd_result, formatter=formatter, out_file=out_file)
                self.raise_event(EVENT_CLI_SUCCESSFUL_EXECUTE, result=cmd_result)
        except KeyboardInterrupt as ex:
            exit_code = 1
            self.result = CommandResultItem(None, error=ex, exit_code=exit_code)
        except Exception as ex:  # pylint: disable=broad-except
            exit_code = self.exception_handler(ex)
            self.result = CommandResultItem(None, error=ex, exit_code=exit_code)
        except SystemExit as ex:
            exit_code = ex.code
            self.result = CommandResultItem(None, error=ex, exit_code=exit_code)
            raise ex
        finally:
            self.raise_event(EVENT_CLI_POST_EXECUTE)

        return exit_code

    def _should_enable_color(self):
        # When run in a normal terminal, color is only enabled when all conditions are met:
        #   1. [core] no_color config is not set
        #   2. stdout is a tty
        #      - Otherwise, if the downstream command doesn't support color, Knack will fail with
        #      BrokenPipeError: [Errno 32] Broken pipe, like `az --version | head --lines=1`
        #      https://github.com/Azure/azure-cli/issues/13413
        #   3. stderr is a tty.
        #      - Otherwise, the output in stderr won't have LEVEL tag
        #   4. out_file is stdout

        no_color_config = self.config.getboolean('core', 'no_color', fallback=False)
        # If color is disabled by config explicitly, never enable color
        if no_color_config:
            self.init_debug_log.append("Color is disabled by config.")
            return False

        if sys.stdout.isatty() and sys.stderr.isatty() and self.out_file is sys.stdout:
            self.init_debug_log.append("Enable color in terminal.")
            return True

        if 'PYCHARM_HOSTED' in os.environ and sys.stdout == sys.__stdout__ and sys.stderr == sys.__stderr__:
            self.init_debug_log.append("Enable color in PyCharm.")
            return True

        self.init_debug_log.append("Cannot enable color.")
        return False
