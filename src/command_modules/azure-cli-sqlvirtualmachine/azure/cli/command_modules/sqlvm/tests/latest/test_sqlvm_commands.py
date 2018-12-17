# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import os

from azure_devtools.scenario_tests import AllowLargeResponse

from azure.cli.core.util import CLIError
from azure.cli.core.mock import DummyCli
from azure.cli.testsdk.base import execute
from azure.cli.testsdk.exceptions import CliTestError
from azure.cli.testsdk import (
    JMESPathCheck,
    JMESPathCheckExists,
    JMESPathCheckGreaterThan,
    NoneCheck,
    ResourceGroupPreparer,
    ScenarioTest,
    StorageAccountPreparer,
    LiveScenarioTest,
    record_only)
from azure.cli.testsdk.preparers import (
    AbstractPreparer,
    SingleValueReplacer)
from datetime import datetime, timedelta
from time import sleep


# Constants
sqlvm_name_prefix = 'clisqlvm'
sqlvm_max_length = 15
sqlvm_group_name_prefix = 'clisqlvmgroup'


class SqlVirtualMachinePreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix=sqlvm_name_prefix, location='westus',
                 vm_user='admin123', vm_password='SecretPassword123', parameter_name='sqlvm',
                 resource_group_parameter_name='resource_group', skip_delete=True):
        super(SqlVirtualMachinePreparer, self).__init__(name_prefix, sqlvm_max_length)
        self.location = location
        self.parameter_name = parameter_name
        self.vm_user = vm_user
        self.vm_password = vm_password
        self.resource_group_parameter_name = resource_group_parameter_name
        self.skip_delete = skip_delete

    def create_resource(self, name, **kwargs):
        group = self._get_resource_group(**kwargs)
        template = 'az vm create -l {} -g {} -n {} --admin-username {} --admin-password {} --image MicrosoftSQLServer:SQL2017-WS2016:SQLDEV:latest'
        execute(DummyCli(), template.format(self.location, group, name, self.vm_user, self.vm_password))
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

class SqlVmScenarioTest(ScenarioTest):
    @ResourceGroupPreparer()
    @SqlVirtualMachinePreparer()
    def test_sqlvm_mgmt(self, resource_group, resource_group_location, sqlvm):

        loc = 'westus'

        # test create sqlvm with minimal required parameters
        sqlvm_1 = self.cmd('sqlvm create -n {} -g {} -l {}'
                           .format(sqlvm, resource_group, loc),
                           checks=[
                               JMESPathCheck('name', sqlvm),
                               JMESPathCheck('location', loc)
                           ]).get_output_in_json()

        # test list sqlvm should be 1
        self.cmd('sqlvm list -g {}'.format(resource_group), checks=[JMESPathCheck('length(@)', 1)])

        # test 
