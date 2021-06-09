# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.testsdk.preparers import ResourceGroupPreparer


class AKSCustomResourceGroupPreparer(ResourceGroupPreparer):
    def __init__(
            self,
            name_prefix='clitest.rg',
            parameter_name='resource_group',
            parameter_name_for_location='resource_group_location',
            location='westus',
            dev_setting_name='AZURE_CLI_TEST_DEV_RESOURCE_GROUP_NAME',
            dev_setting_location='AZURE_CLI_TEST_DEV_RESOURCE_GROUP_LOCATION',
            random_name_length=75,
            key='rg'):
        super(AKSCustomResourceGroupPreparer,
              self).__init__(name_prefix, parameter_name,
                             parameter_name_for_location, location,
                             dev_setting_name, dev_setting_location,
                             random_name_length, key)

        # use environment variable to modify the default value of location
        self.dev_setting_location = os.environ.get(dev_setting_location, None)
        if self.dev_setting_location:
            self.location = self.dev_setting_location
        else:
            self.dev_setting_location = location
