# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import enum
from datetime import timedelta


def get_metadata_from_name(name: str):
    if not name:
        return DetectionMetadata.NONE

    from microsoft_security_utilities_secret_masker.util import to_snake_case
    name = to_snake_case(name.replace(' ', '')).upper()
    for metadata in DetectionMetadata:
        if metadata.name == name:
            return metadata
    return DetectionMetadata.NONE


class DetectionMetadata(enum.IntFlag):
    NONE = 0
    OBSOLETE_FORMAT = 1
    HIGH_ENTROPY = 1 << 1
    FIXED_SIGNATURE = 1 << 2
    EMBEDDED_CHECKSUM = 1 << 3
    REQUIRES_ROTATION = 1 << 4
    UNCLASSIFIED = 1 << 5
    LOW_CONFIDENCE = 1 << 6
    MEDIUM_CONFIDENCE = 1 << 7
    HIGH_CONFIDENCE = 1 << 8
    IDENTIFIABLE = FIXED_SIGNATURE | EMBEDDED_CHECKSUM | HIGH_ENTROPY | HIGH_CONFIDENCE


class Detection(object):
    def __init__(self, id: str, name: str, start: int, end: int, metadata: DetectionMetadata = DetectionMetadata.NONE,
                 rotation_period: timedelta = None, sha256_hash: str = None, redaction_token: str = '***'):
        self.id = id
        self.name = name
        self.start = start
        self.end = end
        self.metadata = metadata
        self.rotation_period = rotation_period
        self.sha256_hash = sha256_hash
        self.redaction_token = redaction_token

    def __str__(self):
        return f'{self.id}.{self.name}:{self.start}-{self.end}:{self.metadata}:{self.sha256_hash}:{self.redaction_token}'
