# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import random
import re
import string
import requests

from knack.util import CLIError
from azure.cli.core.profiles import ResourceType, get_sdk
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.util import get_file_json, shell_safe_json_parse
from azure.cli.command_modules.botservice._params import supported_languages
from azure.cli.command_modules.botservice.bot_json_formatter import BotJsonFormatter
from azure.cli.command_modules.botservice import azure_region_mapper


class BotTemplateDeployer:
    # Function App
    function_template_name = 'functionapp.template.json'
    csharp_function_zip_url = 'https://connectorprod.blob.core.windows.net/bot-packages/csharp-abs-functions_emptybot.zip'  # pylint: disable=line-too-long
    node_function_zip_url = 'https://connectorprod.blob.core.windows.net/bot-packages/node.js-abs-functions_emptybot_funcpack.zip'  # pylint: disable=line-too-long
    v3_webapp_template_name = 'webapp.template.json'
    v3_webapp_csharp_zip_url = 'https://connectorprod.blob.core.windows.net/bot-packages/csharp-abs-webapp_simpleechobot_precompiled.zip'  # pylint: disable=line-too-long
    v3_webapp_node_zip_url = 'https://connectorprod.blob.core.windows.net/bot-packages/node.js-abs-webapp_hello-chatconnector.zip'  # pylint: disable=line-too-long

    v4_webapp_template_name = 'webappv4.template.json'
    v4_webapp_csharp_zip_url = 'https://connectorprod.blob.core.windows.net/bot-packages/csharp-abs-webapp-v4_echobot_precompiled.zip'  # pylint: disable=line-too-long
    v4_webapp_node_zip_url = 'https://connectorprod.blob.core.windows.net/bot-packages/node.js-abs-webapp-v4_echobot.zip'  # pylint: disable=line-too-long

    @staticmethod
    def deploy_arm_template(cli_ctx, resource_group_name,  # pylint: disable=too-many-arguments
                            template_file=None, deployment_name=None,
                            parameters=None, mode=None):
        DeploymentProperties, _ = get_sdk(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES,
                                          'DeploymentProperties', 'TemplateLink', mod='models')

        template = {}
        # TODO: get_file_json() can return None if specified, otherwise it can throw an error.
        template = get_file_json(template_file, preserve_order=True)
        template_obj = template

        # So template should always be a dict, otherwise this next line will fail.
        template_obj['resources'] = template_obj.get('resources', [])
        # template_obj is not used after this point, can remove it.
        parameters = BotTemplateDeployer.__process_parameters(parameters) or {}

        # Turn the template into JSON string, then load it back to a dict, list, etc.
        template = json.loads(json.dumps(template))
        parameters = json.loads(json.dumps(parameters))

        properties = DeploymentProperties(template=template, template_link=None,
                                          parameters=parameters, mode=mode)

        smc = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
        return smc.deployments.create_or_update(resource_group_name, deployment_name, properties, raw=False)

    @staticmethod
    def create_app(cmd, logger, client, resource_group_name, resource_name, description, kind, appid, password,  # pylint:disable=too-many-statements
                   storageAccountName, location, sku_name, appInsightsLocation, language, version):
        """Create WebApp Bot.

        :param cmd:
        :param logger:
        :param client:
        :param resource_group_name:
        :param resource_name:
        :param description:
        :param kind:
        :param appid:
        :param password:
        :param storageAccountName:
        :param location:
        :param sku_name:
        :param appInsightsLocation:
        :param language:
        :param version:
        :return:
        """

        # Normalize language input and check if language is supported.
        language = language.capitalize()
        if language not in supported_languages:
            raise CLIError(
                'Invalid language provided for --lang parameter. Please choose one of the following supported '
                'programming languages for your bot: "Csharp" or "Node"')

        # Based on sdk version, language and kind, select the appropriate zip url containing starter bot source
        if version == 'v3':
            if kind == 'function':
                template_name = BotTemplateDeployer.function_template_name
                if language == 'Csharp':
                    zip_url = BotTemplateDeployer.csharp_function_zip_url
                else:
                    zip_url = BotTemplateDeployer.node_function_zip_url

            else:
                kind = 'sdk'
                template_name = BotTemplateDeployer.v3_webapp_template_name
                if language == 'Csharp':
                    zip_url = BotTemplateDeployer.v3_webapp_csharp_zip_url
                else:
                    zip_url = BotTemplateDeployer.v3_webapp_node_zip_url
        elif version == 'v4':
            if kind == 'function':
                raise CLIError('Function bot creation is not supported for v4 bot sdk.')

            else:
                kind = 'sdk'
                template_name = BotTemplateDeployer.v4_webapp_template_name
                if language == 'Csharp':
                    zip_url = BotTemplateDeployer.v4_webapp_csharp_zip_url
                else:
                    zip_url = BotTemplateDeployer.v4_webapp_node_zip_url

        logger.debug('Detected SDK version %s, kind %s and programming language %s. Using the following template: %s.',
                     version, kind, language, zip_url)

        # Storage prep
        # TODO: Review logic here. Why are we setting 'create_new_storage' to true when storageAccountname not provided?
        create_new_storage = False
        if not storageAccountName:
            create_new_storage = True

            storageAccountName = re.sub(r'[^a-z0-9]', '', resource_name[:10] +
                                        ''.join(
                                            random.choice(string.ascii_lowercase + string.digits) for _ in range(4)))
            site_name = re.sub(r'[^a-z0-9]', '', resource_name[:15] +
                               ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(4)))

            logger.debug('Storage name not provided. If storage is to be created, name to be used is %s.',
                         storageAccountName)
            logger.debug('Web or Function app name to be used is %s.', site_name)

        # Application insights prep
        appInsightsLocation = azure_region_mapper.AzureRegionMapper\
            .get_app_insights_location(appInsightsLocation.lower().replace(' ', ''))

        logger.debug('Application insights location resolved to %s.', appInsightsLocation)

        # ARM Template parameters
        paramsdict = {
            "location": location,
            "kind": kind,
            "sku": sku_name,
            "siteName": site_name,
            "appId": appid,
            "appSecret": password,
            "storageAccountResourceId": "",
            "serverFarmId": "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Web/serverfarms/{2}".format(
                client.config.subscription_id, resource_group_name, resource_name),
            "zipUrl": zip_url,
            "createNewStorage": create_new_storage,
            "storageAccountName": storageAccountName,
            "botEnv": "prod",
            "useAppInsights": True,
            "appInsightsLocation": appInsightsLocation,
            "createServerFarm": True,
            "serverFarmLocation": location.lower().replace(' ', ''),
            "azureWebJobsBotFrameworkDirectLineSecret": "",
            "botId": resource_name
        }
        if description:
            paramsdict['description'] = description

        # TODO: Do we still encrypt this file? Should it be on a user-specified basis?
        # If the bot is a v4 bot, generate an encryption key for the .bot file
        if template_name == 'webappv4.template.json':

            logger.debug('Detected V4 bot. Adding bot encryption key to Azure parameters.')

            bot_encryption_key = BotTemplateDeployer.get_bot_file_encryption_key()
            paramsdict['botFileEncryptionKey'] = bot_encryption_key
        params = {k: {'value': v} for k, v in paramsdict.items()}

        # Get and deploy ARM template
        dir_path = os.path.dirname(os.path.realpath(__file__))

        logger.debug('ARM template creation complete. Deploying ARM template. ')
        deploy_result = BotTemplateDeployer.deploy_arm_template(
            cli_ctx=cmd.cli_ctx,
            resource_group_name=resource_group_name,
            template_file=os.path.join(dir_path, template_name),
            parameters=[[json.dumps(params)]],
            deployment_name=resource_name,
            mode='Incremental'
        )

        deploy_result.wait()

        logger.debug('ARM template deployment complete. Result %s ', deploy_result)
        logger.info('Bot creation completed successfully.')

        return BotJsonFormatter.create_bot_json(cmd, client, resource_group_name, resource_name, logger,
                                                app_password=password)

    @staticmethod
    def get_bot_file_encryption_key():
        """Perform call to https://dev.botframework.com to get a .bot file encryption key.

        :return: string
        """

        # Pulled out of create_app, which is the only place that performs this call
        response = requests.get('https://dev.botframework.com/api/misc/botFileEncryptionKey')

        # Can't a user create a new secret and then re-encrypt the bot file?
        if response.status_code not in [200]:
            raise CLIError('Unable to provision a bot file encryption key. Please try again.')
        return response.text[1:-1]

    @staticmethod
    def update(client, parameters, resource_group_name):
        try:
            return client.update(
                resource_group_name=resource_group_name,
                resource_name=parameters.name,
                **(parameters.__dict__)
            )
        except AttributeError:
            return None

    @staticmethod
    def __process_parameters(parameter_lists):
        def _try_parse_json_object(value):
            try:
                parsed = shell_safe_json_parse(value)
                return parsed.get('parameters', parsed)
            except CLIError:
                return None

        parameters = {}
        for params in parameter_lists or []:
            for item in params:
                param_obj = _try_parse_json_object(item)
                if param_obj:
                    parameters.update(param_obj)

        return parameters
