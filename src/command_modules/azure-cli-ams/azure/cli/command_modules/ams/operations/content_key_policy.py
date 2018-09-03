# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-arguments, too-many-locals, too-many-branches
from knack.util import CLIError

from azure.mgmt.media.models import (ContentKeyPolicyOption, ContentKeyPolicyClearKeyConfiguration,
                                     ContentKeyPolicyOpenRestriction, ContentKeyPolicySymmetricTokenKey,
                                     ContentKeyPolicyRsaTokenKey, ContentKeyPolicyX509CertificateTokenKey,
                                     ContentKeyPolicyTokenRestriction)


def create_content_key_policy(client, resource_group_name, account_name, content_key_policy_name,
                              policy_option_name, description=None,
                              clear_key_configuration=False, open_restriction=False,
                              issuer=None, audience=None, symmetric_token_key=None, rsa_token_key_exponent=None,
                              rsa_token_key_modulus=None, x509_certificate_token_key=None,
                              alt_symmetric_token_keys=None, alt_rsa_token_key_exponents=None,
                              alt_rsa_token_key_modulus=None, alt_x509_certificate_token_keys=None,
                              token_claims=None, restriction_token_type=None,
                              open_id_connect_discovery_document=None):

    return _generate_content_key_policy_object(client, resource_group_name, account_name, content_key_policy_name,
                                               policy_option_name, clear_key_configuration, open_restriction,
                                               issuer, audience, symmetric_token_key, rsa_token_key_exponent,
                                               rsa_token_key_modulus, x509_certificate_token_key,
                                               alt_symmetric_token_keys, alt_rsa_token_key_exponents,
                                               alt_rsa_token_key_modulus, alt_x509_certificate_token_keys,
                                               token_claims, restriction_token_type, open_id_connect_discovery_document,
                                               description)


def add_content_key_policy_option(client, resource_group_name, account_name, content_key_policy_name,
                                  policy_option_name, clear_key_configuration=False, open_restriction=False,
                                  issuer=None, audience=None, symmetric_token_key=None, rsa_token_key_exponent=None,
                                  rsa_token_key_modulus=None, x509_certificate_token_key=None,
                                  alt_symmetric_token_keys=None, alt_rsa_token_key_exponents=None,
                                  alt_rsa_token_key_modulus=None, alt_x509_certificate_token_keys=None,
                                  token_claims=None, restriction_token_type=None,
                                  open_id_connect_discovery_document=None):

    return _generate_content_key_policy_object(client, resource_group_name, account_name, content_key_policy_name,
                                               policy_option_name, clear_key_configuration, open_restriction,
                                               issuer, audience, symmetric_token_key, rsa_token_key_exponent,
                                               rsa_token_key_modulus, x509_certificate_token_key,
                                               alt_symmetric_token_keys, alt_rsa_token_key_exponents,
                                               alt_rsa_token_key_modulus, alt_x509_certificate_token_keys,
                                               token_claims, restriction_token_type, open_id_connect_discovery_document)


def remove_content_key_policy_option(client, resource_group_name, account_name, content_key_policy_name,
                                     policy_option_name):
    policy = client.get(resource_group_name, account_name, content_key_policy_name)

    if all(option.name != policy_option_name for option in policy.options):
        raise CLIError('No policy option found with name "' + policy_option_name + '"')

    policy.options = list(filter(lambda option: option.name != policy_option_name, policy.options))

    return client.create_or_update(resource_group_name, account_name,
                                   content_key_policy_name, policy.options)


# Private methods used

def _generate_content_key_policy_object(client, resource_group_name, account_name, content_key_policy_name,
                                        policy_option_name, clear_key_configuration, open_restriction,
                                        issuer, audience, symmetric_token_key, rsa_token_key_exponent,
                                        rsa_token_key_modulus, x509_certificate_token_key,
                                        alt_symmetric_token_keys, alt_rsa_token_key_exponents,
                                        alt_rsa_token_key_modulus, alt_x509_certificate_token_keys,
                                        token_claims, restriction_token_type,
                                        open_id_connect_discovery_document, description=None):

    configuration = None
    restriction = None

    policy = client.get_policy_properties_with_secrets(resource_group_name, account_name, content_key_policy_name)
    policy_options = policy.options if policy else []

    valid_token_restriction = _valid_token_restriction(symmetric_token_key, rsa_token_key_exponent,
                                                       rsa_token_key_modulus, x509_certificate_token_key,
                                                       restriction_token_type, issuer, audience)

    # TODO: probably some refactor in the near future to avoid having multiple ANDs.
    if open_restriction and valid_token_restriction:
        raise CLIError('You should only use one restriction type.')

    if clear_key_configuration:
        configuration = ContentKeyPolicyClearKeyConfiguration()

    if open_restriction:
        restriction = ContentKeyPolicyOpenRestriction()

    if valid_token_restriction:
        if _token_restriction_keys_available(symmetric_token_key, rsa_token_key_exponent,
                                             rsa_token_key_modulus, x509_certificate_token_key) != 1:
            raise CLIError('You should use alternative (alt) token keys if you have more than one token key.')

        primary_verification_key = None
        _symmetric_keys = _coalesce_str(alt_symmetric_token_keys).split()
        _rsa_key_exponents = _coalesce_str(alt_rsa_token_key_exponents).split()
        _rsa_key_modulus = _coalesce_str(alt_rsa_token_key_modulus).split()
        _x509_keys = _coalesce_str(alt_x509_certificate_token_keys).split()
        alternative_keys = []

        if symmetric_token_key is not None:
            primary_verification_key = _symmetric_token_key_factory(bytearray(symmetric_token_key, 'utf-8'))
        elif rsa_token_key_exponent is not None and rsa_token_key_modulus is not None:
            primary_verification_key = _rsa_token_key_factory(
                bytearray(rsa_token_key_exponent, 'utf-8'), bytearray(rsa_token_key_modulus, 'utf-8'))
        elif x509_certificate_token_key is not None:
            primary_verification_key = _x509_token_key_factory(
                bytearray(x509_certificate_token_key.replace('\\n', '\n'), 'utf-8'))
        else:
            raise CLIError('Invalid token key.')  # This should not happen.. but just in case.

        # Extra validation to make sure exponents and modulus have the same cardinality
        if len(_rsa_key_exponents) != len(_rsa_key_modulus):
            raise CLIError('The number of alternative RSA key exponents and modulus differ.')

        for key in _symmetric_keys:
            alternative_keys.append(_symmetric_token_key_factory(key))

        for exp, mod in zip(_rsa_key_exponents, _rsa_key_modulus):
            alternative_keys.append(_rsa_token_key_factory(exp, mod))

        for key in _x509_keys:
            alternative_keys.append(_x509_token_key_factory(key))

        restriction = ContentKeyPolicyTokenRestriction(
            issuer=issuer, audience=audience, primary_verification_key=primary_verification_key,
            alternate_verification_keys=alternative_keys, required_claims=token_claims,
            restriction_token_type=restriction_token_type,
            open_id_connect_discovery_document=open_id_connect_discovery_document)

    if restriction is None or configuration is None:
        raise CLIError('You must have one restriction and one configuration.')

    policy_option = ContentKeyPolicyOption(name=policy_option_name,
                                           configuration=configuration,
                                           restriction=restriction)

    policy_options.append(policy_option)

    return client.create_or_update(resource_group_name, account_name,
                                   content_key_policy_name, policy_options, description)


def _coalesce_str(value):
    return value or ''


def _symmetric_token_key_factory(symmetric_token_key):
    return ContentKeyPolicySymmetricTokenKey(key_value=symmetric_token_key)


def _rsa_token_key_factory(rsa_token_key_exponent, rsa_token_key_modulus):
    return ContentKeyPolicyRsaTokenKey(
        exponent=rsa_token_key_exponent, modulus=rsa_token_key_modulus)


def _x509_token_key_factory(x509_certificate_token_key):
    return ContentKeyPolicyX509CertificateTokenKey(
        raw_body=x509_certificate_token_key)


def _token_restriction_keys_available(symmetric_token_key, rsa_token_key_exponent, rsa_token_key_modulus,
                                      x509_certificate_token_key):
    available = 0

    if symmetric_token_key is not None:
        available += 1

    if rsa_token_key_exponent is not None and rsa_token_key_modulus is not None:
        available += 1

    if x509_certificate_token_key is not None:
        available += 1

    return available


def _valid_token_restriction(symmetric_token_key, rsa_token_key_exponent, rsa_token_key_modulus,
                             x509_certificate_token_key, restriction_token_type,
                             issuer, audience):
    available_keys = _token_restriction_keys_available(symmetric_token_key, rsa_token_key_exponent,
                                                       rsa_token_key_modulus, x509_certificate_token_key)
    return restriction_token_type and available_keys >= 1 and issuer and audience
