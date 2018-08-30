# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
import uuid
import os
import shutil


class BotTests(ScenarioTest):

    @ResourceGroupPreparer(random_name_length=20)
    def test_registration_bot(self, resource_group):
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
    def test_webapp_bot(self, resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=15),
            'app_id': '0cc66483-d276-4830-9afd-9fe6b654a255',
            'password': 'testpassword'
        })
        dir_path = os.path.join('.', self.kwargs.get('botname'))
        if os.path.exists(dir_path):
            # clean up the folder
            shutil.rmtree(dir_path)

        self.cmd('az bot create -k webapp -g {rg} -n {botname} --appid {app_id} -p {password}', checks=[
            self.check('appId', '{app_id}'),
            self.check('appPassword', '{password}'),
            self.check('resourceGroup', '{rg}'),
            self.check('id', '{botname}'),
            self.check('type', 'abs')
        ])

        # download the bot
        self.cmd('az bot download -g {rg} -n {botname}', checks=[
            self.exists('downloadPath')
        ])
        self.check(os.path.isdir(os.path.join('dir_path', 'postDeployScripts')), True)

        # publish it back
        self.cmd('az bot publish -g {rg} -n {botname} --code-dir {botname}', checks=[
            self.check('active', True)
        ])
        # clean up the folder
        shutil.rmtree(dir_path)
