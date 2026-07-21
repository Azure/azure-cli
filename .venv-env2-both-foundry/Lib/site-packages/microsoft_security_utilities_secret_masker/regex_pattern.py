# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import re
from datetime import timedelta
from microsoft_security_utilities_secret_masker.detection import DetectionMetadata, Detection, get_metadata_from_name


def load_regex_patterns_from_json_file(file_name: str):
    import json
    import os
    json_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'GeneratedRegexPatterns')
    file_path = os.path.join(json_dir, file_name)
    with open(file_path, 'r') as file:
        data = json.load(file)
    regex_patterns = set()
    for section in data:
        regex_patterns.add(load_regex_pattern_from_json(section))
    return regex_patterns


def load_regex_pattern_from_json(pattern: dict):
    id = pattern.get('Id', None)
    name = pattern.get('Name', None)
    regex_pattern = RegexPattern(pattern['Pattern'], id, name)
    if 'DetectionMetadata' in pattern and pattern['DetectionMetadata']:
        metadata_names = pattern['DetectionMetadata'].split(',')
        detection_metadata = 0
        for name in metadata_names:
            detection_metadata |= get_metadata_from_name(name)
        regex_pattern.detection_metadata = detection_metadata
    if 'SniffLiterals' in pattern and pattern['SniffLiterals']:
        regex_pattern.sniff_literals = set(pattern['SniffLiterals'])
    return regex_pattern


def generate_sha256_hash(value: str):
    import hashlib
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


class RegexPattern(object):
    def __init__(self, pattern: str, id: str = '', name: str = '', pattern_metadata: DetectionMetadata = DetectionMetadata.NONE,
                 rotation_period: timedelta = None, sniff_literals: set = None, regex_flags: int = re.ASCII):
        if not pattern:
            raise ValueError('pattern cannot be empty')
        self.pattern = pattern
        self.id = id
        self.name = name
        self.detection_metadata = pattern_metadata
        self.rotation_period = rotation_period
        self.sniff_literals = sniff_literals if sniff_literals else set()
        self.regex_flags = regex_flags

    def __eq__(self, other):
        if other is None:
            return False

        if not isinstance(other, RegexPattern):
            return False

        if self.id != other.id:
            return False

        if self.name != other.name:
            return False

        if self.pattern != other.pattern:
            return False

        if self.detection_metadata != other.detection_metadata:
            return False

        if self.rotation_period != other.rotation_period:
            return False

        if self.regex_flags != other.regex_flags:
            return False

        if len(self.sniff_literals) != len(other.sniff_literals):
            return False

        for literal in self.sniff_literals:
            if literal not in other.sniff_literals:
                return False

        return True

    def __hash__(self):
        result = 17
        result = 31 * result + hash(self.pattern)
        if self.id:
            result = 31 * result + hash(self.id)
        if self.name:
            result = 31 * result + hash(self.name)
        result = 31 * result + hash(self.regex_flags)
        result = 31 * result + hash(self.rotation_period)
        result = 31 * result + hash(self.detection_metadata)
        if self.sniff_literals:
            xor_0 = 0
            for literal in self.sniff_literals:
                xor_0 ^= hash(literal)
            result = 31 * result + xor_0
        return result

    def get_match_id_and_name(self, match: str):
        return self.id, self.name

    def get_detections(self, input: str, generate_sha256_hashes: bool = False):
        detections = []
        if not input:
            return detections

        sniff_match = False
        for literal in self.sniff_literals:
            if input.find(literal) != -1:
                sniff_match = True
                break

        if self.sniff_literals and not sniff_match:
            return detections

        for m in re.finditer(self.pattern, input, self.regex_flags):
            if not m:
                continue
            start = m.start()
            end = m.end()
            value = m.group(0)
            if 'refine' in m.groupdict():
                start = m.start('refine')
                end = m.end('refine')
                value = m.group('refine')
            id, name = self.get_match_id_and_name(value)
            sha256_hash = None
            if generate_sha256_hashes and self.detection_metadata & DetectionMetadata.HIGH_ENTROPY:
                sha256_hash = generate_sha256_hash(value)
            detection = Detection(id, name, start, end, self.detection_metadata,
                                  self.rotation_period, sha256_hash, '+++')
            detections.append(detection)

        return detections
