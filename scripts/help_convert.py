# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
from importlib import  import_module
import os
import yaml

PACKAGE_PREFIX = "azure.cli.command_modules"

def convert(target_mod):
    help_dict = target_mod.helps
    loader_file_path = os.path.abspath(target_mod.__file__)

    result = _get_new_yaml_dict(help_dict)

    out_file = os.path.join(os.path.dirname(loader_file_path),"help.yaml")

    with open(out_file, "w") as f:
        yaml.dump(result, f, default_flow_style=False)

def _get_new_yaml_dict(help_dict):

    result = dict(version=0, content=[])
    content = result['content']

    for command_or_group, yaml_text in help_dict.items():
        help_dict = yaml.load(yaml_text)

        type = help_dict["type"]

        elem = {type: dict(name=command_or_group)}
        elem_content = elem[type]

        if "short-summary" in help_dict:
            elem_content["summary"] = help_dict["short-summary"]

        if "long-summary" in help_dict:
            elem_content["description"] = help_dict["long-summary"]



        content.append(elem)

    return result


if __name__ == "__main__":
    args = sys.argv[1:]

    if len(args) != 1:
        msg = "Error: Script takes only one argument"
        exit(msg)

    MOD_NAME = "{}.{}._help".format(PACKAGE_PREFIX, args[0])

    target_mod = import_module(MOD_NAME)

    convert(target_mod)