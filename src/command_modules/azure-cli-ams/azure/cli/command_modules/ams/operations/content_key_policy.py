# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-arguments, too-many-locals, too-many-branches
import base64, json

from datetime import timedelta
from knack.util import CLIError

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
                              issuer=None, audience=None, symmetric_token_key=None, rsa_token_key_exponent=None,
                              rsa_token_key_modulus=None, x509_certificate_token_key=None,
                              alt_symmetric_token_keys=None, alt_rsa_token_key_exponents=None,
                              alt_rsa_token_key_modulus=None, alt_x509_certificate_token_keys=None,
                              token_claims=None, restriction_token_type=None,
                              open_id_connect_discovery_document=None, widevine_template=None,
                              ask=None, fair_play_pfx_password=None, fair_play_pfx=None,
                              rental_and_lease_key_type=None, rental_duration=None, play_ready_configuration=None):

    policy_option = _generate_content_key_policy_option(policy_option_name, clear_key_configuration, open_restriction,
                                                        issuer, audience, symmetric_token_key, rsa_token_key_exponent,
                                                        rsa_token_key_modulus, x509_certificate_token_key,
                                                        alt_symmetric_token_keys, alt_rsa_token_key_exponents,
                                                        alt_rsa_token_key_modulus, alt_x509_certificate_token_keys,
                                                        token_claims, restriction_token_type, open_id_connect_discovery_document,
                                                        widevine_template, ask, fair_play_pfx_password, fair_play_pfx,
                                                        rental_and_lease_key_type, rental_duration, play_ready_configuration)

    return client.create_or_update(resource_group_name, account_name,
                                   content_key_policy_name, [policy_option], description)


def add_content_key_policy_option(client, resource_group_name, account_name, content_key_policy_name,
                                  policy_option_name, clear_key_configuration=False, open_restriction=False,
                                  issuer=None, audience=None, symmetric_token_key=None, rsa_token_key_exponent=None,
                                  rsa_token_key_modulus=None, x509_certificate_token_key=None,
                                  alt_symmetric_token_keys=None, alt_rsa_token_key_exponents=None,
                                  alt_rsa_token_key_modulus=None, alt_x509_certificate_token_keys=None,
                                  token_claims=None, restriction_token_type=None,
                                  open_id_connect_discovery_document=None, widevine_template=None,
                                  ask=None, fair_play_pfx_password=None, fair_play_pfx=None,
                                  rental_and_lease_key_type=None, rental_duration=None, play_ready_configuration=None):

    policy = client.get_policy_properties_with_secrets(resource_group_name, account_name, content_key_policy_name)

    if not policy:
        raise CLIError('Policy with name "' + content_key_policy_name + '" does not exist in your realm.')

    options = policy.options

    policy_option = _generate_content_key_policy_option(policy_option_name, clear_key_configuration, open_restriction,
                                                        issuer, audience, symmetric_token_key, rsa_token_key_exponent,
                                                        rsa_token_key_modulus, x509_certificate_token_key,
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
        raise CLIError('Policy with name "' + content_key_policy_name + '" does not exist in your realm.')

    if all(option.policy_option_id != policy_option_id for option in policy.options):
        raise CLIError('No policy option found with id "' + policy_option_id + '"')

    policy.options = list(filter(lambda option: option.policy_option_id != policy_option_id, policy.options))

    return client.create_or_update(resource_group_name, account_name,
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
                                        issuer, audience, symmetric_token_key, rsa_token_key_exponent,
                                        rsa_token_key_modulus, x509_certificate_token_key,
                                        alt_symmetric_token_keys, alt_rsa_token_key_exponents,
                                        alt_rsa_token_key_modulus, alt_x509_certificate_token_keys,
                                        token_claims, restriction_token_type,
                                        open_id_connect_discovery_document, widevine_template,
                                        ask, fair_play_pfx_password, fair_play_pfx,
                                        rental_and_lease_key_type, rental_duration, play_ready_configuration):

    configuration = None
    restriction = None

    valid_token_restriction = _valid_token_restriction(symmetric_token_key, rsa_token_key_exponent,
                                                       rsa_token_key_modulus, x509_certificate_token_key,
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
        if _token_restriction_keys_available(symmetric_token_key, rsa_token_key_exponent,
                                             rsa_token_key_modulus, x509_certificate_token_key) != 1:
            raise CLIError('You should use alternative (alt) token keys if you have more than one token key.')

        primary_verification_key = None
        _symmetric_keys = _coalesce_str(alt_symmetric_token_keys).split()
        _rsa_key_exponents = _coalesce_str(alt_rsa_token_key_exponents).split()
        _rsa_key_modulus = _coalesce_str(alt_rsa_token_key_modulus).split()
        _x509_keys = _coalesce_str(alt_x509_certificate_token_keys).split()
        alternative_keys = []
        _token_claims = []

        if symmetric_token_key is not None:
            primary_verification_key = _symmetric_token_key_factory(bytearray(symmetric_token_key, 'utf-8'))
        elif rsa_token_key_exponent is not None and rsa_token_key_modulus is not None:
            primary_verification_key = _rsa_token_key_factory(
                bytearray(rsa_token_key_exponent, 'utf-8'), bytearray(rsa_token_key_modulus, 'utf-8'))
        elif x509_certificate_token_key is not None:
            primary_verification_key = _x509_token_key_factory(
                bytearray(x509_certificate_token_key.replace('\\n', '\n'), 'utf-8'))

        # Extra validation to make sure exponents and modulus have the same cardinality
        if len(_rsa_key_exponents) != len(_rsa_key_modulus):
            raise CLIError('The number of alternative RSA key exponents and modulus differ.')

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
    return value and timedelta(seconds=value) or None


# Counts how many values are truthy on a list.
def _count_truthy(values):
    return len([value for value in values if value])


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
    return _count_truthy([symmetric_token_key, rsa_token_key_exponent and rsa_token_key_modulus,
                          x509_certificate_token_key])


def _valid_token_restriction(symmetric_token_key, rsa_token_key_exponent, rsa_token_key_modulus,
                             x509_certificate_token_key, restriction_token_type,
                             issuer, audience):
    available_keys = _token_restriction_keys_available(symmetric_token_key, rsa_token_key_exponent,
                                                       rsa_token_key_modulus, x509_certificate_token_key)
    return _validate_all_conditions(
        [restriction_token_type, available_keys >= 1, issuer, audience],
        'Malformed content key policy token restriction.')


def _valid_fairplay_configuration(ask, fair_play_pfx_password, fair_play_pfx,
                                  rental_and_lease_key_type, rental_duration):
    return _validate_all_conditions(
        [ask, fair_play_pfx_password, fair_play_pfx, rental_and_lease_key_type, rental_duration],
        'Malformed content key policy FairPlay configuration.')


def _valid_playready_configuration(play_ready_configuration):

    def __valid_license(lic):
        return _validate_all_conditions([lic.get('allow_test_devices') is not None,
                                         lic.get('license_type') in ['NonPersistent', 'Persistent'],
                                         __valid_content_key_location(lic.get('content_key_location')),
                                         lic.get('content_type') in ['Unspecified', 'UltraVioletDownload', 'UltraVioletStreaming'],
                                         lic.get('play_right') is None or __valid_play_right(lic.get('play_right'))],
                                        'Malformed PlayReady license.')

    def __valid_content_key_location(loc):
        return (loc.get('type') == 'ContentKeyPolicyPlayReadyContentEncryptionKeyFromHeader' or
                (loc.get('type') == 'ContentKeyPolicyPlayReadyContentEncryptionKeyFromKeyIdentifier' and
                 loc.get('key_id') is not None))

    def __valid_play_right(prl):
        return _validate_all_conditions([(prl.get('explicit_analog_television_output_restriction') is None or
                                          __valid_eator(prl.get('explicit_analog_television_output_restriction'))),
                                         prl.get('digital_video_only_content_restriction') is not None,
                                         prl.get('image_constraint_for_analog_component_video_restriction') is not None,
                                         prl.get('image_constraint_for_analog_computer_monitor_restriction') is not None,
                                         prl.get('allow_passing_video_content_to_unknown_output') in ['NotAllowed', 'Allowed',
                                                                                                      'AllowedWithVideoConstriction']],
                                        'Malformed license PlayRight.')

    def __valid_eator(eator):
        return _validate_all_conditions([eator.get('best_effort') is not None,
                                         eator.get('configuration_data') is not None],
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
        content_key_location = None
        if ckl.get('type') == 'ContentKeyPolicyPlayReadyContentEncryptionKeyFromHeader':
            content_key_location = ContentKeyPolicyPlayReadyContentEncryptionKeyFromHeader()
        elif ckl.get('type') == 'ContentKeyPolicyPlayReadyContentEncryptionKeyFromKeyIdentifier':
            content_key_location = ContentKeyPolicyPlayReadyContentEncryptionKeyFromKeyIdentifier(
                key_id=ckl.get('key_id')
            )
        return content_key_location

    def __get_eator(eator):
        if eator is None:
            return None
        return ContentKeyPolicyPlayReadyExplicitAnalogTelevisionRestriction(
            best_effort=eator.get('best_effort'),
            configuration_data=eator.get('configuration_data')
        )

    def __get_play_right(prl):
        if prl is None:
            return None
        return ContentKeyPolicyPlayReadyPlayRight(
            first_play_expiration=_coalesce_timedelta(prl.get('first_play_expiration')),
            scms_restriction=prl.get('scms_restriction'),
            agc_and_color_stripe_restriction=prl.get('agc_and_color_stripe_restriction'),
            explicit_analog_television_output_restriction=
                __get_eator(prl.get('explicit_analog_television_output_restriction')),
            digital_video_only_content_restriction=prl.get('digital_video_only_content_restriction'),
            image_constraint_for_analog_component_video_restriction=
                prl.get('image_constraint_for_analog_component_video_restriction'),
            image_constraint_for_analog_computer_monitor_restriction=
                prl.get('image_constraint_for_analog_computer_monitor_restriction'),
            allow_passing_video_content_to_unknown_output=
                prl.get('allow_passing_video_content_to_unknown_output'),
            uncompressed_digital_video_opl=prl.get('uncompressed_digital_video_opl'),
            compressed_digital_video_opl=prl.get('compressed_digital_video_opl'),
            analog_video_opl=prl.get('analog_video_opl'),
            compressed_digital_audio_opl=prl.get('compressed_digital_audio_opl'),
            uncompressed_digital_audio_opl=prl.get('uncompressed_digital_audio_opl')            
        )

    def __get_license(lic):
        return ContentKeyPolicyPlayReadyLicense(
            allow_test_devices=lic.get('allow_test_devices'),
            begin_date=lic.get('begin_date'),
            expiration_date=lic.get('expiration_date'),
            relative_begin_date=_coalesce_timedelta(lic.get('relative_begin_date')),
            relative_expiration_date=_coalesce_timedelta(lic.get('relative_expiration_date')),
            grace_period=_coalesce_timedelta(lic.get('grace_period')),
            play_right=__get_play_right(lic.get('play_right')),
            license_type=lic.get('license_type'),
            content_key_location=__get_content_key_location(
                lic.get('content_key_location')
            ),
            content_type=lic.get('content_type')
        )

    def __get_licenses(lics):
        return [__get_license(lic) for lic in lics]

    return ContentKeyPolicyPlayReadyConfiguration(
        licenses=__get_licenses(content.get('licenses')),
        response_custom_data=content.get('response_custom_data')
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


def _read(path, readType):
    with open(path, readType) as file:
        return file.read()


def _base64(data):
    return base64.b64encode(data)
