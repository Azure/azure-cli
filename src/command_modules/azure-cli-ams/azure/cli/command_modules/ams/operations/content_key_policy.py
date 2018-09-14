# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-arguments, too-many-locals, too-many-branches
import base64
import json
import codecs

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from knack.util import CLIError

from azure.cli.command_modules.ams._utils import parse_timedelta, JsonBytearrayEncoder

from azure.mgmt.media.models import (ContentKeyPolicyOption, ContentKeyPolicyClearKeyConfiguration,
                                     ContentKeyPolicyOpenRestriction, ContentKeyPolicySymmetricTokenKey,
                                     ContentKeyPolicyRsaTokenKey, ContentKeyPolicyX509CertificateTokenKey,
                                     ContentKeyPolicyTokenRestriction, ContentKeyPolicyTokenClaim,
                                     ContentKeyPolicyWidevineConfiguration, ContentKeyPolicyFairPlayConfiguration,
                                     ContentKeyPolicyPlayReadyConfiguration, ContentKeyPolicyPlayReadyLicense,
                                     ContentKeyPolicyPlayReadyContentEncryptionKeyFromHeader,
                                     ContentKeyPolicyPlayReadyContentEncryptionKeyFromKeyIdentifier,
                                     ContentKeyPolicyPlayReadyPlayRight,
                                     ContentKeyPolicyPlayReadyExplicitAnalogTelevisionRestriction)


def create_content_key_policy(client, resource_group_name, account_name, content_key_policy_name,
                              policy_option_name, description=None,
                              clear_key_configuration=False, open_restriction=False,
                              issuer=None, audience=None, token_key=None, symmetric=False, rsa=False, x509=False,
                              alt_symmetric_token_keys=None, alt_rsa_token_key_exponents=None,
                              alt_rsa_token_key_modulus=None, alt_x509_certificate_token_keys=None,
                              token_claims=None, restriction_token_type=None,
                              open_id_connect_discovery_document=None, widevine_template=None,
                              ask=None, fair_play_pfx_password=None, fair_play_pfx=None,
                              rental_and_lease_key_type=None, rental_duration=None, play_ready_configuration=None):

    policy_option = _generate_content_key_policy_option(policy_option_name, clear_key_configuration, open_restriction,
                                                        issuer, audience, token_key, symmetric, rsa, x509,
                                                        alt_symmetric_token_keys, alt_rsa_token_key_exponents,
                                                        alt_rsa_token_key_modulus, alt_x509_certificate_token_keys,
                                                        token_claims, restriction_token_type, open_id_connect_discovery_document,
                                                        widevine_template, ask, fair_play_pfx_password, fair_play_pfx,
                                                        rental_and_lease_key_type, rental_duration, play_ready_configuration)

    return client.create_or_update(resource_group_name, account_name,
                                   content_key_policy_name, [policy_option], description)


def show_content_key_policy(client, resource_group_name, account_name, content_key_policy_name,
                            with_secrets=False):

    if with_secrets:
        content_key_policy = client.get_policy_properties_with_secrets(resource_group_name=resource_group_name, account_name=account_name,
                                                                       content_key_policy_name=content_key_policy_name)
        json_object = json.dumps(content_key_policy, cls=JsonBytearrayEncoder, indent=4)
        return json.loads(json_object)

    return client.get(resource_group_name=resource_group_name, account_name=account_name,
                      content_key_policy_name=content_key_policy_name)


def add_content_key_policy_option(client, resource_group_name, account_name, content_key_policy_name,
                                  policy_option_name, clear_key_configuration=False, open_restriction=False,
                                  issuer=None, audience=None, token_key=None, symmetric=False, rsa=False, x509=False,
                                  alt_symmetric_token_keys=None, alt_rsa_token_key_exponents=None,
                                  alt_rsa_token_key_modulus=None, alt_x509_certificate_token_keys=None,
                                  token_claims=None, restriction_token_type=None,
                                  open_id_connect_discovery_document=None, widevine_template=None,
                                  ask=None, fair_play_pfx_password=None, fair_play_pfx=None,
                                  rental_and_lease_key_type=None, rental_duration=None, play_ready_configuration=None):

    policy = client.get_policy_properties_with_secrets(resource_group_name, account_name, content_key_policy_name)

    if not policy:
        raise CLIError('The content key policy was not found.')

    options = policy.options

    policy_option = _generate_content_key_policy_option(policy_option_name, clear_key_configuration, open_restriction,
                                                        issuer, audience, token_key, symmetric, rsa, x509,
                                                        alt_symmetric_token_keys, alt_rsa_token_key_exponents,
                                                        alt_rsa_token_key_modulus, alt_x509_certificate_token_keys,
                                                        token_claims, restriction_token_type, open_id_connect_discovery_document,
                                                        widevine_template, ask, fair_play_pfx_password, fair_play_pfx,
                                                        rental_and_lease_key_type, rental_duration, play_ready_configuration)

    options.append(policy_option)

    return client.update(resource_group_name, account_name,
                         content_key_policy_name, options, policy.description)


def remove_content_key_policy_option(client, resource_group_name, account_name, content_key_policy_name,
                                     policy_option_id):
    policy = client.get_policy_properties_with_secrets(resource_group_name, account_name, content_key_policy_name)

    if not policy:
        raise CLIError('The content key policy was not found.')

    if all(option.policy_option_id != policy_option_id for option in policy.options):
        raise CLIError('No policy option found with id "' + policy_option_id + '"')

    policy.options = list(filter(lambda option: option.policy_option_id != policy_option_id, policy.options))

    return client.update(resource_group_name, account_name,
                         content_key_policy_name, policy.options)


def update_content_key_policy_setter(client, resource_group_name, account_name, content_key_policy_name,
                                     parameters):
    return client.update(resource_group_name, account_name,
                         content_key_policy_name, parameters.options, parameters.description)


def update_content_key_policy(instance, description=None):
    if not instance:
        raise CLIError('The content key policy was not found.')

    if description is not None:
        instance.description = description

    return instance


# Private methods used

def _generate_content_key_policy_option(policy_option_name, clear_key_configuration, open_restriction,
                                        issuer, audience, token_key, symmetric, rsa, x509,
                                        alt_symmetric_token_keys, alt_rsa_token_key_exponents,
                                        alt_rsa_token_key_modulus, alt_x509_certificate_token_keys,
                                        token_claims, restriction_token_type,
                                        open_id_connect_discovery_document, widevine_template,
                                        ask, fair_play_pfx_password, fair_play_pfx,
                                        rental_and_lease_key_type, rental_duration, play_ready_configuration):

    configuration = None
    restriction = None

    valid_token_restriction = _valid_token_restriction(token_key, rsa, x509, symmetric,
                                                       restriction_token_type, issuer, audience)

    valid_fairplay_configuration = _valid_fairplay_configuration(ask, fair_play_pfx_password,
                                                                 fair_play_pfx, rental_and_lease_key_type,
                                                                 rental_duration)

    valid_playready_configuration = _valid_playready_configuration(play_ready_configuration)

    if _count_truthy([open_restriction, valid_token_restriction]) != 1:
        raise CLIError('You should use exactly one restriction type.')

    if _count_truthy([clear_key_configuration, widevine_template,
                      valid_fairplay_configuration, valid_playready_configuration]) != 1:
        raise CLIError('You should use exactly one configuration type.')

    if clear_key_configuration:
        configuration = ContentKeyPolicyClearKeyConfiguration()

    if widevine_template:
        configuration = ContentKeyPolicyWidevineConfiguration(widevine_template=widevine_template)

    if valid_fairplay_configuration:
        configuration = ContentKeyPolicyFairPlayConfiguration(
            ask=bytearray(ask, 'utf-8'), fair_play_pfx_password=fair_play_pfx_password,
            fair_play_pfx=_base64(_read_binary(fair_play_pfx)).decode('ascii'),
            rental_and_lease_key_type=rental_and_lease_key_type,
            rental_duration=rental_duration)

    if valid_playready_configuration:
        configuration = _play_ready_configuration_factory(json.loads(play_ready_configuration))

    if open_restriction:
        restriction = ContentKeyPolicyOpenRestriction()

    if valid_token_restriction:
        if _count_truthy([rsa, x509, symmetric]) != 1:
            raise CLIError('You should use alternative (alt) token keys if you have more than one token key.')

        primary_verification_key = None
        _symmetric_keys = _coalesce_str(alt_symmetric_token_keys).split()
        _rsa_key_exponents = _coalesce_str(alt_rsa_token_key_exponents).split()
        _rsa_key_modulus = _coalesce_str(alt_rsa_token_key_modulus).split()
        _x509_keys = _coalesce_str(alt_x509_certificate_token_keys).split()
        alternative_keys = []
        _token_claims = []

        if symmetric:
            primary_verification_key = _symmetric_token_key_factory(bytearray(token_key, 'utf-8'))
        elif rsa:
            primary_verification_key = _rsa_token_key_factory(_read(token_key, 'r'))
        elif x509:
            primary_verification_key = _x509_token_key_factory(
                bytearray(_read_binary(token_key)))

        for key in _symmetric_keys:
            alternative_keys.append(_symmetric_token_key_factory(key))

        for exp, mod in zip(_rsa_key_exponents, _rsa_key_modulus):
            alternative_keys.append(_rsa_token_key_factory(exp, mod))

        for key in _x509_keys:
            alternative_keys.append(_x509_token_key_factory(key))

        if token_claims is not None:
            for key in token_claims:
                claim = ContentKeyPolicyTokenClaim(claim_type=key,
                                                   claim_value=token_claims[key])
                _token_claims.append(claim)

        restriction = ContentKeyPolicyTokenRestriction(
            issuer=issuer, audience=audience, primary_verification_key=primary_verification_key,
            alternate_verification_keys=alternative_keys, required_claims=_token_claims,
            restriction_token_type=restriction_token_type,
            open_id_connect_discovery_document=open_id_connect_discovery_document)

    if restriction is None or configuration is None:
        raise CLIError(
            'Could not build content key policy option due to invalid restriction or configuration.')

    return ContentKeyPolicyOption(name=policy_option_name,
                                  configuration=configuration,
                                  restriction=restriction)


# Returns string if not null, or an empty string otherwise.
def _coalesce_str(value):
    return value or ''


def _coalesce_timedelta(value):
    return parse_timedelta(value) if value else None


# Counts how many values are truthy on a list.
def _count_truthy(values):
    return len([value for value in values if value])


def _symmetric_token_key_factory(symmetric_token_key):
    return ContentKeyPolicySymmetricTokenKey(key_value=symmetric_token_key)


def _rsa_token_key_factory(rsa_content):
    rsa_key = serialization.load_pem_public_key(
        rsa_content.encode('ascii'),
        backend=default_backend()
    )

    exp = rsa_key.public_numbers().e
    mod = rsa_key.public_numbers().n

    return ContentKeyPolicyRsaTokenKey(
        exponent=bytearray(_int2bytes(exp)), modulus=bytearray(_int2bytes(mod)))


def _x509_token_key_factory(x509_certificate_token_key):
    return ContentKeyPolicyX509CertificateTokenKey(
        raw_body=x509_certificate_token_key)


def _valid_token_restriction(token_key, rsa, x509, symmetric, restriction_token_type, issuer, audience):
    return _validate_all_conditions(
        [restriction_token_type, token_key and any([rsa, x509, symmetric]), issuer, audience],
        'Malformed content key policy token restriction.')


def _valid_fairplay_configuration(ask, fair_play_pfx_password, fair_play_pfx, rental_and_lease_key_type, rental_duration):
    return _validate_all_conditions(
        [ask, fair_play_pfx_password, fair_play_pfx, rental_and_lease_key_type, rental_duration],
        'Malformed content key policy FairPlay configuration.')


def _valid_playready_configuration(play_ready_configuration):
    if play_ready_configuration is None:
        return False

    def __valid_license(lic):
        return _validate_all_conditions([lic.get('allowTestDevices') is not None,
                                         lic.get('licenseType') in ['NonPersistent', 'Persistent'],
                                         lic.get('contentKeyLocation') is not None,
                                         lic.get('contentType') in ['Unspecified', 'UltraVioletDownload', 'UltraVioletStreaming'],
                                         lic.get('playRight') is None or __valid_play_right(lic.get('playRight'))],
                                        'Malformed PlayReady license.')

    def __valid_play_right(prl):
        return _validate_all_conditions([(prl.get('explicitAnalogTelevisionOutputRestriction') is None or
                                          __valid_eator(prl.get('explicitAnalogTelevisionOutputRestriction'))),
                                         prl.get('digitalVideoOnlyContentRestriction') is not None,
                                         prl.get('imageConstraintForAnalogComponentVideoRestriction') is not None,
                                         prl.get('imageConstraintForAnalogComputerMonitorRestriction') is not None,
                                         prl.get('allowPassingVideoContentToUnknownOutput') in ['NotAllowed', 'Allowed',
                                                                                                'AllowedWithVideoConstriction']],
                                        'Malformed license PlayRight.')

    def __valid_eator(eator):
        return _validate_all_conditions([eator.get('bestEffort') is not None,
                                         eator.get('configurationData') is not None],
                                        'Malformed explicit analog television output restriction.')

    cfg = None

    try:
        cfg = json.loads(play_ready_configuration)
    except ValueError as err:
        raise CLIError('Malformed JSON: ' + str(err))

    return _validate_all_conditions(
        [cfg.get('licenses') is not None,
         len(cfg.get('licenses')) > 0,
         all(__valid_license(l) for l in cfg.get('licenses'))],
        'Malformed content key policy PlayReady configuration'
    )


def _play_ready_configuration_factory(content):

    def __get_content_key_location(ckl):
        if ckl.get('keyId'):
            return ContentKeyPolicyPlayReadyContentEncryptionKeyFromKeyIdentifier(
                key_id=ckl.get('keyId')
            )
        return ContentKeyPolicyPlayReadyContentEncryptionKeyFromHeader()

    def __get_eator(eator):
        if eator is None:
            return None
        return ContentKeyPolicyPlayReadyExplicitAnalogTelevisionRestriction(
            best_effort=eator.get('bestEffort'),
            configuration_data=eator.get('configurationData')
        )

    def __get_play_right(prl):
        if prl is None:
            return None
        return ContentKeyPolicyPlayReadyPlayRight(
            first_play_expiration=_coalesce_timedelta(prl.get('firstPlayExpiration')),
            scms_restriction=prl.get('scmsRestriction'),
            agc_and_color_stripe_restriction=prl.get('agcAndColorStripeRestriction'),
            explicit_analog_television_output_restriction=__get_eator(prl.get('explicitAnalogTelevisionOutputRestriction')),
            digital_video_only_content_restriction=prl.get('digitalVideoOnlyContentRestriction'),
            image_constraint_for_analog_component_video_restriction=prl.get('imageConstraintForAnalogComponentVideoRestriction'),
            image_constraint_for_analog_computer_monitor_restriction=prl.get('imageConstraintForAnalogComputerMonitorRestriction'),
            allow_passing_video_content_to_unknown_output=prl.get('allowPassingVideoContentToUnknownOutput'),
            uncompressed_digital_video_opl=prl.get('uncompressedDigitalVideoOpl'),
            compressed_digital_video_opl=prl.get('compressedDigitalVideoOpl'),
            analog_video_opl=prl.get('analogVideoOpl'),
            compressed_digital_audio_opl=prl.get('compressedDigitalAudioOpl'),
            uncompressed_digital_audio_opl=prl.get('uncompressedDigitalAudioOpl')
        )

    def __get_license(lic):
        return ContentKeyPolicyPlayReadyLicense(
            allow_test_devices=lic.get('allowTestDevices'),
            begin_date=lic.get('beginDate'),
            expiration_date=lic.get('expirationDate'),
            relative_begin_date=_coalesce_timedelta(lic.get('relativeBeginDate')),
            relative_expiration_date=_coalesce_timedelta(lic.get('relativeExpirationDate')),
            grace_period=_coalesce_timedelta(lic.get('gracePeriod')),
            play_right=__get_play_right(lic.get('playRight')),
            license_type=lic.get('licenseType'),
            content_key_location=__get_content_key_location(
                lic.get('contentKeyLocation')
            ),
            content_type=lic.get('contentType')
        )

    def __get_licenses(lics):
        return [__get_license(lic) for lic in lics]

    return ContentKeyPolicyPlayReadyConfiguration(
        licenses=__get_licenses(content.get('licenses')),
        response_custom_data=content.get('responseCustomData')
    )


def _validate_all_conditions(conditions, error_if_malformed):
    well_formed = all(conditions)

    if _count_truthy(conditions) >= 1 and not well_formed:
        raise CLIError(error_if_malformed)

    return well_formed


def _read_json(path):
    return _read(path, 'r')


def _read_binary(path):
    return _read(path, 'rb')


def _read(path, read_type):
    with open(path, read_type) as file:
        return file.read()


def _base64(data):
    return base64.b64encode(data)


def _int2bytes(int_value):
    hex_value = '{0:x}'.format(int_value)
    # make length of hex_value a multiple of two
    hex_value = '0' * (len(hex_value) % 2) + hex_value
    return codecs.decode(hex_value, 'hex_codec')
