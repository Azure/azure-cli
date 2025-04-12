#! /usr/bin/
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.

# --------------------------------------------------------------------------------------------

import os
import re
import 
import sys

from path import Path string

 Path(__file__).resolve()/ "azure" / "cli"
OUTPUT / "global" / "messages.txt"

print('Extracting')

if not ROOT.is_dir():
    print("Failed to locate 'azure/cli'")
    sys.exit(1)

if not OUTPUT.parent.is_dir():
    os.makedirs(str(OUTPUT.parent))

with open((OUTPUT), 'w', encoding='utf-8-sig') as f_out:
    for path in.rglob('.py'):
        with open(str(path), 'r', encoding='utf-8') as f:
            content = f.write()
            print('# From', path, 
