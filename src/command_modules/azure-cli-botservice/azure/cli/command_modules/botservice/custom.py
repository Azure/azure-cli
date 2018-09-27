# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import shutil
import adal  # pylint: disable=import-error
from knack.prompting import prompt_y_n  # pylint: disable=unused-import
from knack.util import CLIError
from knack.log import get_logger
from azure.cli.core._profile import Profile
from azure.cli.command_modules.botservice._webutils import (
    deploy_arm_template,
    enable_zip_deploy,
    get_app_settings,
    _get_site_credential,
    _get_scm_url)
from azure.mgmt.botservice.models import Bot, BotProperties, Sku

logger = get_logger(__name__)


def get_bot_site_name(endpoint):
    try:
        from urllib.parse import urlsplit
    except ImportError:
        from urlparse import urlsplit  # pylint: disable=import-error
    split_parts = urlsplit(endpoint)
    return str(split_parts.netloc.split('.', 1)[0])


def provisionConvergedApp(bot_name):
    botfirstpartyid = 'f3723d34-6ff5-4ceb-a148-d99dcd2511fc'
    aadclientid = '1950a258-227b-4e31-a9cf-717495945fc2'
    tenantid = '72f988bf-86f1-41af-91ab-2d7cd011db47'

    authority = 'https://login.windows.net/{0}'.format(tenantid)
    context = adal.AuthenticationContext(
        authority=authority,
        validate_authority=True,
        api_version=None
    )

    code = context.acquire_user_code(
        resource=botfirstpartyid,
        client_id=aadclientid,
    )

    logger.warning(code['message'])

    token = context.acquire_token_with_device_code(
        resource=botfirstpartyid,
        user_code_info=code,
        client_id=aadclientid
    )
    access_token = token['accessToken']

    import requests
    headers = {'Authorization': 'Bearer {0}'.format(access_token)}
    response = requests.post(
        'https://dev.botframework.com/api/botApp/provisionConvergedApp?name={0}'.format(bot_name),
        headers=headers
    )
    if response.status_code not in [201]:
        raise CLIError('Unable to provision MSA id automatically. Please pass them in as parameters and try again.')
    response_content = json.loads(response.content.decode('utf-8'))
    msa_app_id = response_content['AppId']
    password = response_content['Password']

    return msa_app_id, password


def create(cmd, client, resource_group_name, resource_name, kind, description=None, display_name=None,
           endpoint=None, msa_app_id=None, password=None, tags=None, storageAccountName=None,
           location='Central US', sku_name='F0', appInsightsLocation='South Central US',
           language='Csharp', version='v3'):
    display_name = display_name or resource_name
    kind = kind.lower()

    if not msa_app_id:
        msa_app_id, password = provisionConvergedApp(resource_name)
        logger.warning('obtained msa app id and password. Provisioning bot now.')

    if kind == 'registration':
        kind = 'bot'
        if not endpoint or not msa_app_id:
            raise CLIError('Endpoint and msa app id are required for creating a registration bot')
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
    if kind in ('webapp', 'function'):
        return create_app(cmd, client, resource_group_name, resource_name, description, kind, msa_app_id, password,
                          storageAccountName, location, sku_name, appInsightsLocation, language, version)
    else:
        raise CLIError('Invalid Bot Parameter : Kind')


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
        'subscriptionId': client.config.subscription_id
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
    from azure.mgmt.botservice.models import ConnectionSetting, ConnectionSettingProperties, ConnectionSettingParameter
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


def create_app(cmd, client, resource_group_name, resource_name, description, kind, appid, password, storageAccountName,
               location, sku_name, appInsightsLocation, language, version):
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
            template_name = 'webapp.template.json'
            if language == 'Csharp':
                zip_url = 'https://connectorprod.blob.core.windows.net/bot-packages/csharp-abs-webapp-v4_echobot-aspnetcore_precompiled.zip'  # pylint: disable=line-too-long
            else:
                zip_url = 'https://connectorprod.blob.core.windows.net/bot-packages/node.js-abs-webapp-v4_hello-chatconnector.zip'  # pylint: disable=line-too-long

    create_new_storage = False
    if not storageAccountName:
        import re
        import string
        import random
        create_new_storage = True
        storageAccountName = re.sub(r'[^a-z0-9]', '', resource_name[:10] +
                                    ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(4)))
        site_name = re.sub(r'[^a-z0-9]', '', resource_name[:15] +
                           ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(4)))

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
    params = {k: {'value': v} for k, v in paramsdict.items()}

    dir_path = os.path.dirname(os.path.realpath(__file__))
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


def create_upload_zip(code_dir):
    import zipfile
    file_excludes = ['upload.zip', 'db.lock']
    folder_excludes = ['node_modules', 'packages', 'bin', 'obj']
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


def publish_app(cmd, client, resource_group_name, resource_name, code_dir=None):
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
        raise CLIError('Not a valid azure publish directory. missing post deploy scripts')

    zip_filepath = create_upload_zip(code_dir)
    site_name = get_bot_site_name(raw_bot_properties.properties.endpoint)
    # first try to put the zip in clirepo
    user_name, password = _get_site_credential(cmd.cli_ctx, resource_group_name, site_name, None)
    scm_url = _get_scm_url(cmd, resource_group_name, site_name, None)

    import urllib3
    authorization = urllib3.util.make_headers(basic_auth='{0}:{1}'.format(user_name, password))
    headers = authorization

    import requests
    payload = {
        'command': 'rm -rf clirepo',
        'dir': r'site'
    }
    headers['content-type'] = 'application/json'
    response = requests.post(scm_url + '/api/command', data=json.dumps(payload), headers=headers)
    check_response_status(response)
    response = requests.put(scm_url + '/api/vfs/site/clirepo/', headers=headers)
    check_response_status(response, 201)
    headers['content-type'] = 'application/octet-stream'
    with open(zip_filepath, 'rb') as fs:
        zip_content = fs.read()
        response = requests.put(scm_url + '/api/zip/site/clirepo', headers=headers, data=zip_content)

    output = enable_zip_deploy(cmd, resource_group_name, site_name, 'upload.zip')
    os.remove('upload.zip')
    return output


def download_app(cmd, client, resource_group_name, resource_name, file_save_path=None):
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
        raise CLIError('The path {0} already exists. Please delete it or specify an alternate path'.format(folder_path))
    os.mkdir(folder_path)

    site_name = get_bot_site_name(raw_bot_properties.properties.endpoint)

    user_name, password = _get_site_credential(cmd.cli_ctx, resource_group_name, site_name, None)
    scm_url = _get_scm_url(cmd, resource_group_name, site_name, None)

    import urllib3
    authorization = urllib3.util.make_headers(basic_auth='{0}:{1}'.format(user_name, password))
    headers = authorization
    headers['content-type'] = 'application/json'

    # if repository folder exists, then get those contents for download
    import requests
    response = requests.get(scm_url + '/api/zip/site/clirepo/', headers=authorization, )
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
    import zipfile
    zip_ref = zipfile.ZipFile(download_path)
    zip_ref.extractall(folder_path)
    zip_ref.close()
    os.remove(download_path)
    if not (os.path.exists(os.path.join(folder_path, 'PostDeployScripts', 'deploy.cmd.template')) and
            os.path.exists(os.path.join(folder_path, 'deploy.cmd'))):
        shutil.copyfile(os.path.join(folder_path, 'deploy.cmd'),
                        os.path.join(folder_path, 'PostDeployScripts', 'deploy.cmd.template'))
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
