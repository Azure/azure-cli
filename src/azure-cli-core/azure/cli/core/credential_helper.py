# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
import json
from enum import Enum


class CredentialType(Enum):
    STORAGE_SAS_TOKEN = ('([?&;])sig=[\w%-]+', r'\1sig=_REDACTED_SAS_TOKEN_SIG_', 'Storage SAS token')
    CODE = ('([?&;])code=[\w%+/=-]+', r'\1code=_REDACTED_CODE_', 'Several types of keys/secrets are passed with a query parameter "code"')
    AZCOPY_TOKEN = ('([?&/]|%2F)(SourceKey|DestKey)(=|%3A|%3D|:)(?:[\w/-]|%2F)+(?:==|%3D%3D)', r'\1\2\3_REDACTED_AZCOPY_TOKEN_', 'AzCopy token')
    JWT_TOKEN = ('(?:eyJ0eXAi|eyJhbGci)[\w\-.~+/%]*', '_REDACTED_JWT_TOKEN_', 'JWT token')
    BEARER_TOKEN = ('("|\'|%22)(bearer |bearer%20)[\w\-.~+/]{100,}("|\'|%22)', r'\1\2_REDACTED_BEARER_TOKEN_\3', 'Bearer token')
    SSH_KEY = ('("|\')(ssh-rsa )AAAA[\w\-.~+/]{100,}("|\')', r'\1\2_REDACTED_SSH_KEY_\3', 'SSH key')
    EMAIL_ADDRESS = ('\b[\w.%#+-]+(%40|@)([a-z0-9.-]*\.[a-z]{2,})\b', r'_REDACTED_EMAIL_\1\2', 'Email address')
    GUID = ('([0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12})\b', '_REDACTED_GUID_', 'GUID')

    def __init__(self, regex, replacement, description=''):
        self.regex = regex
        self.replacement = replacement
        self.description = description


def is_containing_credential(content, is_file=False):
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
    elif isinstance(content, json) or isinstance(content, dict):
        content = json.dumps(content)
    return any(re.search(cred_type.regex, content, flags=re.IGNORECASE | re.MULTILINE) for cred_type in CredentialType)


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
    elif isinstance(content, json) or isinstance(content, dict):
        content = json.dumps(content)
    types = [cred_type for cred_type in CredentialType if re.search(cred_type.regex, content, flags=re.IGNORECASE | re.MULTILINE)]
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

    if isinstance(content, json) or isinstance(content, dict):
        content = json.dumps(content)
        content = redact_credential_for_string(content)
        return json.loads(content)
    elif isinstance(content, str):
        return redact_credential_for_string(content)

    return content


def redact_credential_for_string(string):
    for cred_type in CredentialType:
        string = re.sub(cred_type.regex, cred_type.replacement, string, flags=re.IGNORECASE | re.MULTILINE)
    return string
