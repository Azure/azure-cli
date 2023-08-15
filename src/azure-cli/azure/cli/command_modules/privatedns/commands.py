# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-locals
from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.privatedns._client_factory import cf_privatedns_mgmt_zones
from azure.cli.command_modules.privatedns._format import (transform_privatedns_zone_table_output, transform_privatedns_link_table_output, transform_privatedns_record_set_output, transform_privatedns_record_set_table_output)


def load_command_table(self, _):

    network_privatedns_zone_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.privatedns.operations#PrivateZonesOperations.{}',
        client_factory=cf_privatedns_mgmt_zones
    )

    with self.command_group("network private-dns zone", network_privatedns_zone_sdk) as g:
        from .aaz.latest.network.private_dns.zone import List as PrivateDNSZoneList, Show as PrivateDNSZoneShow
        from .custom import PrivateDNSZoneCreate
        self.command_table["network private-dns zone create"] = PrivateDNSZoneCreate(loader=self)
        self.command_table["network private-dns zone list"] = PrivateDNSZoneList(loader=self, table_transformer=transform_privatedns_zone_table_output)
        self.command_table["network private-dns zone show"] = PrivateDNSZoneShow(loader=self, table_transformer=transform_privatedns_zone_table_output)
        g.custom_command("import", "import_zone")
        g.custom_command("export", "export_zone")

    with self.command_group("network private-dns link vnet"):
        from .aaz.latest.network.private_dns.link.vnet import List as PrivateDNSLinkVNetList, Show as PrivateDNSLinkVNetShow
        from .custom import PrivateDNSLinkVNetCreate
        self.command_table["network private-dns link vnet create"] = PrivateDNSLinkVNetCreate(loader=self)
        self.command_table["network private-dns link vnet list"] = PrivateDNSLinkVNetList(loader=self, table_transformer=transform_privatedns_link_table_output)
        self.command_table["network private-dns link vnet show"] = PrivateDNSLinkVNetShow(loader=self, table_transformer=transform_privatedns_link_table_output)

    from .custom import RecordSetACreate, RecordSetAAAACreate, RecordSetCNAMECreate, RecordSetMXCreate, RecordSetPTRCreate, RecordSetSRVCreate, RecordSetTXTCreate
    self.command_table["network private-dns record-set a create"] = RecordSetACreate(loader=self)
    self.command_table["network private-dns record-set aaaa create"] = RecordSetAAAACreate(loader=self)
    self.command_table["network private-dns record-set cname create"] = RecordSetCNAMECreate(loader=self)
    self.command_table["network private-dns record-set mx create"] = RecordSetMXCreate(loader=self)
    self.command_table["network private-dns record-set ptr create"] = RecordSetPTRCreate(loader=self)
    self.command_table["network private-dns record-set srv create"] = RecordSetSRVCreate(loader=self)
    self.command_table["network private-dns record-set txt create"] = RecordSetTXTCreate(loader=self)

    from .custom import RecordSetADelete, RecordSetAAAADelete, RecordSetCNAMEDelete, RecordSetMXDelete, RecordSetPTRDelete, RecordSetSRVDelete, RecordSetTXTDelete
    self.command_table["network private-dns record-set a delete"] = RecordSetADelete(loader=self)
    self.command_table["network private-dns record-set aaaa delete"] = RecordSetAAAADelete(loader=self)
    self.command_table["network private-dns record-set cname delete"] = RecordSetCNAMEDelete(loader=self)
    self.command_table["network private-dns record-set mx delete"] = RecordSetMXDelete(loader=self)
    self.command_table["network private-dns record-set ptr delete"] = RecordSetPTRDelete(loader=self)
    self.command_table["network private-dns record-set srv delete"] = RecordSetSRVDelete(loader=self)
    self.command_table["network private-dns record-set txt delete"] = RecordSetTXTDelete(loader=self)

    from .aaz.latest.network.private_dns.record_set import List as RecordSetList
    from .custom import RecordSetAList, RecordSetAAAAList, RecordSetCNAMEList, RecordSetMXList, RecordSetPTRList, RecordSetSRVList, RecordSetTXTList
    self.command_table["network private-dns record-set list"] = RecordSetList(loader=self, table_transformer=transform_privatedns_record_set_table_output)
    self.command_table["network private-dns record-set a list"] = RecordSetAList(loader=self, table_transformer=transform_privatedns_record_set_table_output)
    self.command_table["network private-dns record-set aaaa list"] = RecordSetAAAAList(loader=self, table_transformer=transform_privatedns_record_set_table_output)
    self.command_table["network private-dns record-set cname list"] = RecordSetCNAMEList(loader=self, table_transformer=transform_privatedns_record_set_table_output)
    self.command_table["network private-dns record-set mx list"] = RecordSetMXList(loader=self, table_transformer=transform_privatedns_record_set_table_output)
    self.command_table["network private-dns record-set ptr list"] = RecordSetPTRList(loader=self, table_transformer=transform_privatedns_record_set_table_output)
    self.command_table["network private-dns record-set srv list"] = RecordSetSRVList(loader=self, table_transformer=transform_privatedns_record_set_table_output)
    self.command_table["network private-dns record-set txt list"] = RecordSetTXTList(loader=self, table_transformer=transform_privatedns_record_set_table_output)

    from .custom import RecordSetAShow, RecordSetAAAAShow, RecordSetCNAMEShow, RecordSetMXShow, RecordSetPTRShow, RecordSetSOAShow, RecordSetSRVShow, RecordSetTXTShow
    self.command_table["network private-dns record-set a show"] = RecordSetAShow(loader=self, table_transformer=transform_privatedns_record_set_table_output)
    self.command_table["network private-dns record-set aaaa show"] = RecordSetAAAAShow(loader=self, table_transformer=transform_privatedns_record_set_table_output)
    self.command_table["network private-dns record-set cname show"] = RecordSetCNAMEShow(loader=self, table_transformer=transform_privatedns_record_set_table_output)
    self.command_table["network private-dns record-set mx show"] = RecordSetMXShow(loader=self, table_transformer=transform_privatedns_record_set_table_output)
    self.command_table["network private-dns record-set ptr show"] = RecordSetPTRShow(loader=self, table_transformer=transform_privatedns_record_set_table_output)
    self.command_table["network private-dns record-set soa show"] = RecordSetSOAShow(loader=self, table_transformer=transform_privatedns_record_set_table_output)
    self.command_table["network private-dns record-set srv show"] = RecordSetSRVShow(loader=self, table_transformer=transform_privatedns_record_set_table_output)
    self.command_table["network private-dns record-set txt show"] = RecordSetTXTShow(loader=self, table_transformer=transform_privatedns_record_set_table_output)

    from .custom import RecordSetAUpdate, RecordSetAAAAUpdate, RecordSetCNAMEUpdate, RecordSetMXUpdate, RecordSetPTRUpdate, RecordSetSRVUpdate, RecordSetTXTUpdate
    self.command_table["network private-dns record-set a update"] = RecordSetAUpdate(loader=self)
    self.command_table["network private-dns record-set aaaa update"] = RecordSetAAAAUpdate(loader=self)
    self.command_table["network private-dns record-set cname update"] = RecordSetCNAMEUpdate(loader=self)
    self.command_table["network private-dns record-set mx update"] = RecordSetMXUpdate(loader=self)
    self.command_table["network private-dns record-set ptr update"] = RecordSetPTRUpdate(loader=self)
    self.command_table["network private-dns record-set srv update"] = RecordSetSRVUpdate(loader=self)
    self.command_table["network private-dns record-set txt update"] = RecordSetTXTUpdate(loader=self)

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
