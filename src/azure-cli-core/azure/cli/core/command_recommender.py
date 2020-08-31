# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import difflib

import azure.cli.core.telemetry as telemetry
from knack.log import get_logger

logger = get_logger(__name__)


class CommandRecommender():
    """Recommend a command for user when user's command fails.
    It combines alladin recommendations and examples in help files."""

    def __init__(self, command, parameters, extension, cli_ctx):
        """
        :param command: The command name in user's input, which should be corrected if misspelled.
        :type command: str
        :param parameters: The parameter arguments in users input.
        :type parameters: list
        :param extension: The extension name in user's input if the command comes from an extension.
        :type extension: str
        :param cli_ctx: CLI context when parser fails.
        :type cli_ctx: knack.cli.CLI
        """
        self.command = command.strip()
        self.extension = extension
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

        import json
        import requests
        from requests import RequestException
        from http import HTTPStatus
        from azure.cli.core import __version__ as version

        api_url = 'https://app.aladdin.microsoft.com/api/v1.0/suggestions'
        headers = {'Content-Type': 'application/json'}
        correlation_id = telemetry._session.correlation_id  # pylint: disable=protected-access
        subscription_id = telemetry._get_azure_subscription_id()  # pylint: disable=protected-access

        context = {
            'versionNumber': version
        }
        if telemetry.is_telemetry_enabled():
            if correlation_id:
                context['correlationId'] = correlation_id
            if subscription_id:
                context['subscriptionId'] = subscription_id

        parameters = [item for item in self.parameters if item not in ['--debug', '--verbose']]
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
        except RequestException as ex:
            logger.debug('Recommendation requests.get() exception: %s', ex)

        recommendations = []
        if response and response.status_code == HTTPStatus.OK:
            for result in response.json():
                # parse the reponse and format the recommendation
                command, parameters, placeholders = result['SuccessCommand'],\
                    result['SuccessCommand_Parameters'].split(','),\
                    result['SuccessCommand_ArgumentPlaceholders'].split('♠')
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
        from azure.cli.core.cloud import CLOUDS_FORBIDDING_ALADDIN_REQUEST

        if self.cli_ctx and self.cli_ctx.cloud \
           and self.cli_ctx.cloud.name not in CLOUDS_FORBIDDING_ALADDIN_REQUEST:
            self._set_aladdin_recommendations()

        # all the recommended commands from help examples and aladdin
        all_commands = self.help_examples + self.aladdin_recommendations
        all_commands.sort(key=len)

        filtered_commands = []
        filtered_choices = []
        target = ''.join(self.parameters)

        for command in all_commands:
            # filter out the commands which begins with a different command group
            if command.startswith('az {}'.format(self.command)):
                parameters = self._get_parameter_list(command)
                normalized_parameters = self._normalize_parameters(parameters)
                filtered_choices.append(''.join(normalized_parameters))
                filtered_commands.append(command)

        # sort the commands by argument matches
        candidates = difflib.get_close_matches(target, filtered_choices, cutoff=0)

        recommend_command = ''
        if candidates:
            index = filtered_choices.index(candidates[0])
            recommend_command = filtered_commands[index]

        return recommend_command

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
                    options = (option for option in options if not isinstance(option, Deprecated))
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
