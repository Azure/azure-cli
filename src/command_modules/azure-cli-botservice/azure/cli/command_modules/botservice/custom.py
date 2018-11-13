# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import requests
import re
import shutil
import string
# TODO: Evalulate the use of requests and urllib3, where urllib3 is a dependency of requests
import urllib3
import random
import zipfile

from .auth.converged_app import ConvergedApp

from knack.util import CLIError
from knack.log import get_logger
from azure.cli.core._profile import Profile
from azure.cli.command_modules.botservice._webutils import (
    deploy_arm_template,
    enable_zip_deploy,
    get_app_settings,
    _get_site_credential,
    _get_scm_url)
from azure.mgmt.botservice.models import (
    Bot,
    BotProperties,
    ConnectionSetting,
    ConnectionSettingProperties,
    ConnectionSettingParameter,
    Sku)

try:
    # Try importing Python 3 urllib.parse
    from urllib.parse import urlsplit
except ImportError:
    # If urllib.parse was not imported, use Python 2 module urlparse
    from urlparse import urlsplit  # pylint: disable=import-error

logger = get_logger(__name__)


def get_bot_site_name(endpoint):
    split_parts = urlsplit(endpoint)
    return str(split_parts.netloc.split('.', 1)[0])


def _get_app_insights_location(key):
    region_map = {
        'australiaeast': 'southeastasia',
        'australiacentral': 'southeastasia',
        'australiacentral2': 'southeastasia',
        'australiasoutheast': 'southeastasia',
        'eastasia': 'southeastasia',
        'southeastasia': 'westus',
        'eastus': 'eastus',
        'eastus2': 'eastus',
        'southcentralus': 'southcentralus',
        'westcentralus': 'westus2',
        'westus': 'westus2',
        'westus2': 'westus2',
        'brazilsouth': 'southcentralus',
        'centralus': 'southcentralus',
        'northcentralus': 'southcentralus',
        'japanwest': 'southeastasia',
        'japaneast': 'southeastasia',
        'southindia': 'southeastasia',
        'centralindia': 'southeastasia',
        'westindia': 'southeastasia',
        'canadacentral': 'southcentralus',
        'canadaeast': 'eastus',
        'koreacentral': 'southeastasia',
        'koreasouth': 'southeastasia',
        'northeurope': 'northeurope',
        'westeurope': 'westeurope',
        'uksouth': 'westeurope',
        'ukwest': 'westeurope',
        'francecentral': 'westeurope',
        'francesouth': 'westeurope'
    }
    return region_map[key]


def create(cmd, client, resource_group_name, resource_name, kind, description=None, display_name=None,
           endpoint=None, msa_app_id=None, password=None, tags=None, storageAccountName=None,
           location='Central US', sku_name='F0', appInsightsLocation='South Central US',
           language='Csharp', version='v3'):

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
        msa_app_id, password = ConvergedApp.provision(resource_name)
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
        return create_app(cmd, client, resource_group_name, resource_name, description, kind, msa_app_id, password,
                          storageAccountName, location, sku_name, appInsightsLocation, language, version)


def create_app(cmd, client, resource_group_name, resource_name, description, kind, appid, password, storageAccountName,
               location, sku_name, appInsightsLocation, language, version):

    # Based on sdk version, language and kind, select the appropriate zip url containing starter bot source
    if version == 'v3':
        if kind == 'function':
            template_name = 'functionapp.template.json'
            if language == 'Csharp':
                zip_url = 'https://connectorprod.blob.core.windows.net/bot-packages/csharp-abs-functions_emptybot.zip'
            else:
                zip_url = 'https://connectorprod.blob.core.windows.net/bot-packages/node.js-abs-functions_emptybot_funcpack.zip'  # pylint: disable=line-too-long

        else:
            kind = 'sdk'
            template_name = 'webapp.template.json'
            if language == 'Csharp':
                zip_url = 'https://connectorprod.blob.core.windows.net/bot-packages/csharp-abs-webapp_simpleechobot_precompiled.zip'  # pylint: disable=line-too-long
            else:
                zip_url = 'https://connectorprod.blob.core.windows.net/bot-packages/node.js-abs-webapp_hello-chatconnector.zip'  # pylint: disable=line-too-long
    elif version == 'v4':
        if kind == 'function':
            raise CLIError('Function bot creation is not supported for v4 bot sdk.')

        else:
            kind = 'sdk'
            template_name = 'webappv4.template.json'
            if language == 'Csharp':
                zip_url = 'https://connectorprod.blob.core.windows.net/bot-packages/csharp-abs-webapp-v4_echobot_precompiled.zip'  # pylint: disable=line-too-long
            else:
                zip_url = 'https://connectorprod.blob.core.windows.net/bot-packages/node.js-abs-webapp-v4_echobot.zip'  # pylint: disable=line-too-long

    # Storage prep
    create_new_storage = False
    if not storageAccountName:
        create_new_storage = True
        storageAccountName = re.sub(r'[^a-z0-9]', '', resource_name[:10] +
                                    ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(4)))
        site_name = re.sub(r'[^a-z0-9]', '', resource_name[:15] +
                           ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(4)))

    # Application insights prep
    appInsightsLocation = _get_app_insights_location(location.lower().replace(' ', ''))

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
    if template_name == 'webappv4.template.json':
        bot_encryption_key = get_bot_file_encryption_key()
        paramsdict['botFileEncryptionKey'] = bot_encryption_key
    params = {k: {'value': v} for k, v in paramsdict.items()}

    # TODO concate 'templates' to file path
    dir_path = os.path.dirname(os.path.realpath(__file__))

    # Deploy ARM template
    deploy_result = deploy_arm_template(
        cli_ctx=cmd.cli_ctx,
        resource_group_name=resource_group_name,
        template_file=os.path.join(dir_path, template_name),
        parameters=[[json.dumps(params)]],
        deployment_name=resource_name,
        mode='Incremental'
    )

    deploy_result.wait()
    return create_bot_json(cmd, client, resource_group_name, resource_name, app_password=password)


def get_bot_file_encryption_key():
    """

    :return:
    """
    
    # Pulled out of create_app, which is the only place that performs this call
    # TODO: Move to class for dev.botframework.com calls?
    response = requests.get('https://dev.botframework.com/api/misc/botFileEncryptionKey')

    # TODO: Tear this out? This method should probably fail gracefully, is a secret needed when the bot is provisioned?
    # Can't a user create a new secret and then re-encrypt the bot file?
    if response.status_code not in [200]:
        raise CLIError('Unable to provision a bot file encryption key. Please try again.')
    return response.text[1:-1]


def update(client, parameters, resource_group_name):
    try:
        return client.update(
            resource_group_name=resource_group_name,
            resource_name=parameters.name,
            **(parameters.__dict__)
        )
    except AttributeError:
        return None


def create_bot_json(cmd, client, resource_group_name, resource_name, app_password=None, raw_bot_properties=None):
    if not raw_bot_properties:
        raw_bot_properties = client.bots.get(
            resource_group_name=resource_group_name,
            resource_name=resource_name
        )
    if not app_password:
        site_name = get_bot_site_name(raw_bot_properties.properties.endpoint)
        app_settings = get_app_settings(
            cmd=cmd,
            resource_group_name=resource_group_name,
            name=site_name
        )
        app_password = [item['value'] for item in app_settings if item['name'] == 'MicrosoftAppPassword'][0]

    profile = Profile(cli_ctx=cmd.cli_ctx)
    return {
        'type': 'abs',
        'id': raw_bot_properties.name,
        'name': raw_bot_properties.properties.display_name,
        'appId': raw_bot_properties.properties.msa_app_id,
        'appPassword': app_password,
        'endpoint': raw_bot_properties.properties.endpoint,
        'resourceGroup': str(resource_group_name),
        'tenantId': profile.get_subscription(subscription=client.config.subscription_id)['tenantId'],
        'subscriptionId': client.config.subscription_id,
        'serviceName': resource_name
    }


def get_bot(cmd, client, resource_group_name, resource_name, bot_json=None):
    raw_bot_properties = client.bots.get(
        resource_group_name=resource_group_name,
        resource_name=resource_name
    )
    if bot_json:
        return create_bot_json(cmd, client, resource_group_name, resource_name, raw_bot_properties=raw_bot_properties)

    return raw_bot_properties


def create_connection(client, resource_group_name, resource_name, connection_name, client_id,
                      client_secret, scopes, service_provider_name, parameters=None):
    service_provider = get_service_providers(client, name=service_provider_name)
    if not service_provider:
        raise CLIError('Invalid Service Provider Name passed. Use listprovider command to see all available providers')
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


def get_service_providers(client, name=None):
    service_provider_response = client.bot_connection.list_service_providers()
    name = name and name.lower()
    if name:
        try:
            return next((item for item in service_provider_response.value if item.properties.service_provider_name.lower() == name.lower()))  # pylint: disable=line-too-long
        except StopIteration:
            raise CLIError('A service provider with the name {0} was not found'.format(name))
    return service_provider_response


def create_upload_zip(code_dir, include_node_modules=True):
    file_excludes = ['upload.zip', 'db.lock', '.env']
    folder_excludes = ['packages', 'bin', 'obj']
    if not include_node_modules:
        folder_excludes.append('node_modules')
    zip_filepath = os.path.abspath('upload.zip')
    save_cwd = os.getcwd()
    os.chdir(code_dir)
    try:
        with zipfile.ZipFile(zip_filepath, 'w',
                             compression=zipfile.ZIP_DEFLATED) as zf:
            path = os.path.normpath(os.curdir)
            for dirpath, dirnames, filenames in os.walk(os.curdir, topdown=True):
                for item in folder_excludes:
                    if item in dirnames:
                        dirnames.remove(item)
                for name in sorted(dirnames):
                    path = os.path.normpath(os.path.join(dirpath, name))
                    zf.write(path, path)
                for name in filenames:
                    if name in file_excludes:
                        continue
                    path = os.path.normpath(os.path.join(dirpath, name))
                    if os.path.isfile(path):
                        zf.write(path, path)
    finally:
        os.chdir(save_cwd)
    return zip_filepath


def check_response_status(response, expected_code=None):
    expected_code = expected_code or 200
    if response.status_code != expected_code:
        raise CLIError('Failed with status code {} and reason {}'.format(
            response.status_code, response.text))


def find_proj(proj_file):
    for root, _, files in os.walk(os.curdir):
        for file_name in files:
            if proj_file == file_name.lower():
                return os.path.relpath(os.path.join(root, file_name))
    raise CLIError('project file not found. Please pass a valid --proj-file.')


def _prepare_publish_v4(code_dir, proj_file):
    save_cwd = os.getcwd()
    os.chdir(code_dir)
    try:
        if not os.path.exists(os.path.join('.', 'package.json')):
            if proj_file is None:
                raise CLIError('expected --proj-file parameter for csharp v4 project.')
            with open('.deployment', 'w') as f:
                f.write('[config]\n')
                proj_file = proj_file.lower()
                proj_file = proj_file if proj_file.endswith('.csproj') else proj_file + '.csproj'
                f.write('SCM_SCRIPT_GENERATOR_ARGS=--aspNetCore {0}\n'.format(find_proj(proj_file)))

        else:
            # put iisnode.yml and web.config
            response = requests.get('https://icscratch.blob.core.windows.net/bot-packages/node_v4_publish.zip')
            with open('temp.zip', 'wb') as f:
                f.write(response.content)

            zip_ref = zipfile.ZipFile('temp.zip')
            zip_ref.extractall()
            zip_ref.close()
            os.remove('temp.zip')
    finally:
        os.chdir(save_cwd)


def _prepare_publish_v4(code_dir, proj_file):
    save_cwd = os.getcwd()
    os.chdir(code_dir)
    try:
        if not os.path.exists(os.path.join('.', 'package.json')):
            if proj_file is None:
                raise CLIError('expected --proj-file parameter for csharp v4 project.')
            with open('.deployment', 'w') as f:
                f.write('[config]\n')
                proj_file = proj_file.lower()
                proj_file = proj_file if proj_file.endswith('.csproj') else proj_file + '.csproj'
                f.write('SCM_SCRIPT_GENERATOR_ARGS=--aspNetCore {0}\n'.format(find_proj(proj_file)))

        else:
            # put iisnode.yml and web.config
            response = requests.get('https://icscratch.blob.core.windows.net/bot-packages/node_v4_publish.zip')
            with open('temp.zip', 'wb') as f:
                f.write(response.content)
            zip_ref = zipfile.ZipFile('temp.zip')
            zip_ref.extractall()
            zip_ref.close()
            os.remove('temp.zip')
    finally:
        os.chdir(save_cwd)


def publish_app(cmd, client, resource_group_name, resource_name, code_dir=None, proj_file=None, sdk_version='v3'):
    # get the bot and ensure it's not a registration only bot
    raw_bot_properties = client.bots.get(
        resource_group_name=resource_group_name,
        resource_name=resource_name
    )
    if raw_bot_properties.kind == 'bot':
        raise CLIError('Source publish is not supported for registration only bots')

    if not code_dir:
        code_dir = os.getcwd()

    if not os.path.isdir(code_dir):
        raise CLIError('Please supply a valid directory path containing your source code')
    # ensure that the directory contains appropriate post deploy scripts folder
    if 'PostDeployScripts' not in os.listdir(code_dir):
        if sdk_version == 'v4':
            # automatically run prepare-publish in case of v4.
            _prepare_publish_v4(code_dir, proj_file)
        else:
            raise CLIError('Not a valid azure publish directory. Please run prepare-publish.')

    zip_filepath = create_upload_zip(code_dir, include_node_modules=False)
    site_name = get_bot_site_name(raw_bot_properties.properties.endpoint)
    # first try to put the zip in clirepo
    user_name, password = _get_site_credential(cmd.cli_ctx, resource_group_name, site_name, None)
    scm_url = _get_scm_url(cmd, resource_group_name, site_name, None)

    authorization = urllib3.util.make_headers(basic_auth='{0}:{1}'.format(user_name, password))
    headers = authorization

    payload = {
        'command': 'rm -rf clirepo',
        'dir': r'site'
    }
    headers['content-type'] = 'application/json'
    response = requests.post(scm_url + '/api/command', data=json.dumps(payload), headers=headers)
    response = requests.put(scm_url + '/api/vfs/site/clirepo/', headers=headers)
    check_response_status(response, 201)
    headers['content-type'] = 'application/octet-stream'
    with open(zip_filepath, 'rb') as fs:
        zip_content = fs.read()
        response = requests.put(scm_url + '/api/zip/site/clirepo', headers=headers, data=zip_content)

    output = enable_zip_deploy(cmd, resource_group_name, site_name, 'upload.zip')
    os.remove('upload.zip')
    if os.path.exists(os.path.join('.', 'package.json')):
        payload = {
            'command': 'npm install',
            'dir': r'site\wwwroot'
        }
        response = requests.post(scm_url + '/api/command', data=json.dumps(payload), headers=headers)

    return output


def download_app(cmd, client, resource_group_name, resource_name, file_save_path=None):  # pylint: disable=too-many-statements, too-many-locals
    # get the bot and ensure it's not a registration only bot
    raw_bot_properties = client.bots.get(
        resource_group_name=resource_group_name,
        resource_name=resource_name
    )
    if raw_bot_properties.kind == 'bot':
        raise CLIError('Source download is not supported for registration only bots')

    file_save_path = file_save_path or os.getcwd()
    if not os.path.isdir(file_save_path):
        raise CLIError('Path name not valid')
    folder_path = os.path.join(file_save_path, resource_name)
    if os.path.exists(folder_path):
        raise CLIError('The path {0} already exists. Please delete this folder or specify an alternate path'.format(folder_path))  # pylint: disable=line-too-long
    os.mkdir(folder_path)

    site_name = get_bot_site_name(raw_bot_properties.properties.endpoint)

    user_name, password = _get_site_credential(cmd.cli_ctx, resource_group_name, site_name, None)
    scm_url = _get_scm_url(cmd, resource_group_name, site_name, None)

    authorization = urllib3.util.make_headers(basic_auth='{0}:{1}'.format(user_name, password))
    headers = authorization
    headers['content-type'] = 'application/json'

    # if repository folder exists, then get those contents for download
    response = requests.get(scm_url + '/api/zip/site/clirepo/', headers=authorization)
    if response.status_code != 200:
        # try getting the bot from wwwroot instead
        payload = {
            'command': 'PostDeployScripts\\prepareSrc.cmd {0}'.format(password),
            'dir': r'site\wwwroot'
        }
        response = requests.post(scm_url + '/api/command', data=json.dumps(payload), headers=headers)
        check_response_status(response)
        response = requests.get(scm_url + '/api/vfs/site/bot-src.zip', headers=authorization)
        check_response_status(response)

    download_path = os.path.join(file_save_path, 'download.zip')
    with open(os.path.join(file_save_path, 'download.zip'), 'wb') as f:
        f.write(response.content)
    zip_ref = zipfile.ZipFile(download_path)
    zip_ref.extractall(folder_path)
    zip_ref.close()
    os.remove(download_path)
    if (os.path.exists(os.path.join(folder_path, 'PostDeployScripts', 'deploy.cmd.template')) and
            os.path.exists(os.path.join(folder_path, 'deploy.cmd'))):
        shutil.copyfile(os.path.join(folder_path, 'deploy.cmd'),
                        os.path.join(folder_path, 'PostDeployScripts', 'deploy.cmd.template'))
    # if the bot contains a bot
    bot_file_path = os.path.join(folder_path, '{0}.bot'.format(resource_name))
    if os.path.exists(bot_file_path):
        app_settings = get_app_settings(
            cmd=cmd,
            resource_group_name=resource_group_name,
            name=site_name
        )
        bot_secret = [item['value'] for item in app_settings if item['name'] == 'botFileSecret']
        # write a .env file #todo: write an appsettings.json file
        bot_env = {
            'botFileSecret': bot_secret[0],
            'botFilePath': '{0}.bot'.format(resource_name),
            'NODE_ENV': 'development'
        }
        if os.path.exists(os.path.join(folder_path, 'package.json')):
            with open(os.path.join(folder_path, '.env'), 'w') as f:
                for key, value in bot_env.items():
                    f.write('{0}={1}\n'.format(key, value))
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

        if not bot_secret:
            bot_env['downloadPath'] = folder_path
            return bot_env

    return {'downloadPath': folder_path}


def prepare_publish(cmd, client, resource_group_name, resource_name, sln_name, proj_name, code_dir=None):
    raw_bot_properties = client.bots.get(
        resource_group_name=resource_group_name,
        resource_name=resource_name
    )
    if raw_bot_properties.kind == 'bot':
        raise CLIError('Prepare Publish is not supported for registration only bots')
    code_dir = code_dir or os.getcwd()
    if not os.path.isdir(code_dir):
        raise CLIError('Please supply a valid directory path containing your source code')

    os.chdir(code_dir)
    # ensure that the directory does not contain appropriate post deploy scripts folder
    if 'PostDeployScripts' in os.listdir(code_dir):
        raise CLIError('Post deploy azure scripts are already in Place.')
    download_path = download_app(cmd, client, resource_group_name, resource_name)

    shutil.copytree(os.path.join(download_path['downloadPath'], 'PostDeployScripts'), 'PostDeployScripts')

    if os.path.exists(os.path.join('PostDeployScripts', 'publish.js.template')):
        shutil.copy(os.path.join(download_path['downloadPath'], 'iisnode.yml'), 'iisnode.yml')
        shutil.copy(os.path.join(download_path['downloadPath'], 'publish.js'), 'publish.js')
        shutil.copy(os.path.join(download_path['downloadPath'], 'web.config'), 'web.config')
    else:
        solution_path = None
        csproj_path = None
        old_namev4 = 'AspNetCore-EchoBot-With-State'
        old_namev3 = 'Microsoft.Bot.Sample.SimpleEchoBot'
        shutil.copy(os.path.join(download_path['downloadPath'], 'build.cmd'), 'build.cmd')
        shutil.copy(os.path.join(download_path['downloadPath'], '.deployment'), '.deployment')
        shutil.copyfile(os.path.join(download_path['downloadPath'], 'PostDeployScripts', 'deploy.cmd.template'),
                        'deploy.cmd')
        # find solution and project name
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

        with open('deploy.cmd') as f:
            content = f.read()

        with open('deploy.cmd', 'w') as f:
            content = content.replace(old_namev3 + '.sln', solution_path)
            content = content.replace(old_namev3 + '.csproj', csproj_path)
            content = content.replace(old_namev4 + '.sln', solution_path)
            content = content.replace(old_namev4 + '.csproj', csproj_path)
            f.write(content)

    shutil.rmtree(download_path['downloadPath'])
