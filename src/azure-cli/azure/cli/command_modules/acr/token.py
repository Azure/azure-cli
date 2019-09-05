# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError
from ._utils import get_resource_group_name_by_registry_name


def acr_token_create(cmd,
                     client,
                     registry_name,
                     token_name,
                     scope_map_name,
                     status=None,
                     resource_group_name=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    from ._utils import get_resource_id_by_registry_name

    token_create_parameters = {
        "Properties": {
            "ScopeMapId": None,
            "Credentials": {
                "Certificates": []
            }
        }
    }

    arm_resource_id = get_resource_id_by_registry_name(cmd.cli_ctx, registry_name)
    scope_map_id = arm_resource_id + "/scopeMaps/" + scope_map_name
    token_create_parameters["Properties"]["ScopeMapId"] = scope_map_id

    if status:
        if status not in ["enabled", "disabled"]:
            raise CLIError("Unkown status: {}. Allowed values are 'enabled' or 'disabled'.".format(status))
        token_create_parameters["Properties"]["Status"] = status

    return client.create(
        resource_group_name,
        registry_name,
        token_name,
        token_create_parameters
    )


def acr_token_delete(cmd,
                     client,
                     registry_name,
                     token_name,
                     yes=None,
                     resource_group_name=None):

    if not yes:
        from knack.prompting import prompt_y_n
        confirmation = prompt_y_n("Deleting the token '{}' will invalidate access to anyone using its credentials. "
                                  "Proceed?".format(token_name))

        if not confirmation:
            return None

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)
    return client.delete(resource_group_name, registry_name, token_name)


def acr_token_update(cmd,
                     client,
                     registry_name,
                     token_name,
                     scope_map_name=None,
                     status=None,
                     resource_group_name=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    from ._utils import get_resource_id_by_registry_name

    token_update_parameters = {}

    scope_map_id = None
    if scope_map_name:
        arm_resource_id = get_resource_id_by_registry_name(cmd.cli_ctx, registry_name)
        scope_map_id = arm_resource_id + "/scopeMaps/" + scope_map_name
        token_update_parameters["ScopeMapId"] = scope_map_id

    if status:
        if status not in ["enabled", "disabled"]:
            raise CLIError("Unkown status: {}. Allowed values are 'enabled' or 'disabled'.".format(status))
        token_update_parameters["Status"] = status

    return client.update(
        resource_group_name,
        registry_name,
        token_name,
        token_update_parameters
    )


def acr_token_show(cmd,
                   client,
                   registry_name,
                   token_name,
                   resource_group_name=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    return client.get(
        resource_group_name,
        registry_name,
        token_name
    )


def acr_token_list(cmd,
                   client,
                   registry_name,
                   resource_group_name=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    return client.list(
        resource_group_name,
        registry_name
    )


# Credential functions


def acr_token_credential_generate(cmd,
                                  client,
                                  registry_name,
                                  token_name,
                                  password1=False,
                                  password2=False,
                                  expiry=None,
                                  months=None,
                                  resource_group_name=None):

    from ._utils import get_resource_id_by_registry_name

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)
    arm_resource_id = get_resource_id_by_registry_name(cmd.cli_ctx, registry_name)
    token_id = arm_resource_id + "/tokens/" + token_name
    generate_credentials_parameters = {"TokenId": token_id}

    if password1 ^ password2:  # We only want to specify a password if only one wass passed.
        generate_credentials_parameters["Name"] = "password1" if password1 else "password2"

    if expiry:
        generate_credentials_parameters["Expiry"] = expiry
    elif months is not None:
        from ._utils import add_months_to_now
        generate_credentials_parameters["Expiry"] = add_months_to_now(months).isoformat(sep='T')

    return client.generate_credentials(
        resource_group_name,
        registry_name,
        generate_credentials_parameters
    )


def acr_token_credential_delete(cmd,
                                client,
                                registry_name,
                                token_name,
                                certificate1=False,
                                certificate2=False,
                                password1=False,
                                password2=False,
                                resource_group_name=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    if (certificate1 or certificate2 or password1 or password2) is False:
        raise CLIError("Nothing to delete")

    token = acr_token_show(cmd,
                           client,
                           registry_name,
                           token_name,
                           resource_group_name)

    new_certificates = token.credentials.certificates
    if certificate1:
        new_certificates = [cert for cert in new_certificates if cert.name != "certificate1"]
    if certificate2:
        new_certificates = [cert for cert in new_certificates if cert.name != "certificate2"]

    new_certificates_payload = []
    for cert in new_certificates:
        new_certificates_payload.append({
            "Name": cert.name
        })

    new_passwords = token.credentials.passwords
    if password1:
        new_passwords = [password for password in new_passwords if password.name != "password1"]
    if password2:
        new_passwords = [password for password in new_passwords if password.name != "password2"]

    new_passwords_payload = []
    for password in new_passwords:
        new_passwords_payload.append({
            "Name": password.name
        })

    token_update_parameters = {
        "Credentials": {
            "Certificates": new_certificates_payload,
            "Passwords": new_passwords_payload
        }
    }

    return client.update(
        resource_group_name,
        registry_name,
        token_name,
        token_update_parameters
    )


def acr_token_credential_add_certificate(cmd,
                                         client,
                                         registry_name,
                                         token_name,
                                         target_certificate,
                                         certificate,
                                         key_vault=None,
                                         create_certificate=False,
                                         resource_group_name=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    token = acr_token_show(cmd,
                           client,
                           registry_name,
                           token_name,
                           resource_group_name)

    certificates_payload = _handle_add_certificate(cmd.cli_ctx,
                                                   token,
                                                   target_certificate,
                                                   key_vault,
                                                   certificate,
                                                   create_certificate)

    token_update_parameters = {
        "Credentials": {
            "Certificates": certificates_payload
        }
    }

    return client.update(
        resource_group_name,
        registry_name,
        token_name,
        token_update_parameters
    )


def _get_key_vault_client(cli_ctx):
    from azure.cli.core._profile import Profile
    from azure.keyvault import KeyVaultAuthentication, KeyVaultClient
    from azure.cli.core.profiles import ResourceType, get_api_version
    version = str(get_api_version(cli_ctx, ResourceType.DATA_KEYVAULT))

    def _get_token(server, resource, scope):  # pylint: disable=unused-argument
        return Profile(cli_ctx=cli_ctx).get_login_credentials(resource)[0]._token_retriever()  # pylint: disable=protected-access

    return KeyVaultClient(KeyVaultAuthentication(_get_token), api_version=version)


def _create_self_signed_cert_with_keyvault(kv_client, vault_url, certificate):
    cert_policy = {
        'attributes': {
            'enabled': True
        },
        'issuer': {
            'name': 'Self'
        },
        'key_props': {
            'exportable': True,
            'key_size': 2048,
            'kty': 'RSA',
            'reuse_key': True
        },
        'lifetime_actions': [{
            'action': {
                'action_type': 'AutoRenew'
            },
            'trigger': {
                'days_before_expiry': 90
            }
        }],
        'secret_props': {
            'contentType': 'application/x-pem-file'
        },
        'x509_props': {
            'ekus': [
                '1.3.6.1.5.5.7.3.1',
                '1.3.6.1.5.5.7.3.2'
            ],
            'key_usage': [
                'digitalSignature',
                'keyEncipherment',
                'keyCertSign'
            ],
            'sans': {
                'dns_names': []
            },
            'subject': 'CN=Azure Container Registry Token Certificate',
            'validity_months': 25
        }
    }

    kv_client.create_certificate(vault_url, certificate, cert_policy)
    import time
    while kv_client.get_certificate_operation(vault_url, certificate).status != 'completed':
        time.sleep(5)


def _handle_key_vault_certificate(cli_ctx, key_vault, certificate, create_certificate):
    kv_client = _get_key_vault_client(cli_ctx)
    vault_url = 'https://{}{}/'.format(key_vault, cli_ctx.cloud.suffixes.keyvault_dns)

    if create_certificate:
        _create_self_signed_cert_with_keyvault(kv_client, vault_url, certificate)

    cert_entity = kv_client.get_certificate(vault_url, certificate, '')

    from base64 import b64encode
    cert_string = '-----BEGIN CERTIFICATE-----\n' + \
                  b64encode(cert_entity.cer).decode('utf-8') + \
                  '\n-----END CERTIFICATE-----\n'
    return b64encode(cert_string.encode()).decode()


def _handle_local_certificate(certificate):
    from base64 import b64encode

    try:
        certificate_content = open(certificate, 'r').read()
    except IOError as e:
        raise CLIError('Could not read local certificate {}. Exception: {}'.format(certificate, str(e)))

    return b64encode(certificate_content.encode()).decode()


def _handle_add_certificate(cli_ctx, token, target_certificate, key_vault, certificate, create_certificate):
    if target_certificate not in ['certificate1', 'certificate2']:
        raise CLIError('Invalid target certificate. Name should be be \'certificate1\' or \'certificate2\'')

    certificates_dict = {}
    for existing_certificate in token.credentials.certificates:
        certificates_dict[existing_certificate.name] = None

    if key_vault:
        encoded_cert = _handle_key_vault_certificate(cli_ctx, key_vault, certificate, create_certificate)
    else:
        if create_certificate:
            raise CLIError('A certificate can only be created for a target key vault')
        encoded_cert = _handle_local_certificate(certificate)

    certificates_dict[target_certificate] = encoded_cert

    certificates_payload = []
    for key in certificates_dict:
        value = certificates_dict[key]
        if value:
            certificate = {
                "Name": key,
                "EncodedPEMCertificate": value
            }
        else:
            certificate = {
                "Name": key
            }
        certificates_payload.append(certificate)

    certificates_payload.sort(key=lambda cert: cert["Name"])
    return certificates_payload
