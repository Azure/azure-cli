#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import json
import os
from azure.cli.core._util import get_file_json

def read_content_if_is_file(string_or_file):
    content = string_or_file
    if os.path.exists(string_or_file):
        with open(string_or_file, 'r') as f:
            content = f.read()
    return content

def load_json(string_or_file_path):
    if os.path.exists(string_or_file_path):
        return get_file_json(string_or_file_path)
    else:
        return json.loads(string_or_file_path)
