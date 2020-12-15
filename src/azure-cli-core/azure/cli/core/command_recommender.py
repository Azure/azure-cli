# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum

import azure.cli.core.telemetry as telemetry
from knack.log import get_logger


logger = get_logger(__name__)


class AladdinUserFaultType(Enum):
    """Define the userfault types required by aladdin service
    to get the command recommendations"""

    ExpectedArgument = 'ExpectedArgument'
    UnrecognizedArguments = 'UnrecognizedArguments'
    ValidationError = 'ValidationError'
    UnknownSubcommand = 'UnknownSubcommand'
    MissingRequiredParameters = 'MissingRequiredParameters'
    MissingRequiredSubcommand = 'MissingRequiredSubcommand'
    StorageAccountNotFound = 'StorageAccountNotFound'
    Unknown = 'Unknown'
    InvalidJMESPathQuery = 'InvalidJMESPathQuery'
    InvalidOutputType = 'InvalidOutputType'
    InvalidParameterValue = 'InvalidParameterValue'
    UnableToParseCommandInput = 'UnableToParseCommandInput'
    ResourceGroupNotFound = 'ResourceGroupNotFound'
    InvalidDateTimeArgumentValue = 'InvalidDateTimeArgumentValue'
    InvalidResourceGroupName = 'InvalidResourceGroupName'
    AzureResourceNotFound = 'AzureResourceNotFound'
    InvalidAccountName = 'InvalidAccountName'


class CommandRecommender():  # pylint: disable=too-few-public-methods
    """Recommend a command for user when user's command fails.
    It combines Aladdin recommendations and examples in help files."""

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
        # the item is a dict with the form {'command': #, 'description': #, 'link': #}
        self.aladdin_recommendations = []

    def set_help_examples(self, examples):  # pylint: disable=too-many-locals
        """Set recommendations from help files"""

        self.help_examples.extend(examples)

    def _set_aladdin_recommendations(self):  # pylint: disable=too-many-locals
        """Set recommendations from aladdin service.
        Call the aladdin service API, parse the response and set the recommendations.
        """

        import hashlib
        import json
        import requests
        from requests import RequestException
        from http import HTTPStatus
        from azure.cli.core import __version__ as version

        # api_url = 'https://app.aladdin.microsoft.com/api/v1.0/suggestions'
        api_url = 'https://aladdindevwestus-app.aladdindevwestus-env.p.azurewebsites.net//api/v1/suggestions'
        correlation_id = telemetry._session.correlation_id  # pylint: disable=protected-access
        subscription_id = telemetry._get_azure_subscription_id()  # pylint: disable=protected-access
        # Used for DDOS protection and rate limiting
        user_id = telemetry._get_user_azure_id()  # pylint: disable=protected-access
        hashed_user_id = hashlib.sha256(user_id.encode('utf-8')).hexdigest()

        headers = {
            'Content-Type': 'application/json',
            'X-UserId': hashed_user_id
        }
        context = {
            'versionNumber': version,
            'errorType': self._get_error_type()
        }

        if telemetry.is_telemetry_enabled():
            if correlation_id:
                context['correlationId'] = correlation_id
            if subscription_id:
                context['subscriptionId'] = subscription_id

        parameters = self._normalize_parameters(self.parameters)
        parameters = [item for item in parameters if item not in ['--debug', '--verbose', '--only-show-errors']]
        query = {
            "command": self.command,
            "parameters": ','.join(parameters)
        }

        response = None
        try:
            response = requests.get(
                api_url,
                params={
                    'query': json.dumps(query),
                    'clientType': 'AzureCli',
                    'context': json.dumps(context)
                },
                headers=headers,
                timeout=1)
            telemetry.set_debug_info('AladdinResponseTime', response.elapsed.total_seconds())

        except RequestException as ex:
            logger.debug('Recommendation requests.get() exception: %s', ex)
            telemetry.set_debug_info('AladdinException', ex.__class__.__name__)

        recommendations = []
        if response and response.status_code == HTTPStatus.OK:
            for result in response.json():
                # parse the response to get the raw command
                raw_command = 'az {} '.format(result['command'])
                for parameter, placeholder in zip(result['parameters'].split(','), result['placeholders'].split('♠')):
                    raw_command += '{} {}{}'.format(parameter, placeholder, ' ' if placeholder else '')

                # format the recommendation
                recommendation = {
                    'command': raw_command.strip(),
                    'description': result['description'],
                    'link': result['link']
                }
                recommendations.append(recommendation)

        self.aladdin_recommendations.extend(recommendations)

    def provide_recommendations(self):
        """Provide recommendations from Aladdin service,
        which include both commands and reference link along with their descriptions.
        """
        from azure.cli.core.style import Style

        def sort_recommendations(recommendations):
            """Sort the recommendations by parameter matching.
            The sorting rules below are applied in oder:
                1. Commands starting with the user's input command name are ahead of those don't
                2. Commands having more matched arguments are ahead of those having less
                3. Commands having less arguments are ahead of those having more
            """

            candidates = []
            target_arg_list = self._normalize_parameters(self.parameters)
            for recommendation in recommendations:
                matches = 0
                arg_list = self._normalize_parameters(recommendation['command'].split(' '))

                # ignore those not starting with the use's input command name
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

        def decorate_command(raw_command):
            """Format the command info to get an decorated command.
            The decorations of a command include:
                1. Use user's input values to replace the placeholders for the parameters users have specified
                2. Apply colorization for the command
            """
            # replace the placeholders with user's input values only when the recommended
            # command's name is the same with user's input command name
            if raw_command.startswith('az {}'.format(self.command)):
                raw_command = self._replace_parameter_values(raw_command)

            # command colorization
            styled_command = []
            command_args = raw_command.split(' ')
            for index, arg in enumerate(command_args):
                spaced_arg = ' {}'.format(arg) if index > 0 else arg
                if index > 0 and command_args[index - 1].startswith('-') and not arg.startswith('-'):
                    styled_command.append((Style.PRIMARY, spaced_arg))
                else:
                    styled_command.append((Style.ACTION, spaced_arg))

            return styled_command

        # get recommendations from Aladdin service
        if not self._disable_aladdin_service() and \
           not self.cli_ctx.config.getboolean('core', 'disable_error_recommendation', False):
            self._set_aladdin_recommendations()

        # recommendations are either from Aladdin or help examples
        recommendations = self.aladdin_recommendations
        if not recommendations:
            recommendations = self.help_examples

        # order the recommendations by parameter matching, get the top 3 recommended commands
        recommendations = sort_recommendations(recommendations)[:3]

        raw_commands = []
        decorated_recommendations = []
        for recommendation in recommendations:
            # generate raw commands recorded in Telemetry
            raw_command = recommendation['command']
            raw_commands.append(raw_command)

            # generate decorated commands shown to users
            decorated_command = decorate_command(raw_command)
            decorated_description = [(Style.SECONDARY, recommendation['description'] + '\n')]
            decorated_recommendations.append((decorated_command, decorated_description))

        # add reference link as a recommendation
        from azure.cli.core.parser import OVERVIEW_REFERENCE
        decorated_link = [(Style.HYPERLINK, OVERVIEW_REFERENCE)]
        if self.aladdin_recommendations:
            decorated_link = [(Style.HYPERLINK, self.aladdin_recommendations[0]['link'])]

        decorated_description = [(Style.SECONDARY, 'Read more about the command in reference docs')]
        decorated_recommendations.append((decorated_link, decorated_description))

        # set the recommend command into Telemetry
        self._set_recommended_command_to_telemetry(raw_commands)

        return decorated_recommendations

    def _set_recommended_command_to_telemetry(self, raw_commands):  # pylint: disable=no-self-use
        """Set the recommended command to Telemetry for analysis. """

        telemetry.set_debug_info('AladdinRecommendCommand', ';'.join(raw_commands))

    def _disable_aladdin_service(self):
        """Decide whether to disable aladdin request when a command fails.
        The possible cases to disable it are:
            1. In air-gapped clouds
            2. In testing environments
        """
        from azure.cli.core.cloud import CLOUDS_FORBIDDING_ALADDIN_REQUEST

        # CLI is not started well
        if not self.cli_ctx or not self.cli_ctx.cloud:
            return True

        # for air-gapped clouds
        if self.cli_ctx.cloud.name in CLOUDS_FORBIDDING_ALADDIN_REQUEST:
            return True

        # for testing environments
        if self.cli_ctx.__class__.__name__ == 'DummyCli':
            return True

        return False

    def _get_parameter_mappings(self):
        """Get the short option to long option mappings of a command. """

        from knack.deprecation import Deprecated

        try:
            cmd_table = self.cli_ctx.invocation.commands_loader.command_table.get(self.command, None)
            parameter_table = cmd_table.arguments if cmd_table else None
        except AttributeError:
            parameter_table = None

        param_mappings = {
            '-h': '--help',
            '-o': '--output',
            '--only-show-errors': None,
            '--help': None,
            '--output': None,
            '--query': None,
            '--debug': None,
            '--verbose': None
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

    def _normalize_parameters(self, raw_parameters):
        """Normalize a parameter list.
        Get the standard parameter names of the raw parameters, which includes:
            1. Use long options to replace short options
            2. Remove the unrecognized parameter names
        An example: ['-g', 'RG', '-n', 'NAME'] ==> {'--resource-group': 'RG', '--name': 'NAME'}
        """

        parameters = self._extract_parameter_names(raw_parameters)
        normalized_parameters = []

        param_mappings = self._get_parameter_mappings()
        for parameter in parameters:
            if parameter in param_mappings:
                normalized_form = param_mappings.get(parameter, None) or parameter
                normalized_parameters.append(normalized_form)
            else:
                logger.debug('"%s" is an invalid parameter for command "%s".', parameter, self.command)

        return sorted(normalized_parameters)

    def _get_error_type(self):
        """The the error type of the failed command from the error message.
        The error types are only consumed by aladdin service for better recommendations.
        """

        error_type = AladdinUserFaultType.Unknown
        if not self.error_msg:
            return error_type.value

        error_msg = self.error_msg.lower()
        if 'unrecognized' in error_msg:
            error_type = AladdinUserFaultType.UnrecognizedArguments
        elif 'expected one argument' in error_msg or 'expected at least one argument' in error_msg \
                or 'value required' in error_msg:
            error_type = AladdinUserFaultType.ExpectedArgument
        elif 'misspelled' in error_msg:
            error_type = AladdinUserFaultType.UnknownSubcommand
        elif 'arguments are required' in error_msg or 'argument required' in error_msg:
            error_type = AladdinUserFaultType.MissingRequiredParameters
            if '_subcommand' in error_msg:
                error_type = AladdinUserFaultType.MissingRequiredSubcommand
            elif '_command_package' in error_msg:
                error_type = AladdinUserFaultType.UnableToParseCommandInput
        elif 'not found' in error_msg or 'could not be found' in error_msg \
                or 'resource not found' in error_msg:
            error_type = AladdinUserFaultType.AzureResourceNotFound
            if 'storage_account' in error_msg or 'storage account' in error_msg:
                error_type = AladdinUserFaultType.StorageAccountNotFound
            elif 'resource_group' in error_msg or 'resource group' in error_msg:
                error_type = AladdinUserFaultType.ResourceGroupNotFound
        elif 'pattern' in error_msg or 'is not a valid value' in error_msg or 'invalid' in error_msg:
            error_type = AladdinUserFaultType.InvalidParameterValue
            if 'jmespath_type' in error_msg:
                error_type = AladdinUserFaultType.InvalidJMESPathQuery
            elif 'datetime_type' in error_msg:
                error_type = AladdinUserFaultType.InvalidDateTimeArgumentValue
            elif '--output' in error_msg:
                error_type = AladdinUserFaultType.InvalidOutputType
            elif 'resource_group' in error_msg:
                error_type = AladdinUserFaultType.InvalidResourceGroupName
            elif 'storage_account' in error_msg:
                error_type = AladdinUserFaultType.InvalidAccountName
        elif "validation error" in error_msg:
            error_type = AladdinUserFaultType.ValidationError

        return error_type.value

    def _extract_parameter_names(self, parameters):  # pylint: disable=no-self-use
        """Extract parameter names from the raw parameters.
        An example: ['-g', 'RG', '-n', 'NAME'] ==> ['-g', '-n']
        """

        from azure.cli.core.commands import AzCliCommandInvoker

        return AzCliCommandInvoker._extract_parameter_names(parameters)  # pylint: disable=protected-access

    def _replace_parameter_values(self, command):
        """Replace the parameter values in recommended command with values in user's command
        An example:
            recommended command: 'az vm create -n MyVm -g MyResourceGroup --image CentOS'
            user's command:  'az vm create --name user_vm -g user_rg'
            ==> 'az vm create -n user_vm -g user_rg --image CentOS'
        """

        def get_parameter_kwargs(parameters):
            """Get name value mappings from parameter list
            An example:
                ['-g', 'RG', '--name=NAME'] ==> {'-g': 'RG', '--name': 'NAME'}
            """

            parameter_kwargs = dict()
            for index, parameter in enumerate(parameters):
                if parameter.startswith('-'):

                    param_name, param_val = parameter, None
                    if '=' in parameter:
                        pieces = parameter.split('=')
                        param_name, param_val = pieces[0], pieces[1]
                    elif index + 1 < len(parameters) and not parameters[index + 1].startswith('-'):
                        param_val = parameters[index + 1]

                    parameter_kwargs[param_name] = param_val

            return parameter_kwargs

        def get_user_param_value(target_param, user_kwargs, param_mappings):
            """Get user's input value for the target_param. """

            standard_user_kwargs = dict()

            for param, val in user_kwargs.items():
                if param in param_mappings:
                    standard_param = param_mappings[param]
                    standard_user_kwargs[standard_param] = val

            if target_param in param_mappings:
                standard_target_param = param_mappings[target_param]
                if standard_target_param in standard_user_kwargs:
                    return standard_user_kwargs[standard_target_param]

            return None

        user_kwargs = get_parameter_kwargs(self.parameters)
        param_mappings = self._get_parameter_mappings()

        command_args = command.split(' ')
        for index, arg in enumerate(command_args):
            if arg.startswith('-') and index + 1 < len(command_args) and not command_args[index + 1].startswith('-'):
                user_param_val = get_user_param_value(arg, user_kwargs, param_mappings)
                if user_param_val:
                    command_args[index + 1] = user_param_val

        return ' '.join(command_args)
