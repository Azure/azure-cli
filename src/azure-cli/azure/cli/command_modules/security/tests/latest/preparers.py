# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ResourceGroupPreparer
from azure.cli.testsdk.base import execute
from azure.cli.core.mock import DummyCli
from azure.cli.testsdk.exceptions import CliTestError
from azure.cli.testsdk.preparers import (AbstractPreparer, SingleValueReplacer)

sqlvm_name_prefix = 'clisqlvm'
sqlvm_domain_prefix = 'domainvm'
sqlvm_group_prefix = 'sqlgroup'
sqlvm_max_length = 15
sql_server_image = 'MicrosoftSQLServer:SQL2017-WS2016:Enterprise:latest'
sql_server_vm_size = 'Standard_DS2_v2'

la_workspace_name_prefix = 'laworkspace'
la_workspace_max_length = 15


class SqlVirtualMachinePreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix=sqlvm_name_prefix, location='eastus2euap',
                 vm_user='admin123', vm_password='SecretPassword123', parameter_name='sqlvm',
                 resource_group_parameter_name='resource_group', skip_delete=False):
        super(SqlVirtualMachinePreparer, self).__init__(name_prefix, sqlvm_max_length)
        self.location = location
        self.parameter_name = parameter_name
        self.vm_user = vm_user
        self.vm_password = vm_password
        self.resource_group_parameter_name = resource_group_parameter_name
        self.skip_delete = skip_delete

    def create_resource(self, name, **kwargs):
        group = self._get_resource_group(**kwargs)
        template = ('az vm create -l {} -g {} -n {} --admin-username {} --admin-password {} --image {} --size {}')
        execute(DummyCli(), template.format(self.location, group, name, self.vm_user,
                                            self.vm_password, sql_server_image, sql_server_vm_size))
        return {self.parameter_name: name}

    def remove_resource(self, name, **kwargs):
        if not self.skip_delete:
            group = self._get_resource_group(**kwargs)
            execute(DummyCli(), 'az vm delete -g {} -n {} --yes --no-wait'.format(group, name))

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a virtual machine a resource group is required. Please add ' \
                       'decorator @{} in front of this preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))


class LogAnalyticsWorkspacePreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix=la_workspace_name_prefix, location='eastus2euap', parameter_name='laworkspace',
                 resource_group_parameter_name='resource_group', skip_delete=False):
        super(LogAnalyticsWorkspacePreparer, self).__init__(name_prefix, la_workspace_max_length)
        self.location = location
        self.parameter_name = parameter_name
        self.resource_group_parameter_name = resource_group_parameter_name
        self.skip_delete = skip_delete

    def create_resource(self, name, **kwargs):
        group = self._get_resource_group(**kwargs)
        template = ('az monitor log-analytics workspace create -l {} -g {} -n {}')
        execute(DummyCli(), template.format(self.location, group, name))
        return {self.parameter_name: name}

    def remove_resource(self, name, **kwargs):
        if not self.skip_delete:
            group = self._get_resource_group(**kwargs)
            template = ('az monitor log-analytics workspace delete -g {} -n {} --yes')
            execute(DummyCli(), template.format(group, name))

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a log analytics workspace a resource group is required. Please add ' \
                       'decorator @{} in front of this preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))
