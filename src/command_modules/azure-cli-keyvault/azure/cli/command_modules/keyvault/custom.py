# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import codecs
import os
import re
import time

from OpenSSL import crypto

from msrestazure.azure_exceptions import CloudError
from azure.mgmt.keyvault.models import (VaultCreateOrUpdateParameters,
                                        VaultProperties,
                                        AccessPolicyEntry,
                                        Permissions,
                                        CertificatePermissions,
                                        KeyPermissions,
                                        SecretPermissions,
                                        Sku,
                                        SkuName)
from azure.graphrbac import GraphRbacManagementClient

from azure.cli.core.telemetry import log_telemetry
from azure.cli.core._util import CLIError
import azure.cli.core._logging as _logging

from azure.keyvault import KeyVaultClient
from azure.cli.command_modules.keyvault._validators import secret_text_encoding_values

logger = _logging.get_az_logger(__name__)

def list_keyvault(client, resource_group_name=None):
    vault_list = client.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else client.list()
    return list(vault_list)

def _get_current_user_object_id(graph_client):
    try:
        current_user = graph_client.objects.get_current_user()
        if current_user and current_user.object_id: #pylint:disable=no-member
            return current_user.object_id #pylint:disable=no-member
    except CloudError:
        pass

def _get_object_id_by_spn(graph_client, spn):
    accounts = list(graph_client.service_principals.list(
        filter="servicePrincipalNames/any(c:c eq '{}')".format(spn)))
    if not accounts:
        logger.warning("Unable to find user with spn '%s'", spn)
        return
    if len(accounts) > 1:
        logger.warning("Multiple service principals found with spn '%s'. "\
                       "You can avoid this by specifying object id.", spn)
        return
    return accounts[0].object_id

def _get_object_id_by_upn(graph_client, upn):
    accounts = list(graph_client.users.list(filter="userPrincipalName eq '{}'".format(upn)))
    if not accounts:
        logger.warning("Unable to find user with upn '%s'", upn)
        return
    if len(accounts) > 1:
        logger.warning("Multiple users principals found with upn '%s'. "\
                       "You can avoid this by specifying object id.", upn)
        return
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
        logger.warning('Current credentials are not from a user or service principal. '\
                       'Azure Key Vault does not work with certificate credentials.')

def _get_object_id(graph_client, subscription=None, spn=None, upn=None):
    if spn:
        return _get_object_id_by_spn(graph_client, spn)
    if upn:
        return _get_object_id_by_upn(graph_client, upn)
    return _get_object_id_from_subscription(graph_client, subscription)

def create_keyvault(client, resource_group_name, vault_name, location, #pylint:disable=too-many-arguments
                    sku=SkuName.standard.value,
                    enabled_for_deployment=None,
                    enabled_for_disk_encryption=None,
                    enabled_for_template_deployment=None,
                    no_self_perms=False,
                    tags=None):
    from azure.cli.core._profile import Profile, CLOUD
    profile = Profile()
    cred, _, tenant_id = profile.get_login_credentials(
        resource=CLOUD.endpoints.active_directory_graph_resource_id)
    graph_client = GraphRbacManagementClient(cred,
                                             tenant_id,
                                             base_url=CLOUD.endpoints.active_directory_graph_resource_id) # pylint: disable=line-too-long
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
                                        KeyPermissions.restore],
                                  secrets=[SecretPermissions.all],
                                  certificates=[CertificatePermissions.all])
        object_id = _get_current_user_object_id(graph_client)
        if not object_id:
            object_id = _get_object_id(graph_client, subscription=subscription)
        if not object_id:
            raise CLIError('Cannot create vault.\n'
                           'Unable to query active directory for information '\
                           'about the current user.\n'
                           'You may try the --no-self-perms flag to create a vault'\
                           ' without permissions.')
        access_policies = [AccessPolicyEntry(tenant_id=tenant_id,
                                             object_id=object_id,
                                             permissions=permissions)]
    properties = VaultProperties(tenant_id=tenant_id,
                                 sku=Sku(name=sku),
                                 access_policies=access_policies,
                                 vault_uri=None,
                                 enabled_for_deployment=enabled_for_deployment,
                                 enabled_for_disk_encryption=enabled_for_disk_encryption,
                                 enabled_for_template_deployment=enabled_for_template_deployment)
    parameters = VaultCreateOrUpdateParameters(location=location,
                                               tags=tags,
                                               properties=properties)
    return client.create_or_update(resource_group_name=resource_group_name,
                                   vault_name=vault_name,
                                   parameters=parameters)
create_keyvault.__doc__ = VaultProperties.__doc__

def _object_id_args_helper(object_id, spn, upn):
    if not object_id:
        from azure.cli.core._profile import Profile, CLOUD
        profile = Profile()
        cred, _, tenant_id = profile.get_login_credentials(
            resource=CLOUD.endpoints.active_directory_graph_resource_id)
        graph_client = GraphRbacManagementClient(cred,
                                                 tenant_id,
                                                 base_url=CLOUD.endpoints.active_directory_graph_resource_id) # pylint: disable=line-too-long
        object_id = _get_object_id(graph_client, spn=spn, upn=upn)
        if not object_id:
            raise CLIError('Unable to get object id from principal name.')
    return object_id

def set_policy(client, resource_group_name, vault_name, #pylint:disable=too-many-arguments
               object_id=None, spn=None, upn=None, key_permissions=None, secret_permissions=None,
               certificate_permissions=None):
    """ Update security policy settings for a Key Vault. """
    object_id = _object_id_args_helper(object_id, spn, upn)
    vault = client.get(resource_group_name=resource_group_name,
                       vault_name=vault_name)
    # Find the existing policy to set
    policy = next((p for p in vault.properties.access_policies \
             if object_id.lower() == p.object_id.lower() and \
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

def delete_policy(client, resource_group_name, vault_name, object_id=None, spn=None, upn=None): #pylint:disable=too-many-arguments
    """ Delete security policy settings for a Key Vault. """
    object_id = _object_id_args_helper(object_id, spn, upn)
    vault = client.get(resource_group_name=resource_group_name,
                       vault_name=vault_name)
    prev_policies_len = len(vault.properties.access_policies)
    vault.properties.access_policies = [p for p in vault.properties.access_policies if \
                                        vault.properties.tenant_id.lower() != p.tenant_id.lower() \
                                        or object_id.lower() != p.object_id.lower()]
    if len(vault.properties.access_policies) == prev_policies_len:
        raise CLIError('No matching policies found')
    return client.create_or_update(resource_group_name=resource_group_name,
                                   vault_name=vault_name,
                                   parameters=VaultCreateOrUpdateParameters(
                                       location=vault.location,
                                       tags=vault.tags,
                                       properties=vault.properties))

# pylint: disable=too-many-arguments
def create_key(client, vault_base_url, key_name, destination, key_size=None, key_ops=None,
               disabled=False, expires=None, not_before=None, tags=None):
    from azure.keyvault.generated.models import KeyAttributes
    key_attrs = KeyAttributes(not disabled, not_before, expires)
    return client.create_key(
        vault_base_url, key_name, destination, key_size, key_ops, key_attrs, tags)
create_key.__doc__ = KeyVaultClient.create_key.__doc__

def backup_key(client, vault_base_url, key_name, file_path):
    backup = client.backup_key(vault_base_url, key_name).value
    with open(file_path, 'wb') as output:
        output.write(backup)
backup_key.__doc__ = KeyVaultClient.backup_key.__doc__

def restore_key(client, vault_base_url, file_path):
    with open(file_path, 'rb') as file_in:
        data = file_in.read()
    return client.restore_key(vault_base_url, data)
restore_key.__doc__ = KeyVaultClient.restore_key.__doc__

# pylint: disable=too-many-arguments,assignment-from-no-return,unused-variable
def import_key(client, vault_base_url, key_name, destination=None, key_ops=None, disabled=False,
               expires=None, not_before=None, tags=None, pem_file=None, pem_password=None,
               byok_file=None):
    """ Import a private key. Supports importing base64 encoded private keys from PEM files.
        Supports importing BYOK keys into HSM for premium KeyVaults. """
    from azure.keyvault.generated.models import \
        (KeyAttributes, JsonWebKey)

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
                except Exception as ex: # pylint:disable=broad-except
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
        except crypto.Error as ex:
            raise CLIError(
                'Import failed: Unable to decrypt private key. --pem-password may be incorrect.')
        except TypeError as ex:
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

def download_secret(client, vault_base_url, secret_name, file_path, encoding=None,
                    secret_version=''):
    """ Download a secret from a KeyVault. """
    if os.path.isfile(file_path) or os.path.isdir(file_path):
        raise CLIError("File or directory named '{}' already exists.".format(file_path))

    secret = client.keyvault.get_secret(vault_base_url, secret_name, secret_version)
    encoding = encoding or secret.tags.get('file-encoding', 'utf-8')
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
    except Exception as ex: # pylint: disable=broad-except
        if os.path.isfile(file_path):
            os.remove(file_path)
        raise ex

def create_certificate(client, vault_base_url, certificate_name, certificate_policy,
                       disabled=False, expires=None, not_before=None, tags=None):
    from azure.keyvault.generated.models import \
        (CertificateAttributes)
    cert_attrs = CertificateAttributes(not disabled, not_before, expires)
    logger.info("Starting long running operation 'keyvault certificate create'")
    client.create_certificate(
        vault_base_url, certificate_name, certificate_policy, cert_attrs, tags)

    if certificate_policy['issuer_parameters']['name'].lower() == 'unknown':
        # return immediately for a pending certificate
        return client.get_certificate_operation(vault_base_url, certificate_name)

    # otherwise loop until the certificate creation is complete
    while True:
        check = client.get_certificate_operation(vault_base_url, certificate_name)
        if check.status != 'inProgress':
            logger.info("Long running operation 'keyvault certificate create' finished with result %s.", check) # pylint: disable=line-too-long
            return check
        try:
            time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Long running operation wait cancelled.")
            raise
        except Exception as client_exception:
            log_telemetry('client exception', log_type='trace')
            message = getattr(client_exception, 'message', client_exception)

            try:
                message = str(message) + ' ' + json.loads(client_exception.response.text) \
                    ['error']['details'][0]['message']
            except: #pylint: disable=bare-except
                pass

            raise CLIError('{}'.format(message))

create_certificate.__doc__ = KeyVaultClient.create_certificate.__doc__

def download_certificate(client, vault_base_url, certificate_name, file_path,
                         encoding='binary', certificate_version=''):
    """ Download a certificate from a KeyVault. """
    if os.path.isfile(file_path) or os.path.isdir(file_path):
        raise CLIError("File or directory named '{}' already exists.".format(file_path))

    cert = client.keyvault.get_certificate(
        vault_base_url, certificate_name, certificate_version).cer

    try:
        with open(file_path, 'wb') as f:
            if encoding == 'binary':
                f.write(cert)
            else:
                import base64
                try:
                    f.write(base64.encodebytes(cert))
                except AttributeError:
                    f.write(base64.encodestring(cert)) # pylint: disable=deprecated-method
    except Exception as ex: # pylint: disable=broad-except
        if os.path.isfile(file_path):
            os.remove(file_path)
        raise ex

def add_certificate_contact(client, vault_base_url, contact_email, contact_name=None,
                            contact_phone=None):
    """ Add a contact to the specified vault to receive notifications of certificate operations. """
    from azure.keyvault.generated.models import \
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
    from azure.keyvault.generated.models import \
        (Contacts, KeyVaultErrorException)
    contacts = client.get_certificate_contacts(vault_base_url).contact_list
    remaining = Contacts([x for x in contacts if x.email_address != contact_email])
    if len(contacts) == len(remaining.contact_list):
        raise CLIError("contact '{}' not found in vault '{}'".format(contact_email, vault_base_url))
    if remaining.contact_list:
        return client.set_certificate_contacts(vault_base_url, remaining.contact_list)
    else:
        return client.delete_certificate_contacts(vault_base_url)

def create_certificate_issuer(client, vault_base_url, issuer_name, provider_name, account_id=None,
                              password=None, disabled=False, organization_id=None):
    """ Create a certificate issuer record.
    :param issuer_name: Unique identifier for the issuer settings.
    :param provider_name: The certificate provider name. Must be registered with your
        tenant ID and in your region.
    :param account_id: The issuer account id/username/etc.
    :param password: The issuer account password/secret/etc.
    :param organization_id: The organization id.
    """
    from azure.keyvault.generated.models import \
        (CertificateIssuerSetParameters, IssuerCredentials, OrganizationDetails, IssuerAttributes,
         AdministratorDetails, KeyVaultErrorException)
    try:
        client.get_certificate_issuer(vault_base_url, issuer_name)
        raise CLIError("issuer '{}' already exists".format(issuer_name))
    except KeyVaultErrorException:
        # ensure issuer does not already exist
        pass
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
    from azure.keyvault.generated.models import \
        (CertificateIssuerSetParameters, IssuerCredentials, OrganizationDetails, IssuerAttributes,
         AdministratorDetails, KeyVaultErrorException)

    def update(obj, prop, value, nullable=False):
        set_value = value if value is not None else getattr(obj, prop, None)
        if not set_value and not nullable:
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
    from azure.keyvault.generated.models import \
        (AdministratorDetails, KeyVaultErrorException)

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
    created_admin = next(x for x in result.organization_details.admin_details \
        if x.email_address == email)
    return created_admin

def delete_certificate_issuer_admin(client, vault_base_url, issuer_name, email):
    """ Remove admin details for the specified certificate issuer. """
    from azure.keyvault.generated.models import \
        (AdministratorDetails, KeyVaultErrorException)
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

def certificate_policy_template():
    from azure.keyvault.generated.models import \
        (CertificatePolicy, CertificateAttributes, KeyProperties, SecretProperties,
         X509CertificateProperties, SubjectAlternativeNames, LifetimeAction, Action, Trigger,
         IssuerParameters)
    from azure.keyvault.generated.models.key_vault_client_enums \
        import ActionType, JsonWebKeyType, KeyUsageType
    # create sample policy
    template = CertificatePolicy(
        key_properties=KeyProperties(
            exportable=False,
            key_type='{{ {} }}'.format(' | '.join([x.value for x in JsonWebKeyType])),
            key_size=2048,
            reuse_key=False),
        secret_properties=SecretProperties('text/plain'),
        x509_certificate_properties=X509CertificateProperties(
            subject_alternative_names=SubjectAlternativeNames(
                emails=['admin@mydomain.com', 'user@mydomain.com'],
                dns_names=['www.mydomain.com'],
                upns=['principal-name']
            ),
            subject='X509 Distinguished Name',
            ekus=['ekus'],
            key_usage=['{{ {} }}'.format(' | '.join([x.value for x in KeyUsageType]))],
            validity_in_months=60
        ),
        lifetime_actions=[
            LifetimeAction(
                Trigger(lifetime_percentage=90, days_before_expiry=7),
                Action(action_type='{{ {} }}'.format(' | '.join([x.value for x in ActionType])))
            )
        ],
        issuer_parameters=IssuerParameters(name='issuer-name'),
        attributes=CertificateAttributes(
            enabled=True
        )
    )
    # remove properties which are read only
    del template.id
    del template.attributes.created
    del template.attributes.updated
    return template
