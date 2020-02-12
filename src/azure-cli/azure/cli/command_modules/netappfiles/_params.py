# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands.parameters import tags_type, resource_group_name_type, get_enum_type, get_three_state_flag
from knack.arguments import CLIArgumentType


def load_arguments(self, _):
    account_name_type = CLIArgumentType(options_list=['--account-name', '-a'], id_part='name', help='Name of the ANF account.')
    pool_name_type = CLIArgumentType(options_list=['--pool-name', '-p'], id_part='child_name_1', help='Name of the ANF pool.')
    volume_name_type = CLIArgumentType(options_list=['--volume-name', '-v'], id_part='child_name_2', help='Name of the ANF volume.')

    with self.argument_context('netappfiles') as c:
        c.argument('resource_group', resource_group_name_type)
        c.argument('tags', arg_type=tags_type)
        c.argument('protocol_types', arg_type=tags_type)
        c.argument('account_name', account_name_type)
        c.argument('pool_name', pool_name_type)
        c.argument('volume_name', volume_name_type)
        c.argument('snapshot_name', options_list=['--snapshot-name', '-s'], help='The name of the ANF snapshot')
        c.argument('tag', tags_type)
        c.argument('service_level', options_list=['--service-level'], arg_type=get_enum_type(['Standard', 'Premium', 'Ultra']), help='Service level')

    with self.argument_context('netappfiles account') as c:
        c.argument('account_name', account_name_type, options_list=['--name', '--account-name', '-n', '-a'])

    with self.argument_context('netappfiles account list') as c:
        c.argument('account_name', help='The name of the ANF account', id_part=None)

    with self.argument_context('netappfiles account ad list') as c:
        c.argument('account_name', help='The name of the ANF account', id_part=None)

    load_additionalArguments(self, account_name_type, pool_name_type, volume_name_type)


def load_additionalArguments(self, account_name_type, pool_name_type, volume_name_type):
    with self.argument_context('netappfiles pool') as c:
        c.argument('account_name', id_part='name')
        c.argument('pool_name', pool_name_type, options_list=['--pool-name', '-p', '--name', '-n'])

    with self.argument_context('netappfiles pool list') as c:
        c.argument('account_name', account_name_type, options_list=['--account-name', '-a'], id_part=None)

    with self.argument_context('netappfiles volume') as c:
        c.argument('account_name', id_part='name')
        c.argument('pool_name', pool_name_type)
        c.argument('volume_name', volume_name_type, options_list=['--volume-name', '-v', '--name', '-n'])

    with self.argument_context('netappfiles volume list') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('pool_name', options_list=['--pool-name', '-p'], help='Name of the ANF pool.', id_part=None)

    with self.argument_context('netappfiles volume export-policy list') as c:
        c.argument('account_name', id_part=None)
        c.argument('pool_name', pool_name_type, id_part=None)
        c.argument('volume_name', volume_name_type, options_list=['--volume-name', '-v', '--name', '-n'], id_part=None)

    with self.argument_context('netappfiles volume replication approve') as c:
        c.argument('account_name', id_part=None)
        c.argument('pool_name', pool_name_type, id_part=None)
        c.argument('volume_name', volume_name_type, options_list=['--volume-name', '-v', '--name', '-n'], id_part=None)
        c.argument('remote_volume_resource_id', options_list=['--remote-volume-resource-id', '-d'], help='The id of the destination replication volume', id_part=None)

    with self.argument_context('netappfiles volume export-policy add') as c:
        c.argument('unix_read_only', help="Indication of read only access", arg_type=get_three_state_flag())
        c.argument('unix_read_write', help="Indication of read and write access", arg_type=get_three_state_flag())
        c.argument('cifs', help="Indication that CIFS protocol is allowed", arg_type=get_three_state_flag())
        c.argument('nfsv3', help="Indication that NFSv3 protocol is allowed", arg_type=get_three_state_flag())
        c.argument('nfsv41', help="Indication that NFSv4.1 protocol is allowed", arg_type=get_three_state_flag())

    with self.argument_context('netappfiles snapshot') as c:
        c.argument('account_name', account_name_type)
        c.argument('pool_name', pool_name_type)
        c.argument('volume_name', volume_name_type)
        c.argument('snapshot_name', id_part='child_name_3', options_list=['--name', '--snapshot-name', '-n', '-s'], help='The name of the ANF snapshot')

    with self.argument_context('netappfiles snapshot list') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('volume_name', options_list=['--volume-name', '-v'], help='The name of the ANF volume', id_part=None)
