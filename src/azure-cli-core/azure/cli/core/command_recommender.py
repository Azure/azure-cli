# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import difflib
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


class CommandRecommender():
    """Recommend a command for user when user's command fails.
    It combines alladin recommendations and examples in help files."""

    def __init__(self, command, parameters, extension, error_msg, cli_ctx):
        """
        :param command: The command name in user's input.
        :type command: str
        :param parameters: The parameter arguments in users input.
        :type parameters: list
        :param extension: The extension name in user's input if the command comes from an extension.
        :type extension: str
        :param error_msg: The error message of the failed command.
        :type error_msg: str
        :param cli_ctx: CLI context when parser fails.
        :type cli_ctx: knack.cli.CLI
        """
        self.command = command.strip()
        self.extension = extension
        self.error_msg = error_msg
        self.cli_ctx = cli_ctx

        self.parameters = self._normalize_parameters(parameters)
        self.help_examples = []
        self.aladdin_recommendations = []

    def set_help_examples(self, examples):
        """Set recommendations from help files"""

        self.help_examples.extend(examples)

    def _set_aladdin_recommendations(self):
        """Set recommendations from aladdin service.
        Call the aladdin service API, parse the response and set the recommendations.
        """

        import hashlib
        import json
        import requests
        from requests import RequestException
        from http import HTTPStatus
        from azure.cli.core import __version__ as version

        api_url = 'https://app.aladdin.microsoft.com/api/v1.0/suggestions'
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

        parameters = [item for item in self.parameters if item not in ['--debug', '--verbose', '--only-show-errors']]
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
                # parse the reponse and format the recommendation
                command, parameters, placeholders = result['command'],\
                    result['parameters'].split(','),\
                    result['placeholders'].split('♠')
                recommendation = 'az {} '.format(command)
                for parameter, placeholder in zip(parameters, placeholders):
                    recommendation += '{} {} '.format(parameter, placeholder)
                recommendations.append(recommendation.strip())

        self.aladdin_recommendations.extend(recommendations)

    def recommend_a_command(self):
        """Recommend a command for user when user's command fails.
        The recommended command will be the best matched one from
        both the help files and the aladdin recommendations.
        """
        if not self._disable_aladdin_service():
            self._set_aladdin_recommendations()

        recommend_command = ''
        if self.help_examples and self.aladdin_recommendations:
            # all the recommended commands from help examples and aladdin
            all_commands = self.help_examples + self.aladdin_recommendations
            all_commands.sort(key=len)

            filtered_commands = []
            filtered_choices = []
            target = ''.join(self.parameters)
            example_command_name = self.help_examples[0].split(' -')[0]

            for command in all_commands:
                # keep only the commands which begin with a same command name with examples
                if command.startswith(example_command_name):
                    parameters = self._get_parameter_list(command)
                    normalized_parameters = self._normalize_parameters(parameters)
                    filtered_choices.append(''.join(normalized_parameters))
                    filtered_commands.append(command)

            # sort the commands by argument matches
            candidates = difflib.get_close_matches(target, filtered_choices, cutoff=0)

            if candidates:
                index = filtered_choices.index(candidates[0])
                recommend_command = filtered_commands[index]

        # fallback to use the first recommended command from Aladdin
        elif self.aladdin_recommendations:
            recommend_command = self.aladdin_recommendations[0]

        # set the recommened command into Telemetry
        self._set_recommended_command_to_telemetry(recommend_command)

        return recommend_command

    def _set_recommended_command_to_telemetry(self, recommend_command):
        """Set the recommended command to Telemetry for analysis. """

        if recommend_command in self.aladdin_recommendations:
            telemetry.set_debug_info('AladdinRecommendCommand', recommend_command)
        elif recommend_command:
            telemetry.set_debug_info('ExampleRecommendCommand', recommend_command)

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

    def _get_parameter_list(self, raw_command):  # pylint: disable=no-self-use
        """Get the paramter list from a raw command string
        An example: 'az group create -n test -l eastus' ==> ['-n', '-l']
        """
        contents = raw_command.split(' ')
        return [item for item in contents if item.startswith('-')]

    def _normalize_parameters(self, parameters):
        """Normalize a parameter list.
        Get the standard form of a parameter list, which includes:
            1. Use long options to replace short options
            2. Remove the unrecognized parameters
            3. Sort the result parameter list
        An example: ['-g', '-n'] ==> ['--name', '--resource-group']
        """

        from knack.deprecation import Deprecated

        normalized_parameters = []
        try:
            cmd_table = self.cli_ctx.invocation.commands_loader.command_table.get(self.command, None)
            parameter_table = cmd_table.arguments if cmd_table else None
        except AttributeError:
            parameter_table = None

        if parameters:
            rules = {
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
                            rules[option] = standard_form
                        rules[standard_form] = None
                    except TypeError:
                        logger.debug('Unexpected argument options `%s` of type `%s`.', options, type(options).__name__)

            for parameter in parameters:
                if parameter in rules:
                    normalized_form = rules.get(parameter, None) or parameter
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
