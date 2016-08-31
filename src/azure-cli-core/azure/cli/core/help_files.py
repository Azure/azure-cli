#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import yaml

# modules should add entries to helps in the form: "group command": "YAML help"
helps = {}

def _load_help_file(delimiters):
    if delimiters in helps:
        return yaml.load(helps[delimiters])
    else:
        return None
