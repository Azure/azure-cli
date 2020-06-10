# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Tools to encode url components using python quoting. This is needed to make non-ascii characters safe for requests.
"""

# Safe characters taken from the sdk:
# https://github.com/Azure/azure-multiapi-storage-python/blob/d4329a838f7d2fa6f0dab584274fd1bd3e77bcc4/azure/multiapi/storage/v2017_04_17/common/_serialization.py#L83
SAFE_CHARS = '/()$=\',~'


def encode_for_url(url_component, safe=SAFE_CHARS):
    from six.moves.urllib.parse import quote as url_quote  # pylint: disable=import-error
    return url_quote(url_component, safe)


def encode_url_path(url, safe=SAFE_CHARS):
    from six.moves.urllib.parse import urlparse, urlunparse  # pylint: disable=import-error
    url_parts = urlparse(url)
    quoted_path = encode_for_url(url_parts.path, safe)
    return urlunparse(url_parts[:2] + (quoted_path,) + url_parts[3:])


def make_encoded_file_url_and_params(file_service, share, file_dir, file_name, sas_token, safe=SAFE_CHARS):
    """
    Makes the file url using the service. Converts the file directory and name into byte-strings if needed and returns
    (url, dir, file) as a tuple. This is needed to account for string encoding differences between python 2 and 3.
    """
    try:
        file_url = file_service.make_file_url(share, file_dir, file_name, sas_token=sas_token)
    except UnicodeEncodeError:
        file_dir = file_dir.encode('utf-8')
        file_name = file_name.encode('utf-8')
        file_url = file_service.make_file_url(share, file_dir, file_name, sas_token=sas_token)

    if not file_dir:
        sep = file_url.find('://')
        file_url = file_url[:sep + 3] + file_url[sep + 3:].replace('//', '/')
    return encode_url_path(file_url, safe), file_dir, file_name
