# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import time
import unittest
from datetime import datetime, timedelta
from dateutil import tz

from azure.cli.testsdk import ResourceGroupPreparer, KeyVaultPreparer, ScenarioTest, LiveScenarioTest

from knack.util import CLIError

secret_text_encoding_values = ['utf-8', 'utf-16le', 'utf-16be', 'ascii']
secret_binary_encoding_values = ['base64', 'hex']
secret_encoding_values = secret_text_encoding_values + secret_binary_encoding_values


def _asn1_to_iso8601(asn1_date):
    import dateutil.parser
    if isinstance(asn1_date, bytes):
        asn1_date = asn1_date.decode('utf-8')
    return dateutil.parser.parse(asn1_date)


TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


def _create_keyvault(test, kwargs, additional_args=None):

    # need premium KeyVault to store keys in HSM
    kwargs['add'] = additional_args or ''
    return test.cmd('keyvault create -g {rg} -n {kv} -l {loc} --sku premium --retention-days 7 {add}')


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
            'kv': self.create_random_name('cli-test-kv-mgmt-', 24),
            'kv2': self.create_random_name('cli-test-kv-mgmt-', 24),
            'kv3': self.create_random_name('cli-test-kv-mgmt-', 24),
            'kv4': self.create_random_name('cli-test-kv-mgmt-', 24),
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
        # test updating updating other properties
        self.cmd('keyvault update -g {rg} -n {kv} --enable-soft-delete --enable-purge-protection '
                 '--enabled-for-deploymen --enabled-for-disk-encryption --enabled-for-template-deployment ',
                 checks=[
                     self.check('name', '{kv}'),
                     self.check('properties.enableSoftDelete', True),
                     self.check('properties.enablePurgeProtection', True),
                     self.check('properties.enabledForDeployment', True),
                     self.check('properties.enabledForDiskEncryption', True),
                     self.check('properties.enabledForTemplateDeployment', True)])
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
    @KeyVaultPreparer(name_prefix='cli-test-kv-key-')
    def test_keyvault_key(self, resource_group):
        self.kwargs.update({
            'loc': 'westus',
            'key': 'key1'
        })

        keyvault = self.cmd('keyvault show -n {kv} -g {rg}').get_output_in_json()
        self.kwargs['obj_id'] = keyvault['properties']['accessPolicies'][0]['objectId']
        key_perms = keyvault['properties']['accessPolicies'][0]['permissions']['keys']
        key_perms.append('purge')
        self.kwargs['key_perms'] = ' '.join(key_perms)
        self.cmd('keyvault set-policy -n {kv} --object-id {obj_id} --key-permissions {key_perms}')

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

        # show key (by id)
        self.cmd('keyvault key show --id {kid1}',
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
        time.sleep(200)
        self.cmd('keyvault key purge --vault-name {kv} -n {key}')
        time.sleep(200)
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

        # create ec keys
        self.cmd('keyvault key create --vault-name {kv} -n eckey1 --kty EC',
                 checks=self.check('key.kty', 'EC'))
        self.cmd('keyvault key create --vault-name {kv} -n eckey1 --curve P-256',
                 checks=[self.check('key.kty', 'EC'), self.check('key.crv', 'P-256')])
        self.cmd('keyvault key delete --vault-name {kv} -n eckey1')

        # import ec PEM
        self.kwargs.update({
            'key_enc_file': os.path.join(TEST_DIR, 'ec521pw.pem'),
            'key_enc_password': 'pass1234',
            'key_plain_file': os.path.join(TEST_DIR, 'ec256.pem')
        })
        self.cmd('keyvault key import --vault-name {kv} -n import-eckey-plain --pem-file "{key_plain_file}" -p software',
                 checks=[self.check('key.kty', 'EC'), self.check('key.crv', 'P-256')])
        self.cmd('keyvault key import --vault-name {kv} -n import-eckey-encrypted --pem-file "{key_enc_file}" --pem-password {key_enc_password}',
                 checks=[self.check('key.kty', 'EC'), self.check('key.crv', 'P-521')])


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
    @KeyVaultPreparer(name_prefix='cli-test-kv-se-')
    def test_keyvault_secret(self, resource_group):

        self.kwargs.update({
            'loc': 'westus',
            'sec': 'secret1'
        })

        keyvault = self.cmd("keyvault show -n {kv} -g {rg}").get_output_in_json()
        self.kwargs['obj_id'] = keyvault['properties']['accessPolicies'][0]['objectId']
        secret_perms = keyvault['properties']['accessPolicies'][0]['permissions']['secrets']
        secret_perms.append('purge')
        self.kwargs['secret_perms'] = ' '.join(secret_perms)
        self.cmd('keyvault set-policy -n {kv} --object-id {obj_id} --secret-permissions {secret_perms}')

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

        # show secret (by id)
        self.cmd('keyvault secret show --id {sid1}',
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
        time.sleep(200)
        self.cmd('keyvault secret purge --vault-name {kv} -n {sec}')
        time.sleep(200)
        self.cmd('keyvault secret list --vault-name {kv}', checks=self.is_empty())

        # restore secret from backup
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
    @KeyVaultPreparer(name_prefix='cli-test-kv-ct-co-')
    def test_keyvault_certificate_contacts(self, resource_group):

        self.kwargs.update({
            'loc': 'westus'
        })

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
    @KeyVaultPreparer(name_prefix='cli-test-kv-ct-is-')
    def test_keyvault_certificate_issuers(self, resource_group):

        self.kwargs.update({
            'loc': 'westus'
        })

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
    @KeyVaultPreparer(name_prefix='cli-test-kv-ct-pe-')
    def test_keyvault_pending_certificate(self, resource_group):

        self.kwargs.update({
            'loc': 'westus',
            'policy_path': os.path.join(TEST_DIR, 'policy_pending.json')
        })

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

        self.cmd('keyvault certificate pending show --vault-name {kv} -n pending-cert', expect_failure=True)


# TODO: Convert to ScenarioTest and re-record when issue #5146 is fixed.
class KeyVaultCertificateDownloadScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_kv_cert_download')
    @KeyVaultPreparer(name_prefix='cli-test-kv-ct-dl-', location='eastus2')
    def test_keyvault_certificate_download(self, resource_group):
        import OpenSSL.crypto

        self.kwargs.update({
            'loc': 'eastus2'
        })

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
    def test_keyvault_certificate_get_default_policy(self):
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
    @KeyVaultPreparer(name_prefix='cli-test-kv-ct-')
    def test_keyvault_certificate_crud(self, resource_group):

        self.kwargs.update({
            'loc': 'westus'
        })

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

        # show certificate (by id)
        self.kwargs.update({'cert_id': versions[0]})
        self.cmd('keyvault certificate show --id {cert_id}',
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


def _generate_certificate(path, keyfile=None, password=None):
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes

    if keyfile:
        with open(path, "rb") as kf:
            key_bytes = kf.read()
            key = serialization.load_pem_private_key(key_bytes, password, default_backend())
    else:
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        key_bytes = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(password) if password else serialization.NoEncryption(),
        )

    # Various details about who we are. For a self-signed certificate the
    # Subject and issuer are always the same.
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u'US'),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u'WA'),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u'Redmond'),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"My Company"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"mysite.com")])

    cert = x509.CertificateBuilder().subject_name(subject) \
                                    .issuer_name(issuer) \
                                    .public_key(key.public_key()) \
                                    .serial_number(x509.random_serial_number()) \
                                    .not_valid_before(datetime.utcnow()) \
                                    .not_valid_after(datetime.utcnow() + timedelta(days=10)) \
                                    .sign(key, hashes.SHA256(), default_backend())

    # Write the cert out to disk
    with open(path, "wb") as f:
        f.write(key_bytes)
        f.write(cert.public_bytes(serialization.Encoding.PEM))


# TODO: Convert to ScenarioTest and re-record when issue #5146 is fixed.
class KeyVaultCertificateImportScenario(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_sd')
    @KeyVaultPreparer(name_prefix='cli-test-kv-ct-im-', location='eastus2')
    def test_keyvault_certificate_import(self, resource_group):

        self.kwargs.update({
            'loc': 'eastus2'
        })

        # test certificate import
        self.kwargs.update({
            'pem_encrypted_file': os.path.join(TEST_DIR, 'import_pem_encrypted_pwd_1234.pem'),
            'pem_encrypted_password': '1234',
            'pem_plain_file': os.path.join(TEST_DIR, 'import_pem_plain.pem'),
            'pem_policy_path': os.path.join(TEST_DIR, 'policy_import_pem.json')
        })

        self.cmd('keyvault certificate import --vault-name {kv} -n pem-cert1 --file "{pem_plain_file}" -p @"{pem_policy_path}"')
        self.cmd('keyvault certificate import --vault-name {kv} -n pem-cert2 --file "{pem_encrypted_file}" --password {pem_encrypted_password} -p @"{pem_policy_path}"')

        # self.kwargs.update({
        #     'pfx_plain_file': os.path.join(TEST_DIR, 'import_pfx.pfx'),
        #     'pfx_policy_path': os.path.join(TEST_DIR, 'policy_import_pfx.json')
        # })
        # self.cmd('keyvault certificate import --vault-name {kv} -n pfx-cert --file "{pfx_plain_file}" -p @"{pfx_policy_path}"')


# TODO: Convert to ScenarioTest and re-record when issue #5146 is fixed.
class KeyVaultSoftDeleteScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_sd')
    def test_keyvault_softdelete(self, resource_group):

        self.kwargs.update({
            'kv': self.create_random_name('cli-test-kv-sd-', 24),
            'loc': 'eastus2'
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

        self.cmd('keyvault set-policy -n {kv} --object-id {obj_id} --key-permissions {key_perms} --secret-permissions {secret_perms} --certificate-permissions {cert_perms}')

        # create secrets keys and certifictes to delete recover and purge
        self.cmd('keyvault secret set --vault-name {kv} -n secret1 --value ABC123',
                 checks=self.check('value', 'ABC123'))
        self.cmd('keyvault secret set --vault-name {kv} -n secret2 --value ABC123',
                 checks=self.check('value', 'ABC123'))

        self.cmd('keyvault key create --vault-name {kv} -n key1 -p software',
                 checks=self.check('attributes.enabled', True))
        self.cmd('keyvault key create --vault-name {kv} -n key2 -p software',
                 checks=self.check('attributes.enabled', True))

        self.kwargs.update({
            'pem_plain_file': os.path.join(TEST_DIR, 'import_pem_plain.pem'),
            'pem_policy_path': os.path.join(TEST_DIR, 'policy_import_pem.json')
        })
        self.cmd('keyvault certificate import --vault-name {kv} -n cert1 --file "{pem_plain_file}" -p @"{pem_policy_path}"')
        self.cmd('keyvault certificate import --vault-name {kv} -n cert2 --file "{pem_plain_file}" -p @"{pem_policy_path}"')

        # delete the secrets keys and certficates
        self.cmd('keyvault secret delete --vault-name {kv} -n secret1')
        self.cmd('keyvault secret delete --vault-name {kv} -n secret2')
        self.cmd('keyvault key delete --vault-name {kv} -n key1')
        self.cmd('keyvault key delete --vault-name {kv} -n key2')
        self.cmd('keyvault certificate delete --vault-name {kv} -n cert1')
        self.cmd('keyvault certificate delete --vault-name {kv} -n cert2')

        time.sleep(200)

        # recover secrets keys and certificates
        self.cmd('keyvault secret recover --vault-name {kv} -n secret1')
        self.cmd('keyvault key recover --vault-name {kv} -n key1')
        self.cmd('keyvault certificate recover --vault-name {kv} -n cert1')

        # purge secrets keys and certificates
        self.cmd('keyvault secret purge --vault-name {kv} -n secret2')
        self.cmd('keyvault key purge --vault-name {kv} -n key2')
        self.cmd('keyvault certificate purge --vault-name {kv} -n cert2')

        # delete and purge the vault
        self.cmd('keyvault delete -n {kv}')
        self.cmd('keyvault purge -n {kv} -l {loc}')


if __name__ == '__main__':
    unittest.main()
