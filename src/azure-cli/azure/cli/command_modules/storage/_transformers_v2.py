# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import base64
from knack.log import get_logger
from knack.util import todict
from .url_quote_util import encode_url_path
from .track2_util import _encode_bytes

storage_account_key_options = {'primary': 'key1', 'secondary': 'key2'}
logger = get_logger(__name__)


def transform_blob_output(result):
    result = todict(result)
    new_result = {
        "content": "",
        "deleted": result.pop('deleted', None),
        "metadata": result.pop('metadata', None),
        "name": result.pop('name', None),
        "properties": {
            "appendBlobCommittedBlockCount": result.pop('appendBlobCommittedBlockCount', None),
            "blobTier": result.pop('blobTier', None),
            "blobTierChangeTime": result.pop('blobTierChangeTime', None),
            "blobTierInferred": result.pop('blobTierInferred', None),
            "blobType": result.pop('blobType', None),
            "contentLength": result.pop('Size', None),
            "contentRange": result.pop('contentRange', None),
            "contentSettings": {
                "cacheControl": result['contentSettings']['cacheControl'],
                "contentDisposition": result['contentSettings']['contentDisposition'],
                "contentEncoding": result['contentSettings']['contentEncoding'],
                "contentLanguage": result['contentSettings']['contentLanguage'],
                "contentMd5": _encode_bytes(result['contentSettings']['contentMd5']),
                "contentType": result['contentSettings']['contentType']
            },
            "copy": result.pop('copy', None),
            "creationTime": result.pop('creationTime', None),
            "deletedTime": result.pop('deletedTime', None),
            "etag": result.pop('etag', None),
            "lastModified": result.pop('lastModified', None),
            "lease": result.pop('lease', None),
            "pageBlobSequenceNumber": result.pop('pageBlobSequenceNumber', None),
            "pageRanges": result.pop('pageRanges', None),
            "remainingRetentionDays": result.pop('remainingRetentionDays', None),
            "serverEncrypted": result.pop('serverEncrypted', None)
        },
        "snapshot": result.pop('snapshot', None)
    }
    del result['contentSettings']
    new_result.update(result)
    return new_result
