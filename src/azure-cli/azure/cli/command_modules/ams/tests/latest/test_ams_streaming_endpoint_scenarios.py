# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys

from azure.cli.core.util import CLIError
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
from azure.cli.command_modules.ams._test_utils import _get_test_data_file


class AmsStreamingEndpointsTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_streaming_endpoint_create_with_akamai_without_ips(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        streaming_endpoint_name = self.create_random_name(prefix="strep", length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'canadacentral',
            'streamingEndpointName': streaming_endpoint_name,
            'identifier': 'id1',
            'expiration': '2030-12-31T16:00:00-08:00',
            'base64Key': 'dGVzdGlkMQ==',
            'scaleUnits': 3
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams streaming-endpoint create -g {rg} -a {amsname} -n {streamingEndpointName} --scale-units {scaleUnits}', checks=[
            self.check('name', '{streamingEndpointName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('location', 'Canada Central'),
            self.check('scaleUnits', '{scaleUnits}')
        ])

        self.cmd('az ams streaming-endpoint akamai add -g {rg} -a {amsname} -n {streamingEndpointName} --identifier {identifier} --expiration {expiration} --base64-key {base64Key}', checks=[
            self.check('name', '{streamingEndpointName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('length(accessControl.akamai.akamaiSignatureHeaderAuthenticationKeyList)', 1)
        ])

        self.cmd('az ams streaming-endpoint akamai remove -g {rg} -a {amsname} -n {streamingEndpointName} --identifier {identifier}', checks=[
            self.check('name', '{streamingEndpointName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('length(accessControl.akamai.akamaiSignatureHeaderAuthenticationKeyList)', 0)
        ])

        self.cmd('az ams streaming-endpoint delete -g {rg} -a {amsname} -n {streamingEndpointName}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_streaming_endpoint_create_with_akamai(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        streaming_endpoint_name = self.create_random_name(prefix="strep", length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'northeurope',
            'streamingEndpointName': streaming_endpoint_name,
            'description': 'test streaming description',
            'maxCacheAge': 11,
            'scaleUnits': 4,
            'tags': 'foo=bar',
            'ips': '1.1.1.1 2.2.2.2',
            'clientAccessPolicy': self._normalize_filename(_get_test_data_file('clientAccessPolicy.xml')),
            'crossDomainPolicy': self._normalize_filename(_get_test_data_file('crossDomainPolicy.xml')),
            'identifier': 'id1',
            'expiration': '2030-12-31T16:00:00-08:00',
            'base64Key': 'dGVzdGlkMQ=='
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams streaming-endpoint create -g {rg} -a {amsname} -n {streamingEndpointName} --ips {ips} --description "{description}" --max-cache-age {maxCacheAge} --scale-units {scaleUnits} --tags "{tags}" --client-access-policy @"{clientAccessPolicy}" --cross-domain-policy @"{crossDomainPolicy}"', checks=[
            self.check('name', '{streamingEndpointName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('location', 'North Europe'),
            self.check('length(accessControl.ip.allow)', '2'),
            self.check('description', '{description}'),
            self.check('maxCacheAge', '{maxCacheAge}'),
            self.check('scaleUnits', '{scaleUnits}'),
            self.check('length(tags)', 1)
        ])

        self.cmd('az ams streaming-endpoint akamai add -g {rg} -a {amsname} -n {streamingEndpointName} --identifier {identifier} --expiration {expiration} --base64-key {base64Key}', checks=[
            self.check('name', '{streamingEndpointName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('length(accessControl.akamai.akamaiSignatureHeaderAuthenticationKeyList)', 1)
        ])

        self.cmd('az ams streaming-endpoint akamai remove -g {rg} -a {amsname} -n {streamingEndpointName} --identifier {identifier}', checks=[
            self.check('name', '{streamingEndpointName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('length(accessControl.akamai.akamaiSignatureHeaderAuthenticationKeyList)', 0)
        ])

        self.cmd('az ams streaming-endpoint delete -g {rg} -a {amsname} -n {streamingEndpointName}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_streaming_endpoint_update(self, storage_account_for_create):
        if sys.version_info.major == 2:  # azure-cli/issues/9386
            return
        amsname = self.create_random_name(prefix='ams', length=12)
        streaming_endpoint_name = self.create_random_name(prefix="strep", length=11)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'australiaeast',
            'streamingEndpointName': streaming_endpoint_name,
            'cdnProvider': 'StandardVerizon',
            'cdnProfile': 'testProfile',
            'description': 'test streaming description',
            'maxCacheAge': 11,
            'scaleUnits': 5,
            'tags': 'foo=bar',
            'clientAccessPolicy': self._normalize_filename(_get_test_data_file('clientAccessPolicy.xml')),
            'crossDomainPolicy': self._normalize_filename(_get_test_data_file('crossDomainPolicy.xml')),
            'ip': '4.4.4.4'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams streaming-endpoint create -g {rg} -a {amsname} -n {streamingEndpointName} --cdn-provider {cdnProvider} --cdn-profile {cdnProfile} --description "{description}" --max-cache-age {maxCacheAge} --scale-units {scaleUnits} --tags "{tags}" --client-access-policy @"{clientAccessPolicy}" --cross-domain-policy @"{crossDomainPolicy}"', checks=[
            self.check('name', '{streamingEndpointName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('location', 'Australia East'),
            self.check('cdnProvider', '{cdnProvider}'),
            self.check('cdnProfile', '{cdnProfile}'),
            self.check('description', '{description}'),
            self.check('maxCacheAge', '{maxCacheAge}'),
            self.check('scaleUnits', '{scaleUnits}'),
            self.check('length(tags)', 1)
        ])

        with self.assertRaises(CLIError):
            self.cmd('az ams streaming-endpoint update -g {rg} -a {amsname} -n {streamingEndpointName} --add access_control.ip.allow {ip}')

        self.kwargs.update({
            'streamingEndpointName': streaming_endpoint_name,
            'cdnProvider': 'PremiumVerizon',
            'cdnProfile': 'testProfile2',
            'description': 'test streaming description2',
            'maxCacheAge': 9,
            'tags': 'foo2=bar2 foo3=bar3',
            'clientAccessPolicy': self._normalize_filename(_get_test_data_file('clientAccessPolicy.xml')),
            'crossDomainPolicy': self._normalize_filename(_get_test_data_file('crossDomainPolicy.xml')),
            'ips': '1.1.1.1 2.2.2.2 192.168.0.0/28'
        })

        self.cmd('az ams streaming-endpoint update -g {rg} -a {amsname} -n {streamingEndpointName} --cdn-provider {cdnProvider} --cdn-profile {cdnProfile} --description "{description}" --max-cache-age {maxCacheAge} --tags {tags} --client-access-policy @"{clientAccessPolicy}" --cross-domain-policy @"{crossDomainPolicy}"', checks=[
            self.check('name', '{streamingEndpointName}'),
            self.check('cdnProvider', '{cdnProvider}'),
            self.check('cdnProfile', '{cdnProfile}'),
            self.check('description', '{description}'),
            self.check('maxCacheAge', '{maxCacheAge}'),
            self.check('length(tags)', 2)
        ])

        self.cmd('az ams streaming-endpoint update -g {rg} -a {amsname} -n {streamingEndpointName} --ips {ips} --disable-cdn')

        self.cmd('az ams streaming-endpoint show -g {rg} -a {amsname} -n {streamingEndpointName}', checks=[
            self.check('name', '{streamingEndpointName}'),
            self.check('cdnProvider', None),
            self.check('cdnProfile', ''),
            self.check('cdnEnabled', False),
            self.check('length(accessControl.ip.allow)', 3),
            self.check('accessControl.ip.allow[2].address', '192.168.0.0'),
            self.check('accessControl.ip.allow[2].subnetPrefixLength', '28')
        ])

        self.cmd('az ams streaming-endpoint delete -g {rg} -a {amsname} -n {streamingEndpointName}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_streaming_endpoint_create(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        streaming_endpoint_name = self.create_random_name(prefix="strep", length=11)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'canadacentral',
            'streamingEndpointName': streaming_endpoint_name,
            'cdnProvider': 'StandardVerizon',
            'cdnProfile': 'testProfile',
            'description': 'test streaming description',
            'maxCacheAge': 11,
            'scaleUnits': 6,
            'tags': 'foo=bar',
            'clientAccessPolicy': self._normalize_filename(_get_test_data_file('clientAccessPolicy.xml')),
            'crossDomainPolicy': self._normalize_filename(_get_test_data_file('crossDomainPolicy.xml'))
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams streaming-endpoint create -g {rg} -a {amsname} -n {streamingEndpointName} --cdn-provider {cdnProvider} --cdn-profile {cdnProfile} --description "{description}" --max-cache-age {maxCacheAge} --scale-units {scaleUnits} --tags "{tags}" --client-access-policy @"{clientAccessPolicy}" --cross-domain-policy @"{crossDomainPolicy}"', checks=[
            self.check('name', '{streamingEndpointName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('location', 'Canada Central'),
            self.check('cdnProvider', '{cdnProvider}'),
            self.check('cdnProfile', '{cdnProfile}'),
            self.check('description', '{description}'),
            self.check('maxCacheAge', '{maxCacheAge}'),
            self.check('scaleUnits', '{scaleUnits}'),
            self.check('length(tags)', 1)
        ])

        self.cmd('az ams streaming-endpoint delete -g {rg} -a {amsname} -n {streamingEndpointName}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_show')
    def test_ams_streaming_endpoint_show(self, storage_account_for_show):
        amsname = self.create_random_name(prefix='ams', length=12)
        streaming_endpoint_name = self.create_random_name(prefix="strep", length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_show,
            'location': 'australiasoutheast',
            'streamingEndpointName': streaming_endpoint_name,
            'cdnProvider': 'StandardVerizon',
            'cdnProfile': 'testProfile',
            'description': 'test streaming description',
            'maxCacheAge': 11,
            'scaleUnits': 7,
            'tags': 'foo=bar',
            'clientAccessPolicy': self._normalize_filename(_get_test_data_file('clientAccessPolicy.xml')),
            'crossDomainPolicy': self._normalize_filename(_get_test_data_file('crossDomainPolicy.xml'))
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams streaming-endpoint create -g {rg} -a {amsname} -n {streamingEndpointName} --cdn-provider {cdnProvider} --cdn-profile {cdnProfile} --description "{description}" --max-cache-age {maxCacheAge} --scale-units {scaleUnits} --tags "{tags}" --client-access-policy @"{clientAccessPolicy}" --cross-domain-policy @"{crossDomainPolicy}"')

        self.cmd('az ams streaming-endpoint show -g {rg} -a {amsname} -n {streamingEndpointName}', checks=[
            self.check('name', '{streamingEndpointName}'),
            self.check('resourceGroup', '{rg}'),
            self.check('location', 'Australia Southeast'),
            self.check('cdnProvider', '{cdnProvider}'),
            self.check('cdnProfile', '{cdnProfile}'),
            self.check('description', '{description}'),
            self.check('maxCacheAge', '{maxCacheAge}'),
            self.check('scaleUnits', '{scaleUnits}'),
            self.check('length(tags)', 1)
        ])

        nonexits_streaming_endpoint_name = self.create_random_name(prefix='se', length=20)
        self.kwargs.update({
            'nonexits_streaming_endpoint_name': nonexits_streaming_endpoint_name
        })
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('az ams streaming-endpoint show -g {rg} -a {amsname} -n {nonexits_streaming_endpoint_name}')

        self.cmd('az ams streaming-endpoint delete -g {rg} -a {amsname} -n {streamingEndpointName}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_delete')
    def test_ams_streaming_endpoint_delete(self, storage_account_for_delete):
        amsname = self.create_random_name(prefix='ams', length=12)
        streaming_endpoint_name1 = self.create_random_name(prefix="strep", length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_delete,
            'location': 'southindia',
            'streamingEndpointName1': streaming_endpoint_name1,
            'cdnProvider': 'StandardVerizon',
            'cdnProfile': 'testProfile',
            'description': 'test streaming description',
            'maxCacheAge': 11,
            'scaleUnits': 8,
            'tags': 'foo=bar',
            'clientAccessPolicy': self._normalize_filename(_get_test_data_file('clientAccessPolicy.xml')),
            'crossDomainPolicy': self._normalize_filename(_get_test_data_file('crossDomainPolicy.xml'))
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams streaming-endpoint create -g {rg} -a {amsname} -n {streamingEndpointName1} --cdn-provider {cdnProvider} --cdn-profile {cdnProfile} --description "{description}" --max-cache-age {maxCacheAge} --scale-units {scaleUnits} --tags "{tags}" --client-access-policy @"{clientAccessPolicy}" --cross-domain-policy @"{crossDomainPolicy}"')

        self.cmd('az ams streaming-endpoint list -g {rg} -a {amsname}', checks=[
            self.check('length(@)', 2)
        ])

        self.cmd('az ams streaming-endpoint delete -g {rg} -a {amsname} -n {streamingEndpointName1}')

        self.cmd('az ams streaming-endpoint list -g {rg} -a {amsname}', checks=[
            self.check('length(@)', 1)
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_scale')
    def test_ams_streaming_endpoint_scale(self, storage_account_for_scale):
        amsname = self.create_random_name(prefix='ams', length=12)
        streaming_endpoint_name = self.create_random_name(prefix="strep", length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_scale,
            'location': 'westindia',
            'streamingEndpointName': streaming_endpoint_name,
            'cdnProvider': 'StandardVerizon',
            'cdnProfile': 'testProfile',
            'description': 'test streaming description',
            'maxCacheAge': 11,
            'scaleUnits': 9,
            'scaleUnits2': 10,
            'tags': 'foo=bar',
            'clientAccessPolicy': self._normalize_filename(_get_test_data_file('clientAccessPolicy.xml')),
            'crossDomainPolicy': self._normalize_filename(_get_test_data_file('crossDomainPolicy.xml'))
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams streaming-endpoint create -g {rg} -a {amsname} -n {streamingEndpointName} --cdn-provider {cdnProvider} --cdn-profile {cdnProfile} --description "{description}" --max-cache-age {maxCacheAge} --scale-units {scaleUnits} --tags "{tags}" --client-access-policy @"{clientAccessPolicy}" --cross-domain-policy @"{crossDomainPolicy}"', checks=[
            self.check('scaleUnits', '{scaleUnits}')
        ])

        self.cmd('az ams streaming-endpoint scale -g {rg} -a {amsname} -n {streamingEndpointName} --scale-unit {scaleUnits2}')

        self.cmd('az ams streaming-endpoint show -g {rg} -a {amsname} -n {streamingEndpointName}', checks=[
            self.check('scaleUnits', '{scaleUnits2}')
        ])

        self.cmd('az ams streaming-endpoint delete -g {rg} -a {amsname} -n {streamingEndpointName}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_streaming_endpoint_start(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        streaming_endpoint_name = self.create_random_name(prefix="strep", length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'centralindia',
            'streamingEndpointName': streaming_endpoint_name,
            'scaleUnits': 4
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams streaming-endpoint create -g {rg} -a {amsname} -n {streamingEndpointName} --scale-units {scaleUnits}')

        self.cmd('az ams streaming-endpoint start -g {rg} -a {amsname} -n {streamingEndpointName}', checks=[
            self.check('resourceState', 'Running')
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_streaming_endpoint_start_async(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        streaming_endpoint_name = self.create_random_name(prefix="strep", length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'centralus',
            'streamingEndpointName': streaming_endpoint_name,
            'scaleUnits': 11
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams streaming-endpoint create -g {rg} -a {amsname} -n {streamingEndpointName} --scale-units {scaleUnits}')

        self.cmd('az ams streaming-endpoint start -g {rg} -a {amsname} -n {streamingEndpointName} --no-wait', checks=[self.is_empty()])

        str_endpoint = self.cmd('az ams streaming-endpoint show -g {rg} -a {amsname} -n {streamingEndpointName}').get_output_in_json()

        resource_states = ['Starting', 'Running']

        self.assertIn(str_endpoint['resourceState'], resource_states)

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_streaming_endpoint_stop_async(self, storage_account_for_create):
        if sys.version_info.major == 2:  # azure-cli/issues/9386
            return
        amsname = self.create_random_name(prefix='ams', length=12)
        streaming_endpoint_name = self.create_random_name(prefix="strep", length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'eastus2',
            'streamingEndpointName': streaming_endpoint_name,
            'scaleUnits': 12
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams streaming-endpoint create -g {rg} -a {amsname} -n {streamingEndpointName} --scale-units {scaleUnits} --auto-start')

        self.cmd('az ams streaming-endpoint stop -g {rg} -a {amsname} -n {streamingEndpointName} --no-wait', checks=[self.is_empty()])

        str_endpoint = self.cmd('az ams streaming-endpoint show -g {rg} -a {amsname} -n {streamingEndpointName}').get_output_in_json()

        resource_states = ['Stopping', 'Stopped']

        self.assertIn(str_endpoint['resourceState'], resource_states)

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_streaming_endpoint_stop(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        streaming_endpoint_name = self.create_random_name(prefix="strep", length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'eastus',
            'streamingEndpointName': streaming_endpoint_name,
            'scaleUnits': 13
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams streaming-endpoint create -g {rg} -a {amsname} -n {streamingEndpointName} --scale-units {scaleUnits} --auto-start', checks=[
            self.check('resourceState', 'Running')
        ])

        self.cmd('az ams streaming-endpoint stop -g {rg} -a {amsname} -n {streamingEndpointName}', checks=[
            self.check('resourceState', 'Stopped')
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_ams_streaming_endpoint_list(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        streaming_endpoint_name = self.create_random_name(prefix="strep", length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus',
            'streamingEndpointName': streaming_endpoint_name,
            'scaleUnits': 14
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams streaming-endpoint create -g {rg} -a {amsname} -n {streamingEndpointName} --scale-units {scaleUnits}')

        self.cmd('az ams streaming-endpoint list -g {rg} -a {amsname}', checks=[
            self.check('length(@)', 2)
        ])

# Helper functions

    def _normalize_filename(cmd, string):
        import platform
        return '"' + string.replace('\\', '/') + '"' if platform.system() != 'Windows' else string
