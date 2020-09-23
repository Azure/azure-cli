# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.testsdk import CliTestError, ResourceGroupPreparer
from azure.cli.testsdk.preparers import AbstractPreparer, SingleValueReplacer
from azure.cli.testsdk.base import execute
# pylint: disable=line-too-long


class VMPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest-vm', parameter_name='vm_name',
                 resource_group_location_parameter_name='resource_group_location',
                 resource_group_parameter_name='resource_group', dev_setting_name='AZURE_CLI_TEST_DEV_BACKUP_VM_NAME'):
        super(VMPreparer, self).__init__(name_prefix, 15)
        from azure.cli.core.mock import DummyCli
        self.cli_ctx = DummyCli()
        self.parameter_name = parameter_name
        self.resource_group = None
        self.resource_group_parameter_name = resource_group_parameter_name
        self.location = None
        self.resource_group_location_parameter_name = resource_group_location_parameter_name
        self.dev_setting_value = os.environ.get(dev_setting_name, None)

    def create_resource(self, name, **kwargs):
        if not self.dev_setting_value:
            self.resource_group = self._get_resource_group(**kwargs)
            self.location = self._get_resource_group_location(**kwargs)
            param_format = '-n {} -g {} --image {} --admin-username {} --admin-password {} --tags {} --nsg-rule None'
            param_tags = 'MabUsed=Yes Owner=sisi Purpose=CLITest DeleteBy=12-2099 AutoShutdown=No'
            param_string = param_format.format(name, self.resource_group, 'Win2012R2Datacenter', name,
                                               '%j^VYw9Q3Z@Cu$*h', param_tags)
            cmd = 'az vm create {}'.format(param_string)
            execute(self.cli_ctx, cmd)
            return {self.parameter_name: name}
        return {self.parameter_name: self.dev_setting_value}

    def remove_resource(self, name, **kwargs):
        # Resource group deletion will take care of this.
        pass

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a vm, a resource group is required. Please add ' \
                       'decorator @{} in front of this VM preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))

    def _get_resource_group_location(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_location_parameter_name)
        except KeyError:
            template = 'To create a vm, a resource group is required. Please add ' \
                       'decorator @{} in front of this VM preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))
