# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long


def load_arguments(self, _):
    with self.argument_context('netappfiles') as c:
        c.argument('resource_group', options_list=['--resource-group', '-g'], required=True, help='The name of the resource group')

    with self.argument_context('netappfiles') as c:
        c.argument('account_name', options_list=['--account-name', '-a'], required=True, help='The name of the ANF account')

    with self.argument_context('netappfiles account') as c:
        c.argument('account_name', id_part='name', options_list=['--account-name', '-n', '-a'], required=True, help='The name of the ANF account')

    with self.argument_context('netappfiles account list') as c:
        c.argument('account_name', help='The name of the ANF account', id_part=None)

    with self.argument_context('netappfiles') as c:
        c.argument('pool_name', options_list=['--pool-name', '-p'], required=True, help='The name of the ANF pool')

    with self.argument_context('netappfiles pool') as c:
        c.argument('account_name', id_part='name')
        c.argument('pool_name', id_part='child_name_1', options_list=['--pool-name', '-n', '-p'], required=True, help='The name of the ANF pool')

    with self.argument_context('netappfiles pool list') as c:
        c.argument('account_name', options_list=['--account-name', '-n', '-a'], help='The name of the ANF account', id_part=None)

    with self.argument_context('netappfiles') as c:
        c.argument('volume_name', options_list=['--volume-name', '-v'], required=True, help='The name of the ANF volume')

    with self.argument_context('netappfiles volume') as c:
        c.argument('account_name', id_part='name')
        c.argument('pool_name', id_part='child_name_1', options_list=['--pool-name', '-p'], required=True, help='The name of the ANF pool')
        c.argument('volume_name', id_part='child_name_2', options_list=['--volume-name', '-n', '-v'], required=True, help='The name of the ANF volume')

    with self.argument_context('netappfiles volume list') as c:
        c.argument('account_name', options_list=['--account-name', '-a'], required=True, help='The name of the ANF account', id_part=None)
        c.argument('pool_name', options_list=['--pool-name', '-n', '-p'], required=True, help='The name of the ANF pool', id_part=None)

    with self.argument_context('netappfiles') as c:
        c.argument('snapshot_name', options_list=['--snapshot-name', '-s'], required=True, help='The name of the ANF snapshot')

    with self.argument_context('netappfiles snapshot') as c:
        c.argument('account_name', options_list=['--account-name', '-a'], id_part='name')
        c.argument('pool_name', id_part='child_name_1', options_list=['--pool-name', '-p'], required=True, help='The name of the ANF pool')
        c.argument('volume_name', id_part='child_name_2', options_list=['--volume-name', '-v'], required=True, help='The name of the ANF volume')
        c.argument('snapshot_name', id_part='child_name_3', options_list=['--snapshot-name', '-n', '-s'], required=True, help='The name of the ANF snapshot')

    with self.argument_context('netappfiles snapshot list') as c:
        c.argument('account_name', options_list=['--account-name', '-a'], required=True, help='The name of the ANF account', id_part=None)
        c.argument('volume_name', options_list=['--volume-name', '-n', '-v'], required=True, help='The name of the ANF volume', id_part=None)

    with self.argument_context('netappfiles') as c:
        c.argument('tag', options_list=['--tags'], required=False, help='A list of space separated tags to apply to the account')
