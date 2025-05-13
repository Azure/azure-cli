# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import json
from azure.cli.core import decorators

sensitive_data_warning_message = '[Warning] This output may compromise security by showing secrets. Learn more at: https://go.microsoft.com/fwlink/?linkid=2258669'
sensitive_data_detailed_warning_message = '[Warning] This output may compromise security by showing the following secrets: {}. Learn more at: https://go.microsoft.com/fwlink/?linkid=2258669'


@decorators.call_once
def get_secret_masker():
    # global secret_masker_instance
    from microsoft_security_utilities_secret_masker import SecretMasker, load_regex_patterns_from_json_file
    regex_patterns = load_regex_patterns_from_json_file('HighConfidenceSecurityModels.json')
    return SecretMasker(regex_patterns)


def is_containing_credential(content, is_file=False):
    """Check if the given content contains credential or not.

    :param content: The content or the file path.
    :type content: Any.
    :param is_file: flag to clarify the content is file path or not.
    :type is_file: bool.
    :param max_level: the max level of credential to check.
    :type max_level: int.
    :returns:  bool.
    """
    if is_file:
        with open(content, 'r') as f:
            content = f.read()
    elif not isinstance(content, str):
        try:
            content = json.dumps(content)
        except TypeError:
            content = str(content)
        except ValueError:
            raise ValueError('The content is not string or json object.')
    return get_secret_masker().detect_secrets(content)


def distinguish_credential(content, is_file=False):
    """Distinguish which property contains credential from the given content.

    :param content: The content(can be string or json object) or the file path.
    :type content: Any.
    :param is_file: flag to clarify the content is file path or not.
    :type is_file: bool.
    :param max_level: the max level of credential to check.
    :type max_level: int.
    :returns: bool, set.
    """
    containing_credential = False
    secret_property_names = set()
    secret_names = set()
    if is_file:
        with open(content, 'r') as f:
            content = json.load(f)

    if isinstance(content, list):
        for item in content:
            _containing_credential, _secret_property_names, _secret_names = distinguish_credential(item)
            containing_credential = containing_credential or _containing_credential
            secret_property_names.update(_secret_property_names)
            secret_names.update(_secret_names)
        return containing_credential, secret_property_names, secret_names

    if isinstance(content, dict):
        for key, value in content.items():
            _containing_credential, _secret_property_names, _secret_names = distinguish_credential(value)
            containing_credential = containing_credential or _containing_credential
            secret_property_names.update(_secret_property_names)
            if _containing_credential:
                secret_property_names.add(key)
                secret_names.update(_secret_names)
        return containing_credential, secret_property_names, secret_names

    detections = is_containing_credential(content)
    if detections:
        containing_credential = True
        for detection in detections:
            secret_names.add(detection.name)
    return containing_credential, secret_property_names, secret_names


def redact_credential(content, is_file=False):
    """Redact credential for the given content.

    :param content: The content(can be string or json object) or the file path.
    :type content: Any.
    :param is_file: flag to clarify the content is file path or not.
    :type is_file: bool.
    :returns: processed content.
    """
    if is_file:
        fp = content
        with open(fp, 'r') as f:
            content = f.read()
        content = redact_credential_for_string(content)
        with open(fp, 'w') as f:
            f.write(content)
        return fp

    if isinstance(content, str):
        return redact_credential_for_string(content)

    try:
        content = json.dumps(content)
        content = redact_credential_for_string(content)
        return json.loads(content)
    except ValueError:
        raise ValueError('The content is not string or json object.')


def redact_credential_for_string(content):
    return get_secret_masker().mask_secrets(content)
