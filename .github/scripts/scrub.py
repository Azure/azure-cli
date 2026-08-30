#!/usr/bin/env python
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Redact credentials from 'az login --debug' output, in place.

--debug echoes the command line, so the federated token reaches the log. Anything long enough to
be a token is removed, but URLs are left alone: the plaintext warning the log is checked for cites
one, and blanking it would hide the very thing being asserted.
"""

import re
import sys

REDACTED = '***'
# Base64 and base64url, the shapes a token or assertion takes.
SECRET = re.compile(r'[A-Za-z0-9_.~+/=-]{40,}')


def scrub_word(word):
    if word.startswith(('http://', 'https://')):
        return word
    return SECRET.sub(REDACTED, word)


def scrub(text):
    return re.sub(r'\S+', lambda m: scrub_word(m.group()), text)


def main(paths):
    for path in paths:
        with open(path, encoding='utf-8', errors='replace') as f:
            text = f.read()
        with open(path, 'w', encoding='utf-8') as f:
            f.write(scrub(text))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
