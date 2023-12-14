# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
import json
from enum import Enum

senstive_data_warning_message = 'The output includes secrets that you must protect. Be sure that you do not include these secrets in your source control. Also verify that no secrets are present in the logs of your command or script. For additional information, see http://aka.ms/clisecrets.'


class CredentialType(Enum):
    STORAGE_SAS_TOKEN = ('([?&;])sig=[\w%-/]+', r'\1sig=_REDACTED_SAS_TOKEN_SIG_', 1, 'Storage SAS token')
    KEY = ('(.*)key=[\w%+/=-]+', r'\1key=_REDACTED_KEY_', 1, 'Several types of keys/secrets are passed with a query parameter "key"')
    JWT_TOKEN = ('(?:eyJ0eXAi|eyJhbGci)[\w\-.~+/%]*', '_REDACTED_JWT_TOKEN_', 0, 'JWT token')
    BEARER_TOKEN = ('(bearer |bearer%20)[\w\-.~+/]{100,}', r'\1_REDACTED_BEARER_TOKEN_', 0, 'Bearer token')
    SSH_KEY = ('(ssh-rsa )AAAA[\w\-.~+/]{100,}', r'\1_REDACTED_SSH_KEY_', 1, 'SSH key')
    EMAIL_ADDRESS = ('[\w.%#+-]+(%40|@)([a-z0-9.-]*\.[a-z]{2,})', r'_REDACTED_EMAIL_\1\2', 99, 'Email address')
    GUID = ('([0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12})', '_REDACTED_GUID_', 999, 'GUID')

    def __init__(self, regex, replacement, level=0, description=''):
        self.regex = regex
        self.replacement = replacement
        self.level = level
        self.description = description


def is_containing_credential(content, is_file=False, max_level=999):
    """Check if the given content contains credential or not.

    :param content: The content or the file path.
    :type content: Any.
    :param is_file: flag to clarify the content is file path or not.
    :type is_file: bool.
    :returns:  bool.
    """
    if is_file:
        with open(content, 'r') as f:
            content = f.read()
    elif not isinstance(content, str):
        try:
            content = json.dumps(content)
        except ValueError:
            raise ValueError('The content is not string or json object.')
    return any(re.search(cred_type.regex, content, flags=re.IGNORECASE | re.MULTILINE) and cred_type.level<=max_level for cred_type in CredentialType)


def distinguish_credential(content, is_file=False):
    """Distinguish which credential types the given content contains.

    :param content: The content(can be string or json object) or the file path.
    :type content: Any.
    :param is_file: flag to clarify the content is file path or not.
    :type is_file: bool.
    :returns: list of CredentialType.
    """
    if is_file:
        with open(content, 'r') as f:
            content = f.read()
    elif not isinstance(content, str):
        try:
            content = json.dumps(content)
        except ValueError:
            raise ValueError('The content is not string or json object.')
    types = [cred_type.name for cred_type in CredentialType if re.search(cred_type.regex, content, flags=re.IGNORECASE | re.MULTILINE)]
    return types


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


def redact_credential_for_string(string):
    for cred_type in CredentialType:
        string = re.sub(cred_type.regex, cred_type.replacement, string, flags=re.IGNORECASE | re.MULTILINE)
    return string
