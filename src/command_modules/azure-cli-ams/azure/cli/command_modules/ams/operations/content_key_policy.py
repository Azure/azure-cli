# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def create_content_key_policy(client, resource_group_name, account_name, content_key_policy_name,
                              description=None, clear_key_configuration=False, open_restriction=False,
                              policy_option_name='Basic policy option'):
    from azure.mgmt.media.models import (ContentKeyPolicyOption, ContentKeyPolicyClearKeyConfiguration,
                                         ContentKeyPolicyOpenRestriction)
    default_configuration = None
    default_restriction = None

    if clear_key_configuration:
        default_configuration = ContentKeyPolicyClearKeyConfiguration()

    if open_restriction:
        default_restriction = ContentKeyPolicyOpenRestriction()

    options = [ContentKeyPolicyOption(name=policy_option_name,
                                      configuration=default_configuration,
                                      restriction=default_restriction)]

    return client.create_or_update(resource_group_name, account_name,
                                   content_key_policy_name, options, description)

def add_content_key_policy_option(client, resource_group_name, account_name, content_key_policy_name,
                                  clear_key_configuration=False, open_restriction=False, 
                                  issuer=None, audience=None, symmetric_token_key=None,
                                  rsa_token_key_exponent=None, rsa_token_key_modulus=None,
                                  x509_certificate_token_key=None, alt_symmetric_token_key=None,
                                  alt_rsa_token_key_exponent=None, alt_rsa_token_key_modulus=None,
                                  alt_x509_certificate_token_key=None, token_claims=None,
                                  restriction_token_type=None, open_id_connect_discovery_document=None):
    print(' ok')

def remove_content_key_policy_option(client):
    print(' nook')
