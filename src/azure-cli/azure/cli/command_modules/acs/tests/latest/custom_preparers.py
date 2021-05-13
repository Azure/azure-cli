# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from datetime import datetime

from azure.cli.testsdk import CliTestError
from azure.cli.testsdk.preparers import NoTrafficRecordingPreparer
from azure_devtools.scenario_tests import SingleValueReplacer
from azure.cli.testsdk.reverse_dependency import get_dummy_cli


class AKSCustomResourceGroupPreparer(NoTrafficRecordingPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest.rg',
                 parameter_name='resource_group',
                 parameter_name_for_location='resource_group_location', location='westus',
                 dev_setting_name='AZURE_CLI_TEST_DEV_RESOURCE_GROUP_NAME',
                 dev_setting_location='AZURE_CLI_TEST_DEV_RESOURCE_GROUP_LOCATION',
                 random_name_length=75, key='rg'):
        if ' ' in name_prefix:
            raise CliTestError(
                'Error: Space character in resource group name prefix \'%s\'' % name_prefix)
        super(AKSCustomResourceGroupPreparer, self).__init__(
            name_prefix, random_name_length)
        self.cli_ctx = get_dummy_cli()
        self.location = location
        self.parameter_name = parameter_name
        self.parameter_name_for_location = parameter_name_for_location
        self.key = key

        self.dev_setting_name = os.environ.get(dev_setting_name, None)
        # use environment variable to modify the default value of location
        self.dev_setting_location = os.environ.get(dev_setting_location, None)
        if self.dev_setting_location:
            self.location = self.dev_setting_location

    def create_resource(self, name, **kwargs):
        if self.dev_setting_name:
            self.test_class_instance.kwargs[self.key] = self.dev_setting_name
            return {self.parameter_name: self.dev_setting_name,
                    self.parameter_name_for_location: self.dev_setting_location}

        tags = {'product': 'azurecli', 'cause': 'automation',
                'date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}
        if 'ENV_JOB_NAME' in os.environ:
            tags['job'] = os.environ['ENV_JOB_NAME']
        tags = ' '.join(['{}={}'.format(key, value)
                        for key, value in tags.items()])
        template = 'az group create --location {} --name {} --tag ' + tags
        self.live_only_execute(
            self.cli_ctx, template.format(self.location, name))

        self.test_class_instance.kwargs[self.key] = name
        return {self.parameter_name: name, self.parameter_name_for_location: self.location}

    def remove_resource(self, name, **kwargs):
        # delete group if test is being recorded and if the group is not a dev rg
        if not self.dev_setting_name:
            self.live_only_execute(
                self.cli_ctx, 'az group delete --name {} --yes --no-wait'.format(name))
