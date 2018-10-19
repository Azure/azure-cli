# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
from importlib import  import_module
import os

try:
    from ruamel.yaml import YAML
    yaml = YAML()
except ImportError as e:
    msg = "{}\npip install ruamel.Yaml to use this script.".format(e)
    exit(msg)

PACKAGE_PREFIX = "azure.cli.command_modules"

def convert(target_mod):
    help_dict = target_mod.helps
    loader_file_path = os.path.abspath(target_mod.__file__)

    result = _get_new_yaml_dict(help_dict)

    out_file = os.path.join(os.path.dirname(loader_file_path),"help.yaml")

    with open(out_file, "w") as f:
        yaml.dump(result, f)

def _get_new_yaml_dict(help_dict):

    result = dict(version=0, content=[])
    content = result['content']

    for command_or_group, yaml_text in help_dict.items():
        help_dict = yaml.load(yaml_text)

        type = help_dict["type"]

        elem = {type: dict(name=command_or_group)}
        elem_content = elem[type]

        _convert_summaries(old_dict=help_dict, new_dict=elem_content)

        if "parameters" in help_dict:
            parameters = []
            for param in help_dict["parameters"]:
                new_param = dict()
                if "name" in param:
                    options = param["name"].split()
                    option = max(options, key = lambda x: len(x))
                    new_param["name"] = option.lstrip('-')
                _convert_summaries(old_dict=param, new_dict=new_param)

                if "populator-commands" in param:
                    new_param["value-source"] = []
                    for item in param["populator-commands"]:
                        new_param["value-source"].append(dict(string=item))
                parameters.append(new_param)
            elem_content["arguments"] = parameters

        if "examples" in help_dict:
            elem_examples = []
            for ex in help_dict["examples"]:
                new_ex = dict()
                if "name" in ex:
                    new_ex["summary"] = ex["name"]
                if "text" in ex:
                    new_ex["command"] = ex["text"]
                if "min_profile" in ex:
                    new_ex["min_profile"] = ex["min_profile"]
                if "max_profile" in ex:
                    new_ex["max_profile"] = ex["max_profile"]
                elem_examples.append(new_ex)
            elem_content["examples"] = elem_examples

        content.append(elem)

    return result

def _convert_summaries(old_dict, new_dict):
    if "short-summary" in old_dict:
        new_dict["summary"] = old_dict["short-summary"]
    if "long-summary" in old_dict:
        new_dict["description"] = old_dict["long-summary"]

if __name__ == "__main__":
    args = sys.argv[1:]

    if len(args) != 1:
        msg = "Error: Script takes only one argument"
        exit(msg)

    MOD_NAME = "{}.{}._help".format(PACKAGE_PREFIX, args[0])

    target_mod = import_module(MOD_NAME)

    convert(target_mod)