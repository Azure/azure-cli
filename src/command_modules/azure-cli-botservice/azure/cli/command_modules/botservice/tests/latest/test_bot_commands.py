# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.mgmt.botservice.models import ErrorException
from knack.util import CLIError
import uuid
import os
import shutil
import json
import requests


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

    def __set_headers(self):
        headers = {'Content-Type': 'application/json'}
        value = ' '.join(['Bearer', self._direct_line_secret])
        headers.update({'Authorization': value})
        self._headers = headers

    def __start_conversation(self):

        # Start conversation and get us a conversationId to use
        url = '/'.join([self._base_url, 'conversations'])
        botresponse = requests.post(url, headers=self._headers)

        # Extract the conversationID for sending messages to bot
        jsonresponse = botresponse.json()
        self._conversationid = jsonresponse['conversationId']


class BotTests(ScenarioTest):

    @ResourceGroupPreparer(random_name_length=20)
    def registration_bot_create(self, resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=10),
            'description': 'description1',
            'endpoint': 'https://www.google.com/api/messages',
            'app_id': str(uuid.uuid4())
        })

        self.cmd(
            'az bot create -k registration -g {rg} -n {botname} -d {description} -e {endpoint} --appid {app_id} --tags key1=value1',
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

        self.cmd('az bot update --set properties.description=description2 -g {rg} -n {botname}', checks=[
            self.check('name', '{botname}'),
            self.check('properties.description', 'description2')
        ])

        self.cmd('az bot delete -g {rg} -n {botname}')

    @ResourceGroupPreparer(random_name_length=20)
    def test_create_v3_webapp_bot(self, resource_group):
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
            'az bot create -k webapp -g {rg} -n {botname} --appid {app_id} -p {password} --location westus '
            '--insights-location "West US 2"',
            checks=[
                self.check('resourceGroup', '{rg}'),
                self.check('id', '{botname}'),
                self.check('type', 'abs')
            ])

        # Talk to bot
        self.__talk_to_bot('hi', 'You said hi')

        # Download the bot
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
    def test_create_v4_webapp_bot(self, resource_group):
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
            'az bot create -k webapp -g {rg} -n {botname} --appid {app_id} -p {password} -v v4',
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
    def test_create_v3_js_webapp_bot(self, resource_group):
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
            'az bot create -k webapp -g {rg} -n {botname} --appid {app_id} -p {password} --location westus '
            '--insights-location "West US 2" --lang Node',
            checks=[
                self.check('resourceGroup', '{rg}'),
                self.check('id', '{botname}'),
                self.check('type', 'abs')
            ])

        # We don't talk to the bot in this test because it takes a while for the node app to be responsive
        # Download the bot
        self.cmd('az bot download -g {rg} -n {botname}', checks=[
            self.exists('downloadPath')
        ])

        self.check(os.path.isdir(os.path.join('dir_path', 'postDeployScripts')), True)

        # Modify bot source
        # TODO implement

        # Publish it back
        self.cmd('az bot publish -g {rg} -n {botname} --code-dir {botname}', checks=[
            self.check('active', True)
        ])
        # clean up the folder
        shutil.rmtree(dir_path)

        # Delete bot
        self.cmd('az bot delete -g {rg} -n {botname}')

    @ResourceGroupPreparer(random_name_length=20)
    def test_create_v4_js_webapp_bot(self, resource_group):
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

        self.cmd('az bot create -k webapp -g {rg} -n {botname} --appid {app_id} -p {password} -v v4 --lang Node',
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
    def test_prepare_publish_with_registration_bot_should_raise_error(self, resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=10),
            'description': 'description1',
            'endpoint': 'https://www.google.com/api/messages',
            'app_id': str(uuid.uuid4())
        })

        self.cmd(
            'az bot create -k registration -g {rg} -n {botname} -d {description} -e {endpoint} --appid {app_id} --tags '
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
            self.cmd('az bot delete -g {rg} -n {botname}')
            pass
        except AssertionError:
            self.cmd('az bot delete -g {rg} -n {botname}')
            raise AssertionError('should have thrown an error for registration-type bot.')
        except Exception as error:
            self.cmd('az bot delete -g {rg} -n {botname}')
            raise error

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
            self.cmd('az bot delete -g {rg} -n {botname}')
            assert cli_error.__str__() == "'az bot prepare-publish' is only for v3 bots. Please use 'az bot publish' " \
                                          "to prepare and publish a v4 bot."

        except Exception as error:
            self.cmd('az bot delete -g {rg} -n {botname}')
            raise error

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
                self.assertTrue(expected_text in text, "Bot response does not match expec\tation: " + text +
                                expected_text)
