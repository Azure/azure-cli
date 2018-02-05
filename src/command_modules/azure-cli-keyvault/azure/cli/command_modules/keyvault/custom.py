# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import codecs
import json
import os
import re
import time

from knack.log import get_logger
from knack.util import CLIError

from OpenSSL import crypto

import azure.cli.core.telemetry as telemetry

from azure.cli.command_modules.keyvault._validators import secret_text_encoding_values

logger = get_logger(__name__)


def _default_certificate_profile():

    from azure.keyvault.models import \
        (Action, ActionType, KeyUsageType, CertificateAttributes, CertificatePolicy, IssuerParameters,
         KeyProperties, LifetimeAction, SecretProperties, X509CertificateProperties, Trigger)

    template = CertificatePolicy(
        key_properties=KeyProperties(
            exportable=True,
            key_type=u'RSA',
            key_size=2048,
            reuse_key=True
        ),
        secret_properties=SecretProperties(
            content_type=u'application/x-pkcs12'
        ),
        x509_certificate_properties=X509CertificateProperties(
            key_usage=[
                KeyUsageType.c_rl_sign,
                KeyUsageType.data_encipherment,
                KeyUsageType.digital_signature,
                KeyUsageType.key_encipherment,
                KeyUsageType.key_agreement,
                KeyUsageType.key_cert_sign
            ],
            subject=u'CN=CLIGetDefaultPolicy',
            validity_in_months=12
        ),
        lifetime_actions=[LifetimeAction(
            trigger=Trigger(
                days_before_expiry=90
            ),
            action=Action(
                action_type=ActionType.auto_renew
            )
        )],
        issuer_parameters=IssuerParameters(
            name=u'Self',
        ),
        attributes=CertificateAttributes(
            enabled=True
        )
    )
    del template.id
    del template.attributes
    del template.issuer_parameters.certificate_type
    del template.lifetime_actions[0].trigger.lifetime_percentage
    del template.x509_certificate_properties.subject_alternative_names
    del template.x509_certificate_properties.ekus
    return template


def _scaffold_certificate_profile():
    from azure.keyvault.models import \
        (Action, ActionType, KeyUsageType, CertificateAttributes, CertificatePolicy, IssuerParameters,
         KeyProperties, LifetimeAction, SecretProperties, X509CertificateProperties, SubjectAlternativeNames, Trigger)

    template = CertificatePolicy(
        key_properties=KeyProperties(
            exportable=True,
            key_type=u'(optional) RSA or RSA-HSM (default RSA)',
            key_size=2048,
            reuse_key=True
        ),
        secret_properties=SecretProperties(
            content_type=u'application/x-pkcs12 or application/x-pem-file'
        ),
        x509_certificate_properties=X509CertificateProperties(
            key_usage=[
                KeyUsageType.c_rl_sign,
                KeyUsageType.data_encipherment,
                KeyUsageType.digital_signature,
                KeyUsageType.key_encipherment,
                KeyUsageType.key_agreement,
                KeyUsageType.key_cert_sign
            ],
            subject_alternative_names=SubjectAlternativeNames(
                emails=[u'hello@contoso.com'],
                dns_names=[u'hr.contoso.com', u'm.contoso.com'],
                upns=[]
            ),
            subject=u'C=US, ST=WA, L=Redmond, O=Contoso, OU=Contoso HR, CN=www.contoso.com',
            ekus=[u'1.3.6.1.5.5.7.3.1'],
            validity_in_months=24
        ),
        lifetime_actions=[LifetimeAction(
            trigger=Trigger(
                days_before_expiry=90
            ),
            action=Action(
                action_type=ActionType.auto_renew
            )
        )],
        issuer_parameters=IssuerParameters(
            name=u'Unknown, Self, or {IssuerName}',
            certificate_type=u'(optional) DigiCert, GlobalSign or WoSign'
        ),
        attributes=CertificateAttributes(
            enabled=True
        )
    )
    del template.id
    del template.attributes
    return template


def list_keyvault(client, resource_group_name=None):
    vault_list = client.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else client.list()
    return list(vault_list)


# pylint: disable=inconsistent-return-statements
def _get_current_user_object_id(graph_client):
    from msrestazure.azure_exceptions import CloudError
    try:
        current_user = graph_client.objects.get_current_user()
        if current_user and current_user.object_id:  # pylint:disable=no-member
            return current_user.object_id  # pylint:disable=no-member
    except CloudError:
        pass


def _get_object_id_by_spn(graph_client, spn):
    accounts = list(graph_client.service_principals.list(
        filter="servicePrincipalNames/any(c:c eq '{}')".format(spn)))
    if not accounts:
        logger.warning("Unable to find user with spn '%s'", spn)
        return None
    if len(accounts) > 1:
        logger.warning("Multiple service principals found with spn '%s'. "
                       "You can avoid this by specifying object id.", spn)
        return None
    return accounts[0].object_id


def _get_object_id_by_upn(graph_client, upn):
    accounts = list(graph_client.users.list(filter="userPrincipalName eq '{}'".format(upn)))
    if not accounts:
        logger.warning("Unable to find user with upn '%s'", upn)
        return None
    if len(accounts) > 1:
        logger.warning("Multiple users principals found with upn '%s'. "
                       "You can avoid this by specifying object id.", upn)
        return None
    return accounts[0].object_id


def _get_object_id_from_subscription(graph_client, subscription):
    if subscription['user']:
        if subscription['user']['type'] == 'user':
            return _get_object_id_by_upn(graph_client, subscription['user']['name'])
        elif subscription['user']['type'] == 'servicePrincipal':
            return _get_object_id_by_spn(graph_client, subscription['user']['name'])
        else:
            logger.warning("Unknown user type '%s'", subscription['user']['type'])
    else:
        logger.warning('Current credentials are not from a user or service principal. '
                       'Azure Key Vault does not work with certificate credentials.')
    return None


def _get_object_id(graph_client, subscription=None, spn=None, upn=None):
    if spn:
        return _get_object_id_by_spn(graph_client, spn)
    if upn:
        return _get_object_id_by_upn(graph_client, upn)
    return _get_object_id_from_subscription(graph_client, subscription)


# region KeyVault Vault
def get_default_policy(client, scaffold=False):  # pylint: disable=unused-argument
    """
    Get a default certificate policy to be used with `az keyvault certificate create`
    :param client:
    :param bool scaffold: create a fully formed policy structure with default values
    :return: policy dict
    :rtype: dict
    """
    return _scaffold_certificate_profile() if scaffold else _default_certificate_profile()


def recover_keyvault(cmd, client, vault_name, resource_group_name, location):
    from azure.mgmt.keyvault.models import (
        VaultCreateOrUpdateParameters, CreateMode, Sku, SkuName)
    from azure.cli.core._profile import Profile

    profile = Profile(cli_ctx=cmd.cli_ctx)
    _, _, tenant_id = profile.get_login_credentials(
        resource=cmd.cli_ctx.cloud.endpoints.active_directory_graph_resource_id)

    params = VaultCreateOrUpdateParameters(location,
                                           properties={'tenant_id': tenant_id,
                                                       'sku': Sku(name=SkuName.standard.value),
                                                       'create_mode': CreateMode.recover.value})

    return client.create_or_update(resource_group_name=resource_group_name,
                                   vault_name=vault_name,
                                   parameters=params)


def create_keyvault(cmd, client,  # pylint: disable=too-many-locals
                    resource_group_name, vault_name, location=None, sku=None,
                    enabled_for_deployment=None,
                    enabled_for_disk_encryption=None,
                    enabled_for_template_deployment=None,
                    enable_soft_delete=None,
                    no_self_perms=None,
                    tags=None):
    from azure.mgmt.keyvault.models import (
        VaultCreateOrUpdateParameters, Permissions, KeyPermissions, SecretPermissions,
        CertificatePermissions, StoragePermissions, AccessPolicyEntry, Sku, VaultProperties)
    from azure.cli.core._profile import Profile
    from azure.graphrbac.models import GraphErrorException
    from azure.graphrbac import GraphRbacManagementClient

    profile = Profile(cli_ctx=cmd.cli_ctx)
    cred, _, tenant_id = profile.get_login_credentials(
        resource=cmd.cli_ctx.cloud.endpoints.active_directory_graph_resource_id)

    graph_client = GraphRbacManagementClient(
        cred,
        tenant_id,
        base_url=cmd.cli_ctx.cloud.endpoints.active_directory_graph_resource_id)
    subscription = profile.get_subscription()
    if no_self_perms:
        access_policies = []
    else:
        permissions = Permissions(keys=[KeyPermissions.get,
                                        KeyPermissions.create,
                                        KeyPermissions.delete,
                                        KeyPermissions.list,
                                        KeyPermissions.update,
                                        KeyPermissions.import_enum,
                                        KeyPermissions.backup,
                                        KeyPermissions.restore,
                                        KeyPermissions.recover],
                                  secrets=[
                                      SecretPermissions.get,
                                      SecretPermissions.list,
                                      SecretPermissions.set,
                                      SecretPermissions.delete,
                                      SecretPermissions.backup,
                                      SecretPermissions.restore,
                                      SecretPermissions.recover],
                                  certificates=[
                                      CertificatePermissions.get,
                                      CertificatePermissions.list,
                                      CertificatePermissions.delete,
                                      CertificatePermissions.create,
                                      CertificatePermissions.import_enum,
                                      CertificatePermissions.update,
                                      CertificatePermissions.managecontacts,
                                      CertificatePermissions.getissuers,
                                      CertificatePermissions.listissuers,
                                      CertificatePermissions.setissuers,
                                      CertificatePermissions.deleteissuers,
                                      CertificatePermissions.manageissuers,
                                      CertificatePermissions.recover],
                                  storage=[
                                      StoragePermissions.get,
                                      StoragePermissions.list,
                                      StoragePermissions.delete,
                                      StoragePermissions.set,
                                      StoragePermissions.update,
                                      StoragePermissions.regeneratekey,
                                      StoragePermissions.setsas,
                                      StoragePermissions.listsas,
                                      StoragePermissions.getsas,
                                      StoragePermissions.deletesas])
        try:
            object_id = _get_current_user_object_id(graph_client)
        except GraphErrorException:
            object_id = _get_object_id(graph_client, subscription=subscription)
        if not object_id:
            raise CLIError('Cannot create vault.\nUnable to query active directory for information '
                           'about the current user.\nYou may try the --no-self-perms flag to '
                           'create a vault without permissions.')
        access_policies = [AccessPolicyEntry(tenant_id=tenant_id,
                                             object_id=object_id,
                                             permissions=permissions)]
    properties = VaultProperties(tenant_id=tenant_id,
                                 sku=Sku(name=sku),
                                 access_policies=access_policies,
                                 vault_uri=None,
                                 enabled_for_deployment=enabled_for_deployment,
                                 enabled_for_disk_encryption=enabled_for_disk_encryption,
                                 enabled_for_template_deployment=enabled_for_template_deployment,
                                 enable_soft_delete=enable_soft_delete)
    parameters = VaultCreateOrUpdateParameters(location=location,
                                               tags=tags,
                                               properties=properties)
    return client.create_or_update(resource_group_name=resource_group_name,
                                   vault_name=vault_name,
                                   parameters=parameters)


def update_keyvault_setter(client, parameters, resource_group_name, vault_name):
    from azure.mgmt.keyvault.models import VaultCreateOrUpdateParameters
    return client.create_or_update(resource_group_name=resource_group_name,
                                   vault_name=vault_name,
                                   parameters=VaultCreateOrUpdateParameters(
                                       location=parameters.location,
                                       properties=parameters.properties))


def update_keyvault(instance, enabled_for_deployment=None, enabled_for_disk_encryption=None,
                    enabled_for_template_deployment=None):
    if enabled_for_deployment is not None:
        instance.properties.enabled_for_deployment = enabled_for_deployment

    if enabled_for_disk_encryption is not None:
        instance.properties.enabled_for_disk_encryption = enabled_for_disk_encryption

    if enabled_for_template_deployment is not None:
        instance.properties.enabled_for_template_deployment = enabled_for_template_deployment

    return instance


def _object_id_args_helper(cli_ctx, object_id, spn, upn):
    if not object_id:
        from azure.cli.core._profile import Profile
        from azure.graphrbac import GraphRbacManagementClient

        profile = Profile(cli_ctx=cli_ctx)
        cred, _, tenant_id = profile.get_login_credentials(
            resource=cli_ctx.cloud.endpoints.active_directory_graph_resource_id)
        graph_client = GraphRbacManagementClient(cred,
                                                 tenant_id,
                                                 base_url=cli_ctx.cloud.endpoints.active_directory_graph_resource_id)
        object_id = _get_object_id(graph_client, spn=spn, upn=upn)
        if not object_id:
            raise CLIError('Unable to get object id from principal name.')
    return object_id


def set_policy(cmd, client, resource_group_name, vault_name,
               object_id=None, spn=None, upn=None, key_permissions=None, secret_permissions=None,
               certificate_permissions=None):
    """ Update security policy settings for a Key Vault. """
    from azure.mgmt.keyvault.models import (
        VaultCreateOrUpdateParameters, AccessPolicyEntry, Permissions)
    object_id = _object_id_args_helper(cmd.cli_ctx, object_id, spn, upn)
    vault = client.get(resource_group_name=resource_group_name,
                       vault_name=vault_name)
    # Find the existing policy to set
    policy = next((p for p in vault.properties.access_policies
                   if object_id.lower() == p.object_id.lower() and
                   vault.properties.tenant_id.lower() == p.tenant_id.lower()), None)
    if not policy:
        # Add new policy as none found
        vault.properties.access_policies.append(AccessPolicyEntry(
            tenant_id=vault.properties.tenant_id,
            object_id=object_id,
            permissions=Permissions(keys=key_permissions,
                                    secrets=secret_permissions,
                                    certificates=certificate_permissions)))
    else:
        # Modify existing policy.
        # If key_permissions is not set, use prev. value (similarly with secret_permissions).
        keys = policy.permissions.keys if key_permissions is None else key_permissions
        secrets = policy.permissions.secrets if secret_permissions is None else secret_permissions
        certs = policy.permissions.certificates \
            if certificate_permissions is None else certificate_permissions
        policy.permissions = Permissions(keys=keys, secrets=secrets, certificates=certs)
    return client.create_or_update(resource_group_name=resource_group_name,
                                   vault_name=vault_name,
                                   parameters=VaultCreateOrUpdateParameters(
                                       location=vault.location,
                                       tags=vault.tags,
                                       properties=vault.properties))


def delete_policy(cmd, client, resource_group_name, vault_name, object_id=None, spn=None, upn=None):
    """ Delete security policy settings for a Key Vault. """
    from azure.mgmt.keyvault.models import VaultCreateOrUpdateParameters
    object_id = _object_id_args_helper(cmd.cli_ctx, object_id, spn, upn)
    vault = client.get(resource_group_name=resource_group_name,
                       vault_name=vault_name)
    prev_policies_len = len(vault.properties.access_policies)
    vault.properties.access_policies = [p for p in vault.properties.access_policies if
                                        vault.properties.tenant_id.lower() != p.tenant_id.lower() or
                                        object_id.lower() != p.object_id.lower()]
    if len(vault.properties.access_policies) == prev_policies_len:
        raise CLIError('No matching policies found')
    return client.create_or_update(resource_group_name=resource_group_name,
                                   vault_name=vault_name,
                                   parameters=VaultCreateOrUpdateParameters(
                                       location=vault.location,
                                       tags=vault.tags,
                                       properties=vault.properties))
# endregion


# region KeyVault Key
def create_key(client, vault_base_url, key_name, destination, key_size=None, key_ops=None,
               disabled=False, expires=None, not_before=None, tags=None):
    from azure.keyvault.models import KeyAttributes
    key_attrs = KeyAttributes(not disabled, not_before, expires)
    return client.create_key(
        vault_base_url, key_name, destination, key_size, key_ops, key_attrs, tags)


def backup_key(client, vault_base_url, key_name, file_path):
    backup = client.backup_key(vault_base_url, key_name).value
    with open(file_path, 'wb') as output:
        output.write(backup)


def restore_key(client, vault_base_url, file_path):
    with open(file_path, 'rb') as file_in:
        data = file_in.read()
    return client.restore_key(vault_base_url, data)


def import_key(client, vault_base_url, key_name, destination=None, key_ops=None, disabled=False, expires=None,
               not_before=None, tags=None, pem_file=None, pem_password=None, byok_file=None):
    """ Import a private key. Supports importing base64 encoded private keys from PEM files.
        Supports importing BYOK keys into HSM for premium KeyVaults. """
    from azure.keyvault.models import KeyAttributes, JsonWebKey

    def _to_bytes(hex_string):
        # zero pads and decodes a hex string
        if len(hex_string) % 2:
            hex_string = '0{}'.format(hex_string)
        return codecs.decode(hex_string, 'hex_codec')

    def _set_rsa_parameters(dest, src):
        # map OpenSSL parameter names to JsonWebKey property names
        conversion_dict = {
            'modulus': 'n',
            'publicExponent': 'e',
            'privateExponent': 'd',
            'prime1': 'p',
            'prime2': 'q',
            'exponent1': 'dp',
            'exponent2': 'dq',
            'coefficient': 'qi'
        }
        # regex: looks for matches that fit the following patterns:
        #   integerPattern: 65537 (0x10001)
        #   hexPattern:
        #      00:a0:91:4d:00:23:4a:c6:83:b2:1b:4c:15:d5:be:
        #      d8:87:bd:c9:59:c2:e5:7a:f5:4a:e7:34:e8:f0:07:
        # The desired match should always be the first component of the match
        regex = re.compile(r'([^:\s]*(:[^\:)]+\))|([^:\s]*(:\s*[0-9A-Fa-f]{2})+))')
        # regex2: extracts the hex string from a format like: 65537 (0x10001)
        regex2 = re.compile(r'(?<=\(0x{1})([0-9A-Fa-f]*)(?=\))')

        key_params = crypto.dump_privatekey(crypto.FILETYPE_TEXT, src).decode('utf-8')
        for match in regex.findall(key_params):
            comps = match[0].split(':', 1)
            name = conversion_dict.get(comps[0], None)
            if name:
                value = comps[1].replace(' ', '').replace('\n', '').replace(':', '')
                try:
                    value = _to_bytes(value)
                except Exception:  # pylint:disable=broad-except
                    # if decoding fails it is because of an integer pattern. Extract the hex
                    # string and retry
                    value = _to_bytes(regex2.findall(value)[0])
                setattr(dest, name, value)

    key_attrs = KeyAttributes(not disabled, not_before, expires)
    key_obj = JsonWebKey(key_ops=key_ops)
    if pem_file:
        key_obj.kty = 'RSA'
        logger.info('Reading %s', pem_file)
        with open(pem_file, 'r') as f:
            pem_data = f.read()
        # load private key and prompt for password if encrypted
        try:
            pem_password = str(pem_password).encode() if pem_password else None
            # despite documentation saying password should be a string, it needs to actually
            # be UTF-8 encoded bytes
            pkey = crypto.load_privatekey(crypto.FILETYPE_PEM, pem_data, pem_password)
        except crypto.Error:
            raise CLIError(
                'Import failed: Unable to decrypt private key. --pem-password may be incorrect.')
        except TypeError:
            raise CLIError('Invalid --pem-password.')
        logger.info('setting RSA parameters from PEM data')
        _set_rsa_parameters(key_obj, pkey)
    elif byok_file:
        with open(byok_file, 'rb') as f:
            byok_data = f.read()
        key_obj.kty = 'RSA-HSM'
        key_obj.t = byok_data

    return client.import_key(
        vault_base_url, key_name, key_obj, destination == 'hsm', key_attrs, tags)
# endregion


# region KeyVault Secret
def download_secret(client, vault_base_url, secret_name, file_path, encoding=None,
                    secret_version=''):
    """ Download a secret from a KeyVault. """
    if os.path.isfile(file_path) or os.path.isdir(file_path):
        raise CLIError("File or directory named '{}' already exists.".format(file_path))

    secret = client.get_secret(vault_base_url, secret_name, secret_version)

    if not encoding:
        encoding = secret.tags.get('file-encoding', 'utf-8') if secret.tags else 'utf-8'

    secret_value = secret.value

    try:
        if encoding in secret_text_encoding_values:
            with open(file_path, 'w') as f:
                f.write(secret_value)
        else:
            if encoding == 'base64':
                import base64
                decoded = base64.b64decode(secret_value)
            elif encoding == 'hex':
                import binascii
                decoded = binascii.unhexlify(secret_value)

            with open(file_path, 'wb') as f:
                f.write(decoded)
    except Exception as ex:  # pylint: disable=broad-except
        if os.path.isfile(file_path):
            os.remove(file_path)
        raise ex


def backup_secret(client, vault_base_url, secret_name, file_path):
    backup = client.backup_secret(vault_base_url, secret_name).value
    with open(file_path, 'wb') as output:
        output.write(backup)


def restore_secret(client, vault_base_url, file_path):
    with open(file_path, 'rb') as file_in:
        data = file_in.read()
    return client.restore_secret(vault_base_url, data)
# endregion


# region KeyVault Certificate
# pylint: disable=inconsistent-return-statements
def create_certificate(client, vault_base_url, certificate_name, certificate_policy,
                       disabled=False, tags=None, validity=None):
    from azure.keyvault.models import CertificateAttributes
    cert_attrs = CertificateAttributes(not disabled)
    logger.info("Starting long-running operation 'keyvault certificate create'")

    if validity is not None:
        certificate_policy['x509_certificate_properties']['validity_in_months'] = validity

    client.create_certificate(
        vault_base_url, certificate_name, certificate_policy, cert_attrs, tags)

    if certificate_policy['issuer_parameters']['name'].lower() == 'unknown':
        # return immediately for a pending certificate
        return client.get_certificate_operation(vault_base_url, certificate_name)

    # otherwise loop until the certificate creation is complete
    while True:
        check = client.get_certificate_operation(vault_base_url, certificate_name)
        if check.status != 'inProgress':
            logger.info(
                "Long-running operation 'keyvault certificate create' finished with result %s.",
                check)
            return check
        try:
            time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Long-running operation wait cancelled.")
            raise
        except Exception as client_exception:
            telemetry.set_exception(exception=client_exception, fault_type='cert-create-error',
                                    summary='Unexpected client exception during cert creation')
            message = getattr(client_exception, 'message', client_exception)

            try:
                ex_message = json.loads(client_exception.response.text)  # pylint: disable=no-member
                message = str(message) + ' ' + ex_message['error']['details'][0]['message']
            except:  # pylint: disable=bare-except
                pass

            raise CLIError('{}'.format(message))


def _asn1_to_iso8601(asn1_date):
    import dateutil.parser
    if isinstance(asn1_date, bytes):
        asn1_date = asn1_date.decode('utf-8')
    return dateutil.parser.parse(asn1_date)


def import_certificate(client, vault_base_url, certificate_name, certificate_data,
                       disabled=False, password=None, certificate_policy=None, tags=None):
    import binascii
    from azure.keyvault.models import CertificateAttributes, SecretProperties, CertificatePolicy

    x509 = None
    content_type = None
    try:
        x509 = crypto.load_certificate(crypto.FILETYPE_PEM, certificate_data)
        # if we get here, we know it was a PEM file
        content_type = 'application/x-pem-file'
        try:
            # for PEM files (including automatic endline conversion for Windows)
            certificate_data = certificate_data.decode('utf-8').replace('\r\n', '\n')
        except UnicodeDecodeError:
            certificate_data = binascii.b2a_base64(certificate_data).decode('utf-8')
    except (ValueError, crypto.Error):
        pass

    if not x509:
        try:
            if password:
                x509 = crypto.load_pkcs12(certificate_data, password).get_certificate()
            else:
                x509 = crypto.load_pkcs12(certificate_data).get_certificate()
            content_type = 'application/x-pkcs12'
            certificate_data = binascii.b2a_base64(certificate_data).decode('utf-8')
        except crypto.Error:
            raise CLIError(
                'We could not parse the provided certificate as .pem or .pfx. Please verify the certificate with OpenSSL.')  # pylint: disable=line-too-long

    not_before, not_after = None, None

    if x509.get_notBefore():
        not_before = _asn1_to_iso8601(x509.get_notBefore())

    if x509.get_notAfter():
        not_after = _asn1_to_iso8601(x509.get_notAfter())

    cert_attrs = CertificateAttributes(
        enabled=not disabled,
        not_before=not_before,
        expires=not_after)

    if certificate_policy:
        secret_props = certificate_policy.get('secret_properties')
        if secret_props:
            secret_props['content_type'] = content_type
        elif certificate_policy and not secret_props:
            certificate_policy['secret_properties'] = SecretProperties(content_type=content_type)
    else:
        certificate_policy = CertificatePolicy(
            secret_properties=SecretProperties(content_type=content_type))

    logger.info("Starting 'keyvault certificate import'")
    result = client.import_certificate(vault_base_url=vault_base_url,
                                       certificate_name=certificate_name,
                                       base64_encoded_certificate=certificate_data,
                                       certificate_attributes=cert_attrs,
                                       certificate_policy=certificate_policy,
                                       tags=tags,
                                       password=password)
    logger.info("Finished 'keyvault certificate import'")
    return result


def download_certificate(client, vault_base_url, certificate_name, file_path,
                         encoding='PEM', certificate_version=''):
    """ Download a certificate from a KeyVault. """
    if os.path.isfile(file_path) or os.path.isdir(file_path):
        raise CLIError("File or directory named '{}' already exists.".format(file_path))

    cert = client.get_certificate(
        vault_base_url, certificate_name, certificate_version).cer

    try:
        with open(file_path, 'wb') as f:
            if encoding == 'DER':
                f.write(cert)
            else:
                import base64
                encoded = base64.encodestring(cert)  # pylint:disable=deprecated-method
                if isinstance(encoded, bytes):
                    encoded = encoded.decode("utf-8")
                encoded = '-----BEGIN CERTIFICATE-----\n' + encoded + '-----END CERTIFICATE-----\n'
                f.write(encoded.encode("utf-8"))
    except Exception as ex:  # pylint: disable=broad-except
        if os.path.isfile(file_path):
            os.remove(file_path)
        raise ex


def add_certificate_contact(client, vault_base_url, contact_email, contact_name=None,
                            contact_phone=None):
    """ Add a contact to the specified vault to receive notifications of certificate operations. """
    from azure.keyvault.models import \
        (Contact, Contacts, KeyVaultErrorException)
    try:
        contacts = client.get_certificate_contacts(vault_base_url)
    except KeyVaultErrorException:
        contacts = Contacts([])
    contact = Contact(contact_email, contact_name, contact_phone)
    if any((x for x in contacts.contact_list if x.email_address == contact_email)):
        raise CLIError("contact '{}' already exists".format(contact_email))
    contacts.contact_list.append(contact)
    return client.set_certificate_contacts(vault_base_url, contacts.contact_list)


def delete_certificate_contact(client, vault_base_url, contact_email):
    """ Remove a certificate contact from the specified vault. """
    from azure.keyvault.models import Contacts
    contacts = client.get_certificate_contacts(vault_base_url).contact_list
    remaining = Contacts([x for x in contacts if x.email_address != contact_email])
    if len(contacts) == len(remaining.contact_list):
        raise CLIError("contact '{}' not found in vault '{}'".format(contact_email, vault_base_url))
    if remaining.contact_list:
        return client.set_certificate_contacts(vault_base_url, remaining.contact_list)
    return client.delete_certificate_contacts(vault_base_url)


def create_certificate_issuer(client, vault_base_url, issuer_name, provider_name, account_id=None,
                              password=None, disabled=None, organization_id=None):
    """ Create a certificate issuer record.
    :param issuer_name: Unique identifier for the issuer settings.
    :param provider_name: The certificate provider name. Must be registered with your
        tenant ID and in your region.
    :param account_id: The issuer account id/username/etc.
    :param password: The issuer account password/secret/etc.
    :param organization_id: The organization id.
    """
    from azure.keyvault.models import IssuerCredentials, OrganizationDetails, IssuerAttributes
    credentials = IssuerCredentials(account_id, password)
    issuer_attrs = IssuerAttributes(not disabled)
    org_details = OrganizationDetails(organization_id, admin_details=[])
    return client.set_certificate_issuer(
        vault_base_url, issuer_name, provider_name, credentials, org_details, issuer_attrs)


def update_certificate_issuer(client, vault_base_url, issuer_name, provider_name=None,
                              account_id=None, password=None, enabled=None, organization_id=None):
    """ Update a certificate issuer record.
    :param issuer_name: Unique identifier for the issuer settings.
    :param provider_name: The certificate provider name. Must be registered with your
        tenant ID and in your region.
    :param account_id: The issuer account id/username/etc.
    :param password: The issuer account password/secret/etc.
    :param organization_id: The organization id.
    """
    def update(obj, prop, value, nullable=False):
        set_value = value if value is not None else getattr(obj, prop, None)
        if set_value is None and not nullable:
            raise CLIError("property '{}' cannot be cleared".format(prop))
        elif not set_value and nullable:
            set_value = None
        setattr(obj, prop, set_value)

    issuer = client.get_certificate_issuer(vault_base_url, issuer_name)
    update(issuer.credentials, 'account_id', account_id, True)
    update(issuer.credentials, 'password', password, True)
    update(issuer.attributes, 'enabled', enabled)
    update(issuer.organization_details, 'id', organization_id, True)
    update(issuer, 'provider', provider_name)
    return client.set_certificate_issuer(
        vault_base_url, issuer_name, issuer.provider, issuer.credentials,
        issuer.organization_details, issuer.attributes)


def list_certificate_issuer_admins(client, vault_base_url, issuer_name):
    """ List admins for a specified certificate issuer. """
    return client.get_certificate_issuer(
        vault_base_url, issuer_name).organization_details.admin_details


def add_certificate_issuer_admin(client, vault_base_url, issuer_name, email, first_name=None,
                                 last_name=None, phone=None):
    """ Add admin details for a specified certificate issuer. """
    from azure.keyvault.models import AdministratorDetails

    issuer = client.get_certificate_issuer(vault_base_url, issuer_name)
    org_details = issuer.organization_details
    admins = org_details.admin_details
    if any((x for x in admins if x.email_address == email)):
        raise CLIError("admin '{}' already exists".format(email))
    new_admin = AdministratorDetails(first_name, last_name, email, phone)
    admins.append(new_admin)
    org_details.admin_details = admins
    result = client.set_certificate_issuer(
        vault_base_url, issuer_name, issuer.provider, issuer.credentials, org_details,
        issuer.attributes)
    created_admin = next(x for x in result.organization_details.admin_details
                         if x.email_address == email)
    return created_admin


def delete_certificate_issuer_admin(client, vault_base_url, issuer_name, email):
    """ Remove admin details for the specified certificate issuer. """
    issuer = client.get_certificate_issuer(vault_base_url, issuer_name)
    org_details = issuer.organization_details
    admins = org_details.admin_details
    remaining = [x for x in admins if x.email_address != email]
    if len(remaining) == len(admins):
        raise CLIError("admin '{}' not found for issuer '{}'".format(email, issuer_name))
    org_details.admin_details = remaining
    client.set_certificate_issuer(
        vault_base_url, issuer_name, issuer.provider, issuer.credentials, org_details,
        issuer.attributes)
# endregion
