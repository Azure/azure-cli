# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import re
import json
from enum import Enum

sensitive_data_warning_message = '[Warning] This output may compromise security by showing secrets. Learn more at: https://go.microsoft.com/fwlink/?linkid=2258669'
sensitive_data_detailed_warning_message = '[Warning] This output may compromise security by showing the following secrets: {}. Learn more at: https://go.microsoft.com/fwlink/?linkid=2258669'


class CredentialType(Enum):
    # ([?&;]) - match character '?' or '&' or ';' as group 1, which is the prefix of signature within sas token
    # sig= - match the literal string 'sig='
    # [\w%-/]+ - match any word character, '-', '%', or '/' one or more times. This is the signature which needs to be redacted
    SAS_TOKEN = (r'([?&;])sig=[\w%-/]+', r'\1sig=_REDACTED_SAS_TOKEN_SIG_', 1, 'SAS token')
    # key= - match the literal string 'key=', could be accountkey, primarykey, secondarykey, etc.
    # [\w%+/=-]+ - match any word character, '%', '+', '/', '=', or '-' one or more times.
    KEY = (r'key=[\w%+/=-]+', r'key=_REDACTED_KEY_', 1, 'Several types of keys/secrets are passed with a query parameter "key"')
    # (?:eyJ0eXAi|eyJhbGci) - match the literal string 'eyJ0eXAi' or 'eyJhbGci' as group 1, which is the prefix of JWT token
    # [\w\-.~+/%]* - match any word character, '-', '.', '~', '+', '/', '%', or '*' zero or more times.
    JWT_TOKEN = (r'(?:eyJ0eXAi|eyJhbGci)[\w\-.~+/%]*', '_REDACTED_JWT_TOKEN_', 0, 'JWT token')
    # (bearer |bearer%20) - match the literal string 'bearer ' or 'bearer%20'
    # [\w\-.~+/]{100,} - match any word character, '-', '.', '~', '+', or '/' one hundred or more times.
    BEARER_TOKEN = (r'(bearer |bearer%20)[\w\-.~+/]{100,}', r'\1_REDACTED_BEARER_TOKEN_', 0, 'Bearer token')
    # (ssh-rsa ) - match the literal string 'ssh-rsa ' as group 1, which is the prefix of ssh key
    # AAAA[\w\-.~+/]{100,} - match 'AAAA' followed by any word character, '-', '.', '~', '+', or '/' one hundred or more times.
    SSH_KEY = (r'(ssh-rsa )AAAA[\w\-.~+/]{100,}', r'\1_REDACTED_SSH_KEY_', 1, 'SSH key')
    # [\w.%#+-] - match any word character, '.', '%', '#', '+', or '-' one or more times.
    # (%40|@) - match character '@' or '%40' as group 1
    # ([a-z0-9.-]*\.[a-z]{2,}) - match any word character, '.', or '-' zero or more times, followed by a '.' and two or more word characters.
    EMAIL_ADDRESS = (r'[\w.%#+-]+(%40|@)([a-z0-9.-]*\.[a-z]{2,})', r'_REDACTED_EMAIL_\1\2', 99, 'Email address')
    # [0-9a-f]{8} - match any character in the range '0' to '9' or 'a' to 'f' exactly eight times.
    # -? - match character '-' zero or one time.
    GUID = (r'([0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12})', '_REDACTED_GUID_', 999, 'GUID')
    # below regexes are shared by ADO cred scan, see definition:
    # https://github.com/microsoft/azure-pipelines-agent/blob/master/src/Microsoft.VisualStudio.Services.Agent/AdditionalMaskingRegexes.CredScan.cs
    AAD_CLIENT_APP = (r'[0-9A-Za-z-_~.]{3}7Q~[0-9A-Za-z-_~.]{31}\b|\b[0-9A-Za-z-_~.]{3}8Q~[0-9A-Za-z-_~.]{34}', '_REDACTED_AAD_CLIENT_APP_', 99, 'AAD client app')
    SYMMETRIC_KEY_512 = (r'[0-9A-Za-z+/]{76}(APIM|ACDb|\+(ABa|AMC|ASt))[0-9A-Za-z+/]{5}[AQgw]==', '_REDACTED_SYMMETRIC_KEY_', 1, '512-bit symmetric key')
    SYMMETRIC_KEY_256 = (r'[0-9A-Za-z+/]{33}(AIoT|\+(ASb|AEh|ARm))[A-P][0-9A-Za-z+/]{5}=', '_REDACTED_SYMMETRIC_KEY_', 1, '256-bit symmetric key')
    AZURE_FUNCTION_KEY = (r'[0-9A-Za-z_\-]{44}AzFu[0-9A-Za-z\-_]{5}[AQgw]==', '_REDACTED_AZURE_FUNCTION_KEY_', 1, 'Azure function key')
    AZURE_SEARCH_KEY = (r'[0-9A-Za-z]{42}AzSe[A-D][0-9A-Za-z]{5}', '_REDACTED_AZURE_SEARCH_KEY_', 1, 'Azure search key')
    AZURE_CONTAINER_REGISTRY_KEY = (r'[0-9A-Za-z+/]{42}\+ACR[A-D][0-9A-Za-z+/]{5}', '_REDACTED_AZURE_CONTAINER_REGISTRY_KEY_', 1, 'Azure container registry key')
    AZURE_CACHE_FOR_REDIS_KEY = (r'[0-9A-Za-z]{33}AzCa[A-P][0-9A-Za-z]{5}=', '_REDACTED_AZURE_CACHE_FOR_REDIS_KEY_', 1, 'Azure cache for redis key')

    def __init__(self, regex, replacement, level=0, description=''):
        self.regex = regex
        self.replacement = replacement
        self.level = level
        self.description = description


def is_containing_credential(content, is_file=False, max_level=9):
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
    return any(re.search(cred_type.regex, content, flags=re.IGNORECASE | re.MULTILINE) and cred_type.level <= max_level
               for cred_type in CredentialType)


def distinguish_credential(content, is_file=False, max_level=9):
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
    if is_file:
        with open(content, 'r') as f:
            content = json.load(f)

    if isinstance(content, list):
        for item in content:
            _containing_credential, _secret_property_names = distinguish_credential(item, max_level=max_level)
            containing_credential = containing_credential or _containing_credential
            secret_property_names.update(_secret_property_names)
        return containing_credential, secret_property_names

    if isinstance(content, dict):
        for key, value in content.items():
            _containing_credential, _secret_property_names = distinguish_credential(value, max_level=max_level)
            containing_credential = containing_credential or _containing_credential
            secret_property_names.update(_secret_property_names)
            if _containing_credential:
                secret_property_names.add(key)
        return containing_credential, secret_property_names

    if is_containing_credential(content, max_level=max_level):
        containing_credential = True
    return containing_credential, secret_property_names


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
