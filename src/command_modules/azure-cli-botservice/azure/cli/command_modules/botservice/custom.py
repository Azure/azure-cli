# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import shutil

from azure.cli.command_modules.botservice.converged_app import ConvergedApp
from azure.cli.command_modules.botservice.bot_json_formatter import BotJsonFormatter
from azure.cli.command_modules.botservice.bot_publish_prep import BotPublishPrep
from azure.cli.command_modules.botservice.bot_template_deployer import BotTemplateDeployer
from azure.cli.command_modules.botservice.kudu_client import KuduClient
from azure.cli.command_modules.botservice.web_app_operations import WebAppOperations
from azure.mgmt.botservice.models import (
    Bot,
    BotProperties,
    ConnectionSetting,
    ConnectionSettingProperties,
    ConnectionSettingParameter,
    Sku)

from knack.util import CLIError
from knack.log import get_logger

logger = get_logger(__name__)


def create(cmd, client, resource_group_name, resource_name, kind, description=None, display_name=None,
           endpoint=None, msa_app_id=None, password=None, tags=None, storageAccountName=None,
           location='Central US', sku_name='F0', appInsightsLocation='South Central US',
           language='Csharp', version='v3'):
    """Create a WebApp, Function, or Channels Registration Bot on Azure.

    This method is directly called via "bot create"

    :param cmd:
    :param client:
    :param resource_group_name:
    :param resource_name:
    :param kind:
    :param description:
    :param display_name:
    :param endpoint:
    :param msa_app_id:
    :param password:
    :param tags:
    :param storageAccountName:
    :param location:
    :param sku_name:
    :param appInsightsLocation:
    :param language:
    :param version:
    :return:
    """

    # If display name was not provided, just use the resource name
    display_name = display_name or resource_name

    # Kind parameter validation
    kind = kind.lower()

    registration_kind = 'registration'
    bot_kind = 'bot'
    webapp_kind = 'webapp'
    function_kind = 'function'

    # Mapping: registration is deprecated, we now use 'bot' kind for registration bots
    if kind == registration_kind:
        kind = bot_kind

    if kind not in (bot_kind, webapp_kind, function_kind):
        raise CLIError('Invalid Bot Parameter : kind. Valid kinds are \'registration\' for registration bots, '
                       '\'webapp\' for webapp bots and \'function\' for function bots. Run \'az bot create -h\' '
                       'for more information.')

    # If a Microsoft application id was not provided, provision one for the user
    if not msa_app_id:

        logger.info('Microsoft application id not passed as a parameter. Provisioning a new Microsoft application.')

        msa_app_id, password = ConvergedApp.provision(resource_name)
        logger.info('Microsoft application provisioning successful. Application Id: %s.', msa_app_id)

    logger.info('Creating Azure Bot Service.')

    # Registration bots: simply call ARM and create the bot
    if kind == bot_kind:

        logger.info('Detected kind %s, validating parameters for the specified kind.', kind)

        # Registration bot specific validation
        if not endpoint:
            raise CLIError('Endpoint is required for creating a registration bot.')
        if not msa_app_id:
            raise CLIError('Microsoft application id is required for creating a registration bot.')

        parameters = Bot(
            location='global',
            sku=Sku(name=sku_name),
            kind=kind,
            tags=tags,
            properties=BotProperties(
                display_name=display_name,
                description=description,
                endpoint=endpoint,
                msa_app_id=msa_app_id
            )
        )
        logger.info('Bot parameters client side validation successful.')
        logger.info('Creating bot.')

        return client.bots.create(
            resource_group_name=resource_group_name,
            resource_name=resource_name,
            parameters=parameters
        )
    # Web app and function bots require deploying custom ARM templates, we do that in a separate method
    else:
        logger.info('Detected kind %s, validating parameters for the specified kind.', kind)

        return BotTemplateDeployer.create_app(cmd, logger, client, resource_group_name, resource_name, description,
                                              kind, msa_app_id, password, storageAccountName, location, sku_name,
                                              appInsightsLocation, language, version)


def get_bot(cmd, client, resource_group_name, resource_name, bot_json=None):
    """Retrieves the bot's application's application settings. If called with '--msbot' flag, the operation outputs
    a collection of data that can be piped into a .bot file.

    This method is directly called via "bot show"
    :param cmd:
    :param client:
    :param resource_group_name:
    :param resource_name:
    :param bot_json:
    """
    raw_bot_properties = client.bots.get(
        resource_group_name=resource_group_name,
        resource_name=resource_name
    )
    if bot_json:
        return BotJsonFormatter.create_bot_json(cmd, client, resource_group_name, resource_name, logger,
                                                raw_bot_properties=raw_bot_properties)

    return raw_bot_properties


def create_connection(client, resource_group_name, resource_name, connection_name, client_id,
                      client_secret, scopes, service_provider_name, parameters=None):
    """Create a custom OAuth service provider.

    This method is directly called via "bot authsetting create"

    :param client:
    :param resource_group_name:
    :param resource_name:
    :param connection_name:
    :param client_id:
    :param client_secret:
    :param scopes:
    :param service_provider_name:
    :param parameters:
    :return:
    """
    service_provider = get_service_providers(client, name=service_provider_name)
    if not service_provider:
        raise CLIError('Invalid Service Provider Name passed. Use "az bot authsetting list-providers" '
                       'command to see all available providers')
    connection_parameters = []
    if parameters:
        for parameter in parameters:
            pair = parameter.split('=', 1)
            if len(pair) == 1:
                raise CLIError('usage error: --parameters STRING=STRING STRING=STRING')
            connection_parameters.append(ConnectionSettingParameter(key=pair[0], value=pair[1]))
    setting = ConnectionSetting(
        location='global',
        properties=ConnectionSettingProperties(
            client_id=client_id,
            client_secret=client_secret,
            scopes=scopes,
            service_provider_id=service_provider.properties.id,
            parameters=connection_parameters
        )
    )
    return client.bot_connection.create(resource_group_name, resource_name, connection_name, setting)


def download_app(cmd, client, resource_group_name, resource_name, file_save_path=None):  # pylint: disable=too-many-statements, too-many-locals
    """Download the bot's source code.

    This method is directly called via "bot download"

    :param cmd:
    :param client:
    :param resource_group_name:
    :param resource_name:
    :param file_save_path:
    :return:
    """
    logger.info('Retrieving bot information from Azure.')

    # Get the bot and ensure it's not a registration only bot
    bot = client.bots.get(
        resource_group_name=resource_group_name,
        resource_name=resource_name
    )
    logger.info('Bot information retrieved successfully from Azure.')

    if bot.kind == 'bot':
        raise CLIError('Source download is not supported for registration only bots')

    if not file_save_path:
        file_save_path = os.getcwd()
        logger.info('Parameter --save-path not provided, defaulting to current working directory, %s. '
                    'For more information, run \'az bot download -h\'', file_save_path)

    file_save_path = file_save_path.strip()
    if not os.path.isdir(file_save_path):
        raise CLIError('Path name not valid')

    # TODO: Verify that the behavior for download and publish is the same in regards to where the files are downloaded
    # TODO: to and uploaded from.
    folder_path = os.path.join(file_save_path, resource_name)

    logger.info('Bot source will be downloaded to %s.', folder_path)

    if os.path.exists(folder_path):
        raise CLIError('The path {0} already exists. '
                       'Please delete this folder or specify an alternate path'.format(folder_path))

    logger.info('Attempting to preemptively create directory %s', folder_path)
    os.mkdir(folder_path)

    logger.info('Creating Kudu client to download bot source.')
    kudu_client = KuduClient(cmd, resource_group_name, resource_name, bot, logger)

    logger.info('Downloading bot source. This operation may take seconds or minutes depending on the size of '
                'your bot source and the download speed of your internet connection.')
    kudu_client.download_bot_zip(file_save_path, folder_path)

    logger.info('Bot source download successful. Preparing bot project.')

    # TODO: Examine cases where PostDeployScripts, deploy.cmd, etc. do not exist.
    if (os.path.exists(os.path.join(folder_path, 'PostDeployScripts', 'deploy.cmd.template')) and
            os.path.exists(os.path.join(folder_path, 'deploy.cmd'))):

        logger.info('Post deployment scripts and deploy.cmd found in source under folder %s. Copying deploy.cmd.')

        shutil.copyfile(os.path.join(folder_path, 'deploy.cmd'),
                        os.path.join(folder_path, 'PostDeployScripts', 'deploy.cmd.template'))

    # If the bot source contains a .bot file
    # TODO: If there is only one bot file, that is the bot file.
    # TODO: If there are more than one bot file, the user must disambiguate before continuing.
    # TODO: Show error and suggest passsing --bot-file-name

    bot_file_path = os.path.join(folder_path, '{0}.bot'.format(resource_name))
    if os.path.exists(bot_file_path):

        logger.info('Detected bot file %s.', bot_file_path)

        app_settings = WebAppOperations.get_app_settings(
            cmd=cmd,
            resource_group_name=resource_group_name,
            name=kudu_client.bot_site_name
        )
        bot_secret = [item['value'] for item in app_settings if item['name'] == 'botFileSecret']

        # Write a .env file
        bot_env = {
            'botFileSecret': bot_secret[0],
            'botFilePath': '{0}.bot'.format(resource_name),
            'NODE_ENV': 'development'
        }
        # If javascript, write .env file content to .env file
        if os.path.exists(os.path.join(folder_path, 'package.json')):

            logger.info('Detected language as javascript. Package.json present at %s. Creating .env file in that '
                        'folder.', folder_path)

            with open(os.path.join(folder_path, '.env'), 'w') as f:
                for key, value in bot_env.items():
                    f.write('{0}={1}\n'.format(key, value))
        # If C#, write .env file content to appsettings.json
        else:

            app_settings_path = os.path.join(folder_path, 'appsettings.json')

            logger.info('Detected language as CSharp. Loading app settings from %s.', app_settings_path)

            existing = None
            if not os.path.exists(app_settings_path):

                logger.info('App settings not found at %s, defaulting app settings to {}.', app_settings_path)
                existing = '{}'
            else:
                with open(app_settings_path, 'r') as f:
                    existing = json.load(f)
            with open(os.path.join(app_settings_path), 'w+') as f:
                for key, value in bot_env.items():
                    existing[key] = value
                f.write(json.dumps(existing))

        # TODO: Optimize this logic and document. If there is not bot secret, add bot_env download path. Why?
        # TODO: Consider just returning downloadPath as a string rather than this object. There seem to be no
        # TODO: usages of the other properties such as botFileSecret
        if not bot_secret:

            logger.info('Bot secret not found. Setting download path to %s', folder_path)

            bot_env['downloadPath'] = folder_path
            return bot_env

    logger.info('Bot download completed successfully.')

    return {'downloadPath': folder_path}


def get_service_providers(client, name=None):
    """Gets supported OAuth Service providers.

    This method is directly called via "bot authsetting list-providers"

    :param client:
    :param name:
    :return:
    """

    service_provider_response = client.bot_connection.list_service_providers()
    name = name and name.lower()
    if name:
        try:
            return next((item for item in service_provider_response.value if
                         item.properties.service_provider_name.lower() == name.lower()))
        except StopIteration:
            raise CLIError('A service provider with the name {0} was not found'.format(name))
    return service_provider_response


def prepare_publish(cmd, client, resource_group_name, resource_name, sln_name, proj_name, code_dir=None, version='v3'):  # pylint:disable=too-many-statements
    """Adds PostDeployScripts folder with necessary scripts to deploy v3 bot to Azure.

    This method is directly called via "bot prepare-publish"

    :param cmd:
    :param client:
    :param resource_group_name:
    :param resource_name:
    :param sln_name:
    :param proj_name:
    :param code_dir:
    :param version:
    :return:
    """

    # The prepare-publish process for v3 bots and v4 bots differ, so if the user specifies a v4 version, end the command
    # and inform user of az bot publish.
    if version == 'v4':
        raise CLIError('\'az bot prepare-publish\' is only for v3 bots. Please use \'az bot publish\' to prepare and '
                       'publish a v4 bot.')

    bot = client.bots.get(
        resource_group_name=resource_group_name,
        resource_name=resource_name
    )
    if bot.kind == 'bot':
        raise CLIError('Prepare Publish is not supported for registration only bots.')

    if not code_dir:
        code_dir = os.getcwd()
        logger.warning('Parameter --code-dir not provided, defaulting to current working directory, %s. For more '
                       'information, run \'az bot prepare-publish -h\'', code_dir)

    code_dir = code_dir.strip()
    if not os.path.isdir(code_dir):
        raise CLIError('Please supply a valid directory path containing your source code. '
                       'Path {0} does not exist.'.format(code_dir))

    os.chdir(code_dir)

    # Ensure that the directory does not contain appropriate post deploy scripts folder
    if 'PostDeployScripts' in os.listdir(code_dir):
        raise CLIError('Post deploy azure scripts are already in Place.')

    # Download bot source
    download_path = download_app(cmd, client, resource_group_name, resource_name)

    shutil.copytree(os.path.join(download_path['downloadPath'], 'PostDeployScripts'), 'PostDeployScripts')

    # If javascript, we need these files there for Azure WebApps to start
    if os.path.exists(os.path.join('PostDeployScripts', 'publish.js.template')):

        logger.info('Detected language javascript.')

        shutil.copy(os.path.join(download_path['downloadPath'], 'iisnode.yml'), 'iisnode.yml')
        shutil.copy(os.path.join(download_path['downloadPath'], 'publish.js'), 'publish.js')
        shutil.copy(os.path.join(download_path['downloadPath'], 'web.config'), 'web.config')

    # If C#, we need other set of files for the WebApp to start including build.cmd
    else:
        logger.info('Detected language CSharp.')
        solution_path = None
        csproj_path = None
        old_namev4 = 'AspNetCore-EchoBot-With-State'
        old_namev3 = 'Microsoft.Bot.Sample.SimpleEchoBot'
        shutil.copy(os.path.join(download_path['downloadPath'], 'build.cmd'), 'build.cmd')
        shutil.copy(os.path.join(download_path['downloadPath'], '.deployment'), '.deployment')

        # "deploy.cmd.template" does not exist for v4 bots. If the next section of code fails due to deploy.cmd.template
        # not being found, it is most likely due to trying to call prepare-publish on a v4 bot.
        # Inform the user of the potential problem and raise the error to exit the process.
        try:
            shutil.copyfile(os.path.join(download_path['downloadPath'], 'PostDeployScripts', 'deploy.cmd.template'),
                            'deploy.cmd')
        except FileNotFoundError as error:
            logger.error('"deploy.cmd.template" not found. This may be due to calling \'az bot prepare-publish\' on a '
                         'v4 bot. To prepare and publish a v4 bot, please instead use \'az bot publish\'.')
            raise CLIError(error)

        # Find solution and project name
        for root, _, files in os.walk(os.curdir):
            if solution_path and csproj_path:
                break
            for fileName in files:
                if solution_path and csproj_path:
                    break
                if fileName == sln_name:
                    solution_path = os.path.relpath(os.path.join(root, fileName))
                if fileName == proj_name:
                    csproj_path = os.path.relpath(os.path.join(root, fileName))

        # Read deploy script contents
        with open('deploy.cmd') as f:
            content = f.read()

        logger.info('Visual studio solution detected: %s.', solution_path)
        logger.info('Visual studio project detected: %s.', csproj_path)

        # Using the deploy.cmd as a template, adapt it to use our solution and csproj
        with open('deploy.cmd', 'w') as f:
            content = content.replace(old_namev3 + '.sln', solution_path)
            content = content.replace(old_namev3 + '.csproj', csproj_path)
            content = content.replace(old_namev4 + '.sln', solution_path)
            content = content.replace(old_namev4 + '.csproj', csproj_path)
            f.write(content)

    shutil.rmtree(download_path['downloadPath'])

    logger.info('Bot prepare publish completed successfully.')


def publish_app(cmd, client, resource_group_name, resource_name, code_dir=None, proj_name=None, version='v3'):
    """Publish local bot code to Azure.

    This method is directly called via "bot publish"

    :param cmd:
    :param client:
    :param resource_group_name:
    :param resource_name:
    :param code_dir:
    :param proj_name:
    :param version:
    :return:
    """
    # Get the bot information and ensure it's not only a registration bot.
    bot = client.bots.get(
        resource_group_name=resource_group_name,
        resource_name=resource_name
    )
    if bot.kind == 'bot':
        raise CLIError('Bot kind is \'bot\', meaning it is a registration bot. '
                       'Source publish is not supported for registration only bots.')

    # If the user does not pass in a path to the local bot project, get the current working directory.
    if not code_dir:
        code_dir = os.getcwd()

        logger.info('Parameter --code-dir not provided, defaulting to current working directory, %s. '
                    'For more information, run \'az bot publish -h\'', code_dir)

    code_dir = code_dir.strip()
    if not os.path.isdir(code_dir):
        raise CLIError('The path %s is not a valid directory. '
                       'Please supply a valid directory path containing your source code.' % code_dir)

    # Ensure that the directory contains appropriate post deploy scripts folder
    if 'PostDeployScripts' not in os.listdir(code_dir):
        if version == 'v4':

            logger.info('Detected SDK version v4. Running prepare publish in code directory %s and for project file %s'  # pylint:disable=logging-not-lazy
                        % (code_dir, proj_name))

            # Automatically run prepare-publish in case of v4.
            BotPublishPrep.prepare_publish_v4(logger, code_dir, proj_name)
        else:
            logger.info('Detected SDK version v3. PostDeploymentScripts folder not found in directory provided: %s',
                        code_dir)

            raise CLIError('Publish directory provided is uses Bot Builder SDK V3, and as a legacy bot needs to be '
                           'prepared for deployment. Please run prepare-publish. For more information, run \'az bot '
                           'prepare-publish -h\'.')

    logger.info('Creating upload zip file.')
    zip_filepath = BotPublishPrep.create_upload_zip(logger, code_dir, include_node_modules=False)
    logger.info('Zip file path created, at %s.', zip_filepath)

    kudu_client = KuduClient(cmd, resource_group_name, resource_name, bot, logger)
    output = kudu_client.publish(zip_filepath)

    logger.info('Bot source published. Preparing bot application to run the new source.')
    os.remove('upload.zip')

    if os.path.exists(os.path.join('.', 'package.json')):
        logger.info('Detected language javascript. Installing node dependencies in remote bot.')
        kudu_client.install_node_dependencies()

    logger.info('Bot publish completed successfully.')

    return output
