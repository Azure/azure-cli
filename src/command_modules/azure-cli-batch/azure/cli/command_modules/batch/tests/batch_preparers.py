# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from azure.cli.testsdk import CliTestError, ResourceGroupPreparer
from azure.cli.testsdk.preparers import AbstractPreparer, SingleValueReplacer
from azure.cli.testsdk.base import execute


class BatchAccountPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clibatch', parameter_name='batch_account_name', location='westus',
                 resource_group_parameter_name='resource_group', skip_delete=True,
                 dev_setting_name='AZURE_CLI_TEST_DEV_BATCH_ACCT_NAME'):
        super(BatchAccountPreparer, self).__init__(name_prefix, 24)
        self.parameter_name = parameter_name
        self.resource_group = None
        self.resource_group_parameter_name = resource_group_parameter_name
        self.skip_delete = skip_delete
        self.location = location
        self.dev_setting_value = os.environ.get(dev_setting_name, None)

    def create_resource(self, name, **kwargs):
        if not self.dev_setting_value:
            self.resource_group = self._get_resource_group(**kwargs)
            cmd = 'az batch account create -n {} -g {} -l {}'.format(name, self.resource_group,
                                                                     self.location)
            execute(cmd)
            return {self.parameter_name: name}
        return {self.parameter_name: self.dev_setting_value}

    def remove_resource(self, name, **kwargs):
        if not self.dev_setting_value and not self.skip_delete:
            cmd = 'az batch account delete -n {} -g {} -y'.format(name, self.resource_group)
            execute(cmd)

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a storage account a resource group is required. Please add ' \
                       'decorator @{} in front of this batch account preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))


class BatchScenarioMixin(object):
    def get_account_info(self, account_name, group_name):
        """Returns the batch account name, key, and endpoint in a tuple."""
        key = self.get_account_key(account_name, group_name)
        endpoint = self.get_account_endpoint(account_name, group_name)
        return account_name, key, endpoint

    def get_account_key(self, *args):
        return self.cmd(
            'batch account keys list -n {} -g {} --query "secondary" -otsv'.format(*args)).output

    def get_account_endpoint(self, *args):
        endpoint = self.cmd('batch account show -n {} -g {}'.format(*args)).get_output_in_json()[
            'accountEndpoint']
        return 'https://' + endpoint

    def batch_cmd(self, cmd, account_info, *args, **kwargs):
        cmd = cmd.format(*args)
        cmd = '{} --account-name {} --account-key "{}" --account-endpoint {}'.format(cmd,
                                                                                     *account_info)
        return self.cmd(cmd, **kwargs)
