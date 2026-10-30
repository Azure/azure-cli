# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import base64
from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


LOCATION = 'westus2'
ACCOUNT_NAME_PREFIX = 'cli-ldap-'
ACCOUNT_NAME_LENGTH = 24
IDENTITY_ID_TEMPLATE = (
    '/subscriptions/{}/resourceGroups/sdk-py-test-rg/providers/'
    'Microsoft.ManagedIdentity/userAssignedIdentities/dap-bind-uksouth-identity'
)
KEY_VAULT_URI = 'https://ldapbind-uksouth-kv-1.vault.azure.net'
SECRET_NAME = 'ldapuser-password'
DOMAIN = 'contoso.com'
LDAP_SERVER = '10.0.2.4'
LDAP_PORT = 389
BIND_DN = 'uid=ldapuser,cn=users,cn=accounts,dc=contoso,dc=com'
BIND_AUTHENTICATION_LEVEL = 'Simple'
CERTIFICATE_CN_HOST = 'ipaserver.contoso.com'
SECURE_LDAP_TYPE = 'LdapOverTLS'
USER_DN = 'cn=users,cn=accounts,dc=contoso,dc=com'
GROUP_DN = 'cn=groups,cn=accounts,dc=contoso,dc=com'


class AzureNetAppFilesAccountLdapConfigurationScenarioTest(ScenarioTest):
    @staticmethod
    def _generate_ldap_ca_certificate():
        """Return a base64-encoded PEM CA certificate without its private key."""
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'CLI LDAP Test CA')])
        now = datetime.now(timezone.utc)
        certificate = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(subject)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=5))
            .not_valid_after(now + timedelta(days=365))
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .add_extension(x509.KeyUsage(
                digital_signature=False,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ), critical=True)
            .sign(key, hashes.SHA256())
        )
        return base64.b64encode(certificate.public_bytes(serialization.Encoding.PEM)).decode('ascii')

    # Live prerequisites: the identity below must have access to the existing
    # Key Vault secret. The generated CA tests configuration, not LDAP connectivity.
    # Record with: azdev test test_account_ldap_configuration --live
    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_ldap_', location=LOCATION,
                           additional_tags={'owner': 'cli_test'})
    def test_account_ldap_configuration(self):
        self.kwargs.update({
            'loc': LOCATION,
            'acc_name': self.create_random_name(prefix=ACCOUNT_NAME_PREFIX, length=ACCOUNT_NAME_LENGTH),
            'identity_id': IDENTITY_ID_TEMPLATE.format(self.get_subscription_id()),
            'key_vault_uri': KEY_VAULT_URI,
            'secret_name': SECRET_NAME,
            'domain': DOMAIN,
            'ldap_server': LDAP_SERVER,
            'ldap_port': LDAP_PORT,
            'bind_dn': BIND_DN,
            'bind_auth_level': BIND_AUTHENTICATION_LEVEL,
            'certificate_cn_host': CERTIFICATE_CN_HOST,
            'secure_ldap_type': SECURE_LDAP_TYPE,
            'user_dn': USER_DN,
            'group_dn': GROUP_DN,
            'server_ca_certificate': self._generate_ldap_ca_certificate(),
        })

        self.cmd(
            'az netappfiles account create -g {rg} -a {acc_name} -l {loc} '
            '--identity-type "SystemAssigned,UserAssigned" --mi-user-assigned "{identity_id}"',
            checks=[
                self.check('name', '{acc_name}'),
                self.check("contains(identity.type, 'SystemAssigned')", True),
                self.check("contains(identity.type, 'UserAssigned')", True),
                self.check('length(identity.userAssignedIdentities)', 1),
            ])

        configuration_checks = [
            self.check('domain', '{domain}'),
            self.check('ldapPort', LDAP_PORT),
            self.check('ldapServers', [LDAP_SERVER]),
            self.check('bindAuthenticationLevel', BIND_AUTHENTICATION_LEVEL),
            self.check('bindDN', '{bind_dn}'),
            self.check('bindPasswordAkvConfig.azureKeyVaultUri', '{key_vault_uri}'),
            self.check('bindPasswordAkvConfig.secretName', '{secret_name}'),
            self.check('bindPasswordAkvConfig.userAssignedIdentity', '{identity_id}'),
            self.check('certificateCNHost', '{certificate_cn_host}'),
            self.check('secureLdapType', SECURE_LDAP_TYPE),
        ]
        self.cmd(
            'az netappfiles account ldap-configuration create --account-name {acc_name} --resource-group {rg} '
            '--domain {domain} --ldap-port {ldap_port} --ldap-servers {ldap_server} '
            '--bind-password-azure-key-vault-uri "{key_vault_uri}" --bind-password-secret-name {secret_name} '
            '--bind-password-user-assigned-identity "{identity_id}" --bind-auth-level {bind_auth_level} '
            '--bind-dn "{bind_dn}" --certificate-cn-host {certificate_cn_host} '
            '--server-ca-certificate "{server_ca_certificate}" --secure-ldap-type {secure_ldap_type}',
            checks=configuration_checks)
        self.cmd(
            'az netappfiles account ldap-configuration wait --account-name {acc_name} --resource-group {rg} '
            '--created --interval 10 --timeout 300')
        self.cmd(
            'az netappfiles account ldap-configuration show --account-name {acc_name} --resource-group {rg}',
            checks=configuration_checks)

        updated_checks = configuration_checks + [
            self.check('userDN', '{user_dn}'),
            self.check('groupDN', '{group_dn}'),
        ]
        self.cmd(
            'az netappfiles account ldap-configuration update --account-name {acc_name} --resource-group {rg} '
            '--user-dn "{user_dn}" --group-dn "{group_dn}"',
            checks=updated_checks)
        self.cmd(
            'az netappfiles account ldap-configuration wait --account-name {acc_name} --resource-group {rg} '
            '--updated --interval 10 --timeout 300')
        self.cmd(
            'az netappfiles account ldap-configuration show --account-name {acc_name} --resource-group {rg}',
            checks=updated_checks)

        self.cmd(
            'az netappfiles account ldap-configuration delete --account-name {acc_name} --resource-group {rg} --yes')
        self.cmd(
            'az netappfiles account ldap-configuration wait --account-name {acc_name} --resource-group {rg} '
            '--custom "!properties.ldapConfiguration" --interval 10 --timeout 300')
        self.cmd('az netappfiles account show -g {rg} -a {acc_name}', checks=[
            self.check('name', '{acc_name}'),
            self.check('ldapConfiguration', None),
        ])
        self.cmd('az netappfiles account delete -g {rg} -a {acc_name} --yes')
