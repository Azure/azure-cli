# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from microsoft_security_utilities_secret_masker.detection import Detection
from microsoft_security_utilities_secret_masker.rw_lock import RWLock


class SecretMasker(object):

    min_secret_length_ceiling = -1

    def __init__(self, regex_secrets=None, generate_sha256_hashes=False, **kwargs):
        super().__init__(**kwargs)
        self.regex_patterns = regex_secrets if regex_secrets else set()
        self.min_secret_length = -1
        self._generate_sha256_hashes = generate_sha256_hashes
        self._explicitly_added_secret_literals = set()
        self._encoded_secret_literals = set()
        self._literal_encoders = set()
        self._rw_lock = RWLock()
        self._elapsed_masking_time = 0

    def add_regex(self, regex_secret):
        try:
            self._rw_lock.acquire_write()
            self.regex_patterns.add(regex_secret)
        finally:
            self._rw_lock.release()

    def add_value(self, value: str):
        if not value:
            return

        if len(value) < self.min_secret_length:
            return

        try:
            self._rw_lock.acquire_read()
            if value in self._explicitly_added_secret_literals:
                return
            literal_encoders = list(self._literal_encoders)
        finally:
            self._rw_lock.release()

        secret_literals = [value]
        for literal_encoder in literal_encoders:
            encoded_value = literal_encoder(value)
            if encoded_value and len(encoded_value) >= self.min_secret_length:
                secret_literals.append(encoded_value)

        try:
            self._rw_lock.acquire_write()
            for secret_literal in secret_literals:
                self._encoded_secret_literals.add(secret_literal)
            self._explicitly_added_secret_literals.add(value)
        finally:
            self._rw_lock.release()

    def add_literal_encoder(self, literal_encoder):
        try:
            self._rw_lock.acquire_read()
            if literal_encoder in self._literal_encoders:
                return
            original_secrets = list(self._explicitly_added_secret_literals)
        finally:
            self._rw_lock.release()

        encoded_secrets = []
        for original_secret in original_secrets:
            encoded_secret = literal_encoder(original_secret)
            if encoded_secret and len(encoded_secret) >= self.min_secret_length:
                encoded_secrets.append(encoded_secret)

        try:
            self._rw_lock.acquire_write()
            self._literal_encoders.add(literal_encoder)
            for encoded_secret in encoded_secrets:
                self._encoded_secret_literals.add(encoded_secret)
        finally:
            self._rw_lock.release()

    def detect_secrets(self, input: str):
        detections = []
        if not input:
            return detections
        if len(self.regex_patterns) == 0 and len(self._explicitly_added_secret_literals) == 0:
            return detections

        try:
            self._rw_lock.acquire_read()

            import timeit
            start_time = timeit.default_timer()

            for regex_pattern in self.regex_patterns:
                detections.extend(regex_pattern.get_detections(input, self._generate_sha256_hashes))

            for secret_literal in self._encoded_secret_literals:
                start = input.find(secret_literal)
                while start != -1:
                    end = start + len(secret_literal)
                    detections.append(Detection('', '', start, end))
                    start = input.find(secret_literal, end)

            end_time = timeit.default_timer()
            self._elapsed_masking_time += end_time - start_time
        finally:
            self._rw_lock.release()

        return detections

    def mask_secrets(self, input: str):
        if not input:
            return input

        detections = self.detect_secrets(input)
        if not detections:
            return input

        merged_detections = []
        current_detection = None
        detections.sort(key=lambda x: x.start)
        for detection in detections:
            if not current_detection:
                current_detection = detection
                continue

            if detection.start <= current_detection.end:
                current_detection.end = max(detection.end, current_detection.end)
                continue

            merged_detections.append(current_detection)
            current_detection = detection
        if current_detection:
            merged_detections.append(current_detection)

        result = ''
        start_index = 0
        for detection in merged_detections:
            result += input[start_index: detection.start]
            result += detection.redaction_token
            start_index = detection.end
        if start_index < len(input):
            result += input[start_index:]

        return result
