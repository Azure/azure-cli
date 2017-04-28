# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


class StorageScenarioMixin(object):
    def get_account_key(self, group, name):
        return self.cmd('storage account keys list -n {} -g {} --query "[0].value" -otsv'
                        .format(name, group)).output

    def get_account_info(self, group, name):
        """Returns the storage account name and key in a tuple"""
        return name, self.get_account_key(group, name)

    def storage_cmd(self, cmd, account_info, *args):
        cmd = cmd.format(*args)
        cmd = '{} --account-name {} --account-key {}'.format(cmd, *account_info)
        return self.cmd(cmd)

    def storage_cmd_negative(self, cmd, account_info, *args):
        cmd = cmd.format(*args)
        cmd = '{} --account-name {} --account-key {}'.format(cmd, *account_info)
        return self.cmd(cmd, expect_failure=True)

    def create_container(self, account_info, prefix='cont', length=24):
        container_name = self.create_random_name(prefix=prefix, length=length)
        self.storage_cmd('storage container create -n {}', account_info, container_name)
        return container_name

    def create_share(self, account_info, prefix='share', length=24):
        share_name = self.create_random_name(prefix=prefix, length=length)
        self.storage_cmd('storage share create -n {}', account_info, share_name)
        return share_name
