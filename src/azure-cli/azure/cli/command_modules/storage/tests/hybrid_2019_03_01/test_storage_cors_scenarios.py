# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os

from azure.cli.testsdk import (ScenarioTest, JMESPathCheck, ResourceGroupPreparer,
                               StorageAccountPreparer, api_version_constraint)
from azure.cli.core.profiles import ResourceType
from azure.cli.core.parser import IncorrectUsageError

@api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2016-12-01')
class StorageCorsTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='account')
    def test_storage_cors_scenario(self, resource_group, account):
        connection_string = self.cmd('storage account show-connection-string -n {} -g {} -otsv'
                                     .format(account, resource_group)).output

        curr_dir = os.path.dirname(os.path.realpath(__file__))
        input_file = os.path.join(curr_dir, 'input-file.json').replace('\\', '\\\\')
        lack_input_file = os.path.join(curr_dir, 'lack-input-file.json').replace('\\', '\\\\')

        self.cmd('storage cors list --connection-string "{}"'.format(connection_string),
                 checks=JMESPathCheck('length(@)', 0))

        self.cmd('storage cors add --method POST --origins http://example.com --services bfq '
                 '--max-age 60 --connection-string "{}"'.format(connection_string))

        self.cmd('storage cors add --method GET --origins http://example.com --services bf '
                 '--connection-string "{}"'.format(connection_string))

        self.cmd('storage cors add --i {} --services bq '
                 '--connection-string "{}"'.format(input_file, connection_string))

        with self.assertRaises(IncorrectUsageError):
            self.cmd('storage cors add --i {} --services fq --max-age 1 '
                     '--connection-string "{}"'.format(input_file, connection_string))

        with self.assertRaises(IncorrectUsageError):
            self.cmd('storage cors add --i {} --services fq --origins azure.com mirosoft.com '
                     '--connection-string "{}"'.format(input_file, connection_string))

        with self.assertRaises(IncorrectUsageError):
            self.cmd('storage cors add --i {} --services fq --methods DELETE HEAD GET '
                     '--connection-string "{}"'.format(input_file, connection_string))

        with self.assertRaises(IncorrectUsageError):
            self.cmd('storage cors add --i {} --services fq --allowed-headers Connection:Keep-Alive key:val '
                     '--connection-string "{}"'.format(input_file, connection_string))

        with self.assertRaises(IncorrectUsageError):
            self.cmd('storage cors add --i {} --services fq --exposed-headers Connection:Keep-Alive key:val '
                     '--connection-string "{}"'.format(input_file, connection_string))

        with self.assertRaises(IncorrectUsageError):
            self.cmd('storage cors add --i {} --services fq '
                     '--connection-string "{}"'.format(lack_input_file, connection_string))

        with self.assertRaises(IncorrectUsageError):
            self.cmd('storage cors add --origins http://example.com --services bf '
                     '--connection-string "{}"'.format(connection_string))

        with self.assertRaises(IncorrectUsageError):
            self.cmd('storage cors add --method GET --services bf '
                     '--connection-string "{}"'.format(connection_string))

        rules = self.cmd('storage cors list --connection-string "{}"'.format(connection_string)).get_output_in_json()
        self.assertEqual(len(rules), 7)
        for rule in rules:
            self.assertNotEqual(rule['Service'], "")

        self.cmd('storage cors clear --services bf --connection-string "{}"'
                 .format(connection_string))

        self.cmd('storage cors list --connection-string "{}"'.format(connection_string), checks=[
            JMESPathCheck('length(@)', 2),
            JMESPathCheck('[0].Service', 'queue'),
            JMESPathCheck('[0].AllowedMethods', 'POST')])

        self.cmd('storage cors clear --services q --connection-string "{}"'
                 .format(connection_string))

        self.cmd('storage cors list --connection-string "{}"'.format(connection_string),
                 checks=JMESPathCheck('length(@)', 0))
