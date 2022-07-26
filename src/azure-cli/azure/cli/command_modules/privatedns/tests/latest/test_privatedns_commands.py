# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import os
import unittest
import time
import json

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, live_only)
from knack.log import get_logger
from knack.util import CLIError
from azure.core.exceptions import (HttpResponseError, ResourceNotFoundError)


logger = get_logger(__name__)
# pylint: disable=line-too-long
regexSubscription = '[0-9a-f]{{8}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{12}}'

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


def GeneratePrivateZoneName(self):
    self.kwargs['zone'] = self.create_random_name(
        "clitest.privatedns.com", length=35)


def GenerateVirtualNetworkName(self):
    self.kwargs['vnet'] = self.create_random_name(
        "clitestprivatednsvnet", length=35)


def GenerateVirtualNetworkLinkName(self):
    self.kwargs['link'] = self.create_random_name(
        "clitestprivatednslink", length=35)


def GenerateRecordSetName(self):
    self.kwargs['recordset'] = self.create_random_name(
        "clitestprivatednsrecordset", length=35)


def GeneratePrivateZoneArmId(self):
    return "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/privateDnsZones/{2}".format(
        regexSubscription, self.kwargs['rg'], self.kwargs['zone'])


def GenerateVirtualNetworkLinkArmId(self):
    return "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/privateDnsZones/{2}/virtualNetworkLinks/{3}".format(
        regexSubscription, self.kwargs['rg'], self.kwargs['zone'], self.kwargs['link'])


def GenerateVirtualNetworkArmId(self):
    return "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/virtualNetworks/{2}".format(
        regexSubscription, self.kwargs['rg'], self.kwargs['vnet'])


def GenerateRecordSetArmId(self):
    return "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/privateDnsZones/{2}/{3}/{4}".format(
        regexSubscription, self.kwargs['rg'], self.kwargs['zone'], self.kwargs['recordType'], self.kwargs['recordset'])


def GenerateTags(self):
    tagKey = self.create_random_name("tagKey", length=15)
    tagVal = self.create_random_name("tagVal", length=15)
    self.kwargs['tags'] = "{0}={1}".format(tagKey, tagVal)
    return tagKey, tagVal


class BaseScenarioTests(ScenarioTest):

    def _Validate_Zones(self, expectedZones, actualZones):
        result = all(zone in actualZones for zone in expectedZones)
        self.check(result, True)

    def _Create_PrivateZones(self, numOfZones=2):
        createdZones = []
        for num in range(numOfZones):
            createdZones.append(self._Create_PrivateZone())
        createdZones.sort(key=lambda x: x['name'])
        return createdZones

    def _Create_PrivateZone(self):
        GeneratePrivateZoneName(self)
        return self.cmd('az network private-dns zone create -g {rg} -n {zone}', checks=[
            self.check('name', '{zone}'),
            self.check_pattern('id', GeneratePrivateZoneArmId(self)),
            self.check('location', 'global'),
            self.check('type', 'Microsoft.Network/privateDnsZones'),
            self.exists('etag'),
            self.check('tags', None),
            self.check('provisioningState', 'Succeeded'),
            self.greater_than('maxNumberOfRecordSets', 0),
            self.greater_than('maxNumberOfVirtualNetworkLinks', 0),
            self.greater_than('maxNumberOfVirtualNetworkLinksWithRegistration', 0),
            self.check('numberOfRecordSets', 1),
            self.check('numberOfVirtualNetworkLinks', 0),
            self.check('numberOfVirtualNetworkLinksWithRegistration', 0),
        ]).get_output_in_json()

    def _Create_VirtualNetwork(self):
        GenerateVirtualNetworkName(self)
        return self.cmd('az network vnet create -g {rg} -n {vnet}', checks=[
            self.check('newVNet.name', '{vnet}'),
            self.check_pattern('newVNet.id', GenerateVirtualNetworkArmId(self))
        ]).get_output_in_json()

    def _Validate_Links(self, expectedLinks, actualLinks):
        result = all(link in actualLinks for link in expectedLinks)
        self.check(result, True)

    def _Create_VirtualNetworkLinks(self, numOfLinks=2):
        self._Create_PrivateZone()
        createdLinks = []
        for num in range(numOfLinks):
            createdLinks.append(
                self._Create_VirtualNetworkLink(createZone=False))
        createdLinks.sort(key=lambda x: x['name'])
        return createdLinks

    def _Create_VirtualNetworkLink(self, registrationEnabled=False, createZone=True):
        self.kwargs['registrationEnabled'] = registrationEnabled
        if createZone is True:
            self._Create_PrivateZone()
        self._Create_VirtualNetwork()
        GenerateVirtualNetworkLinkName(self)
        return self.cmd('az network private-dns link vnet create -g {rg} -n {link} -z {zone} -v {vnet} -e {registrationEnabled}', checks=[
            self.check('name', '{link}'),
            self.check_pattern('id', GenerateVirtualNetworkLinkArmId(self)),
            self.check('location', 'global'),
            self.check('type', 'Microsoft.Network/privateDnsZones/virtualNetworkLinks'),
            self.exists('etag'),
            self.check('tags', None),
            self.check_pattern('virtualNetwork.id', GenerateVirtualNetworkArmId(self)),
            self.check('registrationEnabled', '{registrationEnabled}'),
            self.check('provisioningState', 'Succeeded'),
            self.check_pattern('virtualNetworkLinkState', 'InProgress|Completed')
        ]).get_output_in_json()

    def _RecordType_To_FunctionName(self, key, operation):
        type_dict = {
            'a': {'Create': '_Create_ARecord', 'Delete': '_Delete_ARecord'},
            'aaaa': {'Create': '_Create_AAAARecord', 'Delete': '_Delete_AAAARecord'},
            'cname': {'Create': '_Create_CNAMERecord', 'Delete': '_Delete_CNAMERecord'},
            'mx': {'Create': '_Create_MXRecord', 'Delete': '_Delete_MXRecord'},
            'ptr': {'Create': '_Create_PTRRecord', 'Delete': '_Delete_PTRRecord'},
            'srv': {'Create': '_Create_SRVRecord', 'Delete': '_Delete_SRVRecord'},
            'txt': {'Create': '_Create_TXTRecord', 'Delete': '_Delete_TXTRecord'},
        }
        return type_dict[key.lower()][operation]

    def _Create_RecordSet(self, recordType, zoneName):
        self.kwargs['recordType'] = recordType.lower()
        self.kwargs['zone'] = zoneName
        GenerateRecordSetName(self)
        self.cmd('az network private-dns record-set {recordType} create -g {rg} -n {recordset} -z {zone}', checks=[
            self.check('name', '{recordset}'),
            self.check_pattern('id', GenerateRecordSetArmId(self)),
            self.check_pattern('type', 'Microsoft.Network/privateDnsZones/{recordType}'),
            self.exists('etag'),
            self.check('fqdn', '{recordset}.{zone}.'),
            self.check('metadata', None),
            self.check('isAutoRegistered', False),
            self.check('ttl', 3600)
        ]).get_output_in_json()
        return getattr(self, self._RecordType_To_FunctionName(recordType, 'Create'))(self.kwargs['recordset'], zoneName)

    def _Create_ARecord(self, recordset, zone, arecord='10.0.0.1'):
        self.kwargs['recordset'] = recordset
        self.kwargs['zone'] = zone
        self.kwargs['arecord'] = arecord
        recordsetResult = self.cmd('az network private-dns record-set a add-record -g {rg} -n {recordset} -z {zone} -a {arecord}', checks=[
            self.check('name', '{recordset}')
        ]).get_output_in_json()
        self.assertTrue(arecord in [o['ipv4Address'] for o in recordsetResult.get('aRecords')])
        return recordsetResult

    def _Create_AAAARecord(self, recordset, zone, aaaarecord='::1'):
        self.kwargs['recordset'] = recordset
        self.kwargs['zone'] = zone
        self.kwargs['aaaarecord'] = aaaarecord
        recordsetResult = self.cmd('az network private-dns record-set aaaa add-record -g {rg} -n {recordset} -z {zone} -a {aaaarecord}', checks=[
            self.check('name', '{recordset}')
        ]).get_output_in_json()
        self.assertTrue(aaaarecord in [o['ipv6Address'] for o in recordsetResult.get('aaaaRecords')])
        return recordsetResult

    def _Create_MXRecord(self, recordset, zone, exchange='ex.chan.ge', preference=1):
        self.kwargs['recordset'] = recordset
        self.kwargs['zone'] = zone
        self.kwargs['exchange'] = exchange
        self.kwargs['preference'] = preference
        recordsetResult = self.cmd('az network private-dns record-set mx add-record -g {rg} -n {recordset} -z {zone} -e {exchange} -p {preference}', checks=[
            self.check('name', '{recordset}')
        ]).get_output_in_json()
        self.assertTrue(exchange in [o['exchange'] for o in recordsetResult.get('mxRecords')])
        self.assertTrue(preference in [o['preference'] for o in recordsetResult.get('mxRecords')])
        return recordsetResult

    def _Create_PTRRecord(self, recordset, zone, ptrdname='ptrd.name'):
        self.kwargs['recordset'] = recordset
        self.kwargs['zone'] = zone
        self.kwargs['ptrdname'] = ptrdname
        recordsetResult = self.cmd('az network private-dns record-set ptr add-record -g {rg} -n {recordset} -z {zone} -d {ptrdname}', checks=[
            self.check('name', '{recordset}')
        ]).get_output_in_json()
        self.assertTrue(ptrdname in [o['ptrdname'] for o in recordsetResult.get('ptrRecords')])
        return recordsetResult

    def _Create_SRVRecord(self, recordset, zone, target='targ.et'):
        self.kwargs['recordset'] = recordset
        self.kwargs['zone'] = zone
        self.kwargs['port'] = 120
        self.kwargs['priority'] = 1
        self.kwargs['target'] = target
        self.kwargs['weight'] = 5
        recordsetResult = self.cmd('az network private-dns record-set srv add-record -g {rg} -n {recordset} -z {zone} -r {port} -p {priority} -t {target} -w {weight}', checks=[
            self.check('name', '{recordset}'),
            self.check('srvRecords[0].port', '{port}'),
            self.check('srvRecords[0].priority', '{priority}'),
            self.check('srvRecords[0].weight', '{weight}')
        ]).get_output_in_json()
        self.assertTrue(target in [o['target'] for o in recordsetResult.get('srvRecords')])
        return recordsetResult

    def _Create_TXTRecord(self, recordset, zone, txtrecord='txt record'):
        self.kwargs['recordset'] = recordset
        self.kwargs['zone'] = zone
        self.kwargs['txtrecord'] = txtrecord
        recordsetResult = self.cmd('az network private-dns record-set txt add-record -g {rg} -n {recordset} -z {zone} -v "{txtrecord}"', checks=[
            self.check('name', '{recordset}')
        ]).get_output_in_json()
        self.assertTrue(txtrecord in [o['value'][0] for o in recordsetResult.get('txtRecords')])
        return recordsetResult

    def _Create_CNAMERecord(self, recordset, zone, cname='clitestcname'):
        self.kwargs['recordset'] = recordset
        self.kwargs['zone'] = zone
        self.kwargs['cname'] = cname
        recordsetResult = self.cmd('az network private-dns record-set cname set-record -g {rg} -n {recordset} -z {zone} -c {cname}', checks=[
            self.check('name', '{recordset}')
        ]).get_output_in_json()
        self.assertTrue(cname == recordsetResult.get('cnameRecord').get('cname'))
        return recordsetResult

    def _Update_RecordSet(self, recordset, recordType, zoneName, etag=None):
        self.kwargs['recordset'] = recordset
        self.kwargs['recordType'] = recordType.lower()
        self.kwargs['zone'] = zoneName
        tagKey, tagVal = GenerateTags(self)
        update_cmd = 'az network private-dns record-set {recordType} update -g {rg} -n {recordset} -z {zone} --metadata {tags}'
        if etag is not None:
            self.kwargs['etag'] = etag
            update_cmd = update_cmd + " --if-match {etag}"
        return self.cmd(update_cmd, checks=[
            self.check('name', '{recordset}'),
            self.check('metadata.{}'.format(tagKey), tagVal)
        ]).get_output_in_json()

    def _Show_RecordSet(self, recordset, recordType, zoneName, etag=None):
        self.kwargs['recordset'] = recordset
        self.kwargs['recordType'] = recordType.lower()
        self.kwargs['zone'] = zoneName
        show_cmd = 'az network private-dns record-set {recordType} show -g {rg} -n {recordset} -z {zone}'
        return self.cmd(show_cmd, checks=[
            self.check('name', '{recordset}')
        ]).get_output_in_json()

    def _List_RecordSet(self, recordType, zoneName, etag=None):
        self.kwargs['recordType'] = recordType.lower()
        self.kwargs['zone'] = zoneName
        list_cmd = 'az network private-dns record-set {recordType} list -g {rg} -z {zone}'
        return self.cmd(list_cmd).get_output_in_json()

    def _Delete_ARecord(self, recordset, zone, arecord='10.0.0.1'):
        self.kwargs['recordset'] = recordset
        self.kwargs['zone'] = zone
        self.kwargs['arecord'] = arecord
        recordsetResult = self.cmd('az network private-dns record-set a remove-record -g {rg} -n {recordset} -z {zone} -a {arecord} --keep-empty-record-set', checks=[
            self.check('name', '{recordset}')
        ]).get_output_in_json()
        self.assertTrue(arecord not in [o['ipv4Address'] for o in recordsetResult.get('aRecords', [])])
        return recordsetResult

    def _Delete_AAAARecord(self, recordset, zone, aaaarecord='::1'):
        self.kwargs['recordset'] = recordset
        self.kwargs['zone'] = zone
        self.kwargs['aaaarecord'] = aaaarecord
        recordsetResult = self.cmd('az network private-dns record-set aaaa remove-record -g {rg} -n {recordset} -z {zone} -a {aaaarecord} --keep-empty-record-set', checks=[
            self.check('name', '{recordset}')
        ]).get_output_in_json()
        self.assertTrue(aaaarecord not in [o['ipv6Address'] for o in recordsetResult.get('aaaaRecords', [])])
        return recordsetResult

    def _Delete_MXRecord(self, recordset, zone, exchange='ex.chan.ge', preference=1):
        self.kwargs['recordset'] = recordset
        self.kwargs['zone'] = zone
        self.kwargs['exchange'] = exchange
        self.kwargs['preference'] = preference
        recordsetResult = self.cmd('az network private-dns record-set mx remove-record -g {rg} -n {recordset} -z {zone} -e {exchange} -p {preference} --keep-empty-record-set', checks=[
            self.check('name', '{recordset}')
        ]).get_output_in_json()
        self.assertTrue(exchange not in [o['exchange'] for o in recordsetResult.get('mxRecords', [])])
        self.assertTrue(preference not in [o['preference'] for o in recordsetResult.get('mxRecords', [])])
        return recordsetResult

    def _Delete_PTRRecord(self, recordset, zone, ptrdname='ptrd.name'):
        self.kwargs['recordset'] = recordset
        self.kwargs['zone'] = zone
        self.kwargs['ptrdname'] = ptrdname
        recordsetResult = self.cmd('az network private-dns record-set ptr remove-record -g {rg} -n {recordset} -z {zone} -d {ptrdname} --keep-empty-record-set', checks=[
            self.check('name', '{recordset}')
        ]).get_output_in_json()
        self.assertTrue(ptrdname not in [o['ptrdname'] for o in recordsetResult.get('ptrRecords', [])])
        return recordsetResult

    def _Delete_SRVRecord(self, recordset, zone, target='targ.et'):
        self.kwargs['recordset'] = recordset
        self.kwargs['zone'] = zone
        self.kwargs['port'] = 120
        self.kwargs['priority'] = 1
        self.kwargs['target'] = target
        self.kwargs['weight'] = 5
        recordsetResult = self.cmd('az network private-dns record-set srv remove-record -g {rg} -n {recordset} -z {zone} -r {port} -p {priority} -t {target} -w {weight} --keep-empty-record-set', checks=[
            self.check('name', '{recordset}')
        ]).get_output_in_json()
        self.assertTrue(target not in [o['target'] for o in recordsetResult.get('srvRecords', [])])
        return recordsetResult

    def _Delete_TXTRecord(self, recordset, zone, txtrecord='txt record'):
        self.kwargs['recordset'] = recordset
        self.kwargs['zone'] = zone
        self.kwargs['txtrecord'] = txtrecord
        recordsetResult = self.cmd('az network private-dns record-set txt remove-record -g {rg} -n {recordset} -z {zone} -v "{txtrecord}" --keep-empty-record-set', checks=[
            self.check('name', '{recordset}')
        ]).get_output_in_json()
        self.assertTrue(txtrecord not in [o['value'][0] for o in recordsetResult.get('txtRecords', [])])
        return recordsetResult

    def _Delete_CNAMERecord(self, recordset, zone, cname='clitestcname'):
        self.kwargs['recordset'] = recordset
        self.kwargs['zone'] = zone
        self.kwargs['cname'] = cname
        recordsetResult = self.cmd('az network private-dns record-set cname remove-record -g {rg} -n {recordset} -z {zone} -c {cname} --keep-empty-record-set', checks=[
            self.check('name', '{recordset}')
        ]).get_output_in_json()
        self.assertTrue(cname != recordsetResult.get('cnameRecord', {}).get('cname', ''))
        return recordsetResult

    def _Delete_RecordSet(self, recordset, recordType, zoneName, etag=None):
        self.kwargs['recordset'] = recordset
        self.kwargs['recordType'] = recordType.lower()
        self.kwargs['zone'] = zoneName
        getattr(self, self._RecordType_To_FunctionName(recordType, 'Delete'))(recordset, zoneName)
        self.cmd('az network private-dns record-set {recordType} delete -g {rg} -n {recordset} -z {zone} -y')


class PrivateDnsZonesTests(BaseScenarioTests):

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PutZone_ZoneNotExists_ExpectZoneCreated(self, resource_group):
        self._Create_PrivateZone()

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PutZone_ZoneNotExistsWithTags_ExpectZoneCreatedWithTags(self, resource_group):
        GeneratePrivateZoneName(self)
        tagKey, tagVal = GenerateTags(self)
        self.cmd('az network private-dns zone create -g {rg} -n {zone} --tags {tags}', checks=[
            self.check('name', '{zone}'),
            self.check('tags.{}'.format(tagKey), tagVal),
            self.check('provisioningState', 'Succeeded')
        ])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PutZone_ZoneExistsIfNoneMatchFailure_ExpectError(self, resource_group):
        self._Create_PrivateZone()
        with self.assertRaisesRegex(HttpResponseError, 'PreconditionFailed'):
            self.cmd('az network private-dns zone create -g {rg} -n {zone}')

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PatchZone_ZoneExistsIfMatchSuccess_ExpectZoneUpdated(self, resource_group):
        zoneCreated = self._Create_PrivateZone()
        self.kwargs['etag'] = zoneCreated['etag']
        self.cmd('az network private-dns zone update -g {rg} -n {zone} --if-match {etag}', checks=[
            self.check('name', '{zone}'),
            self.check('provisioningState', 'Succeeded')
        ])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PatchZone_ZoneExistsIfMatchFailure_ExpectError(self, resource_group):
        self._Create_PrivateZone()
        self.kwargs['etag'] = self.create_guid()
        with self.assertRaisesRegex(HttpResponseError, 'etag mismatch'):
            self.cmd('az network private-dns zone update -g {rg} -n {zone} --if-match {etag}')

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PatchZone_ZoneExistsAddTags_ExpectTagsAdded(self, resource_group):
        self._Create_PrivateZone()
        tagKey, tagVal = GenerateTags(self)
        self.cmd('az network private-dns zone update -g {rg} -n {zone} --tags {tags}', checks=[
            self.check('name', '{zone}'),
            self.check('tags.{}'.format(tagKey), tagVal),
            self.check('provisioningState', 'Succeeded')
        ])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PatchZone_ZoneExistsChangeTags_ExpectTagsChanged(self, resource_group):
        GeneratePrivateZoneName(self)
        tagKey, tagVal = GenerateTags(self)
        self.cmd('az network private-dns zone create -g {rg} -n {zone} --tags {tags}', checks=[
            self.check('name', '{zone}'),
            self.check('tags.{}'.format(tagKey), tagVal),
            self.check('provisioningState', 'Succeeded')
        ])
        tagKey, tagVal = GenerateTags(self)
        self.cmd('az network private-dns zone update -g {rg} -n {zone} --tags {tags}', checks=[
            self.check('name', '{zone}'),
            self.check('tags.{}'.format(tagKey), tagVal),
            self.check('provisioningState', 'Succeeded')
        ])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PatchZone_ZoneExistsRemoveTags_ExpectTagsRemoved(self, resource_group):
        GeneratePrivateZoneName(self)
        tagKey, tagVal = GenerateTags(self)
        self.cmd('az network private-dns zone create -g {rg} -n {zone} --tags {tags}', checks=[
            self.check('name', '{zone}'),
            self.check('tags.{}'.format(tagKey), tagVal),
            self.check('provisioningState', 'Succeeded')
        ])
        self.cmd('az network private-dns zone update -g {rg} -n {zone} --tags ""', checks=[
            self.check('name', '{zone}'),
            self.check('tags', '{{}}'),
            self.check('provisioningState', 'Succeeded')
        ])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PatchZone_ZoneNotExists_ExpectError(self, resource_group):
        GeneratePrivateZoneName(self)
        with self.assertRaisesRegex(ResourceNotFoundError, 'ResourceNotFound'):
            self.cmd('az network private-dns zone update -g {rg} -n {zone}')

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PatchZone_ZoneExistsEmptyRequest_ExpectNoError(self, resource_group):
        self._Create_PrivateZone()
        self.cmd('az network private-dns zone update -g {rg} -n {zone}', checks=[
            self.check('name', '{zone}'),
            self.check('provisioningState', 'Succeeded')
        ])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_GetZone_ZoneExists_ExpectZoneRetrieved(self, resource_group):
        self._Create_PrivateZone()
        self.cmd('az network private-dns zone show -g {rg} -n {zone}', checks=[
            self.check('name', '{zone}'),
            self.check_pattern('id', GeneratePrivateZoneArmId(self)),
            self.check('provisioningState', 'Succeeded')
        ])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_GetZone_ZoneNotExists_ExpectError(self, resource_group):
        GeneratePrivateZoneName(self)
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az network private-dns zone show -g {rg} -n {zone}')

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_ListZonesInSubscription_MultipleZonesPresent_ExpectMultipleZonesRetrieved(self, resource_group):
        expectedZones = self._Create_PrivateZones(numOfZones=2)
        returnedZones = self.cmd('az network private-dns zone list', checks=[
            self.greater_than('length(@)', 1)
        ]).get_output_in_json()
        self._Validate_Zones(expectedZones, returnedZones)

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_ListZonesInResourceGroup_MultipleZonesPresent_ExpectMultipleZonesRetrieved(self, resource_group):
        expectedZones = self._Create_PrivateZones(numOfZones=2)
        returnedZones = self.cmd('az network private-dns zone list -g {rg}', checks=[
            self.check('length(@)', 2)
        ]).get_output_in_json()
        self._Validate_Zones(expectedZones, returnedZones)

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_ListZonesInResourceGroup_NoZonesPresent_ExpectNoZonesRetrieved(self, resource_group):
        self.cmd('az network private-dns zone list -g {rg}', checks=[
            self.is_empty()
        ])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_DeleteZone_ZoneExists_ExpectZoneDeleted(self, resource_group):
        self._Create_PrivateZone()
        self.cmd('az network private-dns zone delete -g {rg} -n {zone} -y')

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_DeleteZone_ZoneNotExists_ExpectNoError(self, resource_group):
        GeneratePrivateZoneName(self)
        self.cmd('az network private-dns zone delete -g {rg} -n {zone} -y')


class PrivateDnsLinksTests(BaseScenarioTests):

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PutLink_LinkNotExistsWithoutRegistration_ExpectLinkCreated(self, resource_group):
        self._Create_VirtualNetworkLink()

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PutLink_LinkNotExistsWithRegistration_ExpectLinkCreated(self, resource_group):
        self._Create_VirtualNetworkLink(registrationEnabled=True)

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PutLink_LinkExistsIfNoneMatchFailure_ExpectError(self, resource_group):
        self._Create_VirtualNetworkLink()
        with self.assertRaisesRegex(HttpResponseError, 'PreconditionFailed'):
            self.cmd('az network private-dns link vnet create -g {rg} -n {link} -z {zone} -v {vnet} -e {registrationEnabled}')

    @live_only()    # live only until https://github.com/Azure/azure-python-devtools/pull/58 fixed
    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PatchLink_LinkExistsIfMatchSuccess_ExpectLinkUpdated(self, resource_group):
        linkCreated = self._Create_VirtualNetworkLink()
        self.kwargs['etag'] = linkCreated['etag']
        cmd = "az network private-dns link vnet update -g {rg} -n {link} -z {zone} --if-match '{etag}'"
        self.cmd(cmd, checks=[
            self.check('name', '{link}'),
            self.check('provisioningState', 'Succeeded')
        ])

    @live_only()    # live only until https://github.com/Azure/azure-python-devtools/pull/58 fixed
    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PatchLink_LinkExistsIfMatchFailure_ExpectError(self, resource_group):
        self._Create_VirtualNetworkLink()
        self.kwargs['etag'] = self.create_guid()
        cmd = "az network private-dns link vnet update -g {rg} -n {link} -z {zone} --if-match '{etag}'"
        with self.assertRaisesRegex(HttpResponseError, 'etag mismatch'):
            self.cmd(cmd)

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PatchLink_ZoneNotExists_ExpectError(self, resource_group):
        GeneratePrivateZoneName(self)
        GenerateVirtualNetworkLinkName(self)
        with self.assertRaisesRegex(ResourceNotFoundError, 'ResourceNotFound'):
            self.cmd('az network private-dns link vnet update -g {rg} -n {link} -z {zone}')

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PatchLink_LinkNotExists_ExpectError(self, resource_group):
        self._Create_PrivateZone()
        GenerateVirtualNetworkLinkName(self)
        with self.assertRaisesRegex(ResourceNotFoundError, 'ResourceNotFound'):
            self.cmd('az network private-dns link vnet update -g {rg} -n {link} -z {zone}')

    @live_only()    # live only until https://github.com/Azure/azure-python-devtools/pull/58 fixed
    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PatchLink_LinkExistsEmptyRequest_ExpectNoError(self, resource_group):
        self._Create_VirtualNetworkLink()
        self.cmd('az network private-dns link vnet update -g {rg} -n {link} -z {zone}', checks=[
            self.check('name', '{link}'),
            self.check('provisioningState', 'Succeeded')
        ])

    @live_only()    # live only until https://github.com/Azure/azure-python-devtools/pull/58 fixed
    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PatchLink_EnableRegistration_ExpectRegistrationEnabled(self, resource_group):
        self._Create_VirtualNetworkLink()
        self.kwargs['registrationEnabled'] = True
        self.cmd('az network private-dns link vnet update -g {rg} -n {link} -z {zone} -e {registrationEnabled}', checks=[
            self.check('name', '{link}'),
            self.check('registrationEnabled', '{registrationEnabled}'),
            self.check('provisioningState', 'Succeeded')
        ])

    @live_only()    # live only until https://github.com/Azure/azure-python-devtools/pull/58 fixed
    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PatchLink_DisableRegistration_ExpectRegistrationDisabled(self, resource_group):
        self._Create_VirtualNetworkLink(registrationEnabled=True)
        self.kwargs['registrationEnabled'] = False
        self.cmd('az network private-dns link vnet update -g {rg} -n {link} -z {zone} -e {registrationEnabled}', checks=[
            self.check('name', '{link}'),
            self.check('registrationEnabled', '{registrationEnabled}'),
            self.check('provisioningState', 'Succeeded')
        ])

    @live_only()    # live only until https://github.com/Azure/azure-python-devtools/pull/58 fixed
    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PatchLink_LinkExistsAddTags_ExpectTagsAdded(self, resource_group):
        self._Create_VirtualNetworkLink()
        tagKey, tagVal = GenerateTags(self)
        self.cmd('az network private-dns link vnet update -g {rg} -n {link} -z {zone} --tags {tags}', checks=[
            self.check('name', '{link}'),
            self.check('tags.{}'.format(tagKey), tagVal),
            self.check('provisioningState', 'Succeeded')
        ])

    @live_only()    # live only until https://github.com/Azure/azure-python-devtools/pull/58 fixed
    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PatchLink_LinkExistsChangeTags_ExpectTagsChanged(self, resource_group):
        self._Create_VirtualNetworkLink()
        tagKey, tagVal = GenerateTags(self)
        self.cmd('az network private-dns link vnet update -g {rg} -n {link} -z {zone} --tags {tags}', checks=[
            self.check('name', '{link}'),
            self.check('tags.{}'.format(tagKey), tagVal),
            self.check('provisioningState', 'Succeeded')
        ])
        tagKey, tagVal = GenerateTags(self)
        self.cmd('az network private-dns link vnet update -g {rg} -n {link} -z {zone} --tags {tags}', checks=[
            self.check('name', '{link}'),
            self.check('tags.{}'.format(tagKey), tagVal),
            self.check('provisioningState', 'Succeeded')
        ])

    @live_only()    # live only until https://github.com/Azure/azure-python-devtools/pull/58 fixed
    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PatchLink_LinkExistsRemoveTags_ExpectTagsRemoved(self, resource_group):
        self._Create_VirtualNetworkLink()
        tagKey, tagVal = GenerateTags(self)
        self.cmd('az network private-dns link vnet update -g {rg} -n {link} -z {zone} --tags {tags}', checks=[
            self.check('name', '{link}'),
            self.check('tags.{}'.format(tagKey), tagVal),
            self.check('provisioningState', 'Succeeded')
        ])
        self.cmd('az network private-dns link vnet update -g {rg} -n {link} -z {zone} --tags ""', checks=[
            self.check('name', '{link}'),
            self.check('tags', '{{}}'),
            self.check('provisioningState', 'Succeeded')
        ])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_GetLink_ZoneNotExists_ExpectError(self, resource_group):
        GeneratePrivateZoneName(self)
        GenerateVirtualNetworkLinkName(self)
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az network private-dns link vnet show -g {rg} -n {link} -z {zone}')

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_GetLink_LinkNotExists_ExpectError(self, resource_group):
        self._Create_PrivateZone()
        GenerateVirtualNetworkLinkName(self)
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az network private-dns link vnet show -g {rg} -n {link} -z {zone}')

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_GetLink_LinkExists_ExpectLinkRetrieved(self, resource_group):
        self._Create_VirtualNetworkLink()
        self.cmd('az network private-dns link vnet show -g {rg} -n {link} -z {zone}', checks=[
            self.check('name', '{link}'),
            self.check_pattern('id', GenerateVirtualNetworkLinkArmId(self)),
            self.check('provisioningState', 'Succeeded')
        ])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_ListLinks_NoLinksPresent_ExpectNoLinksRetrieved(self, resource_group):
        self._Create_PrivateZone()
        self.cmd('az network private-dns link vnet list -g {rg} -z {zone}', checks=[
            self.is_empty()
        ])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_ListLinks_MultipleLinksPresent_ExpectMultipleLinksRetrieved(self, resource_group):
        expectedLinks = self._Create_VirtualNetworkLinks(numOfLinks=2)
        returnedLinks = self.cmd('az network private-dns link vnet list -g {rg} -z {zone}', checks=[
            self.check('length(@)', 2)
        ]).get_output_in_json()
        self._Validate_Links(expectedLinks, returnedLinks)

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_DeleteLink_ZoneNotExists_ExpectNoError(self, resource_group):
        GeneratePrivateZoneName(self)
        GenerateVirtualNetworkLinkName(self)
        self.cmd('az network private-dns link vnet delete -g {rg} -n {link} -z {zone} -y')

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_DeleteLink_LinkNotExists_ExpectNoError(self, resource_group):
        self._Create_PrivateZone()
        GenerateVirtualNetworkLinkName(self)
        self.cmd('az network private-dns link vnet delete -g {rg} -n {link} -z {zone} -y')

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_DeleteLink_LinkExists_ExpectLinkDeleted(self, resource_group):
        self._Create_VirtualNetworkLink()
        self.cmd('az network private-dns link vnet delete -g {rg} -n {link} -z {zone} -y')


class PrivateDnsRecordSetsTests(BaseScenarioTests):

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PutRecordSet_ZoneNotExists_ExpectError(self, resource_group):
        GeneratePrivateZoneName(self)
        GenerateRecordSetName(self)
        with self.assertRaisesRegex(ResourceNotFoundError, 'ResourceNotFound'):
            self.cmd('az network private-dns record-set a create -g {rg} -n {recordset} -z {zone}')

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PutRecordSet_IfNoneMatchFailure_ExpectError(self, resource_group):
        zone = self._Create_PrivateZone()
        self._Create_RecordSet('a', zone['name'])
        with self.assertRaisesRegex(HttpResponseError, 'PreconditionFailed'):
            self.cmd('az network private-dns record-set {recordType} create -g {rg} -n {recordset} -z {zone}')

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PatchRecordSet_IfMatchSuccess_ExpectRecordSetUpdated(self, resource_group):
        zone = self._Create_PrivateZone()
        recordset = self._Create_RecordSet('a', zone['name'])
        self._Update_RecordSet(recordset['name'], 'a', zone['name'], recordset['etag'])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PatchRecordSet_IfMatchFailure_ExpectError(self, resource_group):
        zone = self._Create_PrivateZone()
        recordset = self._Create_RecordSet('a', zone['name'])
        etag = self.create_guid()
        with self.assertRaisesRegex(HttpResponseError, 'PreconditionFailed'):
            self._Update_RecordSet(recordset['name'], 'a', zone['name'], etag)

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_GetRecordSet_SoaRecord_ExpectRecordSetRetrieved(self, resource_group):
        self._Create_PrivateZone()
        self.cmd('az network private-dns record-set soa show -g {rg} -z {zone}', checks=[
            self.check('name', '@'),
            self.check('type', 'Microsoft.Network/privateDnsZones/SOA'),
            self.exists('soaRecord.host'),
            self.exists('soaRecord.email'),
            self.exists('soaRecord.serialNumber'),
            self.exists('soaRecord.refreshTime'),
            self.exists('soaRecord.retryTime'),
            self.exists('soaRecord.expireTime'),
            self.exists('soaRecord.minimumTtl')
        ])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PatchRecordSet_SoaRecord_ExpectRecordSetUpdated(self, resource_group):
        self._Create_PrivateZone()
        self.kwargs['email'] = 'example.hostmaster.com'
        self.kwargs['expireTime'] = 1
        self.kwargs['minimumTtl'] = 2
        self.kwargs['retryTime'] = 3
        self.kwargs['refreshTime'] = 4
        self.kwargs['serialNumber'] = 5
        self.kwargs['host'] = 'clitest.hostmaster.com'
        self.cmd('az network private-dns record-set soa update -g {rg} -z {zone} \
            -e {email} -x {expireTime} -m {minimumTtl} -f {refreshTime} -r {retryTime} -s {serialNumber}', checks=[
            self.check('name', '@'),
            self.check('type', 'Microsoft.Network/privateDnsZones/SOA'),
            self.check('soaRecord.email', '{email}'),
            self.check('soaRecord.refreshTime', '{refreshTime}'),
            self.check('soaRecord.retryTime', '{retryTime}'),
            self.check('soaRecord.expireTime', '{expireTime}'),
            self.check('soaRecord.minimumTtl', '{minimumTtl}')
        ])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PatchRecordSet_AddMetadata_ExpectMetadataAdded(self, resource_group):
        zone = self._Create_PrivateZone()
        self._Create_RecordSet('a', zone['name'])
        tagKey, tagVal = GenerateTags(self)
        self.cmd('az network private-dns record-set a update -g {rg} -n {recordset} -z {zone} --metadata {tags}', checks=[
            self.check('name', '{recordset}'),
            self.check('metadata.{}'.format(tagKey), tagVal)
        ])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PatchRecordSet_ChangeMetadata_ExpectMetadataChanged(self, resource_group):
        zone = self._Create_PrivateZone()
        self._Create_RecordSet('a', zone['name'])
        tagKey, tagVal = GenerateTags(self)
        self.cmd('az network private-dns record-set a update -g {rg} -n {recordset} -z {zone} --metadata {tags}', checks=[
            self.check('name', '{recordset}'),
            self.check('metadata.{}'.format(tagKey), tagVal)
        ])
        tagKey, tagVal = GenerateTags(self)
        self.cmd('az network private-dns record-set a update -g {rg} -n {recordset} -z {zone} --metadata {tags}', checks=[
            self.check('name', '{recordset}'),
            self.check('metadata.{}'.format(tagKey), tagVal)
        ])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_PatchRecordSet_RemoveMetadata_ExpectMetadataRemoved(self, resource_group):
        zone = self._Create_PrivateZone()
        self._Create_RecordSet('a', zone['name'])
        tagKey, tagVal = GenerateTags(self)
        self.cmd('az network private-dns record-set a update -g {rg} -n {recordset} -z {zone} --metadata {tags}', checks=[
            self.check('name', '{recordset}'),
            self.check('metadata.{}'.format(tagKey), tagVal)
        ])
        self.cmd('az network private-dns record-set a update -g {rg} -n {recordset} -z {zone} --metadata ""', checks=[
            self.check('name', '{recordset}'),
            self.check('metadata', '{{}}')
        ])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_CrudRecordSet_ARecord_ExpectCrudSuccessful(self, resource_group):
        zone = self._Create_PrivateZone()
        recordset = self._Create_RecordSet('a', zone['name'])
        recordset = self._Update_RecordSet(recordset['name'], 'a', zone['name'])
        recordset = self._Create_ARecord(recordset['name'], zone['name'], '10.0.0.4')
        recordsetResult = self._Show_RecordSet(recordset['name'], 'a', zone['name'])
        self.assertTrue(all(record in recordsetResult.get('aRecords') for record in recordset.get('aRecords')))
        recordset = self._Delete_ARecord(recordset['name'], zone['name'], '10.0.0.4')
        self._Delete_RecordSet(recordset['name'], 'a', zone['name'])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_CrudRecordSet_AAAARecord_ExpectCrudSuccessful(self, resource_group):
        zone = self._Create_PrivateZone()
        recordset = self._Create_RecordSet('aaaa', zone['name'])
        recordset = self._Update_RecordSet(recordset['name'], 'aaaa', zone['name'])
        recordset = self._Create_AAAARecord(recordset['name'], zone['name'], '2001::1')
        recordsetResult = self._Show_RecordSet(recordset['name'], 'aaaa', zone['name'])
        self.assertTrue(all(record in recordsetResult.get('aaaaRecords') for record in recordset.get('aaaaRecords')))
        recordset = self._Delete_AAAARecord(recordset['name'], zone['name'], '2001::1')
        self._Delete_RecordSet(recordset['name'], 'aaaa', zone['name'])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_CrudRecordSet_MXRecord_ExpectCrudSuccessful(self, resource_group):
        zone = self._Create_PrivateZone()
        recordset = self._Create_RecordSet('mx', zone['name'])
        recordset = self._Update_RecordSet(recordset['name'], 'mx', zone['name'])
        recordset = self._Create_MXRecord(recordset['name'], zone['name'], 'ex.change.new', preference=2)
        recordsetResult = self._Show_RecordSet(recordset['name'], 'mx', zone['name'])
        self.assertTrue(all(record in recordsetResult.get('mxRecords') for record in recordset.get('mxRecords')))
        recordset = self._Delete_MXRecord(recordset['name'], zone['name'], 'ex.change.new', preference=2)
        self._Delete_RecordSet(recordset['name'], 'mx', zone['name'])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_CrudRecordSet_PTRRecord_ExpectCrudSuccessful(self, resource_group):
        zone = self._Create_PrivateZone()
        recordset = self._Create_RecordSet('ptr', zone['name'])
        recordset = self._Update_RecordSet(recordset['name'], 'ptr', zone['name'])
        recordset = self._Create_PTRRecord(recordset['name'], zone['name'], 'ptrd.name.new')
        recordsetResult = self._Show_RecordSet(recordset['name'], 'ptr', zone['name'])
        self.assertTrue(all(record in recordsetResult.get('ptrRecords') for record in recordset.get('ptrRecords')))
        recordset = self._Delete_PTRRecord(recordset['name'], zone['name'], 'ptrd.name.new')
        self._Delete_RecordSet(recordset['name'], 'ptr', zone['name'])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_CrudRecordSet_TXTRecord_ExpectCrudSuccessful(self, resource_group):
        zone = self._Create_PrivateZone()
        recordset = self._Create_RecordSet('txt', zone['name'])
        recordset = self._Update_RecordSet(recordset['name'], 'txt', zone['name'])
        recordset = self._Create_TXTRecord(recordset['name'], zone['name'], 'new txt record')
        recordsetResult = self._Show_RecordSet(recordset['name'], 'txt', zone['name'])
        self.assertTrue(all(record in recordsetResult.get('txtRecords') for record in recordset.get('txtRecords')))
        recordset = self._Delete_TXTRecord(recordset['name'], zone['name'], 'new txt record')
        self._Delete_RecordSet(recordset['name'], 'txt', zone['name'])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_CrudRecordSet_CNAMERecord_ExpectCrudSuccessful(self, resource_group):
        zone = self._Create_PrivateZone()
        recordset = self._Create_RecordSet('cname', zone['name'])
        recordset = self._Update_RecordSet(recordset['name'], 'cname', zone['name'])
        recordset = self._Create_CNAMERecord(recordset['name'], zone['name'], 'newclitestcname')
        recordsetResult = self._Show_RecordSet(recordset['name'], 'cname', zone['name'])
        self.assertTrue(recordsetResult.get('cnameRecord') == recordset.get('cnameRecord'))
        recordset = self._Delete_CNAMERecord(recordset['name'], zone['name'], 'newclitestcname')
        self._Delete_RecordSet(recordset['name'], 'cname', zone['name'])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_CrudRecordSet_SRVRecord_ExpectCrudSuccessful(self, resource_group):
        zone = self._Create_PrivateZone()
        recordset = self._Create_RecordSet('srv', zone['name'])
        recordset = self._Update_RecordSet(recordset['name'], 'srv', zone['name'])
        recordset = self._Create_SRVRecord(recordset['name'], zone['name'], 'newsrv.target')
        recordsetResult = self._Show_RecordSet(recordset['name'], 'srv', zone['name'])
        self.assertTrue(all(record in recordsetResult.get('srvRecords') for record in recordset.get('srvRecords')))
        recordset = self._Delete_SRVRecord(recordset['name'], zone['name'], 'newsrv.target')
        self._Delete_RecordSet(recordset['name'], 'srv', zone['name'])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_ListRecordSetsByType_NoRecordSetsPresent_ExpectNoRecordSetsRetrieved(self, resource_group):
        self._Create_PrivateZone()
        self.cmd('az network private-dns record-set a list -g {rg} -z {zone}', checks=[
            self.is_empty()
        ])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_ListRecordSetsByType_MultipleRecordSetsPresent_ExpectMultipleRecordSetsRetrieved(self, resource_group):
        zone = self._Create_PrivateZone()
        recordset1 = self._Create_RecordSet('a', zone['name'])
        recordset2 = self._Create_RecordSet('a', zone['name'])
        recordset3 = self._Create_RecordSet('a', zone['name'])
        recordset4 = self._Create_RecordSet('a', zone['name'])
        createdRecordsets = [recordset1, recordset2, recordset3, recordset4]
        self.cmd('az network private-dns record-set a list -g {rg} -z {zone}', checks=[
            self.check('length(@)', len(createdRecordsets))
        ]).get_output_in_json()

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_ListRecordSetsAcrossType_DefaultRecordSetPresent_ExpectDefaultRecordSetRetrieved(self, resource_group):
        self._Create_PrivateZone()
        self.cmd('az network private-dns record-set list -g {rg} -z {zone}', checks=[
            self.check('length(@)', 1),
            self.exists('@[0].soaRecord'),
            self.check('@[0].name', '@')
        ])

    @ResourceGroupPreparer(name_prefix='clitest_privatedns')
    def test_ListRecordSetsAcrossType_MultipleRecordSetsPresent_ExpectMultipleRecordSetsRetrieved(self, resource_group):
        zone = self._Create_PrivateZone()
        recordset1 = self._Create_RecordSet('a', zone['name'])
        recordset2 = self._Create_RecordSet('aaaa', zone['name'])
        recordset3 = self._Create_RecordSet('txt', zone['name'])
        recordset4 = self._Create_RecordSet('cname', zone['name'])
        recordset5 = self._Create_RecordSet('srv', zone['name'])
        recordset6 = self._Create_RecordSet('mx', zone['name'])
        recordset7 = self._Create_RecordSet('ptr', zone['name'])
        soaRecordset = self.cmd('az network private-dns record-set soa show -g {rg} -z {zone}').get_output_in_json()
        createdRecordsets = [recordset1, recordset2, recordset3, recordset4, recordset5, recordset6, recordset7, soaRecordset]
        self.cmd('az network private-dns record-set list -g {rg} -z {zone}', checks=[
            self.check('length(@)', len(createdRecordsets))
        ]).get_output_in_json()


# Running only live test because of this isue: Confusing error message if play count mismatches - https://github.com/kevin1024/vcrpy/issues/516
@live_only()
class PrivateDnsZoneImportTest(ScenarioTest):

    def _match_record(self, record_set, name, type):
        matches = [x for x in record_set if x['name'] == name and x['type'] == type]
        self.assertEqual(len(matches), 1)
        return matches[0]

    def _list_record_fqdns(self, val):
        return tuple([x['fqdn'] for x in val])

    def _check_records(self, records1, records2):
        self.assertEqual(self._list_record_fqdns(records1), self._list_record_fqdns(records2))
        for record in records1:
            record_match = self._match_record(records2, record['name'], record['type'])
            del record['etag']
            del record_match['etag']
            try:
                self.assertDictEqual(record, record_match)
            except AssertionError:
                raise

    def _test_PrivateDnsZone(self, zone_name, filename):
        """ This tests that a zone file can be imported, exported, and re-imported without any changes to the
            record sets. It does not test that the imported files meet any specific requirements. For that, run
            additional checks in the individual zone file tests.
        """
        self.kwargs.update({
            'zone': zone_name,
            'path': os.path.join(TEST_DIR, 'zone_files', filename),
            'export': os.path.join(TEST_DIR, 'zone_files', filename + '_export.txt')
        })
        # Import from zone file
        self.cmd('network private-dns zone import -n {zone} -g {rg} --file-name "{path}"')
        records1 = self.cmd('network private-dns record-set list -g {rg} -z {zone}').get_output_in_json()

        # Export zone file and delete the zone
        self.cmd('network private-dns zone export -g {rg} -n {zone} --file-name "{export}"')
        self.cmd('network private-dns zone delete -g {rg} -n {zone} -y')
        time.sleep(10)
        for i in range(5):
            try:
                # Reimport zone file and verify both record sets are equivalent
                self.cmd('network private-dns zone import -n {zone} -g {rg} --file-name "{export}"')
                break
            except:
                if i == 4:
                    raise
                time.sleep(10)

        records2 = self.cmd('network private-dns record-set list -g {rg} -z {zone}').get_output_in_json()

        # verify that each record in the original import is unchanged after export/re-import
        self._check_records(records1, records2)

    @ResourceGroupPreparer(name_prefix='test_Private_Dns_import_file_not_found')
    def test_Private_Dns_import_file_operation_error_linux(self, resource_group):
        import sys
        if sys.platform != 'linux':
            self.skipTest('This test should run on Linux platform')

        from azure.cli.core.azclierror import FileOperationError
        with self.assertRaisesRegex(FileOperationError, 'No such file: ') as e:
            self._test_PrivateDnsZone('404zone.com', 'non_existing_zone_description_file.txt')
            self.assertEqual(e.errno, 1)

        with self.assertRaisesRegex(FileOperationError, 'Is a directory: ') as e:
            self._test_PrivateDnsZone('404zone.com', '')
            self.assertEqual(e.errno, 1)

        with self.assertRaisesRegex(FileOperationError, 'Permission denied: ') as e:
            self._test_PrivateDnsZone('404zone.com', '/root/')
            self.assertEqual(e.errno, 1)

    @ResourceGroupPreparer(name_prefix='test_dns_import_file_operation_error_windows')
    def test_Private_Dns_import_file_operation_error_windows(self, resource_group):
        import sys
        if sys.platform != 'win32':
            self.skipTest('This test should run on Windows platform')

        from azure.cli.core.azclierror import FileOperationError
        with self.assertRaisesRegex(FileOperationError, 'No such file: ') as e:
            self._test_PrivateDnsZone('404zone.com', 'non_existing_zone_description_file.txt')
            self.assertEqual(e.errno, 1)

        # Difference with Linux platform while reading a directory
        with self.assertRaisesRegex(FileOperationError, 'Permission denied:') as e:
            self._test_PrivateDnsZone('404zone.com', '.')
            self.assertEqual(e.errno, 1)

    @ResourceGroupPreparer(name_prefix='cli_private_dns_zone1_import')
    def test_Private_Dns_Zone1_Import(self, resource_group):
        self._test_PrivateDnsZone('zone1.com', 'zone1.txt')

    @ResourceGroupPreparer(name_prefix='cli_private_dns_zone2_import')
    def test_Private_Dns_Zone2_Import(self, resource_group):
        self._test_PrivateDnsZone('zone2.com', 'zone2.txt')

    @ResourceGroupPreparer(name_prefix='cli_private_dns_zone3_import')
    def test_Private_Dns_Zone3_Import(self, resource_group):
        self._test_PrivateDnsZone('zone3.com', 'zone3.txt')

    @ResourceGroupPreparer(name_prefix='cli_private_dns_zone4_import')
    def test_Private_Dns_Zone4_Import(self, resource_group):
        self._test_PrivateDnsZone('zone4.com', 'zone4.txt')

    @ResourceGroupPreparer(name_prefix='cli_private_dns_zone5_import')
    def test_Private_Dns_Zone5_Import(self, resource_group):
        self._test_PrivateDnsZone('zone5.com', 'zone5.txt')

    @ResourceGroupPreparer(name_prefix='cli_private_dns_zone6_import')
    def test_Private_Dns_Zone6_Import(self, resource_group):
        self._test_PrivateDnsZone('zone6.com', 'zone6.txt')

    @ResourceGroupPreparer(name_prefix='cli_private_dns_zone7_import')
    def test_Private_Dns_Zone7_Import(self, resource_group):
        self._test_PrivateDnsZone('zone7.com', 'zone7.txt')

    @ResourceGroupPreparer(name_prefix='cli_private_dns_zone8_import')
    def test_Private_Dns_Zone8_Import(self, resource_group):
        self._test_PrivateDnsZone('zone8.com', 'zone8.txt')

    @ResourceGroupPreparer(name_prefix='cli_private_dns_zone_local_import')
    def test_Private_Dns_Zone_Local_Import(self, resource_group):
        self._test_PrivateDnsZone('zone.local', 'zone.local.txt')


if __name__ == '__main__':
    unittest.main()
