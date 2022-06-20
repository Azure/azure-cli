# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import shutil
from uuid import UUID

from azure.cli.core.azclierror import MutuallyExclusiveArgumentError
from azure.cli.command_modules.botservice.bot_json_formatter import BotJsonFormatter
from azure.cli.command_modules.botservice.bot_publish_prep import BotPublishPrep
from azure.cli.command_modules.botservice.constants import CSHARP, JAVASCRIPT, TYPESCRIPT
from azure.cli.command_modules.botservice.kudu_client import KuduClient
from azure.cli.command_modules.botservice.name_availability import NameAvailability
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


def __prepare_configuration_file(cmd, resource_group_name, kudu_client, folder_path):
    """For bots without a bot file."""
    # If no bot file exists, create the language specific configuration file from the bot's Application Settings
    app_settings = WebAppOperations.get_app_settings(
        cmd=cmd,
        resource_group_name=resource_group_name,
        name=kudu_client.bot_site_name
    )

    # Ignorable Application Settings, these are only used on Azure:
    ignorable_settings = ['BotEnv', 'WEBSITE_NODE_DEFAULT_VERSION', 'SCM_DO_BUILD_DURING_DEPLOYMENT']

    if os.path.exists(os.path.join(folder_path, 'package.json')):
        logger.info('Detected runtime as Node.js. Package.json present at %s. Creating .env file in that '
                    'folder.', folder_path)
        with open(os.path.join(folder_path, '.env'), 'w+') as f:
            for setting in app_settings:
                if setting['name'] not in ignorable_settings:
                    f.write('{0}={1}\n'.format(setting['name'], setting['value']))
            f.close()

    else:
        app_settings_path = os.path.join(folder_path, 'appsettings.json')

        logger.info('Detected language as CSharp. Loading app settings from %s.', app_settings_path)
        appsettings_content = {setting['name']: setting['value'] for setting in app_settings
                               if setting['name'] not in ignorable_settings}
        existing = None
        if not os.path.exists(app_settings_path):
            logger.info('App settings not found at %s, defaulting app settings to {}.', app_settings_path)
            existing = {}
        else:
            with open(app_settings_path, 'r') as f:
                existing = json.load(f)
        with open(os.path.join(app_settings_path), 'w+') as f:
            for key, value in appsettings_content.items():
                existing[key] = value
            f.write(json.dumps(existing))


def __handle_failed_name_check(name_response, cmd, client, resource_group_name, resource_name):
    # Creates should be idempotent, verify if the bot already exists inside of the provided Resource Group
    logger.debug('Failed name availability check for provided bot name "%s".\n'
                 'Checking if bot exists in Resource Group "%s".', resource_name, resource_group_name)
    try:
        # If the bot exists, return the bot's information to the user
        existing_bot = get_bot(cmd, client, resource_group_name, resource_name)
        logger.warning('Provided bot name already exists in Resource Group. Returning bot information:')
        return existing_bot
    except Exception as e:
        raise e


def create(cmd, client, resource_group_name, resource_name, msa_app_id, msa_app_type,
           msa_app_tenant_id=None, msa_app_msi_resource_id=None, description=None, display_name=None,
           endpoint=None, tags=None, location='global', sku_name='F0', cmek_key_vault_url=None):
    # Kind only support azure bot for now
    kind = "azurebot"

    # Check the resource name availability for the bot.
    name_response = NameAvailability.check_name_availability(client, resource_name, kind)
    if not name_response.valid:
        return __handle_failed_name_check(name_response, cmd, client, resource_group_name, resource_name)

    if resource_name.find(".") > -1:
        logger.warning('"." found in --name parameter ("%s"). "." is an invalid character for Azure Bot resource names '
                       'and will been removed.', resource_name)
        # Remove or replace invalid "." character
        resource_name = resource_name.replace(".", "")

    try:
        app_id_uuid = UUID(msa_app_id, version=4).hex
        if not msa_app_id.replace('-', '') == app_id_uuid:
            raise ValueError('Invalid MSA App ID detected.')
    except Exception as e:
        logger.debug(e)
        raise CLIError("--appid must be a valid GUID from a Microsoft Azure AD Application Registration. See "
                       "https://docs.microsoft.com/azure/active-directory/develop/quickstart-register-app for "
                       "more information on App Registrations. See 'az bot create --help' for more CLI information.")

    # If display name was not provided, just use the resource name
    display_name = display_name or resource_name

    logger.info('Creating Azure Bot Service.')

    # Registration bot specific validation
    if not endpoint:
        endpoint = ''

    is_cmek_enabled = False
    if cmek_key_vault_url is not None:
        is_cmek_enabled = True

    # Registration bots: simply call ARM and create the bot
    parameters = Bot(
        location=location,
        sku=Sku(name=sku_name),
        kind=kind,
        tags=tags,
        properties=BotProperties(
            display_name=display_name,
            description=description,
            endpoint=endpoint,
            msa_app_id=msa_app_id,
            msa_app_type=msa_app_type,
            msa_app_tenant_id=msa_app_tenant_id,
            msa_app_msi_resource_id=msa_app_msi_resource_id,
            is_cmek_enabled=is_cmek_enabled,
            cmek_key_vault_url=cmek_key_vault_url
        )
    )
    logger.info('Bot parameters client side validation successful.')
    logger.info('Creating bot.')

    return client.bots.create(
        resource_group_name=resource_group_name,
        resource_name=resource_name,
        parameters=parameters
    )


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


def download_app(cmd, client, resource_group_name, resource_name, file_save_path=None):  # pylint: disable=too-many-statements, too-many-locals, too-many-branches
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

            logger.info('Detected runtime as Node.js. Package.json present at %s. Creating .env file in that '
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

    else:
        __prepare_configuration_file(cmd, resource_group_name, kudu_client, folder_path)

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


def prepare_publish(cmd, client, resource_group_name, resource_name, sln_name, proj_file_path, code_dir=None,  # pylint:disable=too-many-statements
                    version='v3'):
    """Adds PostDeployScripts folder with necessary scripts to deploy v3 bot to Azure.

    This method is directly called via "bot prepare-publish"

    :param cmd:
    :param client:
    :param resource_group_name:
    :param resource_name:
    :param sln_name:
    :param proj_file_path:
    :param code_dir:
    :param version:
    :return:
    """

    # The prepare-publish process for v3 bots and v4 bots differ, so if the user specifies a v4 version, end the command
    # and inform user of az bot publish.
    if version == 'v4':
        raise CLIError('\'az bot prepare-publish\' is only for v3 bots. Please use \'az bot publish\' to prepare and '
                       'publish a v4 bot.')

    logger.warning('WARNING: `az bot prepare-publish` is in maintenance mode for v3 bots as support for creating v3 '
                   'SDK bots via `az bot create` will be discontinued on August 1st, 2019. We encourage developers '
                   'move to creating and deploying v4 bots.\n\nFor more information on creating and deploying v4 bots, '
                   'please visit https://aka.ms/create-and-deploy-v4-bot\n\nFor more information on v3 bot '
                   'creation deprecation, please visit this blog post: '
                   'https://blog.botframework.com/2019/06/07/v3-bot-broadcast-message/')

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
        except OSError as error:  # FileNotFoundError introduced in Python 3
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
                if fileName == proj_file_path:
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


def prepare_webapp_deploy(language, code_dir=None, proj_file_path=None):
    if not code_dir:
        code_dir = os.getcwd()
        logger.info('--code-dir not provided, defaulting to current working directory: %s\n'
                    'For more information, run "az bot prepare-deploy -h"', code_dir)
    elif not os.path.exists(code_dir):
        raise CLIError('Provided --code-dir value ({0}) does not exist'.format(code_dir))

    def does_file_exist(file_name):
        if os.path.exists(os.path.join(code_dir, file_name)):
            raise CLIError('%s found in %s\nPlease delete this %s before calling "az bot '   # pylint:disable=logging-not-lazy
                           'prepare-deploy"' % (file_name, code_dir, file_name))
    language = language.lower()

    if language in (JAVASCRIPT, TYPESCRIPT):
        if proj_file_path:
            raise CLIError('--proj-file-path should not be passed in if language is not Csharp')
        does_file_exist('web.config')
        module_source_dir = os.path.dirname(os.path.abspath(__file__))
        if not os.path.exists(os.path.join(code_dir, 'package.json')):
            logger.warning("WARNING: This command should normally be run in the same folder as the package.json for "
                           "Node.js bots. When using 'az webapp deployment source config-zip' the package.json and "
                           "web.config are usually in the same folder and at the root level of the .zip file. See 'az "
                           "bot prepare-deploy --help'.")
        if language == JAVASCRIPT:
            source_web_config = os.path.join(module_source_dir, 'web.config')
            shutil.copy(source_web_config, code_dir)
        else:
            source_web_config = os.path.join(module_source_dir, 'typescript.web.config')
            shutil.copy(source_web_config, code_dir)
            os.rename(os.path.join(code_dir, 'typescript.web.config'), os.path.join(code_dir, 'web.config'))
        logger.info('web.config for %s successfully created.', language)

    else:
        if not proj_file_path:
            raise CLIError('--proj-file-path must be provided if language is Csharp')
        does_file_exist('.deployment')
        csproj_file = os.path.join(code_dir, proj_file_path)
        if not os.path.exists(csproj_file):
            raise CLIError('{0} file not found\nPlease verify the relative path to the .csproj file from the '
                           '--code-dir'.format(csproj_file))

        with open(os.path.join(code_dir, '.deployment'), 'w') as f:
            f.write('[config]\n')
            proj_file = proj_file_path if proj_file_path.lower().endswith('.csproj') else proj_file_path + '.csproj'
            f.write('SCM_SCRIPT_GENERATOR_ARGS=--aspNetCore "{0}"\n'.format(proj_file))
        logger.info('.deployment file successfully created.')
    return True


def publish_app(cmd, client, resource_group_name, resource_name, code_dir=None, proj_file_path=None, version='v4',  # pylint:disable=too-many-statements
                keep_node_modules=None, timeout=None):
    if version == 'v4':
        logger.warning('DEPRECATION WARNING: `az bot publish` is deprecated for v4 bots. We recommend using `az webapp`'
                       ' to deploy your bot to Azure. For more information on how to deploy a v4 bot, see '
                       'https://aka.ms/deploy-your-bot.')
    else:
        logger.warning('WARNING: `az bot publish` is in maintenance mode for v3 bots as support for creating v3 '
                       'SDK bots via `az bot create` will be discontinued on August 1st, 2019. We encourage developers '
                       'move to creating and deploying v4 bots.\n\nFor more information on creating and deploying v4 '
                       'bots, please visit https://aka.ms/create-and-deploy-v4-bot\n\nFor more information on v3 bot '
                       'creation deprecation, please visit this blog post: '
                       'https://blog.botframework.com/2019/06/07/v3-bot-broadcast-message/')

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

    # If local IIS Node.js files exist, this means two things:
    # 1. We may not need to download the necessary web.config and iisnode.yml files to deploy a Node.js bot on IIS.
    # 2. We shouldn't delete their local web.config and issnode.yml files (if they exist).
    iis_publish_info = {
        'lang': CSHARP if not os.path.exists(os.path.join(code_dir, 'package.json')) else JAVASCRIPT,
        'has_web_config': bool(os.path.exists(os.path.join(code_dir, 'web.config'))),
        'has_iisnode_yml': bool(os.path.exists(os.path.join(code_dir, 'iisnode.yml')))
    }

    # Ensure that the directory contains appropriate post deploy scripts folder
    if 'PostDeployScripts' not in os.listdir(code_dir):
        if version == 'v4':

            logger.info('Detected SDK version v4. Running prepare publish in code directory %s and for project file %s'  # pylint:disable=logging-not-lazy
                        % (code_dir, proj_file_path))

            # Automatically run prepare-publish in case of v4.
            BotPublishPrep.prepare_publish_v4(logger, code_dir, proj_file_path, iis_publish_info)
        else:
            logger.info('Detected SDK version v3. PostDeploymentScripts folder not found in directory provided: %s',
                        code_dir)

            raise CLIError('Publish directory provided is uses Bot Builder SDK V3, and as a legacy bot needs to be '
                           'prepared for deployment. Please run prepare-publish. For more information, run \'az bot '
                           'prepare-publish -h\'.')

    zip_filepath = BotPublishPrep.create_upload_zip(logger, code_dir, include_node_modules=False)
    logger.info('Zip file path created, at %s.', zip_filepath)

    kudu_client = KuduClient(cmd, resource_group_name, resource_name, bot, logger)

    output = kudu_client.publish(zip_filepath, timeout, keep_node_modules, iis_publish_info['lang'])

    logger.info('Bot source published. Preparing bot application to run the new source.')
    os.remove('upload.zip')
    # If the bot is a Node.js bot and did not initially have web.config, delete web.config and iisnode.yml.
    if iis_publish_info['lang'] == JAVASCRIPT:
        if not iis_publish_info['has_web_config'] and os.path.exists(os.path.join(code_dir, 'web.config')):
            os.remove(os.path.join(code_dir, 'web.config'))
        if not iis_publish_info['has_iisnode_yml'] and os.path.exists(os.path.join(code_dir, 'iisnode.yml')):
            os.remove(os.path.join(code_dir, 'iisnode.yml'))

        if not iis_publish_info['has_iisnode_yml'] and not iis_publish_info['has_web_config']:
            logger.info("web.config and iisnode.yml for Node.js bot were fetched from Azure for deployment using IIS. "
                        "These files have now been removed from %s."
                        "To see the two files used for your deployment, either visit your bot's Kudu site or download "
                        "the files from https://icscratch.blob.core.windows.net/bot-packages/node_v4_publish.zip",
                        code_dir)
        elif not iis_publish_info['has_iisnode_yml']:
            logger.info("iisnode.yml for Node.js bot was fetched from Azure for deployment using IIS. To see this file "
                        "that was used for your deployment, either visit your bot's Kudu site or download the file "
                        "from https://icscratch.blob.core.windows.net/bot-packages/node_v4_publish.zip")
        elif not iis_publish_info['has_web_config']:
            logger.info("web.config for Node.js bot was fetched from Azure for deployment using IIS. To see this file "
                        "that was used for your deployment, either visit your bot's Kudu site or download the file "
                        "from https://icscratch.blob.core.windows.net/bot-packages/node_v4_publish.zip")

    if os.path.exists(os.path.join('.', 'package.json')) and not keep_node_modules:
        logger.info('Detected language javascript. Installing node dependencies in remote bot.')
        kudu_client.install_node_dependencies()

    if output.get('active'):
        logger.info('Deployment successful!')

    if not output.get('active'):
        scm_url = output.get('url')
        deployment_id = output.get('id')
        # Instead of replacing "latest", which would could be in the bot name, we replace "deployments/latest"
        deployment_url = scm_url.replace('deployments/latest', 'deployments/%s' % deployment_id)
        logger.error('Deployment failed. To find out more information about this deployment, please visit %s.',
                     deployment_url)
    return output


def update(client, resource_group_name, resource_name, endpoint=None, description=None,
           display_name=None, tags=None, sku_name=None, app_insights_key=None,
           app_insights_api_key=None, app_insights_app_id=None, icon_url=None,
           encryption_off=None, cmek_key_vault_url=None):
    bot = client.bots.get(
        resource_group_name=resource_group_name,
        resource_name=resource_name
    )
    sku = Sku(name=sku_name if sku_name else bot.sku.name)
    bot_props = bot.properties

    bot_props.description = description if description else bot_props.description
    bot_props.display_name = display_name if display_name else bot_props.display_name
    bot_props.endpoint = endpoint if endpoint else bot_props.endpoint
    bot_props.icon_url = icon_url if icon_url else bot_props.icon_url

    bot_props.developer_app_insight_key = app_insights_key if app_insights_key else bot_props.developer_app_insight_key
    bot_props.developer_app_insights_application_id = app_insights_app_id if app_insights_app_id \
        else bot_props.developer_app_insights_application_id

    if app_insights_api_key:
        bot_props.developer_app_insights_api_key = app_insights_api_key

    if cmek_key_vault_url is not None and encryption_off is not None:
        error_msg = "Both --encryption-off and a --cmk-key-vault-key-url (encryption ON) were passed. " \
                    "Please use only one: --cmk-key-vault-key-url or --encryption_off"
        raise MutuallyExclusiveArgumentError(error_msg)

    if cmek_key_vault_url is not None:
        bot_props.cmek_key_vault_url = cmek_key_vault_url
        bot_props.is_cmek_enabled = True

    if encryption_off is not None:
        bot_props.is_cmek_enabled = False

    return client.bots.update(resource_group_name,
                              resource_name,
                              tags=tags,
                              sku=sku,
                              properties=bot_props)
