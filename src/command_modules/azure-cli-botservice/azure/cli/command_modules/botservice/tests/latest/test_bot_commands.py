# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.command_modules.botservice.tests.latest.tools.directline_client import DirectLineClient
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.mgmt.botservice.models import ErrorException
from knack.util import CLIError
import uuid
import os
import shutil
import json


class BotTests(ScenarioTest):

    @ResourceGroupPreparer(random_name_length=20)
    def registration_bot_create(self, resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=10),
            'description': 'description1',
            'endpoint': 'https://www.google.com/api/messages',
            'app_id': str(uuid.uuid4())
        })

        self.cmd('az bot create -k registration -g {rg} -n {botname} -d {description} -e {endpoint} --appid {app_id} --tags key1=value1', checks=[
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
            'app_id': 'dabb85a0-c38a-491d-ba91-f4ce1ad22923',
            'password': 'cqeuqQDVTY568;%wmAQ75%_'
        })

        # Delete the bot if already exists
        self.cmd('az bot delete -g {rg} -n {botname}')

        dir_path = os.path.join('.', self.kwargs.get('botname'))
        if os.path.exists(dir_path):
            # clean up the folder
            shutil.rmtree(dir_path)

        self.cmd('az bot create -k webapp -g {rg} -n {botname} --appid {app_id} -p {password} '
                 '--location westus --insights-location "West US 2"', checks=[
            self.check('appId', '{app_id}'),
            self.check('appPassword', '{password}'),
            self.check('resourceGroup', '{rg}'),
            self.check('id', '{botname}'),
            self.check('type', 'abs')
        ])

        # Talk to bot
        #self.__talk_to_bot('hi', '1: You said "hi"')

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

        # Talk to bot and verify that change is reflected
        #self.__talk_to_bot('hi', '1: You said "hi"')

        # Delete bot
        self.cmd('az bot delete -g {rg} -n {botname}')


    @ResourceGroupPreparer(random_name_length=20)
    def test_create_v4_webapp_bot(self, resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=15),
            'app_id': 'dabb85a0-c38a-491d-ba91-f4ce1ad22923',
            'password': 'cqeuqQDVTY568;%wmAQ75%_'
        })

        # Delete the bot if already exists
        self.cmd('az bot delete -g {rg} -n {botname}')

        dir_path = os.path.join('.', self.kwargs.get('botname'))
        if os.path.exists(dir_path):
            # clean up the folder
            shutil.rmtree(dir_path)

        self.cmd('az bot create -k webapp -g {rg} -n {botname} --appid {app_id} -p {password} -v v4', checks=[
            self.check('appId', '{app_id}'),
            self.check('appPassword', '{password}'),
            self.check('resourceGroup', '{rg}'),
            self.check('id', '{botname}'),
            self.check('type', 'abs')
        ])

        # Talk to bot
        #self.__talk_to_bot('hi', 'Turn 1: You sent \'hi\'\n')

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

        # Talk to bot again to check everything went well
        #self.__talk_to_bot('hi', 'Turn 1: You sent \'hi\'\n')

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

        try:
            self.cmd('az bot prepare-publish -g {rg} -n {botname} --sln-name invalid.sln --proj-name invalid.csproj '
                     '--code-dir .')
            raise AssertionError('should have thrown an error.')
        except CLIError as cli_error:
            self.cmd('az bot delete -g {rg} -n {botname}')
            pass
        except AssertionError as assert_error:
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
        except ErrorException as msrest_error:
            # We are expecting an ErrorException which is thrown from azure.mgmt.botservice SDK.
            pass
        except AssertionError as assert_error:
            raise AssertionError('should have thrown an error for an unregistered bot.')
        except Exception as error:
            raise error

    def __talk_to_bot(self, message_text='Hi', expected_text=None):
        """Enables direct line channel, sends a message to the bot,
        and if expected_text is provided, verify that the bot answer matches it."""

        result = self.cmd('az bot directline create -g {rg} -n {botname}', checks=[
            self.check('properties.properties.sites[0].siteName', 'Default Site')
        ])

        json_output = json.loads(result.output)

        # TODO: Remove
        print(result.output)

        directline_key = json_output['properties']['properties']['sites'][0]['key']
        directline_client = DirectLineClient(directline_key)

        send_result = directline_client.send_message(message_text)

        if send_result.status_code != 200:
            self.fail("Failed to send message to bot through directline api. Error:" + str(send_result))

        response, text = directline_client.get_message()

        if response.status_code != 200:
            self.fail("Failed to receive message from bot through directline api. Error:" + str(response))

        if expected_text != None:
            self.assertEqual(expected_text, text, "Bot response does not match expectation")

