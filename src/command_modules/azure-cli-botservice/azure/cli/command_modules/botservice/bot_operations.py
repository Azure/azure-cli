# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import requests
import shutil
# TODO: Evalulate the use of requests and urllib3, where urllib3 is a dependency of requests
import urllib3
import zipfile

from .auth import converged_app
from .bot_json_formatter import BotJsonFormatter
from .bot_publish_helper import BotPublishHelper
from .bot_template_deployer import BotTemplateDeployer
from .http_response_validator import HttpResponseValidator
from .kudu_client import KuduClient
from .web_app_operations import WebAppOperations

from knack.util import CLIError
from knack.log import get_logger
from azure.mgmt.botservice.models import (
    Bot,
    BotProperties,
    ConnectionSetting,
    ConnectionSettingProperties,
    ConnectionSettingParameter,
    Sku)

logger = get_logger(__name__)
# TODO: Investigate if verbose flag is set to true on the logger, or experimenting with it individually to have verbose logging


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
        raise CLIError('Invalid Bot Parameter : kind')

    # TODO validate common parameters

    # If a Microsoft application id was not provided, provision one for the user
    if not msa_app_id:
        msa_app_id, password = converged_app.ConvergedApp.provision(resource_name)
        logger.warning('Microsoft application provisioning successful.')

    logger.warning('Provisioning bot...')

    # Registration bots: simply call ARM and create the bot
    if kind == bot_kind:

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
        return client.bots.create(
            resource_group_name=resource_group_name,
            resource_name=resource_name,
            parameters=parameters
        )
    # Web app and function bots require deploying custom ARM templates, we do that in a separate method
    else:
        return BotTemplateDeployer.create_app(cmd, client, resource_group_name, resource_name, description, kind,
                                              msa_app_id, password, storageAccountName, location, sku_name,
                                              appInsightsLocation, language, version)


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
    # get the bot and ensure it's not a registration only bot
    bot = client.bots.get(
        resource_group_name=resource_group_name,
        resource_name=resource_name
    )
    if bot.kind == 'bot':
        raise CLIError('Source download is not supported for registration only bots')

    # TODO: Informational logging, how to do it? Once we know, do it all over the place :)
    # TODO: warning when defaulting!
    file_save_path = file_save_path or os.getcwd()
    if not os.path.isdir(file_save_path):
        raise CLIError('Path name not valid')

    # TODO: Verify that the behavior for download and publish is the same in regards to where the files are downloaded
    # TODO: to and uploaded from.
    folder_path = os.path.join(file_save_path, resource_name)
    if os.path.exists(folder_path):
        raise CLIError('The path {0} already exists. Please delete this folder or specify an alternate path'.format(folder_path))  # pylint: disable=line-too-long
    os.mkdir(folder_path)

    kudu_client = KuduClient(cmd, resource_group_name, resource_name, bot)
    kudu_client.download_bot_zip(file_save_path, folder_path)

    # TODO: Examine cases where PostDeployScripts, deploy.cmd, etc. do not exist.
    if (os.path.exists(os.path.join(folder_path, 'PostDeployScripts', 'deploy.cmd.template')) and
            os.path.exists(os.path.join(folder_path, 'deploy.cmd'))):
        shutil.copyfile(os.path.join(folder_path, 'deploy.cmd'),
                        os.path.join(folder_path, 'PostDeployScripts', 'deploy.cmd.template'))

    # If the bot source contains a .bot file
    # TODO: If there is only one bot file, that is the bot file.
    # TODO: If there are more than one bot file, the user must disambiguate before continuing. Show error and suggest passsing --bot-file-name
    bot_file_path = os.path.join(folder_path, '{0}.bot'.format(resource_name))
    if os.path.exists(bot_file_path):
        app_settings = WebAppOperations.get_app_settings(
            cmd=cmd,
            resource_group_name=resource_group_name,
            name=kudu_client.bot_site_name
        )
        bot_secret = [item['value'] for item in app_settings if item['name'] == 'botFileSecret']
        # write a .env file #todo: write an appsettings.json file
        bot_env = {
            'botFileSecret': bot_secret[0],
            'botFilePath': '{0}.bot'.format(resource_name),
            'NODE_ENV': 'development'
        }
        # If javascript, write .env file content to .env file
        if os.path.exists(os.path.join(folder_path, 'package.json')):
            with open(os.path.join(folder_path, '.env'), 'w') as f:
                for key, value in bot_env.items():
                    f.write('{0}={1}\n'.format(key, value))
        # If C#, write .env file content to appsettings.json
        else:
            app_settings_path = os.path.join(folder_path, 'appsettings.json')
            existing = None
            if not os.path.exists(app_settings_path):
                existing = '{}'
            else:
                with open(app_settings_path, 'r') as f:
                    existing = json.load(f)
            with open(os.path.join(app_settings_path), 'w+') as f:
                for key, value in bot_env.items():
                    existing[key] = value
                f.write(json.dumps(existing))

        # TODO: understand this. If there is not bot secret,  add bot_env info
        # TODO: Consider just returning downloadPAth as a string rather than this object. There seem to be no
        # usages of the other properties such as botFileSecret
        if not bot_secret:
            bot_env['downloadPath'] = folder_path
            return bot_env

    return {'downloadPath': folder_path}



# TODO: Split into separate commands, one that returns all supported providers, and one that gets a singular provider.
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

# TODO: Add deprecated warning
def prepare_publish(cmd, client, resource_group_name, resource_name, sln_name, proj_name, code_dir=None):
    """

    This method is directly called via "bot prepare-publish"

    :param cmd:
    :param client:
    :param resource_group_name:
    :param resource_name:
    :param sln_name:
    :param proj_name:
    :param code_dir:
    :return:
    """
    # logger.warning('Warning: "az bot prepare-publish" is deprecated. Please use "az bot add-publish-scripts" instead.')
    raw_bot_properties = client.bots.get(
        resource_group_name=resource_group_name,
        resource_name=resource_name
    )
    if raw_bot_properties.kind == 'bot':
        raise CLIError('Prepare Publish is not supported for registration only bots')
    # TODO: If we grab os.getcwd, show message to the user, 'defaulting to local directory, pass --code-dir to override'
    code_dir = code_dir or os.getcwd()
    if not os.path.isdir(code_dir):
        # TODO: Why not say 'you are all set, be happy :)' instead of displaying an error?
        raise CLIError('Please supply a valid directory path containing your source code')

    # TODO: Can we avoid? Changing the current working directory.
    os.chdir(code_dir)

    # Ensure that the directory does not contain appropriate post deploy scripts folder
    if 'PostDeployScripts' in os.listdir(code_dir):
        raise CLIError('Post deploy azure scripts are already in Place.')

    # Download bot source
    # TODO: Why not return a string rather than force callers to dereference a dictionary?
    # TODO: Rename name, this is a dictionary
    download_path = download_app(cmd, client, resource_group_name, resource_name)

    # TODO: If I create a node bot, and then publish a c# bot does this work
    # TODO: Can't we just have a constant PostDeployScripts folder somewhere?
    shutil.copytree(os.path.join(download_path['downloadPath'], 'PostDeployScripts'), 'PostDeployScripts')

    # If javascript, we need these files there for Azure WebApps to start
    if os.path.exists(os.path.join('PostDeployScripts', 'publish.js.template')):
        shutil.copy(os.path.join(download_path['downloadPath'], 'iisnode.yml'), 'iisnode.yml')
        shutil.copy(os.path.join(download_path['downloadPath'], 'publish.js'), 'publish.js')
        shutil.copy(os.path.join(download_path['downloadPath'], 'web.config'), 'web.config')

    # If C#, we need other set of files for the WebApp to start including build.cmd
    else:
        solution_path = None
        csproj_path = None
        old_namev4 = 'AspNetCore-EchoBot-With-State'
        old_namev3 = 'Microsoft.Bot.Sample.SimpleEchoBot'
        shutil.copy(os.path.join(download_path['downloadPath'], 'build.cmd'), 'build.cmd')
        shutil.copy(os.path.join(download_path['downloadPath'], '.deployment'), '.deployment')
        shutil.copyfile(os.path.join(download_path['downloadPath'], 'PostDeployScripts', 'deploy.cmd.template'),
                        'deploy.cmd')
        # Find solution and project name
        # TODO: Maybe we don't want to get into this business. Allow users to specify csproj / sln?
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

        # Using the deploy.cmd as a template, adapt it to use our solution and csproj
        # TODO: Create template deploy.cmd
        with open('deploy.cmd', 'w') as f:
            content = content.replace(old_namev3 + '.sln', solution_path)
            content = content.replace(old_namev3 + '.csproj', csproj_path)
            content = content.replace(old_namev4 + '.sln', solution_path)
            content = content.replace(old_namev4 + '.csproj', csproj_path)
            f.write(content)

    shutil.rmtree(download_path['downloadPath'])


# TODO: WIP
def add_publish_scripts(cmd, client, resource_group_name, resource_name,
                        language='Csharp', sln_name=None, proj_name=None, code_dir=None):
    """Add Azure publish scripts to local bot folder.

    Takes an optional --language argument

    :param cmd:
    :param client:
    :param resource_group_name:
    :param resource_name:
    :param language:
    :param sln_name:
    :param proj_name:
    :param code_dir:
    :return:
    """
    raise NotImplementedError
    bot = client.bots.get(
        resource_group_name=resource_group_name,
        resource_name=resource_name
    )
    if bot.kind == 'bot':
        raise CLIError('Prepare Publish is not supported for registration only bots')
    # TODO: If we grab os.getcwd, show message to the user, 'defaulting to local directory, pass --code-dir to override'
    code_dir = code_dir or os.getcwd()
    if not os.path.isdir(code_dir):
        # TODO: Why not say 'you are all set, be happy :)' instead of displaying an error?
        raise CLIError('Please supply a valid directory path containing your source code')

    # TODO: Can we avoid? Changing the current working directory.
    os.chdir(code_dir)

    # Ensure that the directory does not contain appropriate post deploy scripts folder
    if 'PostDeployScripts' in os.listdir(code_dir):
        raise CLIError('Post deploy azure scripts are already in Place.')

    # Download bot source
    # TODO: Why not return a string rather than force callers to dereference a dictionary?
    # TODO: Rename name, this is a dictionary
    download_path = download_app(cmd, client, resource_group_name, resource_name)

    # TODO: If I create a node bot, and then publish a c# bot does this work
    # TODO: Can't we just have a constant PostDeployScripts folder somewhere?
    shutil.copytree(os.path.join(download_path['downloadPath'], 'PostDeployScripts'), 'PostDeployScripts')

    # If javascript, we need these files there for Azure WebApps to start
    if os.path.exists(os.path.join('PostDeployScripts', 'publish.js.template')):
        shutil.copy(os.path.join(download_path['downloadPath'], 'iisnode.yml'), 'iisnode.yml')
        shutil.copy(os.path.join(download_path['downloadPath'], 'publish.js'), 'publish.js')
        shutil.copy(os.path.join(download_path['downloadPath'], 'web.config'), 'web.config')

    # If C#, we need other set of files for the WebApp to start including build.cmd
    else:
        solution_path = None
        csproj_path = None
        old_namev4 = 'AspNetCore-EchoBot-With-State'
        old_namev3 = 'Microsoft.Bot.Sample.SimpleEchoBot'
        shutil.copy(os.path.join(download_path['downloadPath'], 'build.cmd'), 'build.cmd')
        shutil.copy(os.path.join(download_path['downloadPath'], '.deployment'), '.deployment')
        shutil.copyfile(os.path.join(download_path['downloadPath'], 'PostDeployScripts', 'deploy.cmd.template'),
                        'deploy.cmd')
        # Find solution and project name
        # TODO: Maybe we don't want to get into this business. Allow users to specify csproj / sln?
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

        # Using the deploy.cmd as a template, adapt it to use our solution and csproj
        # TODO: Create template deploy.cmd
        with open('deploy.cmd', 'w') as f:
            content = content.replace(old_namev3 + '.sln', solution_path)
            content = content.replace(old_namev3 + '.csproj', csproj_path)
            content = content.replace(old_namev4 + '.sln', solution_path)
            content = content.replace(old_namev4 + '.csproj', csproj_path)
            f.write(content)

    shutil.rmtree(download_path['downloadPath'])


def publish_app(cmd, client, resource_group_name, resource_name, code_dir=None, proj_file=None, sdk_version='v3'):
    """Publish local bot code to Azure.

    This method is directly called via "bot publish"

    :param cmd:
    :param client:
    :param resource_group_name:
    :param resource_name:
    :param code_dir:
    :param proj_file:
    :param sdk_version:
    :return:
    """
    # Get the bot information and ensure it's not only a registration bot.
    bot = client.bots.get(
        resource_group_name=resource_group_name,
        resource_name=resource_name
    )
    if bot.kind == 'bot':
        raise CLIError('Source publish is not supported for registration only bots')

    # If the user does not pass in a path to the local bot project, get the current working directory.
    if not code_dir:
        # TODO: If we grab os.getcwd, show message to the user, 'defaulting to local directory, pass --code-dir to override'
        code_dir = os.getcwd()

    if not os.path.isdir(code_dir):
        raise CLIError('Please supply a valid directory path containing your source code')
    # ensure that the directory contains appropriate post deploy scripts folder
    # TODO: Find out if PostDeployScripts is language specific -> It is not, but can we streamline this?
    if 'PostDeployScripts' not in os.listdir(code_dir):
        if sdk_version == 'v4':
            # automatically run prepare-publish in case of v4.
            BotPublishHelper.prepare_publish_v4(code_dir, proj_file)
        else:
            raise CLIError('Not a valid azure publish directory. Please run prepare-publish.')

    zip_filepath = BotPublishHelper.create_upload_zip(code_dir, include_node_modules=False)
    kudu_client = KuduClient(cmd, resource_group_name, resource_name, bot)
    output = kudu_client.publish(zip_filepath)
    os.remove('upload.zip')

    # TODO: Examine improving logic for language of the bot.
    if os.path.exists(os.path.join('.', 'package.json')):
        kudu_client.install_node_dependencies()

    return output
