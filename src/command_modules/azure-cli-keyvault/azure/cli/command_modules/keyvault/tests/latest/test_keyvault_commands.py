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
from azure.cli.command_modules.keyvault._params import secret_encoding_values

from azure.cli.testsdk import ResourceGroupPreparer, ScenarioTest, LiveScenarioTest

from knack.util import CLIError


TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


def _create_keyvault(test, kwargs, retry_wait=30, max_retries=10, additional_args=None):

    # need premium KeyVault to store keys in HSM
    kwargs['add'] = additional_args or ''
    vault = test.cmd('keyvault create -g {rg} -n {kv} -l {loc} --sku premium {add}')

    retries = 0
    while True:
        try:
            # if you can connect to the keyvault, proceed with test
            time.sleep(10)
            test.cmd('keyvault key list --vault-name {kv}')
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


class KeyVaultMgmtScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_mgmt')
    def test_keyvault_mgmt(self, resource_group):

        self.kwargs.update({
            'kv': self.create_random_name('cli-keyvault-', 24),
            'kv2': self.create_random_name('cli-keyvault-', 24),
            'kv3': self.create_random_name('cli-keyvault-', 24),
            'kv4': self.create_random_name('cli-keyvault-', 24),
            'loc': 'westus'
        })

        # test create keyvault with default access policy set
        keyvault = self.cmd('keyvault create -g {rg} -n {kv} -l {loc}', checks=[
            self.check('name', '{kv}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}'),
            self.check('type(properties.accessPolicies)', 'array'),
            self.check('length(properties.accessPolicies)', 1),
            self.check('properties.sku.name', 'standard')
        ]).get_output_in_json()
        self.kwargs['policy_id'] = keyvault['properties']['accessPolicies'][0]['objectId']
        self.cmd('keyvault show -n {kv}', checks=[
            self.check('name', '{kv}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}'),
            self.check('type(properties.accessPolicies)', 'array'),
            self.check('length(properties.accessPolicies)', 1),
        ])
        self.cmd('keyvault list -g {rg}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
            self.check('[0].name', '{kv}'),
            self.check('[0].location', '{loc}'),
            self.check('[0].resourceGroup', '{rg}')
        ])
        # test updating keyvault sku name
        self.cmd('keyvault update -g {rg} -n {kv} --set properties.sku.name=premium', checks=[
            self.check('name', '{kv}'),
            self.check('properties.sku.name', 'premium'),
        ])
        # test policy set/delete
        self.cmd('keyvault set-policy -g {rg} -n {kv} --object-id {policy_id} --certificate-permissions get list',
                 checks=self.check('length(properties.accessPolicies[0].permissions.certificates)', 2))
        self.cmd('keyvault delete-policy -g {rg} -n {kv} --object-id {policy_id}', checks=[
            self.check('type(properties.accessPolicies)', 'array'),
            self.check('length(properties.accessPolicies)', 0)
        ])

        # test keyvault delete
        self.cmd('keyvault delete -n {kv}')
        self.cmd('keyvault list -g {rg}', checks=self.is_empty())

        # test create keyvault further

        self.cmd('keyvault create -g {rg} -n {kv2} -l {loc} --no-self-perms', checks=[
            self.check('type(properties.accessPolicies)', 'array'),
            self.check('length(properties.accessPolicies)', 0)
        ])

        self.cmd('keyvault create -g {rg} -n {kv3} -l {loc} --enabled-for-deployment true --enabled-for-disk-encryption true --enabled-for-template-deployment true', checks=[
            self.check('properties.enabledForDeployment', True),
            self.check('properties.enabledForDiskEncryption', True),
            self.check('properties.enabledForTemplateDeployment', True)
        ])
        self.cmd('keyvault create -g {rg} -n {kv4} -l {loc} --sku premium', checks=[
            self.check('properties.sku.name', 'premium')
        ])


class KeyVaultKeyScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_key')
    def test_keyvault_key(self, resource_group):

        self.kwargs.update({
            'kv': self.create_random_name('cli-test-keyvault-', 24),
            'loc': 'westus',
            'key': 'key1'
        })

        _create_keyvault(self, self.kwargs)

        # create a key
        key = self.cmd('keyvault key create --vault-name {kv} -n {key} -p software',
                       checks=self.check('attributes.enabled', True)).get_output_in_json()
        first_kid = key['key']['kid']
        first_version = first_kid.rsplit('/', 1)[1]

        # list keys
        self.cmd('keyvault key list --vault-name {kv}',
                 checks=self.check('length(@)', 1))

        # create a new key version
        key = self.cmd('keyvault key create --vault-name {kv} -n {key} -p software --disabled --ops encrypt decrypt --tags test=foo', checks=[
            self.check('attributes.enabled', False),
            self.check('length(key.keyOps)', 2),
            self.check('tags', {'test': 'foo'})
        ]).get_output_in_json()
        second_kid = key['key']['kid']
        # list key versions
        self.cmd('keyvault key list-versions --vault-name {kv} -n {key}',
                 checks=self.check('length(@)', 2))

        # show key (latest)
        self.cmd('keyvault key show --vault-name {kv} -n {key}',
                 checks=self.check('key.kid', second_kid))

        # show key (specific version)
        self.kwargs.update({
            'version1': first_version,
            'kid1': first_kid,
            'kid2': second_kid
        })
        self.cmd('keyvault key show --vault-name {kv} -n {key} -v {version1}',
                 checks=self.check('key.kid', '{kid1}'))

        # set key attributes
        self.cmd('keyvault key set-attributes --vault-name {kv} -n {key} --enabled true', checks=[
            self.check('key.kid', '{kid2}'),
            self.check('attributes.enabled', True)
        ])

        # backup and then delete key
        key_file = 'backup.key'
        self.kwargs['key_file'] = key_file
        self.cmd('keyvault key backup --vault-name {kv} -n {key} --file {key_file}')
        self.cmd('keyvault key delete --vault-name {kv} -n {key}')
        self.cmd('keyvault key list --vault-name {kv}',
                 checks=self.is_empty())

        # restore key from backup
        self.cmd('keyvault key restore --vault-name {kv} --file {key_file}')
        self.cmd('keyvault key list-versions --vault-name {kv} -n {key}',
                 checks=self.check('length(@)', 2))
        if os.path.isfile(key_file):
            os.remove(key_file)

        # import PEM
        self.kwargs.update({
            'key_enc_file': os.path.join(TEST_DIR, 'mydomain.test.encrypted.pem'),
            'key_enc_password': 'password',
            'key_plain_file': os.path.join(TEST_DIR, 'mydomain.test.pem')
        })
        self.cmd('keyvault key import --vault-name {kv} -n import-key-plain --pem-file "{key_plain_file}" -p software')
        self.cmd('keyvault key import --vault-name {kv} -n import-key-encrypted --pem-file "{key_enc_file}" --pem-password {key_enc_password} -p hsm')


class KeyVaultSecretScenarioTest(ScenarioTest):

    def _test_download_secret(self):
        secret_path = os.path.join(TEST_DIR, 'test_secret.txt')
        self.kwargs['src_path'] = secret_path
        with open(secret_path, 'r') as f:
            expected = f.read().replace('\r\n', '\n')

        def _test_set_and_download(encoding):
            self.kwargs['enc'] = encoding
            self.cmd('keyvault secret set --vault-name {kv} -n download-{enc} --file "{src_path}" --encoding {enc}')
            dest_path = os.path.join(TEST_DIR, 'recover-{}'.format(encoding))
            self.kwargs['dest_path'] = dest_path
            self.cmd('keyvault secret download --vault-name {kv} -n download-{enc} --file "{dest_path}"')
            with open(dest_path, 'r') as f:
                actual = f.read().replace('\r\n', '\n')
            self.assertEqual(actual, expected)
            os.remove(dest_path)

        for encoding in secret_encoding_values:
            _test_set_and_download(encoding)

    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_secret')
    def test_keyvault_secret(self, resource_group):

        self.kwargs.update({
            'kv': self.create_random_name('cli-test-kevault-', 24),
            'loc': 'westus',
            'sec': 'secret1'
        })

        _create_keyvault(self, self.kwargs)

        # create a secret
        secret = self.cmd('keyvault secret set --vault-name {kv} -n {sec} --value ABC123',
                          checks=self.check('value', 'ABC123')).get_output_in_json()
        first_sid = secret['id']
        first_version = first_sid.rsplit('/', 1)[1]
        self.kwargs.update({
            'sid1': first_sid,
            'ver1': first_version
        })

        # list secrets
        self.cmd('keyvault secret list --vault-name {kv}', checks=self.check('length(@)', 1))

        # create a new secret version
        secret = self.cmd('keyvault secret set --vault-name {kv} -n {sec} --value DEF456 --tags test=foo --description "test type"', checks=[
            self.check('value', 'DEF456'),
            self.check('tags', {'file-encoding': 'utf-8', 'test': 'foo'}),
            self.check('contentType', 'test type')
        ]).get_output_in_json()
        self.kwargs['sid2'] = secret['id']

        # list secret versions
        self.cmd('keyvault secret list-versions --vault-name {kv} -n {sec}',
                 checks=self.check('length(@)', 2))

        # show secret (latest)
        self.cmd('keyvault secret show --vault-name {kv} -n {sec}',
                 checks=self.check('id', '{sid2}'))

        # show secret (specific version)
        self.cmd('keyvault secret show --vault-name {kv} -n {sec} -v {ver1}',
                 checks=self.check('id', '{sid1}'))

        # set secret attributes
        self.cmd('keyvault secret set-attributes --vault-name {kv} -n {sec} --enabled false', checks=[
            self.check('id', '{sid2}'),
            self.check('attributes.enabled', False)
        ])

        # backup and then delete secret
        bak_file = 'backup.secret'
        self.kwargs['bak_file'] = bak_file
        self.cmd('keyvault secret backup --vault-name {kv} -n {sec} --file {bak_file}')
        self.cmd('keyvault secret delete --vault-name {kv} -n {sec}')
        self.cmd('keyvault secret list --vault-name {kv}', checks=self.is_empty())

        # restore key from backup
        self.cmd('keyvault secret restore --vault-name {kv} --file {bak_file}')
        self.cmd('keyvault secret list-versions --vault-name {kv} -n {sec}',
                 checks=self.check('length(@)', 2))
        if os.path.isfile(bak_file):
            os.remove(bak_file)

        # delete secret
        self.cmd('keyvault secret delete --vault-name {kv} -n {sec}')
        self.cmd('keyvault secret list --vault-name {kv}',
                 checks=self.is_empty())

        self._test_download_secret()


class KeyVaultCertificateContactsScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_kv_cert_contacts')
    def test_keyvault_certificate_contacts(self, resource_group):

        self.kwargs.update({
            'kv': self.create_random_name('cli-test-keyvault-', 24),
            'loc': 'westus'
        })

        _create_keyvault(self, self.kwargs)

        self.cmd('keyvault certificate contact add --vault-name {kv} --email admin@contoso.com --name "John Doe" --phone 123-456-7890')
        self.cmd('keyvault certificate contact add --vault-name {kv} --email other@contoso.com ')
        self.cmd('keyvault certificate contact list --vault-name {kv}',
                 checks=self.check('length(contactList)', 2))
        self.cmd('keyvault certificate contact delete --vault-name {kv} --email admin@contoso.com')
        self.cmd('keyvault certificate contact list --vault-name {kv}', checks=[
            self.check('length(contactList)', 1),
            self.check('contactList[0].emailAddress', 'other@contoso.com')
        ])


class KeyVaultCertificateIssuerScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_kv_cert_issuer')
    def test_keyvault_certificate_issuers(self, resource_group):

        self.kwargs.update({
            'kv': self.create_random_name('cli-test-keyvault-', 24),
            'loc': 'westus'
        })

        _create_keyvault(self, self.kwargs)

        self.cmd('keyvault certificate issuer create --vault-name {kv} --issuer-name issuer1 --provider Test', checks=[
            self.check('provider', 'Test'),
            self.check('attributes.enabled', True)
        ])
        self.cmd('keyvault certificate issuer show --vault-name {kv} --issuer-name issuer1', checks=[
            self.check('provider', 'Test'),
            self.check('attributes.enabled', True)
        ])
        self.cmd('keyvault certificate issuer update --vault-name {kv} --issuer-name issuer1 --organization-id TestOrg --account-id test_account', checks=[
            self.check('provider', 'Test'),
            self.check('attributes.enabled', True),
            self.check('organizationDetails.id', 'TestOrg'),
            self.check('credentials.accountId', 'test_account')
        ])
        with self.assertRaises(CLIError):
            self.cmd('keyvault certificate issuer update --vault-name {kv} --issuer-name notexist --organization-id TestOrg --account-id test_account')
        self.cmd('keyvault certificate issuer update --vault-name {kv} --issuer-name issuer1 --account-id ""', checks=[
            self.check('provider', 'Test'),
            self.check('attributes.enabled', True),
            self.check('organizationDetails.id', 'TestOrg'),
            self.check('credentials.accountId', None)
        ])
        self.cmd('keyvault certificate issuer list --vault-name {kv}',
                 checks=self.check('length(@)', 1))

        # test admin commands
        self.cmd('keyvault certificate issuer admin add --vault-name {kv} --issuer-name issuer1 --email test@test.com --first-name Test --last-name Admin --phone 123-456-7890', checks=[
            self.check('emailAddress', 'test@test.com'),
            self.check('firstName', 'Test'),
            self.check('lastName', 'Admin'),
            self.check('phone', '123-456-7890'),
        ])
        self.cmd('keyvault certificate issuer admin add --vault-name {kv} --issuer-name issuer1 --email test@test.com')
        self.cmd('keyvault certificate issuer admin add --vault-name {kv} --issuer-name issuer1 --email test2@test.com', checks=[
            self.check('emailAddress', 'test2@test.com'),
            self.check('firstName', None),
            self.check('lastName', None),
            self.check('phone', None),
        ])
        self.cmd('keyvault certificate issuer admin list --vault-name {kv} --issuer-name issuer1',
                 checks=self.check('length(@)', 2))
        self.cmd('keyvault certificate issuer admin delete --vault-name {kv} --issuer-name issuer1 --email test@test.com')
        self.cmd('keyvault certificate issuer admin list --vault-name {kv} --issuer-name issuer1',
                 checks=self.check('length(@)', 1))

        self.cmd('keyvault certificate issuer delete --vault-name {kv} --issuer-name issuer1')
        self.cmd('keyvault certificate issuer list --vault-name {kv}', checks=self.is_empty())


class KeyVaultPendingCertificateScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_kv_cert_pending')
    def test_keyvault_pending_certificate(self, resource_group):

        self.kwargs.update({
            'kv': self.create_random_name('cli-test-keyvault-', 24),
            'loc': 'westus',
            'policy_path': os.path.join(TEST_DIR, 'policy_pending.json')
        })

        _create_keyvault(self, self.kwargs)

        self.kwargs['fake_cert_path'] = os.path.join(TEST_DIR, 'import_pem_plain.pem')
        self.cmd('keyvault certificate create --vault-name {kv} -n pending-cert -p @"{policy_path}"', checks=[
            self.check('statusDetails', 'Pending certificate created. Please Perform Merge to complete the request.'),
            self.check('cancellationRequested', False),
            self.check('status', 'inProgress')
        ])
        self.cmd('keyvault certificate pending show --vault-name {kv} -n pending-cert', checks=[
            self.check('statusDetails', 'Pending certificate created. Please Perform Merge to complete the request.'),
            self.check('cancellationRequested', False),
            self.check('status', 'inProgress')
        ])
        # we do not have a way of actually getting a certificate that would pass this test so
        # we simply ensure that the payload successfully serializes and is received by the server
        with self.assertRaises(CLIError):
            self.cmd('keyvault certificate pending merge --vault-name {kv} -n pending-cert --file "{fake_cert_path}"')
        self.cmd('keyvault certificate pending delete --vault-name {kv} -n pending-cert')

        with self.assertRaises(CLIError):
            self.cmd('keyvault certificate pending show --vault-name {kv} -n pending-cert')


# TODO: Convert to ScenarioTest and re-record when issue #5146 is fixed.
class KeyVaultCertificateDownloadScenarioTest(LiveScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_kv_cert_download')
    def test_keyvault_certificate_download(self, resource_group):
        import OpenSSL.crypto

        self.kwargs.update({
            'kv': self.create_random_name('cli-test-keyvault-', 24),
            'loc': 'westus'
        })

        _create_keyvault(self, self.kwargs)

        pem_file = os.path.join(TEST_DIR, 'import_pem_plain.pem')
        pem_policy_path = os.path.join(TEST_DIR, 'policy_import_pem.json')
        self.kwargs.update({
            'pem_file': pem_file,
            'pem_policy_path': pem_policy_path
        })
        pem_cert = self.cmd('keyvault certificate import --vault-name {kv} -n pem-cert1 --file "{pem_file}" -p @"{pem_policy_path}"').get_output_in_json()
        cert_data = pem_cert['cer']

        dest_binary = os.path.join(TEST_DIR, 'download-binary')
        dest_string = os.path.join(TEST_DIR, 'download-string')
        self.kwargs.update({
            'dest_binary': dest_binary,
            'dest_string': dest_string
        })

        expected_pem = "-----BEGIN CERTIFICATE-----\n" + \
                       cert_data + \
                       '-----END CERTIFICATE-----\n'
        expected_pem = expected_pem.replace('\n', '')

        try:
            self.cmd('keyvault certificate download --vault-name {kv} -n pem-cert1 --file "{dest_binary}" -e DER')
            self.cmd('keyvault certificate download --vault-name {kv} -n pem-cert1 --file "{dest_string}" -e PEM')
            self.cmd('keyvault certificate delete --vault-name {kv} -n pem-cert1')

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


class KeyVaultCertificateDefaultPolicyScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_kv_cert_default_policy')
    def test_keyvault_certificate_get_default_policy(self, resource_group):
        result = self.cmd('keyvault certificate get-default-policy').get_output_in_json()
        self.assertEqual(result['keyProperties']['keyType'], 'RSA')
        self.assertEqual(result['issuerParameters']['name'], 'Self')
        self.assertEqual(result['secretProperties']['contentType'], 'application/x-pkcs12')
        subject = 'CN=CLIGetDefaultPolicy'
        self.assertEqual(result['x509CertificateProperties']['subject'], subject)

        result = self.cmd('keyvault certificate get-default-policy --scaffold').get_output_in_json()
        self.assertIn('RSA or RSA-HSM', result['keyProperties']['keyType'])
        self.assertIn('Self', result['issuerParameters']['name'])
        self.assertIn('application/x-pkcs12', result['secretProperties']['contentType'])
        self.assertIn('Contoso', result['x509CertificateProperties']['subject'])


class KeyVaultCertificateScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_cert')
    def test_keyvault_certificate_crud(self, resource_group):

        self.kwargs.update({
            'kv': self.create_random_name('cli-test-keyvault-', 24),
            'loc': 'westus'
        })

        _create_keyvault(self, self.kwargs)

        policy_path = os.path.join(TEST_DIR, 'policy.json')
        policy2_path = os.path.join(TEST_DIR, 'policy2.json')
        self.kwargs.update({
            'policy_path': policy_path,
            'policy2_path': policy2_path
        })

        # create a certificate
        self.cmd('keyvault certificate create --vault-name {kv} -n cert1 -p @"{policy_path}"',
                 checks=self.check('status', 'completed'))

        # list certificates
        self.cmd('keyvault certificate list --vault-name {kv}',
                 checks=self.check('length(@)', 1))

        # create a new certificate version
        self.cmd('keyvault certificate create --vault-name {kv} -n cert1 -p @"{policy2_path}"', checks=[
            self.check('status', 'completed'),
        ])

        # list certificate versions
        ver_list = self.cmd('keyvault certificate list-versions --vault-name {kv} -n cert1',
                            checks=self.check('length(@)', 2)).get_output_in_json()

        ver_list = sorted(ver_list, key=lambda x: x['attributes']['created'])
        versions = [x['id'] for x in ver_list]

        # show certificate (latest)
        self.cmd('keyvault certificate show --vault-name {kv} -n cert1', checks=[
            self.check('id', versions[1]),
            self.check('policy.x509CertificateProperties.validityInMonths', 50)
        ])

        # show certificate (specific version)
        cert_version = versions[0].rsplit('/', 1)[1]
        self.kwargs['ver1'] = cert_version
        self.cmd('keyvault certificate show --vault-name {kv} -n cert1 -v {ver1}',
                 checks=self.check('id', versions[0]))

        # update certificate attributes
        self.cmd('keyvault certificate set-attributes --vault-name {kv} -n cert1 --enabled false -p @"{policy_path}"', checks=[
            self.check('id', versions[1]),
            self.check('attributes.enabled', False),
            self.check('policy.x509CertificateProperties.validityInMonths', 60)
        ])

        # delete certificate
        self.cmd('keyvault certificate delete --vault-name {kv} -n cert1')
        self.cmd('keyvault certificate list --vault-name {kv}',
                 checks=self.is_empty())


# TODO: Convert to ScenarioTest and re-record when issue #5146 is fixed.
class KeyVaultCertificateImportScenario(LiveScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_sd')
    def test_keyvault_certificate_import(self, resource_group):

        self.kwargs.update({
            'kv': self.create_random_name('cli-test-keyvault-', 24),
            'loc': 'westus'
        })

        _create_keyvault(self, self.kwargs)

        # test certificate import
        self.kwargs.update({
            'pem_encrypted_file': os.path.join(TEST_DIR, 'import_pem_encrypted_pwd_1234.pem'),
            'pem_encrypted_password': '1234',
            'pem_plain_file': os.path.join(TEST_DIR, 'import_pem_plain.pem'),
            'pem_policy_path': os.path.join(TEST_DIR, 'policy_import_pem.json')
        })
        self.cmd('keyvault certificate import --vault-name {kv} -n pem-cert1 --file "{pem_plain_file}" -p @"{pem_policy_path}"')
        self.cmd('keyvault certificate import --vault-name {kv} -n pem-cert2 --file "{pem_encrypted_file}" --password {pem_encrypted_password} -p @"{pem_policy_path}"')

        self.kwargs.update({
            'pfx_plain_file': os.path.join(TEST_DIR, 'import_pfx.pfx'),
            'pfx_policy_path': os.path.join(TEST_DIR, 'policy_import_pfx.json')
        })
        self.cmd('keyvault certificate import --vault-name {kv} -n pfx-cert --file "{pfx_plain_file}" -p @"{pfx_policy_path}"')


# TODO: Convert to ScenarioTest and re-record when issue #5146 is fixed.
class KeyVaultSoftDeleteScenarioTest(LiveScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_sd')
    def test_keyvault_softdelete(self, resource_group):

        self.kwargs.update({
            'kv': self.create_random_name('cli-test-keyvault-', 24),
            'loc': 'westus'
        })

        vault = _create_keyvault(self, self.kwargs, additional_args=' --enable-soft-delete true').get_output_in_json()

        # add all purge permissions to default the access policy
        default_policy = vault['properties']['accessPolicies'][0]
        cert_perms = default_policy['permissions']['certificates']
        key_perms = default_policy['permissions']['keys']
        secret_perms = default_policy['permissions']['secrets']
        obj_id = default_policy['objectId']

        for p in [cert_perms, key_perms, secret_perms]:
            p.append('purge')

        self.kwargs.update({
            'obj_id': obj_id,
            'key_perms': ' '.join(key_perms),
            'secret_perms': ' '.join(secret_perms),
            'cert_perms': ' '.join(cert_perms)
        })

        self.cmd('keyvault set-policy -n {kv} --object-id {obj_id} --key-permissions {key_perms} --secret-permissions {secret_perms} --certificate-permissions {cert_perms`}')

        # create, delete, restore, and purge a secret
        self.cmd('keyvault secret set --vault-name {kv} -n secret1 --value ABC123',
                 checks=self.check('value', 'ABC123'))

        self._delete_entity('secret', 'secret1')
        self._recover_entity('secret', 'secret1')
        self._delete_entity('secret', 'secret1')
        self._purge_entity('secret', 'secret1')

        # create, delete, restore, and purge a key
        self.cmd('keyvault key create --vault-name {kv} -n key1 -p software',
                 checks=self.check('attributes.enabled', True))

        self._delete_entity('key', 'key1')
        self._recover_entity('key', 'key1')
        self._delete_entity('key', 'key1')
        self._purge_entity('key', 'key1')

        # create, delete, restore, and purge a certificate
        self.kwargs.update({
            'pem_plain_file': os.path.join(TEST_DIR, 'import_pem_plain.pem'),
            'pem_policy_pat': os.path.join(TEST_DIR, 'policy_import_pem.json')
        })
        self.cmd('keyvault certificate import --vault-name {kv} -n cert1 --file "{pem_plain_file}" -p @"{pem_policy_path}"')
        self._delete_entity('certificate', 'cert1')
        self._purge_entity('certificate', 'cert1')

        self.cmd('keyvault delete -n {kv}')
        self.cmd('keyvault purge -n {kv} -l {loc}')

    def _delete_entity(self, entity_type, entity_name, retry_wait=3, max_retries=10):
        # delete the specified entity
        self.kwargs.update({
            'ent': entity_type,
            'name': entity_name
        })
        self.cmd('keyvault {ent} delete --vault-name {kv} -n {name}')

        # while getting the deleted entities returns a zero entities
        for _ in range(max_retries):
            try:
                self.cmd('keyvault {ent} show --vault-name {kv} -n {name}')
                time.sleep(retry_wait)
            except Exception as ex:
                if 'not found' in str(ex):
                    return
        self.fail('{} {} not deleted'.format(entity_type, entity_name))

    def _recover_entity(self, entity_type, entity_name, retry_wait=3, max_retries=10):

        # while getting the deleted entities returns a zero entities
        self.kwargs.update({
            'ent': entity_type,
            'name': entity_name
        })

        for _ in range(max_retries):
            try:
                self.cmd('keyvault {ent} recover --vault-name {kv} -n {name}')
                break
            except Exception as ex:
                if 'currently being deleted' in str(ex):
                    time.sleep(retry_wait)

        for _ in range(max_retries):
            try:
                self.cmd('keyvault {ent} show --vault-name {kv} -n {name}')
                return
            except Exception as ex:
                if 'not found' in str(ex) or 'currently being deleted' in str(ex):
                    time.sleep(retry_wait)

        self.fail('{} {} not restored'.format(entity_type, entity_name))

    def _purge_entity(self, entity_type, entity_name, retry_wait=3, max_retries=10):

        # while getting the deleted entities returns a zero entities
        self.kwargs.update({
            'ent': entity_type,
            'name': entity_name
        })

        for _ in range(max_retries):
            try:
                self.cmd('keyvault {ent} purge --vault-name {kv} -n {name}')
                break
            except Exception as ex:
                if 'currently being deleted' in str(ex):
                    time.sleep(retry_wait)

        for _ in range(max_retries):
            try:
                self.cmd('keyvault {ent} show --vault-name {kv} -n {name}')
                time.sleep(retry_wait)
            except Exception as ex:
                if 'not found' in str(ex):
                    return

        self.fail('{} {} not purged'.format(entity_type, entity_name))


if __name__ == '__main__':
    unittest.main()
