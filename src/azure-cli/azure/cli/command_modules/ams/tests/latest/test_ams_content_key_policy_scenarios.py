# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import base64
import os

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
from azure.cli.core.util import CLIError
from azure.core.exceptions import (HttpResponseError)
from azure.cli.command_modules.ams._test_utils import _get_test_data_file


class AmsContentKeyPolicyTests(ScenarioTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_content_key_policy_create_with_playready_fail(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        policy_name = self.create_random_name(prefix='pn', length=12)
        policy_option_name = self.create_random_name(prefix='pon', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'japanwest',
            'contentKeyPolicyName': policy_name,
            'description': 'ExampleDescription',
            'policyOptionName': policy_option_name,
            'playReadyPath': '@' + _get_test_data_file('invalidPlayReadyTemplate.json'),
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        with self.assertRaises(CLIError):
            self.cmd('az ams content-key-policy create -a {amsname} -n {contentKeyPolicyName} -g {rg}  --open-restriction --play-ready-template "{playReadyPath}" --description {description} --policy-option-name {policyOptionName}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_content_key_policy_create_with_playready_success(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        policy_name = self.create_random_name(prefix='pn', length=12)
        policy_option_name = self.create_random_name(prefix='pon', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'japaneast',
            'contentKeyPolicyName': policy_name,
            'description': 'ExampleDescription',
            'policyOptionName': policy_option_name,
            'configurationODataType': '#Microsoft.Media.ContentKeyPolicyPlayReadyConfiguration',
            'restrictionODataType': '#Microsoft.Media.ContentKeyPolicyOpenRestriction',
            'playReadyPath': '@' + _get_test_data_file('validPlayReadyTemplate.json'),
            'responseCustomData': 'custom data',
            'allowTestDevices': True,
            'beginDate': None,
            'expirationDate': '2098-09-15T18:53:00+00:00',
            'relativeBeginDate': '1:01:01',
            'relativeExpirationDate': None,
            'gracePeriod': '2:02:02',
            'licenseType': 'Persistent',
            'contentType': 'Unspecified',
            'keyLocationODataType': '#Microsoft.Media.ContentKeyPolicyPlayReadyContentEncryptionKeyFromKeyIdentifier',
            'keyId': '12345678-aaaa-bbbb-cccc-ddddeeeeffff',
            'firstPlayExpiration': '12:00:00',
            'scmsRestriction': 1,
            'agcAndColorStripeRestriction': 2,
            'digitalVideoOnlyContentRestriction': False,
            'imageConstraintForAnalogComponentVideoRestriction': False,
            'imageConstraintForAnalogComputerMonitorRestriction': False,
            'allowPassingVideoContentToUnknownOutput': 'Allowed',
            'uncompressedDigitalVideoOpl': 300,
            'compressedDigitalVideoOpl': 500,
            'analogVideoOpl': 200,
            'compressedDigitalAudioOpl': 300,
            'uncompressedDigitalAudioOpl': 300,
            'bestEffort': True,
            'configurationData': 0
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams content-key-policy create -a {amsname} -n {contentKeyPolicyName} -g {rg}  --open-restriction --play-ready-template "{playReadyPath}" --description {description} --policy-option-name {policyOptionName}', checks=[
            self.check('name', '{contentKeyPolicyName}'),
            self.check('options[0].configuration.odataType', '{configurationODataType}'),
            self.check('options[0].restriction.odataType', '{restrictionODataType}'),
            self.check('options[0].configuration.responseCustomData', '{responseCustomData}'),
            self.check('options[0].configuration.licenses[0].allowTestDevices', '{allowTestDevices}'),
            self.check('options[0].configuration.licenses[0].beginDate', '{beginDate}'),
            self.check('options[0].configuration.licenses[0].expirationDate', '{expirationDate}'),
            self.check('options[0].configuration.licenses[0].relativeBeginDate', '{relativeBeginDate}'),
            self.check('options[0].configuration.licenses[0].relativeExpirationDate', '{relativeExpirationDate}'),
            self.check('options[0].configuration.licenses[0].gracePeriod', '{gracePeriod}'),
            self.check('options[0].configuration.licenses[0].licenseType', '{licenseType}'),
            self.check('options[0].configuration.licenses[0].contentType', '{contentType}'),
            self.check('options[0].configuration.licenses[0].contentKeyLocation.odataType', '{keyLocationODataType}'),
            self.check('options[0].configuration.licenses[0].contentKeyLocation.keyId', '{keyId}'),
            self.check('options[0].configuration.licenses[0].playRight.firstPlayExpiration', '{firstPlayExpiration}'),
            self.check('options[0].configuration.licenses[0].playRight.scmsRestriction', '{scmsRestriction}'),
            self.check('options[0].configuration.licenses[0].playRight.agcAndColorStripeRestriction', '{agcAndColorStripeRestriction}'),
            self.check('options[0].configuration.licenses[0].playRight.digitalVideoOnlyContentRestriction', '{digitalVideoOnlyContentRestriction}'),
            self.check('options[0].configuration.licenses[0].playRight.imageConstraintForAnalogComponentVideoRestriction', '{imageConstraintForAnalogComponentVideoRestriction}'),
            self.check('options[0].configuration.licenses[0].playRight.imageConstraintForAnalogComputerMonitorRestriction', '{imageConstraintForAnalogComputerMonitorRestriction}'),
            self.check('options[0].configuration.licenses[0].playRight.allowPassingVideoContentToUnknownOutput', '{allowPassingVideoContentToUnknownOutput}'),
            self.check('options[0].configuration.licenses[0].playRight.uncompressedDigitalVideoOpl', '{uncompressedDigitalVideoOpl}'),
            self.check('options[0].configuration.licenses[0].playRight.compressedDigitalVideoOpl', '{compressedDigitalVideoOpl}'),
            self.check('options[0].configuration.licenses[0].playRight.analogVideoOpl', '{analogVideoOpl}'),
            self.check('options[0].configuration.licenses[0].playRight.compressedDigitalAudioOpl', '{compressedDigitalAudioOpl}'),
            self.check('options[0].configuration.licenses[0].playRight.uncompressedDigitalAudioOpl', '{uncompressedDigitalAudioOpl}'),
            self.check('options[0].configuration.licenses[0].playRight.explicitAnalogTelevisionOutputRestriction.bestEffort', '{bestEffort}'),
            self.check('options[0].configuration.licenses[0].playRight.explicitAnalogTelevisionOutputRestriction.configurationData', '{configurationData}')
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_update')
    def test_content_key_policy_update(self, storage_account_for_update):
        amsname = self.create_random_name(prefix='ams', length=12)
        policy_name = self.create_random_name(prefix='pn', length=12)
        policy_option_name = self.create_random_name(prefix='pon', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_update,
            'location': 'australiaeast',
            'contentKeyPolicyName': policy_name,
            'description': 'ExampleDescription',
            'policyOptionName': policy_option_name,
            'configurationODataType': '#Microsoft.Media.ContentKeyPolicyClearKeyConfiguration',
            'issuer': 'Issuer',
            'audience': 'Audience',
            'tokenKey': 'a1b2c3d4e5f6g7h8i9j0',
            'tokenType': 'Symmetric',
            'restrictionTokenType': 'Jwt',
            'restrictionODataType': '#Microsoft.Media.ContentKeyPolicyTokenRestriction',
            'openIDConnectDiscoveryDocument': 'adocument',
            'tokenClaims': 'foo=baz baz=doo fus=rodahh'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.kwargs.update({
            'description': 'AnotherDescription',
            'issuer': 'AnotherIssuer'
        })

        self.cmd('az ams content-key-policy create -a {amsname} -n {contentKeyPolicyName} -g {rg} --description {description} --clear-key-configuration --issuer {issuer} --audience {audience} --token-key "{tokenKey}" --token-key-type {tokenType} --token-type {restrictionTokenType} --token-claims {tokenClaims} --open-id-connect-discovery-document {openIDConnectDiscoveryDocument} --policy-option-name {policyOptionName}', checks=[
            self.check('name', '{contentKeyPolicyName}'),
            self.check('options[0].configuration.odataType', '{configurationODataType}'),
            self.check('options[0].restriction.issuer', '{issuer}'),
            self.check('options[0].restriction.audience', '{audience}'),
            self.check('options[0].restriction.restrictionTokenType', '{restrictionTokenType}'),
            self.check('options[0].restriction.odataType', '{restrictionODataType}'),
            self.check('length(options[0].restriction.requiredClaims)', 3),
            self.check('options[0].restriction.openIdConnectDiscoveryDocument', '{openIDConnectDiscoveryDocument}')
        ])

        self.cmd('az ams content-key-policy update -a {amsname} -n {contentKeyPolicyName} -g {rg} --description {description} --set options[0].restriction.issuer={issuer}', checks=[
            self.check('name', '{contentKeyPolicyName}'),
            self.check('options[0].configuration.odataType', '{configurationODataType}'),
            self.check('options[0].restriction.issuer', '{issuer}'),
            self.check('options[0].restriction.audience', '{audience}'),
            self.check('options[0].restriction.restrictionTokenType', '{restrictionTokenType}'),
            self.check('options[0].restriction.odataType', '{restrictionODataType}'),
            self.check('length(options[0].restriction.requiredClaims)', 3),
            self.check('options[0].restriction.openIdConnectDiscoveryDocument', '{openIDConnectDiscoveryDocument}')
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_content_key_policy_create_with_fairplay(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        policy_name = self.create_random_name(prefix='pn', length=12)
        policy_option_name = self.create_random_name(prefix='pon', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'eastasia',
            'contentKeyPolicyName': policy_name,
            'description': 'ExampleDescription',
            'policyOptionName': policy_option_name,
            'configurationODataType': '#Microsoft.Media.ContentKeyPolicyFairPlayConfiguration',
            'ask': '1234567890ABCDEF1234567890ABCDEF',
            'fairPlayPfx': _get_test_data_file('TestCert2.pfx'),
            'fairPlayPfxPassword': 'password',
            'rentalAndLeaseKeyType': 'Undefined',
            'rentalDuration': 60,
            'restrictionODataType': '#Microsoft.Media.ContentKeyPolicyOpenRestriction'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams content-key-policy create -a {amsname} -n {contentKeyPolicyName} -g {rg} --open-restriction --description {description} --ask {ask} --fair-play-pfx "{fairPlayPfx}" --fair-play-pfx-password {fairPlayPfxPassword} --rental-and-lease-key-type {rentalAndLeaseKeyType} --rental-duration {rentalDuration} --policy-option-name {policyOptionName}', checks=[
            self.check('name', '{contentKeyPolicyName}'),
            self.check('options[0].configuration.odataType', '{configurationODataType}'),
            self.check('options[0].restriction.odataType', '{restrictionODataType}'),
            self.check('options[0].configuration.rentalAndLeaseKeyType', '{rentalAndLeaseKeyType}'),
            self.check('options[0].configuration.rentalDuration', '{rentalDuration}')
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_content_key_policy_create_with_fairplay_offline(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        policy_name = self.create_random_name(prefix='pn', length=12)
        policy_option_name = self.create_random_name(prefix='pon', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'eastasia',
            'contentKeyPolicyName': policy_name,
            'description': 'ExampleDescription',
            'policyOptionName': policy_option_name,
            'configurationODataType': '#Microsoft.Media.ContentKeyPolicyFairPlayConfiguration',
            'ask': '1234567890ABCDEF1234567890ABCDEF',
            'fairPlayPfx': _get_test_data_file('TestCert2.pfx'),
            'fairPlayPfxPassword': 'password',
            'rentalAndLeaseKeyType': 'DualExpiry',
            'fairPlayPlaybackDurationSeconds': 60,
            'fairPlayStorageDurationSeconds': 60,
            'rentalDuration': 60,
            'restrictionODataType': '#Microsoft.Media.ContentKeyPolicyOpenRestriction'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams content-key-policy create -a {amsname} -n {contentKeyPolicyName} -g {rg} --open-restriction --description {description} --ask {ask} --fair-play-pfx "{fairPlayPfx}" --fair-play-pfx-password {fairPlayPfxPassword} --rental-and-lease-key-type {rentalAndLeaseKeyType} --fp-playback-duration-seconds {fairPlayPlaybackDurationSeconds} --fp-storage-duration-seconds {fairPlayStorageDurationSeconds} --rental-duration {rentalDuration} --policy-option-name {policyOptionName}', checks=[
            self.check('name', '{contentKeyPolicyName}'),
            self.check('options[0].configuration.odataType', '{configurationODataType}'),
            self.check('options[0].restriction.odataType', '{restrictionODataType}'),
            self.check('options[0].configuration.rentalAndLeaseKeyType', '{rentalAndLeaseKeyType}'),
            self.check('options[0].configuration.rentalDuration', 0),
            self.check('options[0].configuration.offlineRentalConfiguration.playbackDurationSeconds', '{fairPlayPlaybackDurationSeconds}'),
            self.check('options[0].configuration.offlineRentalConfiguration.storageDurationSeconds', '{fairPlayStorageDurationSeconds}')
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_content_key_policy_create_with_token(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        policy_name = self.create_random_name(prefix='pn', length=12)
        policy_option_name = self.create_random_name(prefix='pon', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'southeastasia',
            'contentKeyPolicyName': policy_name,
            'description': 'ExampleDescription',
            'policyOptionName': policy_option_name,
            'configurationODataType': '#Microsoft.Media.ContentKeyPolicyWidevineConfiguration',
            'jsonFile': '@' + _get_test_data_file('widevineTemplate.json'),
            'issuer': 'Issuer',
            'audience': 'Audience',
            'tokenKey': _get_test_data_file('rsaToken.pem'),
            'tokenType': 'RSA',
            'restrictionTokenType': 'Jwt',
            'restrictionODataType': '#Microsoft.Media.ContentKeyPolicyTokenRestriction',
            'openIDConnectDiscoveryDocument': 'adocument',
            'tokenClaims': 'foo=baz baz=doo fus=rodahh'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams content-key-policy create -a {amsname} -n {contentKeyPolicyName} -g {rg} --description {description} --issuer {issuer} --audience {audience} --token-key "{tokenKey}" --token-key-type {tokenType} --token-type {restrictionTokenType} --widevine-template "{jsonFile}" --token-claims {tokenClaims} --open-id-connect-discovery-document {openIDConnectDiscoveryDocument} --policy-option-name {policyOptionName}', checks=[
            self.check('name', '{contentKeyPolicyName}'),
            self.check('options[0].configuration.odataType', '{configurationODataType}'),
            self.check('options[0].restriction.issuer', '{issuer}'),
            self.check('options[0].restriction.audience', '{audience}'),
            self.check('options[0].restriction.restrictionTokenType', '{restrictionTokenType}'),
            self.check('options[0].restriction.odataType', '{restrictionODataType}'),
            self.check('length(options[0].restriction.requiredClaims)', 3),
            self.check('options[0].restriction.openIdConnectDiscoveryDocument', '{openIDConnectDiscoveryDocument}')
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_content_key_policy_create_with_widevine(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        policy_name = self.create_random_name(prefix='pn', length=12)
        policy_option_name = self.create_random_name(prefix='pon', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westus',
            'contentKeyPolicyName': policy_name,
            'description': 'ExampleDescription',
            'policyOptionName': policy_option_name,
            'configurationODataType': '#Microsoft.Media.ContentKeyPolicyWidevineConfiguration',
            'jsonFile': '@' + _get_test_data_file('widevineTemplate.json')
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams content-key-policy create -a {amsname} -n {contentKeyPolicyName} -g {rg} --description {description} --widevine-template "{jsonFile}" --open-restriction --policy-option-name {policyOptionName}', checks=[
            self.check('name', '{contentKeyPolicyName}'),
            self.check('options[0].configuration.odataType', '{configurationODataType}')
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    def test_content_key_policy_create_basic(self, storage_account_for_create):
        amsname = self.create_random_name(prefix='ams', length=12)
        policy_name = self.create_random_name(prefix='mm', length=12)
        policy_option_name = self.create_random_name(prefix='pon', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_create,
            'location': 'westindia',
            'contentKeyPolicyName': policy_name,
            'description': 'ExampleDescription',
            'policyOptionName': policy_option_name,
            'configurationODataType': '#Microsoft.Media.ContentKeyPolicyClearKeyConfiguration',
            'restrictionODataType': '#Microsoft.Media.ContentKeyPolicyOpenRestriction'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams content-key-policy create -a {amsname} -n {contentKeyPolicyName} -g {rg} --description {description} --clear-key-configuration --open-restriction --policy-option-name {policyOptionName}', checks=[
            self.check('name', '{contentKeyPolicyName}'),
            self.check('length(options)', 1),
            self.check('description', '{description}'),
            self.check('resourceGroup', '{rg}'),
            self.check('options[0].name', '{policyOptionName}'),
            self.check('options[0].configuration.odataType', '{configurationODataType}'),
            self.check('options[0].restriction.odataType', '{restrictionODataType}')
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_show')
    def test_content_key_policy_show_basic(self, storage_account_for_show):
        amsname = self.create_random_name(prefix='ams', length=12)
        policy_name = self.create_random_name(prefix='pn', length=12)
        policy_option_name = self.create_random_name(prefix='pon', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_show,
            'location': 'canadacentral',
            'contentKeyPolicyName': policy_name,
            'description': 'ExampleDescription',
            'policyOptionName': policy_option_name,
            'configurationODataType': '#Microsoft.Media.ContentKeyPolicyClearKeyConfiguration',
            'restrictionODataType': '#Microsoft.Media.ContentKeyPolicyOpenRestriction'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams content-key-policy create -a {amsname} -n {contentKeyPolicyName} -g {rg} --description {description} --clear-key-configuration --open-restriction --policy-option-name {policyOptionName}')

        self.cmd('az ams content-key-policy show -a {amsname} -n {contentKeyPolicyName} -g {rg}', checks=[
            self.check('name', '{contentKeyPolicyName}'),
            self.check('length(options)', 1),
            self.check('description', '{description}'),
            self.check('resourceGroup', '{rg}'),
            self.check('options[0].name', '{policyOptionName}'),
            self.check('options[0].configuration.odataType', '{configurationODataType}'),
            self.check('options[0].restriction.odataType', '{restrictionODataType}')
        ])

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_show')
    def test_content_key_policy_show_with_secrets(self, storage_account_for_show):
        amsname = self.create_random_name(prefix='ams', length=12)
        policy_name = self.create_random_name(prefix='pn', length=12)
        policy_option_name = self.create_random_name(prefix='pon', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_show,
            'location': 'canadaeast',
            'contentKeyPolicyName': policy_name,
            'description': 'ExampleDescription',
            'policyOptionName': policy_option_name,
            'configurationODataType': '#Microsoft.Media.ContentKeyPolicyClearKeyConfiguration',
            'restrictionODataType': '#Microsoft.Media.ContentKeyPolicyOpenRestriction',
            'restrictionTokenType': 'Jwt',
            'issuer': 'issuer',
            'audience': 'audience',
            'tokenKey': _get_test_data_file('x509Token.pem'),
            'tokenType': 'X509'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams content-key-policy create -a {amsname} -g {rg} -n {contentKeyPolicyName} --clear-key-configuration --policy-option-name {policyOptionName} --token-key "{tokenKey}" --token-key-type {tokenType} --issuer {issuer} --audience {audience} --token-type {restrictionTokenType}')

        self.cmd('az ams content-key-policy show -a {amsname} -n {contentKeyPolicyName} -g {rg}', checks=[
            self.check('options[0].restriction.primaryVerificationKey.rawBody', None)
        ])

        output = self.cmd('az ams content-key-policy show -a {amsname} -n {contentKeyPolicyName} -g {rg} --with-secrets').get_output_in_json()

        self.assertNotEquals(output.get('options')[0].get('restriction').get('primaryVerificationKey').get('rawBody'), None)

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_delete')
    def test_content_key_policy_delete_list(self, storage_account_for_delete):
        amsname = self.create_random_name(prefix='ams', length=12)
        policy_name = self.create_random_name(prefix='pn', length=12)
        policy_option_name = self.create_random_name(prefix='pon', length=12)

        self.kwargs.update({
            'amsname': amsname,
            'storageAccount': storage_account_for_delete,
            'location': 'eastus',
            'contentKeyPolicyName': policy_name,
            'description': 'ExampleDescription',
            'policyOptionName': policy_option_name,
            'configurationODataType': '#Microsoft.Media.ContentKeyPolicyClearKeyConfiguration',
            'restrictionODataType': '#Microsoft.Media.ContentKeyPolicyOpenRestriction'
        })

        self.cmd('az ams account create -n {amsname} -g {rg} --storage-account {storageAccount} -l {location}')

        self.cmd('az ams content-key-policy create -a {amsname} -n {contentKeyPolicyName} -g {rg} --description {description} --clear-key-configuration --open-restriction --policy-option-name {policyOptionName}')

        self.cmd('az ams content-key-policy list -a {amsname} -g {rg}', checks=[
            self.check('length(@)', 1)
        ])

        self.cmd('az ams content-key-policy delete -a {amsname} -g {rg} -n {contentKeyPolicyName}')

        self.cmd('az ams content-key-policy list -a {amsname} -g {rg}', checks=[
            self.check('length(@)', 0)
        ])
