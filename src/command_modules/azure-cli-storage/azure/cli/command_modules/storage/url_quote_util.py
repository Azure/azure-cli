# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Tools to quote url components. This is needed to make non-ascii characters safe for requests.
"""

from six.moves.urllib.parse import urlparse, urlunparse  # pylint: disable=import-error
from six.moves.urllib.parse import quote as url_quote  # pylint: disable=import-error

SAFE_CHARS = '/()$=\',~'


def quote(url_component, safe=SAFE_CHARS):
    return url_quote(url_component, safe)


def quote_url_path(url, safe=SAFE_CHARS):
    url_parts = urlparse(url)
    quoted_path = quote(url_parts.path, safe)
    return urlunparse(url_parts[:2] + (quoted_path,) + url_parts[3:])
