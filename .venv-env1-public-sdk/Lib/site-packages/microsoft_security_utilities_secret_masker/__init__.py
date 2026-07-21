# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

__VERSION__ = '1.0.0b4'

from .secret_masker import SecretMasker
from .regex_pattern import RegexPattern, load_regex_pattern_from_json, load_regex_patterns_from_json_file
from .detection import DetectionMetadata, Detection