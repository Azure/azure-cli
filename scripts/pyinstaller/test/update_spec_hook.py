# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

SPEC_PATH = 'az.spec'

with open(SPEC_PATH, 'r') as fp:
    content = fp.read()
with open(SPEC_PATH, 'w') as fp:
    fp.write(content.replace('./scripts/pyinstaller/hooks/az/release/', './scripts/pyinstaller/hooks/az/test/'))