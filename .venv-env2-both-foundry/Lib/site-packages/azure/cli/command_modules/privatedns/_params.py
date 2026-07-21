# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-statements
from argcomplete.completers import FilesCompleter
from knack.arguments import CLIArgumentType, ignore_type
from azure.cli.core.commands.parameters import (tags_type, file_type)
from azure.cli.command_modules.privatedns._validators import (
    privatedns_zone_name_type, validate_privatedns_metadata, validate_privatedns_record_type)


def load_arguments(self, _):
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')

    with self.argument_context('network private-dns') as c:
        c.argument('tags', tags_type)
        c.argument('relative_record_set_name', name_arg_type, help='The name of the record set, relative to the name of the Private DNS zone.')
        c.argument('private_zone_name', options_list=('--zone-name', '-z'), help='The name of the Private DNS zone.', type=privatedns_zone_name_type)
        c.argument('metadata', tags_type, help='Metadata in space-separated key=value pairs. This overwrites any existing metadata.', validator=validate_privatedns_metadata)

    with self.argument_context('network private-dns zone') as c:
        c.argument('private_zone_name', name_arg_type, type=privatedns_zone_name_type)
        c.ignore('location')

    with self.argument_context('network private-dns record-set') as c:
        c.argument('record_type', ignore_type, validator=validate_privatedns_record_type)

    for item in ['', 'a', 'aaaa', 'cname', 'mx', 'ptr', 'srv', 'txt']:
        with self.argument_context('network private-dns record-set {} create'.format(item)) as c:
            c.argument('ttl', type=int, help='Record set TTL (time-to-live)')

    for item in ['a', 'aaaa', 'cname', 'mx', 'ptr', 'srv', 'txt']:
        with self.argument_context('network private-dns record-set {} add-record'.format(item)) as c:
            c.argument('relative_record_set_name', options_list=('--record-set-name', '-n'), help='The name of the record set relative to the zone. Creates a new record set if one does not exist.')

        with self.argument_context('network private-dns record-set {} remove-record'.format(item)) as c:
            c.argument('relative_record_set_name', options_list=('--record-set-name', '-n'), help='The name of the record set relative to the zone.')
            c.argument('keep_empty_record_set', action='store_true', help='Keep the empty record set if the last record is removed.')

    with self.argument_context('network private-dns record-set cname set-record') as c:
        c.argument('relative_record_set_name', options_list=['--record-set-name', '-n'], help='The name of the record set relative to the zone. Creates a new record set if one does not exist.')

    with self.argument_context('network private-dns record-set soa') as c:
        c.argument('relative_record_set_name', ignore_type, default='@')

    with self.argument_context('network private-dns record-set a') as c:
        c.argument('ipv4_address', options_list=('--ipv4-address', '-a'), help='IPV4 address in string notation.')

    with self.argument_context('network private-dns record-set aaaa') as c:
        c.argument('ipv6_address', options_list=('--ipv6-address', '-a'), help='IPV6 address in string notation.')

    with self.argument_context('network private-dns record-set cname') as c:
        c.argument('cname', options_list=('--cname', '-c'), help='Canonical name.')

    with self.argument_context('network private-dns record-set mx') as c:
        c.argument('exchange', options_list=('--exchange', '-e'), help='Exchange metric.')
        c.argument('preference', options_list=('--preference', '-p'), help='Preference metric.')

    with self.argument_context('network private-dns record-set ptr') as c:
        c.argument('dname', options_list=('--ptrdname', '-d'), help='PTR target domain name.')

    with self.argument_context('network private-dns record-set soa') as c:
        c.argument('host', options_list=('--host', '-t'), help='Host name.')
        c.argument('email', options_list=('--email', '-e'), help='Email address.')
        c.argument('expire_time', type=int, options_list=('--expire-time', '-x'), help='Expire time (seconds).')
        c.argument('minimum_ttl', type=int, options_list=('--minimum-ttl', '-m'), help='Minimum TTL (time-to-live, seconds).')
        c.argument('refresh_time', type=int, options_list=('--refresh-time', '-f'), help='Refresh value (seconds).')
        c.argument('retry_time', type=int, options_list=('--retry-time', '-r'), help='Retry time (seconds).')
        c.argument('serial_number', type=int, options_list=('--serial-number', '-s'), help='Serial number.')

    with self.argument_context('network private-dns record-set srv') as c:
        c.argument('priority', type=int, options_list=('--priority', '-p'), help='Priority metric.')
        c.argument('weight', type=int, options_list=('--weight', '-w'), help='Weight metric.')
        c.argument('port', type=int, options_list=('--port', '-r'), help='Service port.')
        c.argument('target', options_list=('--target', '-t'), help='Target domain name.')

    with self.argument_context('network private-dns record-set txt') as c:
        c.argument('value', options_list=('--value', '-v'), nargs='+', help='Space-separated list of text values which will be concatenated together.')

    with self.argument_context('network private-dns zone import') as c:
        c.argument('file_name', options_list=['--file-name', '-f'], type=file_type, completer=FilesCompleter(), help='Path to the Private DNS zone file to import')

    with self.argument_context('network private-dns zone export') as c:
        c.argument('file_name', options_list=['--file-name', '-f'], type=file_type, completer=FilesCompleter(), help='Path to the Private DNS zone file to save')
