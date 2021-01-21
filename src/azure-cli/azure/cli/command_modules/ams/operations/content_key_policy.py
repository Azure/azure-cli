# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-arguments, too-many-locals, too-many-branches, too-many-statements
import base64
import codecs
import json

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from knack.util import CLIError

from azure.cli.command_modules.ams._sdk_utils import get_tokens
from azure.cli.command_modules.ams._utils import (parse_timedelta,
                                                  parse_duration,
                                                  JsonBytearrayEncoder,
                                                  build_resource_not_found_message,
                                                  show_resource_not_found_message)

from azure.mgmt.media.models import (ContentKeyPolicyOption, ContentKeyPolicyClearKeyConfiguration,
                                     ContentKeyPolicyOpenRestriction, ContentKeyPolicySymmetricTokenKey,
                                     ContentKeyPolicyRsaTokenKey, ContentKeyPolicyX509CertificateTokenKey,
                                     ContentKeyPolicyTokenRestriction, ContentKeyPolicyTokenClaim,
                                     ContentKeyPolicyWidevineConfiguration, ContentKeyPolicyFairPlayConfiguration,
                                     ContentKeyPolicyFairPlayOfflineRentalConfiguration,
                                     ContentKeyPolicyPlayReadyConfiguration, ContentKeyPolicyPlayReadyLicense,
                                     ContentKeyPolicyPlayReadyContentEncryptionKeyFromHeader,
                                     ContentKeyPolicyPlayReadyContentEncryptionKeyFromKeyIdentifier,
                                     ContentKeyPolicyPlayReadyPlayRight,
                                     ContentKeyPolicyPlayReadyExplicitAnalogTelevisionRestriction)


def create_content_key_policy(client, resource_group_name, account_name, content_key_policy_name,
                              policy_option_name, description=None,
                              clear_key_configuration=False, open_restriction=False,
                              issuer=None, audience=None, token_key=None, token_key_type=None,
                              alt_symmetric_token_keys=None, alt_rsa_token_keys=None, alt_x509_token_keys=None,
                              token_claims=None, token_type=None, open_id_connect_discovery_document=None,
                              widevine_template=None, ask=None, fair_play_pfx_password=None, fair_play_pfx=None,
                              rental_and_lease_key_type=None, rental_duration=None, play_ready_template=None,
                              fp_playback_duration_seconds=None, fp_storage_duration_seconds=None):

    policy_option = _generate_content_key_policy_option(policy_option_name, clear_key_configuration, open_restriction,
                                                        issuer, audience, token_key, token_key_type,
                                                        alt_symmetric_token_keys, alt_rsa_token_keys,
                                                        alt_x509_token_keys, token_claims, token_type,
                                                        open_id_connect_discovery_document, widevine_template,
                                                        ask, fair_play_pfx_password, fair_play_pfx,
                                                        rental_and_lease_key_type, rental_duration, play_ready_template,
                                                        fp_playback_duration_seconds, fp_storage_duration_seconds)

    return client.create_or_update(resource_group_name, account_name,
                                   content_key_policy_name, [policy_option], description)


def show_content_key_policy(client, resource_group_name, account_name, content_key_policy_name,
                            with_secrets=False):

    if with_secrets:
        content_key_policy = client.get_policy_properties_with_secrets(
            resource_group_name=resource_group_name,
            account_name=account_name,
            content_key_policy_name=content_key_policy_name)

        if not content_key_policy:
            show_resource_not_found_message(
                account_name, resource_group_name, 'contenKeyPolicies', content_key_policy_name)

        json_object = json.dumps(content_key_policy, cls=JsonBytearrayEncoder, indent=4)
        return json.loads(json_object)

    content_key_policy = client.get(
        resource_group_name=resource_group_name,
        account_name=account_name,
        content_key_policy_name=content_key_policy_name)

    if not content_key_policy:
        show_resource_not_found_message(
            account_name, resource_group_name, 'contenKeyPolicies', content_key_policy_name)

    return content_key_policy


def add_content_key_policy_option(client, resource_group_name, account_name, content_key_policy_name,
                                  policy_option_name, clear_key_configuration=False, open_restriction=False,
                                  issuer=None, audience=None, token_key=None, token_key_type=None,
                                  alt_symmetric_token_keys=None, alt_rsa_token_keys=None, alt_x509_token_keys=None,
                                  token_claims=None, token_type=None, open_id_connect_discovery_document=None,
                                  widevine_template=None, ask=None, fair_play_pfx_password=None, fair_play_pfx=None,
                                  rental_and_lease_key_type=None, rental_duration=None, play_ready_template=None,
                                  fp_playback_duration_seconds=None, fp_storage_duration_seconds=None):

    policy = client.get_policy_properties_with_secrets(resource_group_name, account_name, content_key_policy_name)

    if not policy:
        raise CLIError(build_resource_not_found_message(
            account_name, resource_group_name, 'contentKeyPolicies', content_key_policy_name))

    options = policy.options

    policy_option = _generate_content_key_policy_option(policy_option_name, clear_key_configuration, open_restriction,
                                                        issuer, audience, token_key, token_key_type,
                                                        alt_symmetric_token_keys, alt_rsa_token_keys,
                                                        alt_x509_token_keys, token_claims, token_type,
                                                        open_id_connect_discovery_document, widevine_template,
                                                        ask, fair_play_pfx_password, fair_play_pfx,
                                                        rental_and_lease_key_type, rental_duration, play_ready_template,
                                                        fp_playback_duration_seconds, fp_storage_duration_seconds)

    options.append(policy_option)

    return client.update(resource_group_name, account_name,
                         content_key_policy_name, options, policy.description)


def remove_content_key_policy_option(client, resource_group_name, account_name, content_key_policy_name,
                                     policy_option_id):
    policy = client.get_policy_properties_with_secrets(resource_group_name, account_name, content_key_policy_name)

    if not policy:
        raise CLIError(build_resource_not_found_message(
            account_name, resource_group_name, 'contentKeyPolicies', content_key_policy_name))

    if all(option.policy_option_id != policy_option_id for option in policy.options):
        raise CLIError('No policy option found with id "' + policy_option_id + '"')

    policy.options = list(filter(lambda option: option.policy_option_id != policy_option_id, policy.options))

    return client.update(resource_group_name, account_name,
                         content_key_policy_name, policy.options)


def update_content_key_policy_option(client, resource_group_name, account_name, content_key_policy_name,
                                     policy_option_id, policy_option_name=None, issuer=None, audience=None,
                                     token_key=None, token_key_type=None, add_alt_token_key=None,
                                     add_alt_token_key_type=None, token_claims=None, token_type=None,
                                     open_id_connect_discovery_document=None, widevine_template=None,
                                     ask=None, fair_play_pfx_password=None, fair_play_pfx=None,
                                     rental_and_lease_key_type=None, rental_duration=None, play_ready_template=None,
                                     fp_playback_duration_seconds=None, fp_storage_duration_seconds=None):
    policy = client.get_policy_properties_with_secrets(
        resource_group_name=resource_group_name,
        account_name=account_name,
        content_key_policy_name=content_key_policy_name)

    if not policy:
        raise CLIError(build_resource_not_found_message(
            account_name, resource_group_name, 'contentKeyPolicies', content_key_policy_name))

    policy_option = next((option for option in policy.options if option.policy_option_id == policy_option_id), None)

    if policy_option is None:
        raise CLIError('Policy option with id "' + policy_option_id + '" was not found.')

    if policy_option_name is not None:
        policy_option.name = policy_option_name

    if isinstance(policy_option.restriction, ContentKeyPolicyTokenRestriction):
        if issuer is not None:
            policy_option.restriction.issuer = issuer

        if audience is not None:
            policy_option.restriction.audience = audience

        if token_key is not None and token_key_type is not None:
            if token_key_type == 'Symmetric':
                policy_option.restriction.primary_verification_key = _symmetric_token_key_factory(token_key)
            elif token_key_type == 'RSA':
                policy_option.restriction.primary_verification_key = _rsa_token_key_factory(token_key)
            elif token_key_type == 'X509':
                policy_option.restriction.primary_verification_key = _x509_token_key_factory(token_key)

        if add_alt_token_key is not None and add_alt_token_key_type is not None:
            if add_alt_token_key_type == 'Symmetric':
                policy_option.restriction.alternate_verification_keys.append(
                    _symmetric_token_key_factory(add_alt_token_key))
            elif add_alt_token_key_type == 'RSA':
                policy_option.restriction.alternate_verification_keys.append(
                    _rsa_token_key_factory(add_alt_token_key))
            elif add_alt_token_key_type == 'X509':
                policy_option.restriction.alternate_verification_keys.append(
                    _x509_token_key_factory(add_alt_token_key))

        if token_claims is not None:
            policy_option.restriction.token_claims = []
            for key in token_claims:
                claim = ContentKeyPolicyTokenClaim(claim_type=key,
                                                   claim_value=token_claims[key])
                policy_option.restriction.token_claims.append(claim)

        if token_type is not None:
            policy_option.restriction.restriction_token_type = token_type

        if open_id_connect_discovery_document is not None:
            policy_option.restriction.open_id_connect_discovery_document = open_id_connect_discovery_document

    if isinstance(policy_option.configuration, ContentKeyPolicyWidevineConfiguration):
        if widevine_template is not None:
            policy_option.configuration = ContentKeyPolicyWidevineConfiguration(widevine_template=widevine_template)
    elif isinstance(policy_option.configuration, ContentKeyPolicyFairPlayConfiguration):
        if ask is not None:
            policy_option.configuration.ask = bytearray.fromhex(ask)

        if fair_play_pfx_password is not None:
            policy_option.configuration.fair_play_pfx_password = fair_play_pfx_password

        if fair_play_pfx is not None:
            policy_option.configuration.fair_play_pfx = _b64_to_str(_read_binary(fair_play_pfx)).decode('ascii')

        if rental_and_lease_key_type is not None:
            policy_option.configuration.rental_and_lease_key_type = rental_and_lease_key_type

        if rental_duration is not None:
            policy_option.configuration.rental_duration = rental_duration

        if fp_playback_duration_seconds is not None:
            policy_option.configuration.fp_playback_duration_seconds = fp_playback_duration_seconds

        if fp_storage_duration_seconds is not None:
            policy_option.configuration.fp_storage_duration_seconds = fp_storage_duration_seconds

    elif isinstance(policy_option.configuration, ContentKeyPolicyPlayReadyConfiguration):
        if play_ready_template is not None and _valid_playready_configuration(play_ready_template):
            _play_ready_configuration_factory(json.loads(play_ready_template))

    return client.update(resource_group_name, account_name,
                         content_key_policy_name, policy.options, policy.description)


def update_content_key_policy_setter(client, resource_group_name, account_name, content_key_policy_name,
                                     parameters):
    return client.update(resource_group_name, account_name,
                         content_key_policy_name, parameters.options, parameters.description)


def update_content_key_policy(instance, description=None):
    if not instance:
        raise CLIError("The content key policy '{}' was not found.".format(instance))

    if description is not None:
        instance.description = description

    return instance


# Private methods used

def _generate_content_key_policy_option(policy_option_name, clear_key_configuration, open_restriction,
                                        issuer, audience, token_key, token_key_type,
                                        alt_symmetric_token_keys, alt_rsa_token_keys, alt_x509_token_keys,
                                        token_claims, token_type, open_id_connect_discovery_document,
                                        widevine_template, ask, fair_play_pfx_password, fair_play_pfx,
                                        rental_and_lease_key_type, rental_duration, play_ready_template,
                                        fp_playback_duration_seconds, fp_storage_duration_seconds):

    configuration = None
    restriction = None

    valid_token_restriction = _valid_token_restriction(token_key, token_key_type,
                                                       token_type, issuer, audience)

    valid_fairplay_configuration = _valid_fairplay_configuration(ask, fair_play_pfx_password,
                                                                 fair_play_pfx, rental_and_lease_key_type,
                                                                 rental_duration)

    valid_playready_configuration = _valid_playready_configuration(play_ready_template)

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
        offline_configuration = None
        if rental_and_lease_key_type == 'DualExpiry':
            offline_configuration = ContentKeyPolicyFairPlayOfflineRentalConfiguration(
                playback_duration_seconds=fp_playback_duration_seconds,
                storage_duration_seconds=fp_storage_duration_seconds)
        if ask is not None:
            ask = bytearray.fromhex(ask)
        configuration = ContentKeyPolicyFairPlayConfiguration(
            ask=ask,
            fair_play_pfx_password=fair_play_pfx_password,
            fair_play_pfx=_b64_to_str(_read_binary(fair_play_pfx)).decode('ascii'),
            rental_and_lease_key_type=rental_and_lease_key_type,
            rental_duration=rental_duration, offline_rental_configuration=offline_configuration)

    if valid_playready_configuration:
        configuration = _play_ready_configuration_factory(json.loads(play_ready_template))

    if open_restriction:
        restriction = ContentKeyPolicyOpenRestriction()

    if valid_token_restriction:
        primary_verification_key = None
        alternate_keys = []
        _token_claims = []

        if token_key is not None:
            if token_key_type == 'Symmetric':
                primary_verification_key = _symmetric_token_key_factory(token_key)
            elif token_key_type == 'RSA':
                primary_verification_key = _rsa_token_key_factory(token_key)
            elif token_key_type == 'X509':
                primary_verification_key = _x509_token_key_factory(token_key)

        for key in _coalesce_lst(alt_symmetric_token_keys):
            alternate_keys.append(_symmetric_token_key_factory(key))

        for key in _coalesce_lst(alt_rsa_token_keys):
            alternate_keys.append(_rsa_token_key_factory(key))

        for key in _coalesce_lst(alt_x509_token_keys):
            alternate_keys.append(_x509_token_key_factory(key))

        if token_claims is not None:
            for key in token_claims:
                claim = ContentKeyPolicyTokenClaim(claim_type=key,
                                                   claim_value=token_claims[key])
                _token_claims.append(claim)

        restriction = ContentKeyPolicyTokenRestriction(
            issuer=issuer, audience=audience, primary_verification_key=primary_verification_key,
            alternate_verification_keys=alternate_keys, required_claims=_token_claims,
            restriction_token_type=token_type,
            open_id_connect_discovery_document=open_id_connect_discovery_document)

    return ContentKeyPolicyOption(name=policy_option_name,
                                  configuration=configuration,
                                  restriction=restriction)


# Utility functions
# Returns string if not null, or an empty string otherwise.
def _coalesce_lst(value):
    return value or []


def _coalesce_duration(value):
    return parse_duration(value) if value else None


def _coalesce_timedelta(value):
    return parse_timedelta(value) if value else None


def _read_json(path):
    return _read(path, 'r')


def _read_binary(path):
    return _read(path, 'rb')


def _read(path, read_type):
    with open(path, read_type) as file:
        return file.read()


def _b64_to_str(data):
    return base64.b64encode(data)


def _int2bytes(int_value):
    hex_value = '{0:x}'.format(int_value)
    # make length of hex_value a multiple of two
    hex_value = '0' * (len(hex_value) % 2) + hex_value
    return codecs.decode(hex_value, 'hex_codec')


# Counts how many values are truthy on a list.
def _count_truthy(values):
    return len([value for value in values if value])


# Factories
def _symmetric_token_key_factory(input_symmetric):
    key = bytearray(input_symmetric, 'utf-8')
    return ContentKeyPolicySymmetricTokenKey(key_value=key)


def _rsa_token_key_factory(input_rsa):
    content = _read(input_rsa, 'r')
    rsa_key = serialization.load_pem_public_key(
        content.encode('ascii'),
        backend=default_backend()
    )

    exp = rsa_key.public_numbers().e
    mod = rsa_key.public_numbers().n

    return ContentKeyPolicyRsaTokenKey(
        exponent=bytearray(_int2bytes(exp)), modulus=bytearray(_int2bytes(mod)))


def _x509_token_key_factory(input_x509):
    content = _read(input_x509, 'r')
    return ContentKeyPolicyX509CertificateTokenKey(
        raw_body=bytearray(content, 'ascii'))


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
            first_play_expiration=_coalesce_duration(prl.get('firstPlayExpiration')),
            scms_restriction=prl.get('scmsRestriction'),
            agc_and_color_stripe_restriction=prl.get('agcAndColorStripeRestriction'),
            explicit_analog_television_output_restriction=__get_eator(
                prl.get('explicitAnalogTelevisionOutputRestriction')),
            digital_video_only_content_restriction=prl.get('digitalVideoOnlyContentRestriction'),
            image_constraint_for_analog_component_video_restriction=prl.get(
                'imageConstraintForAnalogComponentVideoRestriction'),
            image_constraint_for_analog_computer_monitor_restriction=prl.get(
                'imageConstraintForAnalogComputerMonitorRestriction'),
            allow_passing_video_content_to_unknown_output=prl.get('allowPassingVideoContentToUnknownOutput'),
            uncompressed_digital_video_opl=prl.get('uncompressedDigitalVideoOpl'),
            compressed_digital_video_opl=prl.get('compressedDigitalVideoOpl'),
            analog_video_opl=prl.get('analogVideoOpl'),
            compressed_digital_audio_opl=prl.get('compressedDigitalAudioOpl'),
            uncompressed_digital_audio_opl=prl.get('uncompressedDigitalAudioOpl')
        )

    def __get_license(lic):
        import dateutil.parser
        if lic.get('expirationDate') is None:
            expiration_date = None
        else:
            expiration_date = dateutil.parser.parse(lic.get('expirationDate'))

        return ContentKeyPolicyPlayReadyLicense(
            allow_test_devices=lic.get('allowTestDevices'),
            begin_date=lic.get('beginDate'),
            expiration_date=expiration_date,
            relative_begin_date=_coalesce_duration(lic.get('relativeBeginDate')),
            relative_expiration_date=_coalesce_duration(lic.get('relativeExpirationDate')),
            grace_period=_coalesce_duration(lic.get('gracePeriod')),
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


# Validator methods
def _valid_token_restriction(token_key, token_key_type, token_type, issuer, audience):
    return any([token_type, token_key, token_key_type in get_tokens(), issuer, audience])


def _valid_fairplay_configuration(ask, fair_play_pfx_password, fair_play_pfx,
                                  rental_and_lease_key_type, rental_duration):
    return any([ask, fair_play_pfx_password, fair_play_pfx, rental_and_lease_key_type, rental_duration])


def _valid_playready_configuration(play_ready_template):
    if play_ready_template is None:
        return False

    def __valid_license(lic):
        return any([lic.get('allowTestDevices') is not None,
                    lic.get('licenseType') in ['NonPersistent', 'Persistent'],
                    lic.get('contentKeyLocation') is not None,
                    lic.get('contentType') in ['Unspecified', 'UltraVioletDownload', 'UltraVioletStreaming'],
                    lic.get('playRight') is None or __valid_play_right(lic.get('playRight'))])

    def __valid_play_right(prl):
        return any([(prl.get('explicitAnalogTelevisionOutputRestriction') is None or
                     __valid_eator(prl.get('explicitAnalogTelevisionOutputRestriction'))),
                    prl.get('digitalVideoOnlyContentRestriction') is not None,
                    prl.get('imageConstraintForAnalogComponentVideoRestriction') is not None,
                    prl.get('imageConstraintForAnalogComputerMonitorRestriction') is not None,
                    prl.get('allowPassingVideoContentToUnknownOutput') in ['NotAllowed', 'Allowed',
                                                                           'AllowedWithVideoConstriction']])

    def __valid_eator(eator):
        return any([eator.get('bestEffort') is not None,
                    eator.get('configurationData') is not None])

    cfg = None

    try:
        cfg = json.loads(play_ready_template)
    except ValueError as err:
        raise CLIError('Malformed JSON: ' + str(err))

    return any(
        [cfg.get('licenses') is not None,
         len(cfg.get('licenses')) > 0,
         all(__valid_license(license) for license in cfg.get('licenses'))]
    )
