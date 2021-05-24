# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import time
import unittest
from datetime import datetime, timedelta
from dateutil import tz

from azure.cli.testsdk import ResourceGroupPreparer, ScenarioTest, LiveScenarioTest

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
KEYS_DIR = os.path.join(TEST_DIR, 'keys')


def _create_keyvault(test, kwargs, additional_args=None):
    # need premium KeyVault to store keys in HSM
    # if --enable-soft-delete is not specified, turn that off to prevent the tests from leaving waste behind
    if additional_args is None:
        additional_args = ''
    if '--enable-soft-delete' not in additional_args:
        additional_args += ' --enable-soft-delete false'
    kwargs['add'] = additional_args
    return test.cmd('keyvault create -g {rg} -n {kv} -l {loc} --sku premium {add}')


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
    @unittest.skip("Need to check this")
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
        keyvault = self.cmd('keyvault create -g {rg} -n {kv} -l {loc} --enable-soft-delete false', checks=[
            self.check('name', '{kv}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}'),
            self.check('type(properties.accessPolicies)', 'array'),
            self.check('length(properties.accessPolicies)', 1),
            self.check('properties.sku.name', 'standard'),
            self.check('properties.enableSoftDelete', False),
            self.check('properties.enablePurgeProtection', None),
            self.check('properties.softDeleteRetentionInDays', 90)
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
        self.cmd('keyvault update -g {rg} -n {kv} --enable-soft-delete '
                 '--enabled-for-deployment --enabled-for-disk-encryption --enabled-for-template-deployment '
                 '--bypass AzureServices --default-action Deny',
                 checks=[
                     self.check('name', '{kv}'),
                     self.check('properties.enableSoftDelete', True),
                     self.check('properties.enablePurgeProtection', None),
                     self.check('properties.enabledForDeployment', True),
                     self.check('properties.enabledForDiskEncryption', True),
                     self.check('properties.enabledForTemplateDeployment', True),
                     self.check('properties.networkAcls.bypass', 'AzureServices'),
                     self.check('properties.networkAcls.defaultAction', 'Deny')
                 ])
        # test policy set/delete
        self.cmd('keyvault set-policy -g {rg} -n {kv} --object-id {policy_id} --key-permissions get wrapkey wrapKey',
                 checks=self.check('length(properties.accessPolicies[0].permissions.keys)', 2))
        self.cmd('keyvault set-policy -g {rg} -n {kv} --object-id {policy_id} --key-permissions get wrapkey wrapkey',
                 checks=self.check('length(properties.accessPolicies[0].permissions.keys)', 2))
        self.cmd('keyvault set-policy -g {rg} -n {kv} --object-id {policy_id} --certificate-permissions get list',
                 checks=self.check('length(properties.accessPolicies[0].permissions.certificates)', 2))
        self.cmd('keyvault delete-policy -g {rg} -n {kv} --object-id {policy_id}', checks=[
            self.check('type(properties.accessPolicies)', 'array'),
            self.check('length(properties.accessPolicies)', 0)
        ])

        # test keyvault delete
        self.cmd('keyvault delete -n {kv}')
        self.cmd('keyvault list -g {rg}', checks=self.is_empty())
        self.cmd('keyvault purge -n {kv}')
        # ' will be parsed by shlex, so need escaping
        self.cmd(r"az keyvault list-deleted --query [?name==\'{kv}\']", checks=self.is_empty())

        # test create keyvault further
        self.cmd('keyvault create -g {rg} -n {kv2} -l {loc} '  # enableSoftDelete is True if omitted
                 '--retention-days 7 '
                 '--sku premium '
                 '--enabled-for-deployment true --enabled-for-disk-encryption true --enabled-for-template-deployment true '
                 '--no-self-perms ',  # no self permission assigned
                 checks=[
                     self.check('properties.enableSoftDelete', True),
                     self.check('properties.softDeleteRetentionInDays', 7),
                     self.check('properties.sku.name', 'premium'),
                     self.check('properties.enabledForDeployment', True),
                     self.check('properties.enabledForDiskEncryption', True),
                     self.check('properties.enabledForTemplateDeployment', True),
                     self.check('type(properties.accessPolicies)', 'array'),
                     self.check('length(properties.accessPolicies)', 0),
                 ])
        self.cmd('keyvault delete -n {kv2}')
        self.cmd('keyvault purge -n {kv2}')

        # test explicitly set '--enable-soft-delete true --enable-purge-protection true'
        # unfortunately this will leave some waste behind, so make it the last test to lowered the execution count
        self.cmd('keyvault create -g {rg} -n {kv4} -l {loc} --enable-soft-delete true --enable-purge-protection true',
                 checks=[self.check('properties.enableSoftDelete', True),
                         self.check('properties.enablePurgeProtection', True)])

        # test '--enable-rbac-authorization'
        # temporarily disable this since our test subscription doesn't support RBAC authorization
        """
        self.kwargs.update({
            'kv': self.create_random_name('cli-test-keyvault-', 24),
            'loc': 'eastus2'
        })
        _create_keyvault(self, self.kwargs, additional_args='--enable-rbac-authorization')

        self.cmd('keyvault show -n {kv}', checks=self.check('properties.enableRbacAuthorization', True))

        with self.assertRaises(CLIError):
            self.cmd('keyvault set-policy -n {kv} --object-id 00000000-0000-0000-0000-000000000000 '
                     '--key-permissions get')
        with self.assertRaises(CLIError):
            self.cmd('keyvault delete-policy -n {kv} --object-id 00000000-0000-0000-0000-000000000000')

        self.cmd('keyvault update -n {kv} --enable-rbac-authorization false',
                 checks=self.check('properties.enableRbacAuthorization', False))
        self.cmd('keyvault update -n {kv} --enable-rbac-authorization true',
                 checks=self.check('properties.enableRbacAuthorization', True))
        """


# class KeyVaultKeyScenarioTest(ScenarioTest):
#     @ResourceGroupPreparer(name_prefix='cli_test_keyvault_key', location='westus')
#     def test_keyvault_key(self, resource_group):
#         self.kwargs.update({
#             'kv': self.create_random_name('cli-test-kv-key-', 24),
#             'loc': 'westus',
#             'key': 'key1'
#         })
#         keyvault = _create_keyvault(self, self.kwargs).get_output_in_json()
#         self.kwargs['obj_id'] = keyvault['properties']['accessPolicies'][0]['objectId']
#         key_perms = keyvault['properties']['accessPolicies'][0]['permissions']['keys']
#         key_perms.extend(['encrypt', 'decrypt'])
#         self.kwargs['key_perms'] = ' '.join(key_perms)

#         # create a key
#         key = self.cmd('keyvault key create --vault-name {kv} -n {key} -p software',
#                        checks=self.check('attributes.enabled', True)).get_output_in_json()
#         first_kid = key['key']['kid']
#         first_version = first_kid.rsplit('/', 1)[1]

#         # encrypt/decrypt
#         self.cmd('keyvault set-policy -n {kv} --object-id {obj_id} --key-permissions {key_perms}')
#         self.kwargs['plaintext_value'] = 'abcdef'
#         self.kwargs['base64_value'] = 'YWJjZGVm'
#         self.kwargs['encryption_result1'] = self.cmd('keyvault key encrypt -n {key} --vault-name {kv} -a RSA-OAEP --value "{plaintext_value}" --data-type plaintext').get_output_in_json()['result']
#         self.kwargs['encryption_result2'] = self.cmd('keyvault key encrypt -n {key} --vault-name {kv} -a RSA-OAEP --value "{base64_value}" --data-type base64').get_output_in_json()['result']
#         self.cmd('keyvault key decrypt -n {key} --vault-name {kv} -a RSA-OAEP --value "{encryption_result1}" --data-type plaintext',
#                  checks=self.check('result', '{plaintext_value}'))
#         self.cmd('keyvault key decrypt -n {key} --vault-name {kv} -a RSA-OAEP --value "{encryption_result2}" --data-type base64',
#                  checks=self.check('result', '{base64_value}'))

#         # list keys
#         self.cmd('keyvault key list --vault-name {kv}',
#                  checks=[
#                      self.check('length(@)', 1),
#                      self.exists('[0].name')
#                  ])
#         self.cmd('keyvault key list --vault-name {kv} --maxresults 10',
#                  checks=self.check('length(@)', 1))

#         # create a new key version
#         key = self.cmd('keyvault key create --vault-name {kv} -n {key} -p software --disabled --ops encrypt decrypt '
#                        '--tags test=foo',
#                        checks=[
#                            self.check('attributes.enabled', False),
#                            self.check('length(key.keyOps)', 2),
#                            self.check('tags', {'test': 'foo'})
#                        ]).get_output_in_json()
#         second_kid = key['key']['kid']
#         pure_kid = '/'.join(second_kid.split('/')[:-1])  # Remove version field
#         self.kwargs['kid'] = second_kid
#         self.kwargs['pkid'] = pure_kid

#         # list key versions
#         self.cmd('keyvault key list-versions --vault-name {kv} -n {key}',
#                  checks=self.check('length(@)', 2))
#         self.cmd('keyvault key list-versions --vault-name {kv} -n {key} --maxresults 10',
#                  checks=self.check('length(@)', 2))
#         self.cmd('keyvault key list-versions --id {kid}', checks=self.check('length(@)', 2))
#         self.cmd('keyvault key list-versions --id {pkid}', checks=self.check('length(@)', 2))

#         # show key (latest)
#         self.cmd('keyvault key show --vault-name {kv} -n {key}',
#                  checks=self.check('key.kid', second_kid))

#         # show key (specific version)
#         self.kwargs.update({
#             'version1': first_version,
#             'kid1': first_kid,
#             'kid2': second_kid
#         })
#         self.cmd('keyvault key show --vault-name {kv} -n {key} -v {version1}',
#                  checks=self.check('key.kid', '{kid1}'))

#         # show key (by id)
#         self.cmd('keyvault key show --id {kid1}',
#                  checks=self.check('key.kid', '{kid1}'))

#         # set key attributes
#         self.cmd('keyvault key set-attributes --vault-name {kv} -n {key} --enabled true', checks=[
#             self.check('key.kid', '{kid2}'),
#             self.check('attributes.enabled', True)
#         ])

#         # backup and then delete key
#         key_file = 'backup.key'
#         self.kwargs['key_file'] = key_file
#         self.cmd('keyvault key backup --vault-name {kv} -n {key} --file {key_file}')
#         self.cmd('keyvault key delete --vault-name {kv} -n {key}')
#         self.cmd('keyvault key list --vault-name {kv}', checks=self.is_empty())
#         self.cmd('keyvault key list --vault-name {kv} --maxresults 10', checks=self.is_empty())

#         # restore key from backup
#         self.cmd('keyvault key restore --vault-name {kv} --file {key_file}')
#         self.cmd('keyvault key list-versions --vault-name {kv} -n {key}',
#                  checks=[
#                      self.check('length(@)', 2),
#                      self.exists('[0].name'),
#                      self.exists('[1].name')
#                  ])
#         self.cmd('keyvault key list-versions --vault-name {kv} -n {key} --maxresults 10',
#                  checks=self.check('length(@)', 2))
#         if os.path.isfile(key_file):
#             os.remove(key_file)

#         # import PEM from file
#         self.kwargs.update({
#             'key_enc_file': os.path.join(TEST_DIR, 'mydomain.test.encrypted.pem'),
#             'key_enc_password': 'password',
#             'key_plain_file': os.path.join(TEST_DIR, 'mydomain.test.pem')
#         })
#         self.cmd('keyvault key import --vault-name {kv} -n import-key-plain --pem-file "{key_plain_file}" -p software')
#         self.cmd('keyvault key import --vault-name {kv} -n import-key-encrypted --pem-file "{key_enc_file}" --pem-password {key_enc_password} -p hsm')

#         # import PEM from string
#         with open(os.path.join(TEST_DIR, 'mydomain.test.encrypted.pem'), 'rb') as f:
#             key_enc_string = f.read().decode('UTF-8')
#         with open(os.path.join(TEST_DIR, 'mydomain.test.pem'), 'rb') as f:
#             key_plain_string = f.read().decode('UTF-8')
#         self.kwargs.update({
#             'key_enc_string': key_enc_string,
#             'key_enc_password': 'password',
#             'key_plain_string': key_plain_string
#         })
#         self.cmd("keyvault key import --vault-name {kv} -n import-key-plain --pem-string '{key_plain_string}' -p software")
#         self.cmd('keyvault key import --vault-name {kv} -n import-key-encrypted --pem-string "{key_enc_string}" --pem-password {key_enc_password} -p hsm')

#         # create ec keys
#         self.cmd('keyvault key create --vault-name {kv} -n eckey1 --kty EC',
#                  checks=self.check('key.kty', 'EC'))
#         self.cmd('keyvault key create --vault-name {kv} -n eckey1 --curve P-256',
#                  checks=[self.check('key.kty', 'EC'), self.check('key.crv', 'P-256')])
#         self.cmd('keyvault key delete --vault-name {kv} -n eckey1')

#         # import ec PEM
#         self.kwargs.update({
#             'key_enc_file': os.path.join(TEST_DIR, 'ec521pw.pem'),
#             'key_enc_password': 'pass1234',
#             'key_plain_file': os.path.join(TEST_DIR, 'ec256.pem')
#         })
#         self.cmd('keyvault key import --vault-name {kv} -n import-eckey-plain --pem-file "{key_plain_file}" -p software',
#                  checks=[self.check('key.kty', 'EC'), self.check('key.crv', 'P-256')])
#         self.cmd('keyvault key import --vault-name {kv} -n import-eckey-encrypted --pem-file "{key_enc_file}" --pem-password {key_enc_password}',
#                  checks=[self.check('key.kty', 'EC'), self.check('key.crv', 'P-521')])

#         self.kwargs.update({
#             'kv': self.create_random_name('cli-test-kv-key-', 24),
#             'loc': 'westus'
#         })
#         _create_keyvault(self, self.kwargs)

#         # create KEK
#         self.cmd('keyvault key create --vault-name {kv} --name key1 --kty RSA-HSM --size 2048 --ops import',
#                  checks=[self.check('key.kty', 'RSA-HSM'), self.check('key.keyOps', ['import'])])
#         self.cmd('keyvault key create --vault-name {kv} --name key2 --kty RSA-HSM --size 3072 --ops import',
#                  checks=[self.check('key.kty', 'RSA-HSM'), self.check('key.keyOps', ['import'])])
#         self.cmd('keyvault key create --vault-name {kv} --name key2 --kty RSA-HSM --size 4096 --ops import',
#                  checks=[self.check('key.kty', 'RSA-HSM'), self.check('key.keyOps', ['import'])])


# class KeyVaultSecretSoftDeleteScenarioTest(ScenarioTest):
#     @ResourceGroupPreparer(name_prefix='cli_test_keyvault_secret_soft_delete')
#     def test_keyvault_secret_soft_delete(self, resource_group):
#         self.kwargs.update({
#             'kv': self.create_random_name('cli-test-kv-se-sd-', 24),
#             'loc': 'westus',
#             'sec': 'secret1'
#         })
#         _create_keyvault(self, self.kwargs, additional_args='--enable-soft-delete')
#         self.cmd('keyvault show -n {kv}', checks=self.check('properties.enableSoftDelete', True))

#         max_timeout = 100
#         time_counter = 0
#         while time_counter <= max_timeout:
#             try:
#                 # show deleted
#                 self.cmd('keyvault secret set --vault-name {kv} -n {sec} --value ABC123',
#                          checks=self.check('value', 'ABC123'))
#                 data = self.cmd('keyvault secret delete --vault-name {kv} -n {sec}').get_output_in_json()
#                 self.kwargs['secret_id'] = data['id']
#                 self.kwargs['secret_recovery_id'] = data['recoveryId']
#                 self.cmd('keyvault secret list-deleted --vault-name {kv}', checks=self.check('length(@)', 1))
#                 self.cmd('keyvault secret list-deleted --vault-name {kv} --maxresults 10',
#                          checks=self.check('length(@)', 1))
#                 self.cmd('keyvault secret show-deleted --id {secret_recovery_id}',
#                          checks=self.check('id', '{secret_id}'))
#                 self.cmd('keyvault secret show-deleted --vault-name {kv} -n {sec}',
#                          checks=self.check('id', '{secret_id}'))
#             except:  # pylint: disable=bare-except
#                 time.sleep(10)
#                 time_counter += 10
#             else:
#                 break


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

    # @ResourceGroupPreparer(name_prefix='cli_test_keyvault_secret')
    # def test_keyvault_secret(self, resource_group):
    #     self.kwargs.update({
    #         'kv': self.create_random_name('cli-test-kv-se-', 24),
    #         'loc': 'westus',
    #         'sec': 'secret1'
    #     })
    #     _create_keyvault(self, self.kwargs)

    #     # create a secret
    #     secret = self.cmd('keyvault secret set --vault-name {kv} -n {sec} --value ABC123',
    #                       checks=self.check('value', 'ABC123')).get_output_in_json()
    #     first_sid = secret['id']
    #     first_sname = first_sid.split('/')[4]
    #     first_version = first_sid.rsplit('/', 1)[1]
    #     self.kwargs.update({
    #         'sid1': first_sid,
    #         'ver1': first_version
    #     })

    #     # list secrets
    #     self.cmd('keyvault secret list --vault-name {kv}',
    #              checks=[
    #                  self.check('length(@)', 1),
    #                  self.check('[0].name', first_sname)
    #              ])
    #     self.cmd('keyvault secret list --vault-name {kv} --maxresults 10', checks=self.check('length(@)', 1))

    #     # create a new secret version
    #     secret = self.cmd('keyvault secret set --vault-name {kv} -n {sec} --value DEF456 --tags test=foo --description "test type"', checks=[
    #         self.check('value', 'DEF456'),
    #         self.check('tags', {'file-encoding': 'utf-8', 'test': 'foo'}),
    #         self.check('contentType', 'test type'),
    #         self.check('name', first_sname)
    #     ]).get_output_in_json()
    #     self.kwargs['sid2'] = secret['id']

    #     # list secret versions
    #     self.cmd('keyvault secret list-versions --vault-name {kv} -n {sec}',
    #              checks=self.check('length(@)', 2))
    #     self.cmd('keyvault secret list-versions --vault-name {kv} -n {sec} --maxresults 10',
    #              checks=self.check('length(@)', 2))

    #     # show secret (latest)
    #     self.cmd('keyvault secret show --vault-name {kv} -n {sec}',
    #              checks=[
    #                  self.check('id', '{sid2}'),
    #                  self.check('name', '{sec}')
    #              ])

    #     # show secret (specific version)
    #     self.cmd('keyvault secret show --vault-name {kv} -n {sec} -v {ver1}',
    #              checks=self.check('id', '{sid1}'))

    #     # show secret (by id)
    #     self.cmd('keyvault secret show --id {sid1}',
    #              checks=self.check('id', '{sid1}'))

    #     # set secret attributes
    #     self.cmd('keyvault secret set-attributes --vault-name {kv} -n {sec} --enabled false', checks=[
    #         self.check('id', '{sid2}'),
    #         self.check('attributes.enabled', False),
    #         self.check('name', '{sec}')
    #     ])

    #     # backup and then delete secret
    #     bak_file = 'backup.secret'
    #     self.kwargs['bak_file'] = bak_file
    #     self.cmd('keyvault secret backup --vault-name {kv} -n {sec} --file {bak_file}')
    #     self.cmd('keyvault secret delete --vault-name {kv} -n {sec}', checks=self.check('name', '{sec}'))
    #     self.cmd('keyvault secret list --vault-name {kv}', checks=self.is_empty())

    #     # restore secret from backup
    #     self.cmd('keyvault secret restore --vault-name {kv} --file {bak_file}', checks=self.check('name', '{sec}'))
    #     self.cmd('keyvault secret list-versions --vault-name {kv} -n {sec}',
    #              checks=self.check('length(@)', 2))
    #     if os.path.isfile(bak_file):
    #         os.remove(bak_file)

    #     # delete secret
    #     self.cmd('keyvault secret delete --vault-name {kv} -n {sec}')
    #     self.cmd('keyvault secret list --vault-name {kv}', checks=self.is_empty())
    #     self.cmd('keyvault secret list --vault-name {kv} --maxresults 10', checks=self.is_empty())

    #     self._test_download_secret()


# class KeyVaultCertificateContactsScenarioTest(ScenarioTest):
#     @ResourceGroupPreparer(name_prefix='cli_test_kv_cert_contacts')
#     def test_keyvault_certificate_contacts(self, resource_group):
#         self.kwargs.update({
#             'kv': self.create_random_name('cli-test-kv-ct-co-', 24),
#             'loc': 'westus'
#         })

#         _create_keyvault(self, self.kwargs)

#         self.cmd('keyvault certificate contact add --vault-name {kv} --email admin@contoso.com --name "John Doe" --phone 123-456-7890')
#         self.cmd('keyvault certificate contact add --vault-name {kv} --email other@contoso.com ')
#         self.cmd('keyvault certificate contact list --vault-name {kv}',
#                  checks=self.check('length(contactList)', 2))
#         self.cmd('keyvault certificate contact delete --vault-name {kv} --email admin@contoso.com')
#         self.cmd('keyvault certificate contact list --vault-name {kv}', checks=[
#             self.check('length(contactList)', 1),
#             self.check('contactList[0].emailAddress', 'other@contoso.com')
#         ])


# class KeyVaultCertificateIssuerScenarioTest(ScenarioTest):
#     @ResourceGroupPreparer(name_prefix='cli_test_kv_cert_issuer')
#     def test_keyvault_certificate_issuers(self, resource_group):
#         self.kwargs.update({
#             'kv': self.create_random_name('cli-test-kv-ct-is-', 24),
#             'loc': 'westus'
#         })

#         _create_keyvault(self, self.kwargs)

#         self.cmd('keyvault certificate issuer create --vault-name {kv} --issuer-name issuer1 --provider Test', checks=[
#             self.check('provider', 'Test'),
#             self.check('attributes.enabled', True)
#         ])
#         self.cmd('keyvault certificate issuer show --vault-name {kv} --issuer-name issuer1', checks=[
#             self.check('provider', 'Test'),
#             self.check('attributes.enabled', True)
#         ])
#         self.cmd('keyvault certificate issuer update --vault-name {kv} --issuer-name issuer1 --organization-id TestOrg --account-id test_account', checks=[
#             self.check('provider', 'Test'),
#             self.check('attributes.enabled', True),
#             self.check('organizationDetails.id', 'TestOrg'),
#             self.check('credentials.accountId', 'test_account')
#         ])
#         with self.assertRaises(CLIError):
#             self.cmd('keyvault certificate issuer update --vault-name {kv} --issuer-name notexist --organization-id TestOrg --account-id test_account')
#         self.cmd('keyvault certificate issuer update --vault-name {kv} --issuer-name issuer1 --account-id ""', checks=[
#             self.check('provider', 'Test'),
#             self.check('attributes.enabled', True),
#             self.check('organizationDetails.id', 'TestOrg'),
#             self.check('credentials.accountId', None)
#         ])
#         self.cmd('keyvault certificate issuer list --vault-name {kv}',
#                  checks=self.check('length(@)', 1))

#         # test admin commands
#         self.cmd('keyvault certificate issuer admin add --vault-name {kv} --issuer-name issuer1 --email test@test.com --first-name Test --last-name Admin --phone 123-456-7890', checks=[
#             self.check('emailAddress', 'test@test.com'),
#             self.check('firstName', 'Test'),
#             self.check('lastName', 'Admin'),
#             self.check('phone', '123-456-7890'),
#         ])
#         self.cmd('keyvault certificate issuer admin add --vault-name {kv} --issuer-name issuer1 --email test2@test.com', checks=[
#             self.check('emailAddress', 'test2@test.com'),
#             self.check('firstName', None),
#             self.check('lastName', None),
#             self.check('phone', None),
#         ])
#         self.cmd('keyvault certificate issuer admin list --vault-name {kv} --issuer-name issuer1',
#                  checks=self.check('length(@)', 2))
#         self.cmd('keyvault certificate issuer admin delete --vault-name {kv} --issuer-name issuer1 --email test@test.com')
#         self.cmd('keyvault certificate issuer admin list --vault-name {kv} --issuer-name issuer1',
#                  checks=self.check('length(@)', 1))

#         self.cmd('keyvault certificate issuer delete --vault-name {kv} --issuer-name issuer1')
#         self.cmd('keyvault certificate issuer list --vault-name {kv}', checks=self.is_empty())


# class KeyVaultPendingCertificateScenarioTest(ScenarioTest):
#     @ResourceGroupPreparer(name_prefix='cli_test_kv_cert_pending')
#     def test_keyvault_pending_certificate(self, resource_group):
#         self.kwargs.update({
#             'kv': self.create_random_name('cli-test-kv-ct-pe-', 24),
#             'loc': 'westus',
#             'policy_path': os.path.join(TEST_DIR, 'policy_pending.json')
#         })

#         _create_keyvault(self, self.kwargs)

#         self.kwargs['fake_cert_path'] = os.path.join(TEST_DIR, 'import_pem_plain.pem')
#         self.cmd('keyvault certificate create --vault-name {kv} -n pending-cert -p @"{policy_path}"', checks=[
#             self.check('statusDetails', 'Pending certificate created. Please Perform Merge to complete the request.'),
#             self.check('cancellationRequested', False),
#             self.check('status', 'inProgress'),
#             self.check('name', 'pending-cert')
#         ])
#         self.cmd('keyvault certificate pending show --vault-name {kv} -n pending-cert', checks=[
#             self.check('statusDetails', 'Pending certificate created. Please Perform Merge to complete the request.'),
#             self.check('cancellationRequested', False),
#             self.check('status', 'inProgress'),
#             self.check('name', 'pending-cert')
#         ])

#         # we do not have a way of actually getting a certificate that would pass this test so
#         # we simply ensure that the payload successfully serializes and is received by the server
#         with self.assertRaises(CLIError):
#             self.cmd('keyvault certificate pending merge --vault-name {kv} -n pending-cert --file "{fake_cert_path}"')
#         self.cmd('keyvault certificate pending delete --vault-name {kv} -n pending-cert',
#                  checks=self.check('name', 'pending-cert'))

#         self.cmd('keyvault certificate pending show --vault-name {kv} -n pending-cert', expect_failure=True)


# TODO: Convert to ScenarioTest and re-record when issue #5146 is fixed.
# class KeyVaultCertificateDownloadScenarioTest(ScenarioTest):
#     @ResourceGroupPreparer(name_prefix='cli_test_kv_cert_download')
#     def test_keyvault_certificate_download(self, resource_group):
#         import OpenSSL.crypto

#         self.kwargs.update({
#             'kv': self.create_random_name('cli-test-kv-ct-dl-', 24),
#             'loc': 'eastus2'
#         })

#         _create_keyvault(self, self.kwargs)

#         pem_file = os.path.join(TEST_DIR, 'import_pem_plain.pem')
#         pem_policy_path = os.path.join(TEST_DIR, 'policy_import_pem.json')
#         self.kwargs.update({
#             'pem_file': pem_file,
#             'pem_policy_path': pem_policy_path
#         })
#         pem_cert = self.cmd('keyvault certificate import --vault-name {kv} -n pem-cert1 --file "{pem_file}" -p @"{pem_policy_path}"').get_output_in_json()
#         cert_data = pem_cert['cer']

#         dest_binary = os.path.join(TEST_DIR, 'download-binary')
#         dest_string = os.path.join(TEST_DIR, 'download-string')
#         self.kwargs.update({
#             'dest_binary': dest_binary,
#             'dest_string': dest_string
#         })

#         expected_pem = "-----BEGIN CERTIFICATE-----\n" + \
#                        cert_data + \
#                        '-----END CERTIFICATE-----\n'
#         expected_pem = expected_pem.replace('\n', '')

#         try:
#             self.cmd('keyvault certificate download --vault-name {kv} -n pem-cert1 --file "{dest_binary}" -e DER')
#             self.cmd('keyvault certificate download --vault-name {kv} -n pem-cert1 --file "{dest_string}" -e PEM')
#             self.cmd('keyvault certificate delete --vault-name {kv} -n pem-cert1')

#             def verify(path, file_type):
#                 with open(path, 'rb') as f:
#                     x509 = OpenSSL.crypto.load_certificate(file_type, f.read())
#                     actual_pem = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, x509)
#                     if isinstance(actual_pem, bytes):
#                         actual_pem = actual_pem.decode("utf-8")
#                     self.assertIn(expected_pem, actual_pem.replace('\n', ''))

#             verify(dest_binary, OpenSSL.crypto.FILETYPE_ASN1)
#             verify(dest_string, OpenSSL.crypto.FILETYPE_PEM)
#         finally:
#             if os.path.exists(dest_binary):
#                 os.remove(dest_binary)
#             if os.path.exists(dest_string):
#                 os.remove(dest_string)


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


# class KeyVaultCertificateScenarioTest(ScenarioTest):
#     @ResourceGroupPreparer(name_prefix='cli_test_keyvault_cert')
#     def test_keyvault_certificate_crud(self, resource_group):
#         self.kwargs.update({
#             'kv': self.create_random_name('cli-test-kv-ct-', 24),
#             'loc': 'westus'
#         })

#         keyvault = _create_keyvault(self, self.kwargs).get_output_in_json()
#         self.kwargs['obj_id'] = keyvault['properties']['accessPolicies'][0]['objectId']

#         policy_path = os.path.join(TEST_DIR, 'policy.json')
#         policy2_path = os.path.join(TEST_DIR, 'policy2.json')
#         policy3_path = os.path.join(TEST_DIR, 'policy3.json')
#         cert_secret_path = os.path.join(TEST_DIR, 'cert_secret')
#         self.kwargs.update({
#             'policy_path': policy_path,
#             'policy2_path': policy2_path,
#             'policy3_path': policy3_path,
#             'cert_secret_path': cert_secret_path
#         })

#         # create certificates
#         self.cmd('keyvault certificate create --vault-name {kv} -n cert1 -p @"{policy_path}"',
#                  checks=[
#                      self.check('status', 'completed'),
#                      self.check('name', 'cert1')
#                  ])
#         self.cmd('keyvault certificate create --vault-name {kv} -n cert2 -p @"{policy_path}"',
#                  checks=[
#                      self.check('status', 'completed'),
#                      self.check('name', 'cert2')
#                  ])

#         # import with same policy
#         policy = self.cmd('keyvault certificate show --vault-name {kv} -n cert2 --query policy').get_output_in_json()
#         if not os.path.exists(policy3_path) or self.is_live:
#             with open(policy3_path, "w") as f:
#                 f.write(json.dumps(policy))

#         if not os.path.exists(cert_secret_path) or self.is_live:
#             if os.path.exists(cert_secret_path):
#                 os.remove(cert_secret_path)
#             self.cmd('keyvault secret download --vault-name {kv} --file "{cert_secret_path}" -n cert2 --encoding base64')

#         self.cmd('keyvault certificate import --vault-name {kv} --file "{cert_secret_path}" -n cert2 -p @"{policy3_path}"',
#                  checks=[
#                      self.check('name', 'cert2'),
#                      self.check('policy.secretProperties.contentType',
#                                 policy['secretProperties']['contentType'])
#                  ])
#         self.cmd('keyvault certificate delete --vault-name {kv} -n cert2')

#         # list certificates
#         self.cmd('keyvault certificate list --vault-name {kv}',
#                  checks=[
#                      self.check('length(@)', 1),
#                      self.check('[0].name', 'cert1')
#                  ])
#         self.cmd('keyvault certificate list --vault-name {kv} --maxresults 10',
#                  checks=self.check('length(@)', 1))

#         # create a new certificate version
#         self.cmd('keyvault certificate create --vault-name {kv} -n cert1 -p @"{policy2_path}"', checks=[
#             self.check('status', 'completed'),
#         ])

#         # list certificate versions
#         self.cmd('keyvault certificate list-versions --vault-name {kv} -n cert1 --maxresults 10',
#                  checks=[
#                      self.check('length(@)', 2),
#                      self.check('[0].name', 'cert1')
#                  ])
#         ver_list = self.cmd('keyvault certificate list-versions --vault-name {kv} -n cert1',
#                             checks=self.check('length(@)', 2)).get_output_in_json()

#         ver_list = sorted(ver_list, key=lambda x: x['attributes']['created'])
#         versions = [x['id'] for x in ver_list]

#         # show certificate (latest)
#         self.cmd('keyvault certificate show --vault-name {kv} -n cert1', checks=[
#             self.check('id', versions[1]),
#             self.check('policy.x509CertificateProperties.validityInMonths', 50),
#             self.check('name', 'cert1')
#         ])

#         # show certificate (specific version)
#         cert_version = versions[0].rsplit('/', 1)[1]
#         self.kwargs['ver1'] = cert_version
#         self.cmd('keyvault certificate show --vault-name {kv} -n cert1 -v {ver1}',
#                  checks=self.check('id', versions[0]))

#         # show certificate (by id)
#         self.kwargs.update({'cert_id': versions[0]})
#         self.cmd('keyvault certificate show --id {cert_id}',
#                  checks=self.check('id', versions[0]))

#         # plan to not display the managed keys/secrets
#         self.cmd('keyvault key list --vault-name {kv}', checks=self.is_empty())
#         self.cmd('keyvault secret list --vault-name {kv}', checks=self.is_empty())
#         self.cmd('keyvault key show --vault-name {kv} -n cert1',
#                  checks=self.check('managed', True))
#         self.cmd('keyvault secret show --vault-name {kv} -n cert1',
#                  checks=self.check('managed', True))

#         # update certificate attributes
#         self.cmd('keyvault certificate set-attributes --vault-name {kv} -n cert1 --enabled false -p @"{policy_path}"', checks=[
#             self.check('id', versions[1]),
#             self.check('attributes.enabled', False),
#             self.check('policy.x509CertificateProperties.validityInMonths', 60),
#             self.check('name', 'cert1')
#         ])

#         # delete certificate
#         self.cmd('keyvault certificate delete --vault-name {kv} -n cert1')


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
# class KeyVaultCertificateImportScenario(ScenarioTest):
#     @ResourceGroupPreparer(name_prefix='cli_test_keyvault_cert_import')
#     def test_keyvault_certificate_import(self, resource_group):
#         self.kwargs.update({
#             'kv': self.create_random_name('cli-test-kv-ct-im-', 24),
#             'loc': 'eastus2'
#         })

#         _create_keyvault(self, self.kwargs)

#         # Create certificate with encrypted key
#         # openssl req -newkey rsa:2048 -nodes -keyout key.pem -x509 -days 3650 -out cert.pem
#         # openssl pkcs8 -in key.pem -topk8 -v1 PBE-SHA1-3DES -out key.pem
#         # type key.pem cert.pem > import_pem_encrypted_pwd_1234.pem
#         # del key.pem cert.pem

#         # Create certificate with plain key
#         # openssl req -newkey rsa:2048 -nodes -keyout key.pem -x509 -days 3650 -out cert.pem
#         # type key.pem cert.pem > import_pem_plain.pem
#         # del key.pem cert.pem

#         # test certificate import
#         self.kwargs.update({
#             'pem_encrypted_file': os.path.join(TEST_DIR, 'import_pem_encrypted_pwd_1234.pem'),
#             'pem_encrypted_password': '1234',
#             'pem_plain_file': os.path.join(TEST_DIR, 'import_pem_plain.pem'),
#             'pem_policy_path': os.path.join(TEST_DIR, 'policy_import_pem.json')
#         })

#         self.cmd('keyvault certificate import --vault-name {kv} -n pem-cert1 --file "{pem_plain_file}" -p @"{pem_policy_path}"')
#         self.cmd('keyvault certificate import --vault-name {kv} -n pem-cert2 --file "{pem_encrypted_file}" --password {pem_encrypted_password} -p @"{pem_policy_path}"')

#         # Test certificate file not exist
#         with self.assertRaises(CLIError):
#             self.cmd('keyvault certificate import --vault-name {kv} -n pem-cert2 --file "notexist.json" -p @"{pem_policy_path}"')

#         # self.kwargs.update({
#         #     'pfx_plain_file': os.path.join(TEST_DIR, 'import_pfx.pfx'),
#         #     'pfx_policy_path': os.path.join(TEST_DIR, 'policy_import_pfx.json')
#         # })
#         # self.cmd('keyvault certificate import --vault-name {kv} -n pfx-cert --file "{pfx_plain_file}" -p @"{pfx_policy_path}"')


# TODO: Convert to ScenarioTest and re-record when issue #5146 is fixed.
# class KeyVaultSoftDeleteScenarioTest(ScenarioTest):
#     @ResourceGroupPreparer(name_prefix='cli_test_keyvault_sd')
#     def test_keyvault_softdelete(self, resource_group):
#         self.kwargs.update({
#             'kv': self.create_random_name('cli-test-kv-sd-', 24),
#             'loc': 'eastus2'
#         })

#         vault = _create_keyvault(self, self.kwargs, additional_args=' --enable-soft-delete true').get_output_in_json()

#         # add all purge permissions to default the access policy
#         default_policy = vault['properties']['accessPolicies'][0]
#         cert_perms = default_policy['permissions']['certificates']
#         key_perms = default_policy['permissions']['keys']
#         secret_perms = default_policy['permissions']['secrets']
#         obj_id = default_policy['objectId']

#         for p in [cert_perms, key_perms, secret_perms]:
#             p.append('purge')

#         self.kwargs.update({
#             'obj_id': obj_id,
#             'key_perms': ' '.join(key_perms),
#             'secret_perms': ' '.join(secret_perms),
#             'cert_perms': ' '.join(cert_perms)
#         })

#         self.cmd('keyvault set-policy -n {kv} --object-id {obj_id} --key-permissions {key_perms} --secret-permissions {secret_perms} --certificate-permissions {cert_perms}')

#         # create secrets keys and certificates to delete recover and purge
#         self.cmd('keyvault secret set --vault-name {kv} -n secret1 --value ABC123',
#                  checks=self.check('value', 'ABC123'))
#         self.cmd('keyvault secret set --vault-name {kv} -n secret2 --value ABC123',
#                  checks=self.check('value', 'ABC123'))

#         self.cmd('keyvault key create --vault-name {kv} -n key1 -p software',
#                  checks=self.check('attributes.enabled', True))
#         self.cmd('keyvault key create --vault-name {kv} -n key2 -p software',
#                  checks=self.check('attributes.enabled', True))

#         self.kwargs.update({
#             'pem_plain_file': os.path.join(TEST_DIR, 'import_pem_plain.pem'),
#             'pem_policy_path': os.path.join(TEST_DIR, 'policy_import_pem.json')
#         })
#         self.cmd('keyvault certificate import --vault-name {kv} -n cert1 --file "{pem_plain_file}" -p @"{pem_policy_path}"')
#         self.cmd('keyvault certificate import --vault-name {kv} -n cert2 --file "{pem_plain_file}" -p @"{pem_policy_path}"')

#         # delete the secrets keys and certificates
#         self.cmd('keyvault secret delete --vault-name {kv} -n secret1')
#         self.cmd('keyvault secret delete --vault-name {kv} -n secret2')
#         self.cmd('keyvault key delete --vault-name {kv} -n key1')
#         self.cmd('keyvault key delete --vault-name {kv} -n key2')
#         self.cmd('keyvault certificate delete --vault-name {kv} -n cert1')
#         self.cmd('keyvault certificate delete --vault-name {kv} -n cert2')

#         max_timeout = 100
#         time_counter = 0
#         while time_counter <= max_timeout:
#             try:
#                 # recover secrets keys and certificates
#                 self.cmd('keyvault secret recover --vault-name {kv} -n secret1')
#                 self.cmd('keyvault key recover --vault-name {kv} -n key1')
#                 self.cmd('keyvault certificate recover --vault-name {kv} -n cert1')
#             except:  # pylint: disable=bare-except
#                 time.sleep(10)
#                 time_counter += 10
#             else:
#                 break

#         # purge secrets keys and certificates
#         self.cmd('keyvault secret purge --vault-name {kv} -n secret2')
#         self.cmd('keyvault key purge --vault-name {kv} -n key2')
#         self.cmd('keyvault certificate purge --vault-name {kv} -n cert2')

#         # recover and purge
#         self.cmd('keyvault delete -n {kv}')
#         self.cmd('keyvault recover -n {kv}', checks=self.check('name', '{kv}'))
#         self.cmd('keyvault delete -n {kv}')
#         self.cmd('keyvault purge -n {kv}')

#         # recover and purge with location
#         _create_keyvault(self, self.kwargs, additional_args=' --enable-soft-delete true').get_output_in_json()
#         self.cmd('keyvault delete -n {kv}')
#         self.cmd('keyvault recover -n {kv} -l {loc}', checks=self.check('name', '{kv}'))
#         self.cmd('keyvault delete -n {kv}')
#         self.cmd('keyvault purge -n {kv} -l {loc}')


class KeyVaultStorageAccountScenarioTest(ScenarioTest):
    def _create_managable_storage_account(self):
        storageacct = self.cmd('az storage account create -g {rg} -n {sa}').get_output_in_json()
        self.kwargs.update({
            'sa_rid': storageacct['id']
        })
        if self.is_live:
            self.cmd('az role assignment create --role "Storage Account Key Operator Service Role" '
                     '--assignee cfa8b339-82a2-471a-a3c9-0fc0be7a4093 --scope {sa_rid}',
                     checks=[self.check('scope', storageacct['id'])])
        return storageacct

    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_sa')
    @unittest.skip('We have to skip this as the service/SDK is buggy.')
    def test_keyvault_storage_account(self, resource_group):
        self.kwargs.update({
            'kv': self.create_random_name('cli-test-kv-sa-', 24),
            'sa': 'clitestkvsa0000002',
            'loc': 'westus'
        })

        _create_keyvault(self, self.kwargs)

        # create a storage account
        self._create_managable_storage_account()
        kv_sa = self.cmd('keyvault storage add --vault-name {kv} -n {sa} --active-key-name key1 '
                         '--auto-regenerate-key --regeneration-period P90D --resource-id {sa_rid}',
                         checks=[self.check('activeKeyName', 'key1'),
                                 self.check('attributes.enabled', True),
                                 self.check('autoRegenerateKey', True),
                                 self.check('regenerationPeriod', 'P90D'),
                                 self.check('resourceId', '{sa_rid}')]).get_output_in_json()
        self.kwargs.update({
            'sa_id': kv_sa['id']
        })

        # create an account sas definition
        acct_sas_template = self.cmd('storage account generate-sas --expiry 2020-01-01 --permissions acdlpruw '
                                     '--resource-types sco --services bfqt --https-only --account-name {sa} '
                                     '--account-key 00000000').output[1:-2]
        self.kwargs.update({
            'acct_temp': acct_sas_template,
            'acct_sas_name': 'allacctaccess'
        })
        sas_def = self.cmd('keyvault storage sas-definition create --vault-name {kv} --account-name {sa} '
                           '-n {acct_sas_name} --validity-period PT4H --sas-type account --template-uri "{acct_temp}"',
                           checks=[self.check('attributes.enabled', True)]).get_output_in_json()
        self.kwargs.update({
            'acct_sas_sid': sas_def['secretId'],
            'acct_sas_id': sas_def['id'],
        })

        # use the account sas token to create a container and a blob
        acct_sas_token = self.cmd('keyvault secret show --id {acct_sas_sid} --query value').output

        self.kwargs.update({
            'acct_sas': acct_sas_token,
            'c': 'cont1',
            'b': 'blob1',
            'f': os.path.join(TEST_DIR, 'test_secret.txt')
        })
        self.cmd('storage container create -n {c} --account-name {sa} --sas-token {acct_sas}',
                 checks=[self.check('created', True)])

        self.cmd('storage blob upload -f "{f}" -c {c} -n {b} --account-name {sa} --sas-token {acct_sas}',
                 checks=[self.exists('lastModified')])

        # create a service sas token for the accessing the blob
        blob_sas_template = self.cmd('storage blob generate-sas -c {c} -n {b} --account-name {sa}'
                                     ' --account-key 00000000 --permissions r').output[1:-2]
        blob_url = self.cmd('storage blob url -c {c} -n {b} --account-name {sa}').output[1:-2]

        blob_temp = '{}?{}'.format(blob_url, blob_sas_template)
        print('blob_temp', blob_temp)
        self.kwargs.update({
            'blob_temp': blob_temp,
            'blob_sas_name': 'blob1r'
        })

        sas_def = self.cmd('keyvault storage sas-definition create --vault-name {kv} --account-name {sa} '
                           '-n {blob_sas_name} --sas-type service --validity-period P1D --template-uri "{blob_temp}"',
                           checks=[self.check('attributes.enabled', True)]).get_output_in_json()

        self.kwargs.update({
            'blob_sas_sid': sas_def['secretId'],
            'blob_sas_id': sas_def['id']
        })

        # use the blob sas token to read the blob
        blob_sas_token = self.cmd('keyvault secret show --id {blob_sas_sid} --query value').output
        self.kwargs.update({
            'blob_sas': blob_sas_token
        })

        self.cmd('storage blob show -c {c} -n {b} --account-name {sa} --sas-token {blob_sas}',
                 checks=[self.check('name', '{b}')])

        # regenerate the storage account key
        self.cmd('keyvault storage regenerate-key --id {sa_id} --key-name key1')

        # use the blob sas token to read the blob
        blob_sas_token = self.cmd('keyvault secret show --id {blob_sas_sid} --query value').output
        self.kwargs.update({
            'blob_sas': blob_sas_token
        })

        self.cmd('storage blob show -c {c} -n {b} --account-name {sa} --sas-token {blob_sas}',
                 checks=[self.check('name', '{b}')])

        # list the sas definitions
        self.cmd('keyvault storage sas-definition list --vault-name {kv} --account-name {sa}',
                 checks=[self.check('length(@)', 2)])

        # show a sas definition by (vault, account-name, name) and by id
        self.cmd('keyvault storage sas-definition show --vault-name {kv} --account-name {sa} -n {blob_sas_name}',
                 checks=[self.check('id', '{blob_sas_id}')])
        self.cmd('keyvault storage sas-definition show --id {acct_sas_id}',
                 checks=[self.check('id', '{acct_sas_id}')])

        # delete a sas definition by (vault, account-name, name) and by id
        self.cmd('keyvault storage sas-definition delete --vault-name {kv} --account-name {sa} -n {blob_sas_name}')
        self.cmd('keyvault storage sas-definition delete --id {acct_sas_id}')

        # list the sas definitions and secrets verfy none are left
        self.cmd('keyvault storage sas-definition list --vault-name {kv} --account-name {sa}',
                 checks=[self.check('length(@)', 0)])
        self.cmd('keyvault secret list --vault-name {kv}', checks=[self.check('length(@)', 0)])

        # list the storage accounts
        self.cmd('keyvault storage list --vault-name {kv}', checks=[self.check('length(@)', 1)])

        # show the storage account by vault and name and by id
        self.cmd('keyvault storage show --vault-name {kv} -n {sa}',
                 checks=[self.check('resourceId', '{sa_rid}')])
        self.cmd('keyvault storage show --id {sa_id}',
                 checks=[self.check('resourceId', '{sa_rid}')])

        # delete the storage account and verify no storage accounts exist in the vault
        self.cmd('keyvault storage remove --id {sa_id}')
        self.cmd('keyvault storage list --vault-name {kv}', checks=[self.check('length(@)', 0)])


if __name__ == '__main__':
    unittest.main()
