# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import telemetry
from knack.log import get_logger


logger = get_logger(__name__)


class CommandRecommender:  # pylint: disable=too-few-public-methods
    """Recommend a command for user when user's command fails.
    It uses examples from help files to provide recommendations."""

    def __init__(self, command, parameters, extension, error_msg, cli_ctx):
        """
        :param command: The command name in user's input.
        :type command: str
        :param parameters: The raw parameters in users input.
        :type parameters: list
        :param extension: The extension name in user's input if the command comes from an extension.
        :type extension: str
        :param error_msg: The error message of the failed command.
        :type error_msg: str
        :param cli_ctx: CLI context when parser fails.
        :type cli_ctx: knack.cli.CLI
        """
        self.command = command.strip()
        self.parameters = parameters
        self.extension = extension
        self.error_msg = error_msg
        self.cli_ctx = cli_ctx
        # the item is a dict with the form {'command': #, 'description': #}
        self.help_examples = []

    def set_help_examples(self, examples):
        """Set help examples.

        :param examples: The examples from CLI help file.
        :type examples: list
        """

        self.help_examples.extend(examples)

    def provide_recommendations(self):
        """Provide recommendations when a command fails.

        The recommendations are from CLI help examples,
        which include both commands and reference links along with their descriptions.

        :return: The decorated recommendations
        :type: list
        """

        from azure.cli.core.style import Style, highlight_command
        from azure.cli.core.parser import OVERVIEW_REFERENCE

        def sort_recommendations(recommendations):
            """Sort the recommendations by parameter matching.

            The sorting rules below are applied in order:
                1. Commands starting with the user's input command name are ahead of those don't
                2. Commands having more matched arguments are ahead of those having less
                3. Commands having less arguments are ahead of those having more

            :param recommendations: The unordered recommendations
            :type recommendations: list
            :return: The ordered recommendations
            :type: list
            """

            candidates = []
            target_arg_list = self._normalize_parameters(self.parameters)
            for recommendation in recommendations:
                matches = 0
                arg_list = self._normalize_parameters(recommendation['command'].split(' '))

                # ignore commands that do not start with the use's input command name
                if recommendation['command'].startswith('az {}'.format(self.command)):
                    for arg in arg_list:
                        if arg in target_arg_list:
                            matches += 1
                else:
                    matches = -1

                candidates.append({
                    'recommendation': recommendation,
                    'arg_list': arg_list,
                    'matches': matches
                })

            # sort the candidates by the number of matched arguments and total arguments
            candidates.sort(key=lambda item: (item['matches'], -len(item['arg_list'])), reverse=True)

            return [candidate['recommendation'] for candidate in candidates]

        def replace_param_values(command):  # pylint: disable=unused-variable
            """Replace the parameter values in a command with user's input values

            :param command: The command whose parameter value needs to be replaced
            :type command: str
            :return: The command with parameter values being replaced
            :type: str
            """

            # replace the parameter values only when the recommended
            # command's name is the same with user's input command name
            if not command.startswith('az {}'.format(self.command)):
                return command

            source_kwargs = get_parameter_kwargs(self.parameters)
            param_mappings = self._get_param_mappings()

            return replace_parameter_values(command, source_kwargs, param_mappings)

        # do not recommend commands if it is disabled by config
        if self.cli_ctx and self.cli_ctx.config.get('core', 'error_recommendation', 'on').upper() == 'OFF':
            return []

        recommendations = self.help_examples

        # sort the recommendations by parameter matching, get the top 3 recommended commands
        recommendations = sort_recommendations(recommendations)[:3]

        raw_commands = []
        decorated_recommendations = []
        for recommendation in recommendations:
            # generate raw commands recorded in Telemetry
            raw_command = recommendation['command']
            raw_commands.append(raw_command)

            # disable the parameter replacement feature because it will make command description inaccurate
            # raw_command = replace_param_values(raw_command)

            # generate decorated commands shown to users
            decorated_command = highlight_command(raw_command)
            decorated_description = [(
                Style.SECONDARY,
                recommendation.get('description', 'No description is found.') + '\n'
            )]
            decorated_recommendations.append((decorated_command, decorated_description))

        # add reference link as a recommendation
        decorated_link = [(Style.HYPERLINK, OVERVIEW_REFERENCE)]

        decorated_description = [(Style.SECONDARY, 'Read more about the command in reference docs')]
        decorated_recommendations.append((decorated_link, decorated_description))

        # set the recommend command into Telemetry
        self._set_recommended_command_to_telemetry(raw_commands)

        return decorated_recommendations

    def _set_recommended_command_to_telemetry(self, raw_commands):
        """Set the recommended commands to Telemetry

        :param raw_commands: The recommended raw commands
        :type raw_commands: list
        """

        telemetry.set_debug_info('ExampleRecommendCommand', ';'.join(raw_commands))

    def _normalize_parameters(self, args):
        """Normalize a parameter list.

        Get the standard parameter name list of the raw parameters, which includes:
            1. Use long options to replace short options
            2. Remove the unrecognized parameter names
            3. Sort the parameter names by their lengths
        An example: ['-g', 'RG', '-n', 'NAME'] ==> ['--resource-group', '--name']

        :param args: The raw arg list of a command
        :type args: list
        :return: A standard, valid and sorted parameter name list
        :type: list
        """

        from azure.cli.core.commands import AzCliCommandInvoker

        parameters = AzCliCommandInvoker._extract_parameter_names(args)  # pylint: disable=protected-access
        normalized_parameters = []

        param_mappings = self._get_param_mappings()
        for parameter in parameters:
            if parameter in param_mappings:
                normalized_form = param_mappings.get(parameter, None) or parameter
                normalized_parameters.append(normalized_form)
            else:
                logger.debug('"%s" is an invalid parameter for command "%s".', parameter, self.command)

        return sorted(normalized_parameters)

    def _get_param_mappings(self):
        try:
            cmd_table = self.cli_ctx.invocation.commands_loader.command_table.get(self.command, None)
        except AttributeError:
            cmd_table = None

        return get_parameter_mappings(cmd_table)


def get_parameter_mappings(command_table):
    """Get the short option to long option mappings of a command

    :param parameter_table: CLI command object
    :type parameter_table: knack.commands.CLICommand
    :param command_name: The command name
    :type command name: str
    :return: The short to long option mappings of the parameters
    :type: dict
    """

    from knack.deprecation import Deprecated

    parameter_table = None
    if hasattr(command_table, 'arguments'):
        parameter_table = command_table.arguments

    param_mappings = {
        '-h': '--help',
        '-o': '--output',
        '--only-show-errors': None,
        '--help': None,
        '--output': None,
        '--query': None,
        '--debug': None,
        '--verbose': None,
        '--yes': None,
        '--no-wait': None
    }

    if parameter_table:
        for argument in parameter_table.values():
            options = argument.type.settings['options_list']
            options = [option for option in options if not isinstance(option, Deprecated)]
            # skip the positional arguments
            if not options:
                continue
            try:
                sorted_options = sorted(options, key=len, reverse=True)
                standard_form = sorted_options[0]

                for option in sorted_options[1:]:
                    param_mappings[option] = standard_form
                param_mappings[standard_form] = standard_form
            except TypeError:
                logger.debug('Unexpected argument options `%s` of type `%s`.', options, type(options).__name__)

    return param_mappings


def get_parameter_kwargs(args):
    """Get parameter name-value mappings from the raw arg list
    An example: ['-g', 'RG', '--name=NAME'] ==> {'-g': 'RG', '--name': 'NAME'}

    :param args: The raw arg list of a command
    :type args: list
    :return: The parameter name-value mappings
    :type: dict
    """

    parameter_kwargs = {}
    for index, parameter in enumerate(args):
        if parameter.startswith('-'):

            param_name, param_val = parameter, None
            if '=' in parameter:
                pieces = parameter.split('=')
                param_name, param_val = pieces[0], pieces[1]
            elif index + 1 < len(args) and not args[index + 1].startswith('-'):
                param_val = args[index + 1]

            if param_val is not None and ' ' in param_val:
                param_val = '"{}"'.format(param_val)
            parameter_kwargs[param_name] = param_val

    return parameter_kwargs


def replace_parameter_values(target_command, source_kwargs, param_mappings):
    """Replace the parameter values in target_command with values in source_kwargs

    :param target_command: The command in which the parameter values need to be replaced
    :type target_command: str
    :param source_kwargs: The source key-val pairs used to replace the values
    :type source_kwargs: dict
    :param param_mappings: The short-long option mappings in terms of the target_command
    :type param_mappings: dict
    :returns: The target command with parameter values being replaced
    :type: str
    """

    def get_user_param_value(target_param):
        """Get the value that is used as the replaced value of target_param

        :param target_param: The parameter name whose value needs to be replaced
        :type target_param: str
        :return: The replaced value for target_param
        :type: str
        """
        standard_source_kwargs = {}

        for param, val in source_kwargs.items():
            if param in param_mappings:
                standard_param = param_mappings[param]
                standard_source_kwargs[standard_param] = val

        if target_param in param_mappings:
            standard_target_param = param_mappings[target_param]
            if standard_target_param in standard_source_kwargs:
                return standard_source_kwargs[standard_target_param]

        return None

    command_args = target_command.split(' ')
    for index, arg in enumerate(command_args):
        if arg.startswith('-') and index + 1 < len(command_args) and not command_args[index + 1].startswith('-'):
            user_param_val = get_user_param_value(arg)
            if user_param_val:
                command_args[index + 1] = user_param_val

    return ' '.join(command_args)
