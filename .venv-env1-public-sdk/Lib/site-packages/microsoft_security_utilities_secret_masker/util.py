# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

def to_snake_case(value: str):
    return ''.join(['_' + i.lower() if i.isupper() else i for i in value]).lstrip('_')
