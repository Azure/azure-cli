# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Tools to encode url components using python quoting. This is needed to make non-ascii characters safe for requests.
"""

from six.moves.urllib.parse import urlparse, urlunparse  # pylint: disable=import-error
from six.moves.urllib.parse import quote as url_quote  # pylint: disable=import-error

SAFE_CHARS = '/()$=\',~'


def encode_for_url(url_component, safe=SAFE_CHARS):
    return url_quote(url_component, safe)


def encode_url_path(url, safe=SAFE_CHARS):
    url_parts = urlparse(url)
    quoted_path = encode_for_url(url_parts.path, safe)
    return urlunparse(url_parts[:2] + (quoted_path,) + url_parts[3:])


def make_encoded_file_url_and_names(file_service, share, file_dir, file_name, sas_token, safe=SAFE_CHARS):
    """
    Makes the file url using the service. Encodes the file directory and name if needed and returns url, dir, file
    as a tuple. This is needed to account for encoding differences between python 2 and 3.
    """
    try:
        file_url = file_service.make_file_url(share, file_dir, file_name, sas_token=sas_token)
    except UnicodeEncodeError:
        file_dir = file_dir.encode('utf-8')
        file_name = file_name.encode('utf-8')
        file_url = file_service.make_file_url(share, file_dir, file_name, sas_token=sas_token)
    return (encode_url_path(file_url, safe), file_dir, file_name)
