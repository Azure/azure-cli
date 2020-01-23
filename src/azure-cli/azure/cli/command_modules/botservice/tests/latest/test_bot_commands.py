# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import filecmp
import os
import json
import shutil
import uuid
import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock
import requests
from azure.cli.command_modules.botservice.custom import prepare_webapp_deploy
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, LiveScenarioTest
from azure.mgmt.botservice.models import ErrorException
from knack.util import CLIError


class DirectLineClient(object):
    """Shared methods for the parsed result objects."""

    def __init__(self, direct_line_secret):
        self._direct_line_secret = direct_line_secret
        self._base_url = 'https://directline.botframework.com/v3/directline'
        self.__set_headers()
        self.__start_conversation()
        self._watermark = ''

    def send_message(self, text, retry_count=3):
        """Send raw text to bot framework using direct line api"""
        url = '/'.join([self._base_url, 'conversations', self._conversationid, 'activities'])
        json_payload = {
            'conversationId': self._conversationid,
            'type': 'message',
            'from': {'id': 'user1'},
            'text': text
        }

        success = False
        current_retry = 0
        while not success and current_retry < retry_count:
            bot_response = requests.post(url, headers=self._headers, json=json_payload)
            current_retry += 1
            if bot_response.status_code == 200:
                success = True

        return bot_response

    def get_message(self, retry_count=3):
        """Get a response message back from the bot framework using direct line api"""
        url = '/'.join([self._base_url, 'conversations', self._conversationid, 'activities'])
        url = url + '?watermark=' + self._watermark

        success = False
        current_retry = 0
        while not success and current_retry < retry_count:
            bot_response = requests.get(url, headers=self._headers,
                                        json={'conversationId': self._conversationid})
            current_retry += 1
            if bot_response.status_code == 200:
                success = True
                json_response = bot_response.json()

                if 'watermark' in json_response:
                    self._watermark = json_response['watermark']

                if 'activities' in json_response:
                    activities_count = len(json_response['activities'])
                    if activities_count > 0:
                        return bot_response, json_response['activities'][activities_count - 1]['text']
                    else:
                        return bot_response, "No new messages"
        return bot_response, "error contacting bot for response"

    def __set_headers(self, resource_group):
        headers = {'Content-Type': 'application/json'}
        value = ' '.join(['Bearer', self._direct_line_secret])
        headers.update({'Authorization': value})
        self._headers = headers

    def __start_conversation(self, resource_group):

        # Start conversation and get us a conversationId to use
        url = '/'.join([self._base_url, 'conversations'])
        botresponse = requests.post(url, headers=self._headers)

        # Extract the conversationID for sending messages to bot
        jsonresponse = botresponse.json()
        self._conversationid = jsonresponse['conversationId']


class BotTests(ScenarioTest):

    @ResourceGroupPreparer(random_name_length=20)
    def test_botservice_registration_bot_create(self, resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=10),
            'description': 'description1',
            'endpoint': 'https://www.google.com/api/messages',
            'app_id': str(uuid.uuid4()),
            'password': str(uuid.uuid4())
        })

        self.cmd(
            'az bot create -k registration -g {rg} -n {botname} -d {description} -e {endpoint} --appid {app_id} -p '
            '{password} --tags key1=value1',
            checks=[
                self.check('name', '{botname}'),
                self.check('properties.description', '{description}'),
                self.check('resourceGroup', '{rg}'),
                self.check('location', 'global'),
                self.check('tags.key1', 'value1')
            ])

        self.cmd('az bot show -g {rg} -n {botname}', checks=[
            self.check('name', '{botname}')
        ])

        self.cmd('az bot update --description description2 -g {rg} -n {botname}', checks=[
            self.check('name', '{botname}'),
            self.check('properties.description', 'description2')
        ])

        self.cmd('az bot delete -g {rg} -n {botname}')

    @ResourceGroupPreparer(random_name_length=20)
    def test_botservice_create_should_be_idempotent_and_return_existing_bot_info(self, resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=10),
            'description': 'description1',
            'endpoint': 'https://www.google.com/api/messages',
            'app_id': str(uuid.uuid4()),
            'password': str(uuid.uuid4())
        })

        self.cmd(
            'az bot create -k registration -g {rg} -n {botname} -d {description} -e {endpoint} --appid {app_id} -p '
            '{password} --tags key1=value1',
            checks=[
                self.check('name', '{botname}'),
                self.check('properties.description', '{description}'),
                self.check('resourceGroup', '{rg}'),
                self.check('location', 'global'),
                self.check('tags.key1', 'value1')
            ])

        self.cmd(
            'az bot create -k registration -g {rg} -n {botname} -d {description} -e {endpoint} --appid {app_id} -p '
            '{password} --tags key1=value1',
            checks=[
                self.check('name', '{botname}'),
                self.check('properties.description', '{description}'),
                self.check('resourceGroup', '{rg}'),
                self.check('location', 'global'),
                self.check('tags.key1', 'value1')
            ])

    @ResourceGroupPreparer(random_name_length=20)
    def test_botservice_create_v4_csharp_echo_webapp_bot(self, resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=15),
            'app_id': str(uuid.uuid4()),
            'password': str(uuid.uuid4())
        })

        # Delete the bot if already exists
        self.cmd('az bot delete -g {rg} -n {botname}')

        dir_path = os.path.join('.', self.kwargs.get('botname'))

        if os.path.exists(dir_path):
            # Clean up the folder
            shutil.rmtree(dir_path)

        self.cmd(
            'az bot create -k webapp -g {rg} -n {botname} --appid {app_id} -p {password} --lang Csharp --echo',
            checks=[
                self.check('resourceGroup', '{rg}'),
                self.check('id', '{botname}'),
                self.check('type', 'abs')
            ])

        # Talk to bot
        self.__talk_to_bot('hi', 'You sent \'hi\'')

        # Download the bot source
        self.cmd('az bot download -g {rg} -n {botname}', checks=[
            self.exists('downloadPath')
        ])
        self.check(os.path.isdir(os.path.join('dir_path', 'postDeployScripts')), True)

        # Publish it back
        self.cmd('az bot publish -g {rg} -n {botname} --code-dir {botname}', checks=[
            self.check('active', True)
        ])
        # Clean up the folder
        shutil.rmtree(dir_path)

        # Delete bot
        self.cmd('az bot delete -g {rg} -n {botname}')

    @ResourceGroupPreparer(random_name_length=20)
    def test_botservice_create_v4_js_echo_webapp_bot(self, resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=15),
            'app_id': str(uuid.uuid4()),
            'password': str(uuid.uuid4())
        })

        # Delete the bot if already exists
        self.cmd('az bot delete -g {rg} -n {botname}')

        dir_path = os.path.join('.', self.kwargs.get('botname'))
        if os.path.exists(dir_path):
            # clean up the folder
            shutil.rmtree(dir_path)

        self.cmd('az bot create -k webapp -g {rg} -n {botname} --appid {app_id} -p {password} --lang Javascript --echo',
                 checks={
                     self.check('resourceGroup', '{rg}'),
                     self.check('id', '{botname}'),
                     self.check('type', 'abs')
                 })

        # Download the bot source
        self.cmd('az bot download -g {rg} -n {botname}', checks=[
            self.exists('downloadPath')
        ])
        self.check(os.path.isdir(os.path.join('dir_path', 'postDeployScripts')), True)

        # Publish it back
        self.cmd('az bot publish -g {rg} -n {botname} --code-dir {botname}', checks=[
            self.check('active', True)
        ])
        # Clean up the folder
        shutil.rmtree(dir_path)

        # Delete bot
        self.cmd('az bot delete -g {rg} -n {botname}')

    @ResourceGroupPreparer(random_name_length=20)
    def test_botservice_create_v4_js_empty_webapp_for_webapp_bot(self, resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=15),
            'app_id': str(uuid.uuid4()),
            'password': str(uuid.uuid4())
        })
        self.cmd(
            'az bot create -k webapp -g {rg} -n {botname} --appid {app_id} -p {password} --lang Javascript')

    @ResourceGroupPreparer(random_name_length=20)
    def test_botservice_download_should_create_appsettings_for_v4_csharp_webapp_echo_bots_no_bot_file(self,
                                                                                                      resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=15),
            'app_id': str(uuid.uuid4()),
            'password': str(uuid.uuid4())
        })

        # Delete the bot if already exists
        self.cmd('az bot delete -g {rg} -n {botname}')

        dir_path = os.path.join('.', self.kwargs.get('botname'))
        if os.path.exists(dir_path):
            # clean up the folder
            shutil.rmtree(dir_path)

        results = self.cmd('az bot create -k webapp -g {rg} -n {botname} --appid {app_id} -p {password} --lang Csharp '
                           '--echo',
                           checks={
                               self.check('resourceGroup', '{rg}'),
                               self.check('id', '{botname}'),
                               self.check('type', 'abs')
                           })

        bot_name = results.get_output_in_json()['name']

        results = self.cmd('az bot download -g {rg} -n {botname}', checks={self.exists('downloadPath')})
        results = results.get_output_in_json()

        assert os.path.exists(os.path.join(results['downloadPath'], 'appsettings.json'))
        assert not os.path.exists(os.path.join(results['downloadPath'], '{0}.bot'.format(bot_name)))
        with open(os.path.join(results['downloadPath'], 'appsettings.json')) as settings:
            appsettings = json.load(settings)
            assert appsettings['MicrosoftAppId']
            assert appsettings['MicrosoftAppPassword']

        if os.path.exists(dir_path):
            # clean up the folder
            shutil.rmtree(dir_path)

    @ResourceGroupPreparer(random_name_length=20)
    def test_botservice_download_should_create_env_file_for_v4_node_webapp_echo_bots_no_bot_file(self, resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=15),
            'app_id': str(uuid.uuid4()),
            'password': str(uuid.uuid4())
        })

        # Delete the bot if already exists
        self.cmd('az bot delete -g {rg} -n {botname}')

        dir_path = os.path.join('.', self.kwargs.get('botname'))
        if os.path.exists(dir_path):
            # clean up the folder
            shutil.rmtree(dir_path)

        self.cmd(
            'az bot create -k webapp -g {rg} -n {botname} --appid {app_id} -p {password} --lang Javascript --echo',
            checks={
                self.check('resourceGroup', '{rg}'),
                self.check('id', '{botname}'),
                self.check('type', 'abs')
            })

        results = self.cmd('az bot download -g {rg} -n {botname}', checks={self.exists('downloadPath')})
        results = results.get_output_in_json()

        assert os.path.exists(os.path.join(results['downloadPath'], '.env'))
        with open(os.path.join(results['downloadPath'], '.env')) as settings:
            env = [env_var.split('=') for env_var in settings.read().split('\n')]
            env = {env[0][0]: env[0][1], env[1][0]: env[1][0]}
            assert env['MicrosoftAppId']
            assert env['MicrosoftAppPassword']

        if os.path.exists(dir_path):
            # clean up the folder
            shutil.rmtree(dir_path)

    @ResourceGroupPreparer(random_name_length=20)
    def test_botservice_keep_node_modules_should_not_empty_node_modules_or_install_dependencies(self, resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=15),
            'app_id': str(uuid.uuid4()),
            'password': str(uuid.uuid4())
        })

        # Delete the bot if already exists
        self.cmd('az bot delete -g {rg} -n {botname}')

        dir_path = os.path.join('.', self.kwargs.get('botname'))
        if os.path.exists(dir_path):
            # clean up the folder
            shutil.rmtree(dir_path)

        self.cmd('az bot create -k webapp -g {rg} -n {botname} --appid {app_id} -p {password} --lang Javascript --echo',
                 checks={
                     self.check('resourceGroup', '{rg}'),
                     self.check('id', '{botname}'),
                     self.check('type', 'abs')
                 })

        # Talk to bot
        self.__talk_to_bot('hi', 'You sent \'hi\'')

        # Download the bot source
        self.cmd('az bot download -g {rg} -n {botname}', checks=[
            self.exists('downloadPath')
        ])

        # Publish it back
        self.cmd('az bot publish -g {rg} -n {botname} --code-dir {botname} --keep-node-modules', checks=[
            self.check('active', True)
        ])
        # Clean up the folder
        shutil.rmtree(dir_path)

    @ResourceGroupPreparer(random_name_length=20)
    def test_botservice_create_should_create_registration_bot_without_endpoint(self, resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=15),
            'app_id': str(uuid.uuid4())
        })

        # Delete the bot if already exists
        self.cmd('az bot delete -g {rg} -n {botname}')

        self.cmd('az bot create -k registration -g {rg} -n {botname} --appid {app_id}')

    @ResourceGroupPreparer(random_name_length=20)
    def test_create_v4_webapp_bot_should_succeed_with_ending_hyphen(self, resource_group):
        bot_name = self.create_random_name(prefix='cli', length=15) + '-'
        valid_app_name = bot_name[:-1]
        self.kwargs.update({
            'valid_app_name': valid_app_name,
            'botname': bot_name,
            'app_id': str(uuid.uuid4()),
            'password': str(uuid.uuid4())
        })

        # Delete the bot if already exists
        self.cmd('az bot delete -g {rg} -n {botname}')

        dir_path = os.path.join('.', self.kwargs.get('botname'))

        if os.path.exists(dir_path):
            # Clean up the folder
            shutil.rmtree(dir_path)

        self.cmd('az bot create -k webapp -g {rg} -n {botname} --appid {app_id} -p {password} --lang Csharp',
                 checks=[
                     self.check('resourceGroup', '{rg}'),
                     self.check('id', '{botname}'),
                     self.check('type', 'abs'),
                     self.check('endpoint', 'https://{valid_app_name}.azurewebsites.net/api/messages')
                 ])

    @ResourceGroupPreparer(random_name_length=20)
    def test_botservice_show_on_v4_js_webapp_bot(self, resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=15),
            'app_id': str(uuid.uuid4()),
            'password': str(uuid.uuid4())
        })

        # Delete the bot if already exists
        self.cmd('az bot delete -g {rg} -n {botname}')

        dir_path = os.path.join('.', self.kwargs.get('botname'))
        if os.path.exists(dir_path):
            # clean up the folder
            shutil.rmtree(dir_path)

        self.cmd('az bot create -k webapp -g {rg} -n {botname} --appid {app_id} -p {password} --lang Javascript',
                 checks={
                     self.check('resourceGroup', '{rg}'),
                     self.check('id', '{botname}'),
                     self.check('type', 'abs')
                 })

        self.cmd('az bot show -g {rg} -n {botname} --msbot', checks=[
            self.exists('appPassword'),
            self.check('id', '{botname}'),
            self.check('resourceGroup', '{rg}'),
            self.check('type', 'abs')
        ])

    @ResourceGroupPreparer(random_name_length=20)
    def test_botservice_show_on_v4_csharp_webapp_bot(self, resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=15),
            'app_id': str(uuid.uuid4()),
            'password': str(uuid.uuid4())
        })

        # Delete the bot if already exists
        self.cmd('az bot delete -g {rg} -n {botname}')

        dir_path = os.path.join('.', self.kwargs.get('botname'))
        if os.path.exists(dir_path):
            # clean up the folder
            shutil.rmtree(dir_path)

        self.cmd('az bot create -k webapp -g {rg} -n {botname} --appid {app_id} -p {password} --lang Csharp',
                 checks={
                     self.check('resourceGroup', '{rg}'),
                     self.check('id', '{botname}'),
                     self.check('type', 'abs')
                 })

        self.cmd('az bot show -g {rg} -n {botname} --msbot', checks=[
            self.exists('appPassword'),
            self.check('id', '{botname}'),
            self.check('resourceGroup', '{rg}'),
            self.check('type', 'abs')
        ])

    @ResourceGroupPreparer(random_name_length=20)
    def test_botservice_publish_remove_node_iis_files_if_not_already_local(self, resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=15),
            'app_id': str(uuid.uuid4()),
            'password': str(uuid.uuid4())
        })

        dir_path = os.path.join('.', self.kwargs.get('botname'))
        if os.path.exists(dir_path):
            # clean up the folder
            shutil.rmtree(dir_path)

        self.cmd('az bot create -k webapp -g {rg} -n {botname} --appid {app_id} -p {password} --lang Javascript --echo',
                 checks={
                     self.check('resourceGroup', '{rg}'),
                     self.check('id', '{botname}'),
                     self.check('type', 'abs')
                 })

        # Download the bot source
        self.cmd('az bot download -g {rg} -n {botname}', checks=[
            self.exists('downloadPath')
        ])
        self.check(os.path.isdir(os.path.join('dir_path', 'postDeployScripts')), True)
        # Remove the IIS for Node.js files and PostDeployScripts folder
        shutil.rmtree(os.path.join(dir_path, 'PostDeployScripts'))
        os.remove(os.path.join(dir_path, 'web.config'))
        os.remove(os.path.join(dir_path, 'iisnode.yml'))
        # Publish it back
        self.cmd('az bot publish -g {rg} -n {botname} --code-dir {botname}', checks=[
            self.check('active', True)
        ])

        # Publish should not have left web.config and iisnode.yml files since they did not previously exist in code_dir
        self.check(os.path.exists(os.path.join(dir_path, 'web.config')), False)
        self.check(os.path.exists(os.path.join(dir_path, 'iisnode.yml')), False)

        # Clean up the folder
        shutil.rmtree(dir_path)

    @ResourceGroupPreparer(random_name_length=20)
    def test_prepare_publish_with_registration_bot_should_raise_error(self, resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=10),
            'description': 'description1',
            'endpoint': 'https://www.google.com/api/messages',
            'app_id': str(uuid.uuid4()),
            'password': str(uuid.uuid4())
        })

        self.cmd(
            'az bot create -k registration -g {rg} -n {botname} -d {description} -e {endpoint} --appid {app_id} -p {password} --tags '
            'key1=value1',
            checks=[
                self.check('name', '{botname}'),
                self.check('properties.description', '{description}'),
                self.check('resourceGroup', '{rg}'),
                self.check('location', 'global'),
                self.check('tags.key1', 'value1')
            ])

        self.cmd('az bot show -g {rg} -n {botname}', checks=[
            self.check('name', '{botname}')
        ])

        try:
            self.cmd('az bot prepare-publish -g {rg} -n {botname} --sln-name invalid.sln --proj-name invalid.csproj '
                     '--code-dir .')
            raise AssertionError('should have thrown an error.')
        except CLIError:
            pass
        except AssertionError:
            raise AssertionError('should have thrown an error for registration-type bot.')

    @ResourceGroupPreparer(random_name_length=20)
    def test_prepare_publish_with_unregistered_bot_name_should_fail(self, resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=10),
        })

        try:
            self.cmd('az bot prepare-publish -g {rg} -n {botname} --sln-name invalid.sln --proj-name invalid.csproj '
                     '--code-dir .')
            raise AssertionError('should have thrown an error.')
        except ErrorException:
            # We are expecting an ErrorException which is thrown from azure.mgmt.botservice SDK.
            pass
        except AssertionError:
            raise AssertionError('should have thrown an error for an unregistered bot.')
        except Exception as error:
            raise error

    @ResourceGroupPreparer(random_name_length=20)
    def test_prepare_publish_should_raise_cli_error_when_version_is_v4(self, resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=15),
            'sln_name': 'invalid.sln',
            'proj_name': 'invalid.csproj',
            'version': 'v4'
        })

        # Delete the bot if already exists
        self.cmd('az bot delete -g {rg} -n {botname}')

        dir_path = os.path.join('.', self.kwargs.get('botname'))
        if os.path.exists(dir_path):
            # Clean up the folder
            shutil.rmtree(dir_path)

        try:
            self.cmd('az bot prepare-publish -g {rg} -n {botname} --sln-name {sln_name} --proj-name {proj_name} -v v4')
            raise Exception("'az bot prepare-publish' should have failed with a --version argument of 'v4'")
        except CLIError as cli_error:
            assert cli_error.__str__() == "'az bot prepare-publish' is only for v3 bots. Please use 'az bot publish' " \
                                          "to prepare and publish a v4 bot."

        except Exception as error:
            raise error

    @ResourceGroupPreparer(random_name_length=20)
    def test_botservice_update_should_update_bot_properties(self, resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=15),
            'app_id': str(uuid.uuid4()),
            'display_name': 'clitestbot',
            'endpoint': 'https://dev.botframework.com/api/messages',
            'description': 'HelloWorld!',
            'ai-key': str(uuid.uuid4()),
            'ai-api-key': self.create_random_name(prefix='cli.', length=40),
            'ai-app-id': str(uuid.uuid4()),
            'tag': 'Hello',
            'tag-value': 'Microsoft!'
        })

        self.cmd('az bot delete -g {rg} -n {botname}')

        self.cmd('az bot create -k registration -g {rg} -n {botname} --appid {app_id}',
                 checks={
                     self.check('resourceGroup', '{rg}'),
                     self.check('id', '{botname}'),
                     self.check('type', 'abs')
                 })

        results = self.cmd('az bot update -g {rg} -n {botname} -e "{endpoint}" --description {description} --sku S1 '
                           '-d {display_name} --ai-key {ai-key} --ai-api-key {ai-api-key} --ai-app-id {ai-app-id} --tags '
                           '{tag}={tag-value} --icon-url https://dev.botframework.com/client/images/channels/icons/directline.png',
                           checks=[
                               self.check('name', '{botname}'),
                               self.check('resourceGroup', '{rg}')])
        results = results.get_output_in_json()

        assert results['sku']['name'] == 'S1'
        # assert results['properties']['displayName'] == 'clitestbot'  # Temporarily disabling until fix in service is deployed.
        assert results['properties']['endpoint'] == 'https://dev.botframework.com/api/messages'
        assert results['properties']['description'] == 'HelloWorld!'
        assert results['tags']['Hello'] == 'Microsoft!'
        assert results['properties']['developerAppInsightKey']
        # The "developerAppInsightsApiKey" is a secret and is always null when retrieved.
        assert not results['properties']['developerAppInsightsApiKey']
        assert results['properties']['developerAppInsightsApplicationId']
        assert results['properties']['iconUrl'] == 'https://dev.botframework.com/client/images/channels/icons/directline.png'

    @ResourceGroupPreparer(random_name_length=20)
    def test_botservice_create_should_raise_error_for_invalid_app_id_args(self, resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=15),
            'short_app_id': str(uuid.uuid4())[:34],
            'password': str(uuid.uuid4()),
            'numbers_id': "223232"
        })

        expected_error = "--appid must be a valid GUID from a Microsoft Azure AD Application Registration. See " \
                         "https://docs.microsoft.com/azure/active-directory/develop/quickstart-register-app " \
                         "for more information on App Registrations. See 'az bot create --help' for more CLI " \
                         "information."
        try:
            self.cmd('az bot create -k webapp -g {rg} -n {botname} --appid {numbers_id} -p {password} --lang '
                     'Javascript --echo')
            raise AssertionError()
        except CLIError as cli_error:
            assert cli_error.__str__() == expected_error
        except AssertionError:
            raise AssertionError('should have thrown an error for appid that is not valid GUID.')

        try:
            self.cmd('az bot create -k webapp -g {rg} -n {botname} --appid {short_app_id} -p {password} --lang '
                     'Javascript --echo')
            raise AssertionError()
        except CLIError as cli_error:
            assert cli_error.__str__() == expected_error
        except AssertionError:
            raise AssertionError('should have thrown an error for appid that is not valid GUID.')

        try:
            self.cmd('az bot create -k webapp -g {rg} -n {botname} --appid "" -p {password} --lang '
                     'Javascript --echo')
            raise AssertionError()
        except CLIError as cli_error:
            assert cli_error.__str__() == expected_error
        except AssertionError:
            raise AssertionError('should have thrown an error for appid that is not valid GUID.')

    @ResourceGroupPreparer(random_name_length=20)
    def test_botservice_create_should_raise_error_for_empty_password_strings_for_webapp_bots(self, resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=15),
            'app_id': str(uuid.uuid4())
        })

        try:
            self.cmd('az bot create -k webapp -g {rg} -n {botname} --appid {app_id} -p "" --lang Javascript --echo')
            raise AssertionError()
        except CLIError as cli_error:
            assert cli_error.__str__() == "--password cannot have a length of 0 for Web App Bots. This value is used to " \
                                          "authorize calls to your bot. See 'az bot create --help'."
        except AssertionError:
            raise AssertionError('should have thrown an error for empty string passwords.')

    @ResourceGroupPreparer(random_name_length=20)
    def test_botservice_create_should_raise_error_with_no_password_for_webapp_bots(self, resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=15),
            'app_id': str(uuid.uuid4())
        })

        try:
            self.cmd('az bot create -k webapp -g {rg} -n {botname} --appid {app_id} --lang Javascript --echo')
            raise AssertionError()
        except CLIError as cli_error:
            assert cli_error.__str__() == "--password cannot have a length of 0 for Web App Bots. This value is used to " \
                                          "authorize calls to your bot. See 'az bot create --help'."
        except AssertionError:
            raise AssertionError('should have thrown an error for empty string passwords.')

    @ResourceGroupPreparer(random_name_length=20)
    @ResourceGroupPreparer(key='rg2', random_name_length=20)
    def test_botservice_should_throw_if_name_is_unavailable(self, resource_group):
        bot_name = self.create_random_name(prefix='cli', length=10)
        self.kwargs.update({
            'botname': bot_name,
            'description': 'description1',
            'endpoint': 'https://www.google.com/api/messages',
            'app_id': str(uuid.uuid4()),
            'password': str(uuid.uuid4())
        })

        self.cmd(
            'az bot create -k registration -g {rg} -n {botname} -d {description} -e {endpoint} --appid {app_id}',
            checks=[
                self.check('name', '{botname}'),
                self.check('properties.description', '{description}'),
                self.check('resourceGroup', '{rg}'),
                self.check('location', 'global'),
            ])

        try:
            self.cmd(
                'az bot create -k registration -g {rg2} -n {botname} -d {description} -e {endpoint} --appid {app_id}')
            raise AssertionError()
        except CLIError as cli_error:
            assert cli_error.__str__().startswith('Unable to create bot.\nReason: ')
        except AssertionError:
            raise AssertionError('should have thrown an error for unavailable name.')

    def __talk_to_bot(self, message_text='Hi', expected_text=None):
        """Enables direct line channel, sends a message to the bot,
        and if expected_text is provided, verify that the bot answer matches it."""

        # This setting is for local testing, specifying an app id and password. Set it to true to test directline.
        # For automation, we set it to false by default to avoid handling keys for now.
        use_directline = False

        # It is not possible to talk to the bot in playback mode.
        if self.is_live and use_directline:
            result = self.cmd('az bot directline create -g {rg} -n {botname}', checks=[
                self.check('properties.properties.sites[0].siteName', 'Default Site')
            ])

            json_output = json.loads(result.output)

            directline_key = json_output['properties']['properties']['sites'][0]['key']
            directline_client = DirectLineClient(directline_key)

            send_result = directline_client.send_message(message_text)

            if send_result.status_code != 200:
                self.fail("Failed to send message to bot through directline api. Response:" +
                          json.dumps(send_result.json()))

            response, text = directline_client.get_message()

            if response.status_code != 200:
                self.fail("Failed to receive message from bot through directline api. Error:" + response.json())

            if expected_text:
                self.assertTrue(expected_text in text, "Bot response does not match expectation: " + text +
                                expected_text)


class BotLiveOnlyTests(LiveScenarioTest):
    @ResourceGroupPreparer(random_name_length=20)
    def test_botservice_create_should_remove_invalid_char_from_name_when_registration(self, resource_group):
        bot_name = self.create_random_name(prefix='cli.', length=15)
        self.kwargs.update({
            'botname': bot_name,
            'app_id': str(uuid.uuid4()),
            'password': str(uuid.uuid4())
        })

        self.cmd('az bot create -k registration -g {rg} -n {botname} --appid {app_id} -p {password} '
                 '-e https://testurl.com/api/messages',
                 checks={
                     self.check('resourceGroup', '{rg}'),
                     self.check('type', 'Microsoft.BotService/botServices')
                 })

    @ResourceGroupPreparer(random_name_length=20)
    def test_botservice_create_should_remove_invalid_char_from_name_when_webapp(self, resource_group):
        bot_name = self.create_random_name(prefix='cli.', length=15)
        valid_bot_name = bot_name.replace(".", "")
        self.kwargs.update({
            'valid_bot_name': valid_bot_name,
            'botname': bot_name,
            'app_id': str(uuid.uuid4()),
            'password': str(uuid.uuid4())
        })

        self.cmd('az bot create -k webapp -g {rg} -n {botname} --appid {app_id} -p {password} --lang Javascript',
                 checks={
                     self.check('resourceGroup', '{rg}'),
                     self.check('id', '{valid_bot_name}'),
                     self.check('type', 'abs')
                 })


class BotLocalErrorsTests(unittest.TestCase):
    def test_botservice_prepare_deploy_should_fail_if_code_dir_doesnt_exist(self):
        code_dir = 'does_not_exist'
        language = 'Javascript'
        proj_file_path = None

        try:
            prepare_webapp_deploy(language, code_dir, proj_file_path)
            raise Exception("'az bot prepare-publish' should have failed with nonexistent --code-dir value")
        except CLIError as cli_error:
            print(cli_error.__str__())
            assert cli_error.__str__() == 'Provided --code-dir value (does_not_exist) does not exist'
        except Exception as error:
            raise error

    def test_botservice_prepare_deploy_javascript_should_fail_with_proj_file_path(self):
        code_dir = None
        language = 'Javascript'
        proj_file_path = 'node_bot/test.csproj'

        try:
            prepare_webapp_deploy(language, code_dir, proj_file_path)
            raise Exception("'az bot prepare-publish --lang Javascript' should have failed with --proj-file-path")
        except CLIError as cli_error:
            assert cli_error.__str__() == '--proj-file-path should not be passed in if language is not Csharp'
        except Exception as error:
            raise error

    def test_botservice_prepare_deploy_javascript(self):
        code_dir = 'node_bot_javascript'
        language = 'Javascript'
        proj_file_path = None

        if os.path.exists(code_dir):
            # clean up the folder
            shutil.rmtree(code_dir)
        os.mkdir(code_dir)
        prepare_webapp_deploy(language, code_dir, proj_file_path)
        assert os.path.exists(os.path.join(code_dir, 'web.config'))
        shutil.rmtree(code_dir)

    def test_botservice_prepare_deploy_typescript_should_fail_with_proj_file_path(self):
        code_dir = None
        language = 'Typescript'
        proj_file_path = 'node_bot/test.csproj'

        try:
            prepare_webapp_deploy(language, code_dir, proj_file_path)
            raise Exception("'az bot prepare-publish --lang Typescript' should have failed with --proj-file-path")
        except CLIError as cli_error:
            assert cli_error.__str__() == '--proj-file-path should not be passed in if language is not Csharp'

    def test_botservice_prepare_deploy_typescript(self):
        code_dir = 'node_bot_typescript'
        language = 'Typescript'
        proj_file_path = None

        if os.path.exists(code_dir):
            # clean up the folder
            shutil.rmtree(code_dir)
        os.mkdir(code_dir)
        prepare_webapp_deploy(language, code_dir, proj_file_path)
        assert os.path.exists(os.path.join(code_dir, 'web.config'))
        shutil.rmtree(code_dir)

    def test_botservice_prepare_deploy_csharp(self):
        code_dir = 'csharp_bot_success'
        language = 'Csharp'
        proj_file_path = 'test.csproj'

        if os.path.exists(code_dir):
            # clean up the folder
            shutil.rmtree(code_dir)
        os.mkdir(code_dir)
        open(os.path.join(code_dir, proj_file_path), 'w')

        prepare_webapp_deploy(language, code_dir, proj_file_path)
        assert os.path.exists(os.path.join(code_dir, '.deployment'))
        with open(os.path.join(code_dir, '.deployment')) as d:
            assert d.readline() == '[config]\n'
            assert d.readline() == 'SCM_SCRIPT_GENERATOR_ARGS=--aspNetCore "{0}"\n'.format(proj_file_path)
        shutil.rmtree(code_dir)

    def test_botservice_prepare_deploy_csharp_preserve_filename_casing(self):
        code_dir = 'csharp_bot_success_casing'
        language = 'Csharp'
        proj_file_path = 'Azure_azure-cli_11390.csproj'

        if os.path.exists(code_dir):
            # clean up the folder
            shutil.rmtree(code_dir)
        os.mkdir(code_dir)
        open(os.path.join(code_dir, proj_file_path), 'w')

        prepare_webapp_deploy(language, code_dir, proj_file_path)
        assert os.path.exists(os.path.join(code_dir, '.deployment'))
        with open(os.path.join(code_dir, '.deployment')) as d:
            assert d.readline() == '[config]\n'
            assert d.readline() == 'SCM_SCRIPT_GENERATOR_ARGS=--aspNetCore "{0}"\n'.format(proj_file_path)
        shutil.rmtree(code_dir)

    def test_botservice_prepare_deploy_csharp_no_proj_file(self):
        code_dir = None
        language = 'Csharp'
        proj_file_path = None

        try:
            prepare_webapp_deploy(language, code_dir, proj_file_path)
            raise Exception("'az bot prepare-publish --lang Csharp' should have failed with no --proj-file-path")
        except CLIError as cli_error:
            assert cli_error.__str__() == '--proj-file-path must be provided if language is Csharp'

    def test_botservice_prepare_deploy_csharp_fail_if_deployment_file_exists(self):
        code_dir = 'csharp_bot_deployment'
        language = 'Csharp'
        proj_file_path = 'test.csproj'

        if os.path.exists(code_dir):
            # clean up the folder
            shutil.rmtree(code_dir)
        os.mkdir(code_dir)
        open(os.path.join(code_dir, proj_file_path), 'w')
        open(os.path.join(code_dir, '.deployment'), 'w')

        try:
            prepare_webapp_deploy(language, code_dir, proj_file_path)
            shutil.rmtree(code_dir)
        except CLIError as cli_error:
            shutil.rmtree(code_dir)
            assert cli_error.__str__() == '.deployment found in csharp_bot_deployment\nPlease delete this .deployment before ' \
                                          'calling "az bot prepare-deploy"'
        except Exception as error:
            shutil.rmtree(code_dir)
            raise error

    def test_botservice_prepare_deploy_javascript_fail_if_web_config_exists(self):
        code_dir = 'node_bot_web_config'
        language = 'Javascript'
        proj_file_path = None

        if os.path.exists(code_dir):
            # clean up the folder
            shutil.rmtree(code_dir)
        os.mkdir(code_dir)
        open(os.path.join(code_dir, 'web.config'), 'w')

        try:
            prepare_webapp_deploy(language, code_dir, proj_file_path)
            shutil.rmtree(code_dir)
        except CLIError as cli_error:
            shutil.rmtree(code_dir)
            assert cli_error.__str__() == 'web.config found in node_bot_web_config\nPlease delete this web.config before ' \
                                          'calling "az bot prepare-deploy"'
        except Exception as error:
            shutil.rmtree(code_dir)
            raise error
