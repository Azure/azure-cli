# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import os
import time
import unittest
from datetime import datetime
from dateutil import tz

from azure.cli.command_modules.keyvault.custom import _asn1_to_iso8601

from knack.util import CLIError
from azure.cli.testsdk.vcr_test_base import (ResourceGroupVCRTestBase, JMESPathCheck,
                                             NoneCheck)

from azure.cli.command_modules.keyvault._params import secret_encoding_values

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


def _create_keyvault(test,
                     vault_name, resource_group, location, retry_wait=30, max_retries=10, additional_args=None):

    # need premium KeyVault to store keys in HSM
    vault = test.cmd('keyvault create -g {} -n {} -l {} --sku premium {}'.format(resource_group, vault_name,
                                                                                 location, additional_args or ''))

    retries = 0
    while True:
        try:
            # if you can connect to the keyvault, proceed with test
            test.cmd('keyvault key list --vault-name {}'.format(vault_name))
            return vault
        except CLIError as ex:
            # because it can take time for the DNS registration to propagate, periodically retry
            # until we can connect to the keyvault. During the wait, you should try to manually
            # flush the DNS cache in a separate terminal. Since this is OS dependent, we cannot
            # reliably do this programmatically.
            if 'Max retries exceeded attempting to connect to vault' in str(
                    ex) and retries < max_retries:
                retries += 1
                print('\tWaiting for DNS changes to propagate. Please try manually flushing your')
                print('\tDNS cache. (ex: \'ipconfig /flushdns\' on Windows)')
                print(
                    '\t\tRetrying ({}/{}) in {} seconds\n'.format(retries, max_retries, retry_wait))
                time.sleep(retry_wait)
            else:
                raise ex


class DateTimeParseTest(unittest.TestCase):
    def test_parse_asn1_date(self):
        expected = datetime(year=2017,
                            month=4,
                            day=24,
                            hour=16,
                            minute=37,
                            second=20,
                            tzinfo=tz.tzutc())
        self.assertEqual(_asn1_to_iso8601("20170424163720Z"), expected)


class KeyVaultMgmtScenarioTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(KeyVaultMgmtScenarioTest, self).__init__(__file__, test_method,
                                                       resource_group='cli-test-keyvault-mgmt')
        self.keyvault_names = ['cli-keyvault-12345-0',
                               'cli-keyvault-12345-1',
                               'cli-keyvault-12345-2',
                               'cli-keyvault-12345-3']
        self.location = 'westus'

    def test_keyvault_mgmt(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        kv = self.keyvault_names[0]
        loc = self.location
        # test create keyvault with default access policy set
        keyvault = self.cmd('keyvault create -g {} -n {} -l {}'.format(rg, kv, loc), checks=[
            JMESPathCheck('name', kv),
            JMESPathCheck('location', loc),
            JMESPathCheck('resourceGroup', rg),
            JMESPathCheck('type(properties.accessPolicies)', 'array'),
            JMESPathCheck('length(properties.accessPolicies)', 1),
            JMESPathCheck('properties.sku.name', 'standard')
        ])
        policy_id = keyvault['properties']['accessPolicies'][0]['objectId']
        self.cmd('keyvault show -n {}'.format(kv), checks=[
            JMESPathCheck('name', kv),
            JMESPathCheck('location', loc),
            JMESPathCheck('resourceGroup', rg),
            JMESPathCheck('type(properties.accessPolicies)', 'array'),
            JMESPathCheck('length(properties.accessPolicies)', 1),
        ])
        self.cmd('keyvault list -g {}'.format(rg), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', kv),
            JMESPathCheck('[0].location', loc),
            JMESPathCheck('[0].resourceGroup', rg),
        ])
        # test updating keyvault sku name
        self.cmd('keyvault update -g {} -n {} --set properties.sku.name=premium'.format(rg, kv),
                 checks=[
                     JMESPathCheck('name', kv),
                     JMESPathCheck('properties.sku.name', 'premium'),
                 ])
        # test policy set/delete
        self.cmd(
            'keyvault set-policy -g {} -n {} --object-id {} --certificate-permissions get list'.format(
                rg, kv, policy_id),
            checks=JMESPathCheck('length(properties.accessPolicies[0].permissions.certificates)',
                                 2))
        self.cmd('keyvault delete-policy -g {} -n {} --object-id {}'.format(rg, kv, policy_id),
                 checks=[
                     JMESPathCheck('type(properties.accessPolicies)', 'array'),
                     JMESPathCheck('length(properties.accessPolicies)', 0)
                 ])

        # test keyvault delete
        self.cmd('keyvault delete -n {}'.format(kv))
        self.cmd('keyvault list -g {}'.format(rg), checks=NoneCheck())

        # test create keyvault further
        self.cmd(
            'keyvault create -g {} -n {} -l {} --no-self-perms'.format(rg, self.keyvault_names[1],
                                                                       loc), checks=[
                JMESPathCheck('type(properties.accessPolicies)', 'array'),
                JMESPathCheck('length(properties.accessPolicies)', 0)
            ])
        self.cmd('keyvault create -g {} -n {} -l {} --enabled-for-deployment true '
                 '--enabled-for-disk-encryption true --enabled-for-template-deployment true'
                 .format(rg, self.keyvault_names[2], loc),
                 checks=[JMESPathCheck('properties.enabledForDeployment', True),
                         JMESPathCheck('properties.enabledForDiskEncryption', True),
                         JMESPathCheck('properties.enabledForTemplateDeployment', True)])
        self.cmd(
            'keyvault create -g {} -n {} -l {} --sku premium'.format(rg, self.keyvault_names[3],
                                                                     loc), checks=[
                JMESPathCheck('properties.sku.name', 'premium')
            ])


class KeyVaultKeyScenarioTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(KeyVaultKeyScenarioTest, self).__init__(__file__, test_method,
                                                      resource_group='cli-test-keyvault-key')
        self.keyvault_name = 'cli-keyvault-test-key'
        self.location = 'westus'

    def test_keyvault_key(self):
        self.execute()

    def body(self):
        _create_keyvault(self, self.keyvault_name, self.resource_group, self.location)
        kv = self.keyvault_name
        # create a key
        key = self.cmd('keyvault key create --vault-name {} -n key1 -p software'.format(kv),
                       checks=JMESPathCheck('attributes.enabled', True))
        first_kid = key['key']['kid']
        first_version = first_kid.rsplit('/', 1)[1]

        # list keys
        self.cmd('keyvault key list --vault-name {}'.format(kv),
                 checks=JMESPathCheck('length(@)', 1))

        # create a new key version
        key = self.cmd(
            'keyvault key create --vault-name {} -n key1 -p software --disabled --ops encrypt decrypt --tags test=foo'.format(
                kv), checks=[
                JMESPathCheck('attributes.enabled', False),
                JMESPathCheck('length(key.keyOps)', 2),
                JMESPathCheck('tags', {'test': 'foo'})
            ])
        second_kid = key['key']['kid']
        # list key versions
        self.cmd('keyvault key list-versions --vault-name {} -n key1'.format(kv),
                 checks=JMESPathCheck('length(@)', 2))

        # show key (latest)
        self.cmd('keyvault key show --vault-name {} -n key1'.format(kv),
                 checks=JMESPathCheck('key.kid', second_kid))

        # show key (specific version)
        self.cmd('keyvault key show --vault-name {} -n key1 -v {}'.format(kv, first_version),
                 checks=JMESPathCheck('key.kid', first_kid))

        # set key attributes
        self.cmd('keyvault key set-attributes --vault-name {} -n key1 --enabled true'.format(kv),
                 checks=[
                     JMESPathCheck('key.kid', second_kid),
                     JMESPathCheck('attributes.enabled', True)
                 ])

        # backup and then delete key
        key_file = 'backup.key'
        self.cmd('keyvault key backup --vault-name {} -n key1 --file {}'.format(kv, key_file))
        self.cmd('keyvault key delete --vault-name {} -n key1'.format(kv))
        self.cmd('keyvault key list --vault-name {}'.format(kv),
                 checks=NoneCheck())

        # restore key from backup
        self.cmd('keyvault key restore --vault-name {} --file {}'.format(kv, key_file))
        self.cmd('keyvault key list-versions --vault-name {} -n key1'.format(kv),
                 checks=JMESPathCheck('length(@)', 2))
        if os.path.isfile(key_file):
            os.remove(key_file)

        # import PEM
        key_enc_file = os.path.join(TEST_DIR, 'mydomain.test.encrypted.pem')
        key_enc_password = 'password'
        key_plain_file = os.path.join(TEST_DIR, 'mydomain.test.pem')
        self.cmd(
            'keyvault key import --vault-name {} -n import-key-plain --pem-file "{}" -p software'.format(
                kv, key_plain_file))
        self.cmd(
            'keyvault key import --vault-name {} -n import-key-encrypted --pem-file "{}" --pem-password {} -p hsm'.format(
                kv, key_enc_file, key_enc_password))


class KeyVaultSecretScenarioTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(KeyVaultSecretScenarioTest, self).__init__(__file__, test_method,
                                                         resource_group='cli-test-keyvault-secret')
        self.keyvault_name = 'cli-test-keyvault-secret'
        self.location = 'westus'

    def test_keyvault_secret(self):
        self.execute()

    def _test_download_secret(self):
        kv = self.keyvault_name
        secret_path = os.path.join(TEST_DIR, 'test_secret.txt')
        with open(secret_path, 'r') as f:
            expected = f.read().replace('\r\n', '\n')

        def _test_set_and_download(encoding):
            self.cmd(
                'keyvault secret set --vault-name {} -n download-{} --file "{}" --encoding {}'.format(
                    kv, encoding, secret_path, encoding))
            dest_path = os.path.join(TEST_DIR, 'recover-{}'.format(encoding))
            self.cmd(
                'keyvault secret download --vault-name {} -n download-{} --file "{}"'.format(kv,
                                                                                             encoding,
                                                                                             dest_path))
            with open(dest_path, 'r') as f:
                actual = f.read().replace('\r\n', '\n')
            self.assertEqual(actual, expected)
            os.remove(dest_path)

        for encoding in secret_encoding_values:
            _test_set_and_download(encoding)

    def body(self):
        _create_keyvault(self, self.keyvault_name, self.resource_group, self.location)
        kv = self.keyvault_name
        # create a secret
        secret = self.cmd(
            'keyvault secret set --vault-name {} -n secret1 --value ABC123'.format(kv),
            checks=JMESPathCheck('value', 'ABC123'))
        first_kid = secret['id']
        first_version = first_kid.rsplit('/', 1)[1]

        # list secrets
        self.cmd('keyvault secret list --vault-name {}'.format(kv),
                 checks=JMESPathCheck('length(@)', 1))

        # create a new secret version
        secret = self.cmd(
            'keyvault secret set --vault-name {} -n secret1 --value DEF456 --tags test=foo --description "test type"'.format(
                kv), checks=[
                JMESPathCheck('value', 'DEF456'),
                JMESPathCheck('tags', {'file-encoding': 'utf-8', 'test': 'foo'}),
                JMESPathCheck('contentType', 'test type')
            ])
        second_kid = secret['id']

        # list secret versions
        self.cmd('keyvault secret list-versions --vault-name {} -n secret1'.format(kv),
                 checks=JMESPathCheck('length(@)', 2))

        # show secret (latest)
        self.cmd('keyvault secret show --vault-name {} -n secret1'.format(kv),
                 checks=JMESPathCheck('id', second_kid))

        # show secret (specific version)
        self.cmd('keyvault secret show --vault-name {} -n secret1 -v {}'.format(kv, first_version),
                 checks=JMESPathCheck('id', first_kid))

        # set secret attributes
        self.cmd(
            'keyvault secret set-attributes --vault-name {} -n secret1 --enabled false'.format(kv),
            checks=[
                JMESPathCheck('id', second_kid),
                JMESPathCheck('attributes.enabled', False)
            ])

        # backup and then delete secret
        bak_file = 'backup.secret'
        self.cmd('keyvault secret backup --vault-name {} -n secret1 --file {}'.format(kv, bak_file))
        self.cmd('keyvault secret delete --vault-name {} -n secret1'.format(kv))
        self.cmd('keyvault secret list --vault-name {}'.format(kv),
                 checks=NoneCheck())

        # restore key from backup
        self.cmd('keyvault secret restore --vault-name {} --file {}'.format(kv, bak_file))
        self.cmd('keyvault secret list-versions --vault-name {} -n secret1'.format(kv),
                 checks=JMESPathCheck('length(@)', 2))
        if os.path.isfile(bak_file):
            os.remove(bak_file)

        # delete secret
        self.cmd('keyvault secret delete --vault-name {} -n secret1'.format(kv))
        self.cmd('keyvault secret list --vault-name {}'.format(kv),
                 checks=NoneCheck())

        self._test_download_secret()


class KeyVaultCertificateScenarioTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(KeyVaultCertificateScenarioTest, self).__init__(__file__, test_method,
                                                              resource_group='cli-test-keyvault-cert')
        self.keyvault_name = 'cli-test-keyvault-cert1'
        self.location = 'westus'

    def test_keyvault_certificate(self):
        self.execute()

    def _test_keyvault_certificate_contacts(self):
        kv = self.keyvault_name
        self.cmd(
            'keyvault certificate contact add --vault-name {} --email admin@contoso.com --name "John Doe" --phone 123-456-7890'.format(
                kv))
        self.cmd(
            'keyvault certificate contact add --vault-name {} --email other@contoso.com '.format(
                kv))
        self.cmd('keyvault certificate contact list --vault-name {}'.format(kv),
                 checks=JMESPathCheck('length(contactList)', 2))
        self.cmd(
            'keyvault certificate contact delete --vault-name {} --email admin@contoso.com'.format(
                kv))
        self.cmd('keyvault certificate contact list --vault-name {}'.format(kv), checks=[
            JMESPathCheck('length(contactList)', 1),
            JMESPathCheck('contactList[0].emailAddress', 'other@contoso.com')
        ])

    def _test_keyvault_certificate_issuers(self):
        kv = self.keyvault_name
        self.cmd(
            'keyvault certificate issuer create --vault-name {} --issuer-name issuer1 --provider Test'.format(
                kv), checks=[
                JMESPathCheck('provider', 'Test'),
                JMESPathCheck('attributes.enabled', True)
            ])
        self.cmd(
            'keyvault certificate issuer show --vault-name {} --issuer-name issuer1'.format(kv),
            checks=[
                JMESPathCheck('provider', 'Test'),
                JMESPathCheck('attributes.enabled', True)
            ])
        self.cmd(
            'keyvault certificate issuer update --vault-name {} --issuer-name issuer1 --organization-id TestOrg --account-id test_account'.format(
                kv), checks=[
                JMESPathCheck('provider', 'Test'),
                JMESPathCheck('attributes.enabled', True),
                JMESPathCheck('organizationDetails.id', 'TestOrg'),
                JMESPathCheck('credentials.accountId', 'test_account')
            ])
        with self.assertRaises(CLIError):
            self.cmd(
                'keyvault certificate issuer update --vault-name {} --issuer-name notexist --organization-id TestOrg --account-id test_account'.format(
                    kv))
        self.cmd(
            'keyvault certificate issuer update --vault-name {} --issuer-name issuer1 --account-id ""'.format(
                kv), checks=[
                JMESPathCheck('provider', 'Test'),
                JMESPathCheck('attributes.enabled', True),
                JMESPathCheck('organizationDetails.id', 'TestOrg'),
                JMESPathCheck('credentials.accountId', None)
            ])
        self.cmd('keyvault certificate issuer list --vault-name {}'.format(kv),
                 checks=JMESPathCheck('length(@)', 1))

        # test admin commands
        self.cmd(
            'keyvault certificate issuer admin add --vault-name {} --issuer-name issuer1 --email test@test.com --first-name Test --last-name Admin --phone 123-456-7890'.format(
                kv), checks=[
                JMESPathCheck('emailAddress', 'test@test.com'),
                JMESPathCheck('firstName', 'Test'),
                JMESPathCheck('lastName', 'Admin'),
                JMESPathCheck('phone', '123-456-7890'),
            ])
        with self.assertRaises(CLIError):
            self.cmd(
                'keyvault certificate issuer admin add --vault-name {} --issuer-name issuer1 --email test@test.com'.format(
                    kv))
        self.cmd(
            'keyvault certificate issuer admin add --vault-name {} --issuer-name issuer1 --email test2@test.com'.format(
                kv), checks=[
                JMESPathCheck('emailAddress', 'test2@test.com'),
                JMESPathCheck('firstName', None),
                JMESPathCheck('lastName', None),
                JMESPathCheck('phone', None),
            ])
        self.cmd(
            'keyvault certificate issuer admin list --vault-name {} --issuer-name issuer1'.format(
                kv),
            checks=JMESPathCheck('length(@)', 2))
        self.cmd(
            'keyvault certificate issuer admin delete --vault-name {} --issuer-name issuer1 --email test@test.com'.format(
                kv))
        self.cmd(
            'keyvault certificate issuer admin list --vault-name {} --issuer-name issuer1'.format(
                kv),
            checks=JMESPathCheck('length(@)', 1))

        self.cmd(
            'keyvault certificate issuer delete --vault-name {} --issuer-name issuer1'.format(kv))
        self.cmd('keyvault certificate issuer list --vault-name {}'.format(kv), checks=NoneCheck())

    def _test_keyvault_pending_certificate(self):
        kv = self.keyvault_name
        policy_path = os.path.join(TEST_DIR, 'policy_pending.json')
        fake_cert_path = os.path.join(TEST_DIR, 'import_pem_plain.pem')
        self.cmd('keyvault certificate create --vault-name {} -n pending-cert -p @"{}"'.format(kv,
                                                                                               policy_path),
                 checks=[
                     JMESPathCheck('statusDetails',
                                   'Pending certificate created. Please Perform Merge to complete the request.'),
                     JMESPathCheck('cancellationRequested', False),
                     JMESPathCheck('status', 'inProgress')
                 ])
        self.cmd('keyvault certificate pending show --vault-name {} -n pending-cert'.format(kv),
                 checks=[
                     JMESPathCheck('statusDetails',
                                   'Pending certificate created. Please Perform Merge to complete the request.'),
                     JMESPathCheck('cancellationRequested', False),
                     JMESPathCheck('status', 'inProgress')
                 ])
        # we do not have a way of actually getting a certificate that would pass this test so
        # we simply ensure that the payload successfully serializes and is received by the server
        self.cmd(
            'keyvault certificate pending merge --vault-name {} -n pending-cert --file "{}"'.format(
                kv, fake_cert_path),
            allowed_exceptions="Public key from x509 certificate and key of this instance doesn't match")
        self.cmd('keyvault certificate pending delete --vault-name {} -n pending-cert'.format(kv))
        self.cmd('keyvault certificate pending show --vault-name {} -n pending-cert'.format(kv),
                 allowed_exceptions='Pending certificate not found')

    def _test_certificate_download(self):
        import OpenSSL.crypto

        kv = self.keyvault_name
        pem_file = os.path.join(TEST_DIR, 'import_pem_plain.pem')
        pem_policy_path = os.path.join(TEST_DIR, 'policy_import_pem.json')
        pem_cert = self.cmd(
            'keyvault certificate import --vault-name {} -n pem-cert1 --file "{}" -p @"{}"'.format(
                kv, pem_file, pem_policy_path))
        cert_data = pem_cert['cer']

        dest_binary = os.path.join(TEST_DIR, 'download-binary')
        dest_string = os.path.join(TEST_DIR, 'download-string')

        expected_pem = "-----BEGIN CERTIFICATE-----\n" + \
                       cert_data + \
                       '-----END CERTIFICATE-----\n'
        expected_pem = expected_pem.replace('\n', '')

        try:
            self.cmd(
                'keyvault certificate download --vault-name {} -n pem-cert1 --file "{}" -e DER'.format(
                    kv, dest_binary))
            self.cmd(
                'keyvault certificate download --vault-name {} -n pem-cert1 --file "{}" -e PEM'.format(
                    kv, dest_string))
            self.cmd('keyvault certificate delete --vault-name {} -n pem-cert1'.format(kv))

            def verify(path, file_type):
                with open(path, 'rb') as f:
                    x509 = OpenSSL.crypto.load_certificate(file_type, f.read())
                    actual_pem = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, x509)
                    if isinstance(actual_pem, bytes):
                        actual_pem = actual_pem.decode("utf-8")
                    self.assertIn(expected_pem, actual_pem.replace('\n', ''))

            verify(dest_binary, OpenSSL.crypto.FILETYPE_ASN1)
            verify(dest_string, OpenSSL.crypto.FILETYPE_PEM)
        finally:
            if os.path.exists(dest_binary):
                os.remove(dest_binary)
            if os.path.exists(dest_string):
                os.remove(dest_string)

    def _test_keyvault_certificate_get_default_policy(self):
        result = self.cmd('keyvault certificate get-default-policy')
        self.assertEqual(result['keyProperties']['keyType'], 'RSA')
        self.assertEqual(result['issuerParameters']['name'], 'Self')
        self.assertEqual(result['secretProperties']['contentType'], 'application/x-pkcs12')
        subject = 'CN=CLIGetDefaultPolicy'
        self.assertEqual(result['x509CertificateProperties']['subject'], subject)

        result = self.cmd('keyvault certificate get-default-policy --scaffold')
        self.assertIn('RSA or RSA-HSM', result['keyProperties']['keyType'])
        self.assertIn('Self', result['issuerParameters']['name'])
        self.assertIn('application/x-pkcs12', result['secretProperties']['contentType'])
        self.assertIn('Contoso', result['x509CertificateProperties']['subject'])

    def body(self):

        self._test_keyvault_certificate_get_default_policy()

        _create_keyvault(self, self.keyvault_name, self.resource_group, self.location)

        kv = self.keyvault_name

        self._test_certificate_download()
        policy_path = os.path.join(TEST_DIR, 'policy.json')
        policy2_path = os.path.join(TEST_DIR, 'policy2.json')

        # create a certificate
        self.cmd(
            'keyvault certificate create --vault-name {} -n cert1 -p @"{}"'.format(kv, policy_path),
            checks=JMESPathCheck('status', 'completed'))

        # list certificates
        self.cmd('keyvault certificate list --vault-name {}'.format(kv),
                 checks=JMESPathCheck('length(@)', 1))

        # create a new certificate version
        self.cmd('keyvault certificate create --vault-name {} -n cert1 -p @"{}"'.format(kv,
                                                                                        policy2_path),
                 checks=[
                     JMESPathCheck('status', 'completed'),
                 ])

        # list certificate versions
        ver_list = self.cmd(
            'keyvault certificate list-versions --vault-name {} -n cert1'.format(kv),
            checks=JMESPathCheck('length(@)', 2))

        ver_list = sorted(ver_list, key=lambda x: x['attributes']['created'])
        versions = [x['id'] for x in ver_list]

        # show certificate (latest)
        self.cmd('keyvault certificate show --vault-name {} -n cert1'.format(kv), checks=[
            JMESPathCheck('id', versions[1]),
            JMESPathCheck('policy.x509CertificateProperties.validityInMonths', 50)
        ])

        # show certificate (specific version)
        cert_version = versions[0].rsplit('/', 1)[1]
        self.cmd(
            'keyvault certificate show --vault-name {} -n cert1 -v {}'.format(kv, cert_version),
            checks=JMESPathCheck('id', versions[0]))

        # update certificate attributes
        self.cmd(
            'keyvault certificate set-attributes --vault-name {} -n cert1 --enabled false -p @"{}"'.format(
                kv, policy_path), checks=[
                JMESPathCheck('id', versions[1]),
                JMESPathCheck('attributes.enabled', False),
                JMESPathCheck('policy.x509CertificateProperties.validityInMonths', 60)
            ])

        self._test_keyvault_certificate_contacts()
        self._test_keyvault_certificate_issuers()
        self._test_keyvault_pending_certificate()

        # delete certificate
        self.cmd('keyvault certificate delete --vault-name {} -n cert1'.format(kv))
        self.cmd('keyvault certificate list --vault-name {}'.format(kv),
                 checks=NoneCheck())

        # test certificate import
        pem_encrypted_file = os.path.join(TEST_DIR, 'import_pem_encrypted_pwd_1234.pem')
        pem_encrypted_password = '1234'
        pem_plain_file = os.path.join(TEST_DIR, 'import_pem_plain.pem')
        pem_policy_path = os.path.join(TEST_DIR, 'policy_import_pem.json')
        self.cmd(
            'keyvault certificate import --vault-name {} -n pem-cert1 --file "{}" -p @"{}"'.format(
                kv, pem_plain_file, pem_policy_path))
        self.cmd(
            'keyvault certificate import --vault-name {} -n pem-cert2 --file "{}" --password {} -p @"{}"'.format(
                kv, pem_encrypted_file, pem_encrypted_password, pem_policy_path))

        pfx_plain_file = os.path.join(TEST_DIR, 'import_pfx.pfx')
        pfx_policy_path = os.path.join(TEST_DIR, 'policy_import_pfx.json')
        self.cmd(
            'keyvault certificate import --vault-name {} -n pfx-cert --file "{}" -p @"{}"'.format(
                kv, pfx_plain_file, pfx_policy_path))


class KeyVaultSoftDeleteScenarioTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(KeyVaultSoftDeleteScenarioTest, self).__init__(__file__, test_method,
                                                             resource_group='cli-test-kv-sd')
        self.keyvault_name = 'cli-kv-test-softdelete'
        self.location = 'westus'

    def test_keyvault_softdelete(self):
        self.execute()

    def body(self):
        vault = _create_keyvault(self, self.keyvault_name, self.resource_group, self.location,
                                 additional_args='--enable-soft-delete true')
        kv = self.keyvault_name

        # add all purge permissions to default the access policy
        default_policy = vault['properties']['accessPolicies'][0]
        certPerms = default_policy['permissions']['certificates']
        keyPerms = default_policy['permissions']['keys']
        secretPerms = default_policy['permissions']['secrets']

        for p in [certPerms, keyPerms, secretPerms]:
            p.append('purge')

        cmdstr = 'keyvault set-policy -n {} --object-id {} --key-permissions {} --secret-permissions {} --certificate-permissions {}'.format(
            kv, default_policy['objectId'], ' '.join(keyPerms), ' '.join(secretPerms), ' '.join(certPerms))
        print(cmdstr)

        self.cmd(cmdstr)

        # create, delete, restore, and purge a secret
        self.cmd('keyvault secret set --vault-name {} -n secret1 --value ABC123'.format(kv),
                 checks=JMESPathCheck('value', 'ABC123'))
        self._delete_entity('secret', 'secret1')
        self._recover_entity('secret', 'secret1')
        self._delete_entity('secret', 'secret1')
        self.cmd('keyvault secret purge --vault-name {} -n secret1'.format(kv))

        # create, delete, restore, and purge a key
        self.cmd('keyvault key create --vault-name {} -n key1 -p software'.format(kv),
                 checks=JMESPathCheck('attributes.enabled', True))
        self._delete_entity('key', 'key1')
        self._recover_entity('key', 'key1')
        self._delete_entity('key', 'key1')
        self.cmd('keyvault key purge --vault-name {} -n key1'.format(kv))

        # create, delete, restore, and purge a certificate
        pem_plain_file = os.path.join(TEST_DIR, 'import_pem_plain.pem')
        pem_policy_path = os.path.join(TEST_DIR, 'policy_import_pem.json')
        self.cmd('keyvault certificate import --vault-name {} -n cert1 --file "{}" -p @"{}"'.format(kv,
                                                                                                    pem_plain_file,
                                                                                                    pem_policy_path))
        self._delete_entity('certificate', 'cert1')
        self.cmd('keyvault certificate purge --vault-name {} -n cert1'.format(kv))

        self.cmd('keyvault delete -n {}'.format(kv))
        self.cmd('keyvault purge -n {} -l {}'.format(kv, self.location))

    def _delete_entity(self, entity_type, entity_name, retry_wait=3, max_retries=10):
        # delete the specified entity
        self.cmd('keyvault {} delete --vault-name {} -n {}'.format(entity_type, self.keyvault_name, entity_name))

        retry_count = 0
        # while getting the deleted entities returns a zero entities
        while not self.cmd('keyvault {} list-deleted --vault-name {}'.format(entity_type, self.keyvault_name)) \
                and retry_count < max_retries:
            retry_count += 1
            time.sleep(retry_wait)

        if retry_count >= max_retries:
            self.assertFail('{} {} not deleted'.format(entity_type, entity_name))

    def _recover_entity(self, entity_type, entity_name, retry_wait=3, max_retries=10):
        # delete the specified entity
        self.cmd('keyvault {} recover --vault-name {} -n {}'.format(entity_type, self.keyvault_name, entity_name))

        retry_count = 0
        # while getting the deleted entities returns a zero entities
        while not self.cmd('keyvault {} list --vault-name {}'.format(entity_type, self.keyvault_name)) \
                and retry_count < max_retries:
            retry_count += 1
            time.sleep(retry_wait)

        if retry_count >= max_retries:
            self.assertFail('{} {} not restored'.format(entity_type, entity_name))


if __name__ == '__main__':
    unittest.main()
