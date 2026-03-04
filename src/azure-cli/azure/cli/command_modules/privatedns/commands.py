# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-locals
from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.privatedns._client_factory import cf_privatedns_mgmt_zones
from azure.cli.command_modules.privatedns._format import transform_privatedns_record_set_output


def load_command_table(self, _):

    network_privatedns_zone_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.privatedns.operations#PrivateZonesOperations.{}',
        client_factory=cf_privatedns_mgmt_zones
    )

    with self.command_group("network private-dns zone", network_privatedns_zone_sdk) as g:
        g.custom_command("import", "import_zone")
        g.custom_command("export", "export_zone")

    supported_records = ['a', 'aaaa', 'mx', 'ptr', 'srv', 'txt']
    for record in supported_records:
        with self.command_group('network private-dns record-set {}'.format(record)) as g:
            g.custom_command('add-record', 'add_privatedns_{}_record'.format(record), transform=transform_privatedns_record_set_output)
            g.custom_command('remove-record', 'remove_privatedns_{}_record'.format(record), transform=transform_privatedns_record_set_output)

    with self.command_group('network private-dns record-set soa') as g:
        g.custom_command('update', 'update_privatedns_soa_record', transform=transform_privatedns_record_set_output)

    with self.command_group('network private-dns record-set cname') as g:
        g.custom_command('set-record', 'add_privatedns_cname_record', transform=transform_privatedns_record_set_output)
        g.custom_command('remove-record', 'remove_privatedns_cname_record', transform=transform_privatedns_record_set_output)
