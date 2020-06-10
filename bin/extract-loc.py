#! /usr/bin/env python3
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import re
import subprocess
import sys

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "src" / "azure" / "cli"
OUTPUT = ROOT / "locale" / "en-US" / "messages.txt"

print('Extracting from:', ROOT)

if not ROOT.is_dir():
    print("Failed to locate 'azure/cli'")
    sys.exit(1)

if not OUTPUT.parent.is_dir():
    os.makedirs(str(OUTPUT.parent))

with open(str(OUTPUT), 'w', encoding='utf-8-sig') as f_out:
    for path in ROOT.rglob('*.py'):
        with open(str(path), 'r', encoding='utf-8') as f:
            content = f.read()
        for m in re.finditer(r'[^\w_]_\(("(.+)"|\'(.+)\')\)', content):
            print('# From', path, ':', m.span()[0], file=f_out)
            print('KEY:', m.group(2) or m.group(3), file=f_out)
            print(m.group(2) or m.group(3), file=f_out)
            print(file=f_out)
