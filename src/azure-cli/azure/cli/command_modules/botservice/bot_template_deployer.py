# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import re
import requests

from knack.util import CLIError
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.profiles import ResourceType, get_sdk
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.util import get_file_json, shell_safe_json_parse
from azure.cli.command_modules.botservice.bot_json_formatter import BotJsonFormatter
from azure.cli.command_modules.botservice.constants import CSHARP, JAVASCRIPT


class BotTemplateDeployer:

    v4_webapp_template_name = 'webappv4.template.json'

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

        resource_management_client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
        return LongRunningOperation(cli_ctx, 'Deploying ARM Tempalte')(
            resource_management_client.deployments.create_or_update(resource_group_name,
                                                                    deployment_name,
                                                                    properties, raw=False))

    @staticmethod
    def create_app(cmd, logger, client, resource_group_name, resource_name, description, kind, appid, password,  # pylint:disable=too-many-statements
                   location, sku_name, language, bot_template_type):
        kind = 'sdk' if kind == 'webapp' else kind
        (zip_url, template_name) = BotTemplateDeployer.__retrieve_bot_template_link(language,
                                                                                    bot_template_type)

        logger.debug('Detected kind %s and programming language %s. Using the following template: %s.',
                     kind, language, zip_url)

        site_name = re.sub(r'[^a-z0-9\-]', '', resource_name[:40].lower())

        # The name of Azure Web Sites cannot end with "-", e.g. "testname-.azurewbesites.net" is invalid.
        # The valid name would be "testname.azurewebsites.net"
        while site_name[-1] == '-':
            site_name = site_name[:-1]
        logger.debug('Web app name to be used is %s.', site_name)

        # ARM Template parameters
        paramsdict = {
            "location": location,
            "kind": kind,
            "sku": sku_name,
            "siteName": site_name,
            "appId": appid,
            "appSecret": password,
            "serverFarmId": "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Web/serverfarms/{2}".format(
                client.config.subscription_id, resource_group_name, resource_name),
            "zipUrl": zip_url,
            "botEnv": "prod",
            "createServerFarm": True,
            "serverFarmLocation": location.lower().replace(' ', ''),
            "botId": resource_name
        }
        if description:
            paramsdict['description'] = description

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

        logger.debug('ARM template deployment complete. Result %s ', deploy_result)
        logger.info('Bot creation completed successfully.')

        return BotJsonFormatter.create_bot_json(cmd, client, resource_group_name, resource_name, logger,
                                                app_password=password)

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

    @staticmethod
    def __retrieve_bot_template_link(language, bot_template_type):
        if not bot_template_type:
            return '', BotTemplateDeployer.v4_webapp_template_name

        response = requests.get('https://dev.botframework.com/api/misc/bottemplateroot')
        if response.status_code != 200:
            raise CLIError('Unable to get bot code template from CDN. Please file an issue on {0}'.format(
                'https://github.com/microsoft/botframework-sdk'
            ))
        cdn_link = response.text.strip('"')

        template_name = BotTemplateDeployer.v4_webapp_template_name
        if language == CSHARP and bot_template_type == 'echo':
            cdn_link = cdn_link + 'csharp-abs-webapp-v4_echobot_precompiled.zip'
        elif language == JAVASCRIPT and bot_template_type == 'echo':
            cdn_link = cdn_link + 'node.js-abs-webapp-v4_echobot.zip'

        return cdn_link, template_name
