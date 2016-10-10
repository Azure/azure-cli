#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=line-too-long,too-many-arguments,too-many-function-args,too-many-public-methods
from azure.cli.command_modules.keyvault.keyvaultclient import KeyVaultClient as _KeyVaultClient

class KeyVaultClient(object):

    def __init__(self, credentials, api_version='2015-06-01', accept_language='en-US', long_running_operation_retry_timeout=30, generate_client_request_id=True, filepath=None):
        self.keyvault = _KeyVaultClient(credentials, api_version, accept_language, long_running_operation_retry_timeout, generate_client_request_id, filepath)

    def create_key(self, vault_base_url, key_name, kty, key_size=None, key_ops=None, key_attributes=None, tags=None, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.create_key(vault_base_url, key_name, kty, key_size, key_ops, key_attributes, tags, custom_headers, raw, **operation_config)
    create_key.__doc__ = _KeyVaultClient.create_key.__doc__

    def import_key(self, vault_base_url, key_name, key, hsm=None, key_attributes=None, tags=None, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.import_key(vault_base_url, key_name, key, hsm, key_attributes, tags, custom_headers, raw, **operation_config)
    import_key.__doc__ = _KeyVaultClient.import_key.__doc__

    def delete_key(self, vault_base_url, key_name, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.delete_key(vault_base_url, key_name, custom_headers, raw, **operation_config)
    delete_key.__doc__ = _KeyVaultClient.delete_key.__doc__

    def update_key(self, vault_base_url, key_name, key_version='', key_ops=None, key_attributes=None, tags=None, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.update_key(vault_base_url, key_name, key_version, key_ops, key_attributes, tags, custom_headers, raw, **operation_config)
    update_key.__doc__ = _KeyVaultClient.update_key.__doc__

    def get_key(self, vault_base_url, key_name, key_version='', custom_headers=None, raw=False, **operation_config):
        return self.keyvault.get_key(vault_base_url, key_name, key_version, custom_headers, raw, **operation_config)
    get_key.__doc__ = _KeyVaultClient.get_key.__doc__

    def get_key_versions(self, vault_base_url, key_name, maxresults=None, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.get_key_versions(vault_base_url, key_name, maxresults, custom_headers, raw, **operation_config)
    get_key_versions.__doc__ = _KeyVaultClient.get_key_versions.__doc__

    def get_keys(self, vault_base_url, maxresults=None, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.get_keys(vault_base_url, maxresults, custom_headers, raw, **operation_config)
    get_keys.__doc__ = _KeyVaultClient.get_keys.__doc__

    def backup_key(self, vault_base_url, key_name, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.backup_key(vault_base_url, key_name, custom_headers, raw, **operation_config)
    backup_key.__doc__ = _KeyVaultClient.backup_key.__doc__

    def restore_key(self, vault_base_url, key_bundle_backup, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.restore_key(vault_base_url, key_bundle_backup, custom_headers, raw, **operation_config)
    restore_key.__doc__ = _KeyVaultClient.restore_key.__doc__

    def encrypt(self, vault_base_url, key_name, algorithm, value, key_version='', custom_headers=None, raw=False, **operation_config):
        return self.keyvault.encrypt(vault_base_url, key_name, key_version, algorithm, value, custom_headers, raw, **operation_config)
    encrypt.__doc__ = _KeyVaultClient.encrypt.__doc__

    def decrypt(self, vault_base_url, key_name, algorithm, value, key_version='', custom_headers=None, raw=False, **operation_config):
        return self.keyvault.decrypt(vault_base_url, key_name, key_version, algorithm, value, custom_headers, raw, **operation_config)
    decrypt.__doc__ = _KeyVaultClient.decrypt.__doc__

    def sign(self, vault_base_url, key_name, algorithm, value, key_version='', custom_headers=None, raw=False, **operation_config):
        return self.keyvault.sign(vault_base_url, key_name, key_version, algorithm, value, custom_headers, raw, **operation_config)
    sign.__doc__ = _KeyVaultClient.sign.__doc__

    def verify(self, vault_base_url, key_name, algorithm, digest, signature, key_version='', custom_headers=None, raw=False, **operation_config):
        return self.keyvault.verify(vault_base_url, key_name, key_version, algorithm, digest, signature, custom_headers, raw, **operation_config)
    verify.__doc__ = _KeyVaultClient.verify.__doc__

    def wrap_key(self, vault_base_url, key_name, algorithm, value, key_version='', custom_headers=None, raw=False, **operation_config):
        return self.keyvault.wrap_key(self, vault_base_url, key_name, key_version, algorithm, value, custom_headers, raw, **operation_config)
    wrap_key.__doc__ = _KeyVaultClient.wrap_key.__doc__

    def set_secret(self, vault_base_url, secret_name, value, tags=None, content_type=None, secret_attributes=None, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.set_secret(vault_base_url, secret_name, value, tags, content_type, secret_attributes, custom_headers, raw, **operation_config)
    set_secret.__doc__ = _KeyVaultClient.set_secret.__doc__

    def delete_secret(self, vault_base_url, secret_name, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.delete_secret(vault_base_url, secret_name, custom_headers, raw, **operation_config)
    delete_secret.__doc__ = _KeyVaultClient.delete_secret.__doc__

    def update_secret(self, vault_base_url, secret_name, secret_version='', content_type=None, secret_attributes=None, tags=None, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.update_secret(vault_base_url, secret_name, secret_version, content_type, secret_attributes, tags, custom_headers, raw, **operation_config)
    update_secret.__doc__ = _KeyVaultClient.update_secret.__doc__

    def get_secret(self, vault_base_url, secret_name, secret_version='', custom_headers=None, raw=False, **operation_config):
        return self.keyvault.get_secret(vault_base_url, secret_name, secret_version, custom_headers, raw, **operation_config)
    get_secret.__doc__ = _KeyVaultClient.get_secret.__doc__

    def get_secrets(self, vault_base_url, maxresults=None, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.get_secrets(vault_base_url, maxresults, custom_headers, raw, **operation_config)
    get_secrets.__doc__ = _KeyVaultClient.get_secrets.__doc__

    def get_secret_versions(self, vault_base_url, secret_name, maxresults=None, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.get_secret_versions(vault_base_url, secret_name, maxresults, custom_headers, raw, **operation_config)
    get_secret_versions.__doc__ = _KeyVaultClient.get_secret_versions.__doc__

    def get_certificates(self, vault_base_url, maxresults=None, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.get_certificates(vault_base_url, maxresults, custom_headers, raw, **operation_config)
    get_certificates.__doc__ = _KeyVaultClient.get_certificates.__doc__

    def delete_certificate(self, vault_base_url, certificate_name, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.delete_certificate(vault_base_url, certificate_name, custom_headers, raw, **operation_config)
    delete_certificate.__doc__ = _KeyVaultClient.delete_certificate.__doc__

    # pylint: disable=redefined-builtin
    def set_certificate_contacts(self, vault_base_url, id=None, contact_list=None, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.set_certificate_contacts(vault_base_url, id, contact_list, custom_headers, raw, **operation_config)
    set_certificate_contacts.__doc__ = _KeyVaultClient.set_certificate_contacts.__doc__

    def get_certificate_contacts(self, vault_base_url, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.get_certificate_contacts(vault_base_url, custom_headers, raw, **operation_config)
    get_certificate_contacts.__doc__ = _KeyVaultClient.get_certificate_contacts.__doc__

    def delete_certificate_contacts(self, vault_base_url, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.delete_certificate_contacts(vault_base_url, custom_headers, raw, **operation_config)
    delete_certificate_contacts.__doc__ = _KeyVaultClient.delete_certificate_contacts.__doc__

    def get_certificate_issuers(self, vault_base_url, maxresults=None, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.get_certificate_issuers(vault_base_url, maxresults, custom_headers, raw, **operation_config)
    get_certificate_issuers.__doc__ = _KeyVaultClient.get_certificate_issuers.__doc__

    def set_certificate_issuer(self, vault_base_url, issuer_name, provider, credentials=None, organization_details=None, attributes=None, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.set_certificate_issuer(vault_base_url, issuer_name, provider, credentials, organization_details, attributes, custom_headers, raw, **operation_config)
    set_certificate_issuer.__doc__ = _KeyVaultClient.set_certificate_issuer.__doc__

    def update_certificate_issuer(self, vault_base_url, issuer_name, provider=None, credentials=None, organization_details=None, attributes=None, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.update_certificate_issuer(vault_base_url, issuer_name, provider, credentials, organization_details, attributes, custom_headers, raw, **operation_config)
    update_certificate_issuer.__doc__ = _KeyVaultClient.update_certificate_issuer.__doc__

    def get_certificate_issuer(self, vault_base_url, issuer_name, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.get_certificate_issuer(vault_base_url, issuer_name, custom_headers, raw, **operation_config)
    get_certificate_issuer.__doc__ = _KeyVaultClient.get_certificate_issuer.__doc__

    def delete_certificate_issuer(self, vault_base_url, issuer_name, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.delete_certificate_issuer(vault_base_url, issuer_name, custom_headers, raw, **operation_config)
    delete_certificate_issuer.__doc__ = _KeyVaultClient.delete_certificate_issuer.__doc__

    def create_certificate(self, vault_base_url, certificate_name, certificate_policy=None, certificate_attributes=None, tags=None, custom_headers=None, raw=False, **operation_config):
        operation = self.keyvault.create_certificate(vault_base_url, certificate_name, certificate_policy, certificate_attributes, tags, custom_headers, raw, **operation_config)
        # TODO: Custom polling logic
        return operation
    create_certificate.__doc__ = _KeyVaultClient.create_certificate.__doc__

    def import_certificate(self, vault_base_url, certificate_name, base64_encoded_certificate, password=None, certificate_policy=None, certificate_attributes=None, tags=None, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.import_certificate(vault_base_url, certificate_name, base64_encoded_certificate, password, certificate_policy, certificate_attributes, tags, custom_headers, raw, **operation_config)
    import_certificate.__doc__ = _KeyVaultClient.import_certificate.__doc__

    def get_certificate_versions(self, vault_base_url, certificate_name, maxresults=None, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.get_certificate_versions(vault_base_url, certificate_name, maxresults, custom_headers, raw, **operation_config)
    get_certificate_versions.__doc__ = _KeyVaultClient.get_certificate_versions.__doc__

    def get_certificate_policy(self, vault_base_url, certificate_name, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.get_certificate_policy(vault_base_url, certificate_name, custom_headers, raw, **operation_config)
    get_certificate_policy.__doc__ = _KeyVaultClient.get_certificate_policy.__doc__

    def update_certificate_policy(self, vault_base_url, certificate_name, certificate_policy, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.update_certificate_policy(vault_base_url, certificate_name, certificate_policy, custom_headers, raw, **operation_config)
    update_certificate_policy.__doc__ = _KeyVaultClient.update_certificate_policy.__doc__

    def update_certificate(self, vault_base_url, certificate_name, certificate_version='', certificate_policy=None, certificate_attributes=None, tags=None, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.update_certificate(vault_base_url, certificate_name, certificate_version, certificate_policy, certificate_attributes, tags, custom_headers, raw, **operation_config)
    update_certificate.__doc__ = _KeyVaultClient.update_certificate.__doc__

    def get_certificate(self, vault_base_url, certificate_name, certificate_version='', custom_headers=None, raw=False, **operation_config):
        return self.keyvault.get_certificate(vault_base_url, certificate_name, certificate_version, custom_headers, raw, **operation_config)
    get_certificate.__doc__ = _KeyVaultClient.get_certificate.__doc__

    def update_certificate_operation(self, vault_base_url, certificate_name, cancellation_requested, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.update_certificate_operation(vault_base_url, certificate_name, cancellation_requested, custom_headers, raw, **operation_config)
    update_certificate_operation.__doc__ = _KeyVaultClient.update_certificate_operation.__doc__

    def get_certificate_operation(self, vault_base_url, certificate_name, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.get_certificate_operation(vault_base_url, certificate_name, custom_headers, raw, **operation_config)
    get_certificate_operation.__doc__ = _KeyVaultClient.get_certificate_operation.__doc__

    def delete_certificate_operation(self, vault_base_url, certificate_name, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.delete_certificate_operation(vault_base_url, certificate_name, custom_headers, raw, **operation_config)
    delete_certificate_operation.__doc__ = _KeyVaultClient.delete_certificate_operation.__doc__

    def merge_certificate(self, vault_base_url, certificate_name, x509_certificates, certificate_attributes=None, tags=None, custom_headers=None, raw=False, **operation_config):
        return self.keyvault.merge_certificate(vault_base_url, certificate_name, x509_certificates, certificate_attributes, tags, custom_headers, raw, **operation_config)
    merge_certificate.__doc__ = _KeyVaultClient.merge_certificate.__doc__

try:
    KeyVaultClient.__doc__ = _KeyVaultClient.__doc__
except AttributeError:
    pass
