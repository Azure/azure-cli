# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
from importlib import import_module
import os
import subprocess
import difflib
from pprint import pprint

from azure.cli.core import get_default_cli
from azure.cli.core.file_util import get_all_help, create_invoker_and_load_cmds_and_args

try:
    from ruamel.yaml import YAML
    yaml = YAML()
except ImportError as e:
    msg = "{}\npip install ruamel.Yaml to use this script.".format(e)
    exit(msg)

PACKAGE_PREFIX = "azure.cli.command_modules"

failed = 0


# this must be called before loading any command modules. Otherwise helps object will have every help.py file's contents
def convert(target_mod, mod_name, test=False):
    help_dict = target_mod.helps
    loader_file_path = os.path.abspath(target_mod.__file__)

    out_file = os.path.join(os.path.dirname(loader_file_path), "help.yaml")
    if test and os.path.exists(out_file):
        print("{}/help.yaml already exists.\nPlease remove: {}\nand re-run this command.\n".format(mod_name, out_file))
        exit(1)

    result = _get_new_yaml_dict(help_dict)

    return out_file, result


def _get_new_yaml_dict(help_dict):

    result = dict(version=1, content=[])
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
                    option = max(options, key=lambda x: len(x))
                    new_param["name"] = option.lstrip('-')
                _convert_summaries(old_dict=param, new_dict=new_param)

                if "populator-commands" in param:
                    new_param["value-sources"] = []
                    for item in param["populator-commands"]:
                        new_param["value-sources"].append(dict(string=item))
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

def assert_help_objs_equal(old_help, new_help):
    assert_true_or_warn(old_help.name, new_help.name)
    assert_true_or_warn(old_help.type, new_help.type)
    assert_true_or_warn(old_help.short_summary, new_help.short_summary)
    assert_true_or_warn(old_help.long_summary, new_help.long_summary)
    assert_true_or_warn(old_help.command, new_help.command)

    old_examples = sorted(old_help.examples, key=lambda x: x.name)
    new_examples = sorted(new_help.examples, key=lambda x: x.name)
    assert_true_or_warn(len(old_examples), len(new_examples))
    # note: this cannot test if min / max version were added as these fields weren't stored in helpfile objects previously.
    for old_ex, new_ex in zip(old_examples, new_examples):
        assert_true_or_warn (old_ex.text, new_ex.text)

    assert_true_or_warn(old_help.deprecate_info, new_help.deprecate_info)
    assert_true_or_warn(old_help.preview_info, new_help.preview_info)

    # group and not command, we are done checking.
    if old_help.type == "group":
        return

    old_parameters = sorted(old_help.parameters, key=lambda x: x.name_source)
    new_parameters = sorted(new_help.parameters, key=lambda x: x.name_source)
    assert_true_or_warn(len(old_parameters), len(new_parameters))
    assert_params_equal(old_parameters, new_parameters)


def assert_params_equal(old_parameters, new_parameters):
    for old, new in zip(old_parameters, new_parameters):
        assert_true_or_warn (old.short_summary, new.short_summary)
        assert_true_or_warn (old.long_summary, new.long_summary)

        old_value_sources = sorted(old.value_sources)
        new_value_sources = sorted(new.value_sources)
        assert_true_or_warn (old_value_sources, new_value_sources)


def assert_true_or_warn(x, y):
    try:
        if x != y:
            if isinstance(x, str):
                matcher = difflib.SequenceMatcher(a=x, b=y)
                print("Ratio: {}".format(matcher.ratio()))
                d = difflib.Differ()
                result = list(d.compare(x.splitlines(keepends=True), y.splitlines(keepends=True)))

                help_link = "https://docs.python.org/3.7/library/difflib.html#difflib.Differ"
                print("Showing diff... (See {} for more info).".format(help_link))
                pprint(result)

                if matcher.ratio() > 0.9:
                    print("These two values have a similarity ratio of {}/1.0. "
                          "Test will count them as similar. Please review.".format(matcher.ratio()))
                else:
                    assert x == y
            else:
                assert x == y

    except AssertionError:
        # if is list try to find exactly where there is failure
        if isinstance(x, list) and len(x) == len(y):
            for x_1, y_1 in zip(x, y):
                assert_true_or_warn(x_1, y_1)
        else:
            print("\nvalues:\n\n{}\n\nand\n\n{}\n\nare not equal.\n".format(x, y))

            global failed
            failed+=1

            if failed > 15:
                print("More than 15 assertions failed. Exiting tests.\n")
                exit(1)


if __name__ == "__main__":
    if sys.version_info[0] < 3:
        raise Exception("This script requires Python 3")

    args = sys.argv[1:]
    test = False

    if "--help" in args or "-h" in args:
        print('Usage: python help_convert.py (MOD | MOD "TEST")\n')
        exit(0)

    if len(args) > 2:
        msg = 'Usage: python help_convert.py (MOD | MOD "TEST")\n'
        exit(msg)

    if len(args) == 2:
        if args[1].lower() != "test":
            msg = 'Usage: python help_convert.py (MOD | MOD "TEST")\n'
            exit(msg)
        else:
            test = True

    # attempt to find and load the desired module.
    MOD_NAME = "{}.{}._help".format(PACKAGE_PREFIX, args[0])
    target_mod = import_module(MOD_NAME)

    if test:
        # setup CLI to enable command loader
        az_cli = get_default_cli()

        # convert _help.py contents to help.yaml. Write out help.yaml
        print("Generating new help.yaml file contents. Holding off on writing contents...")
        out_file, result = convert(target_mod, args[0], test=True)

        print("Loading Commands...")
        # load commands, args, and help
        create_invoker_and_load_cmds_and_args(az_cli)

        # format loaded help
        print("Loading all old help...")
        old_loaded_help = {data.command: data for data in get_all_help(az_cli) if data.command}

        print("Now writing out new help.yaml file contents...")
        with open(out_file, "w") as f:
            yaml.dump(result, f)

        print("Loading all help again...")
        new_loaded_help = {data.command: data for data in get_all_help(az_cli) if data.command}

        diff_dict = {}
        for command in old_loaded_help:
            if command.startswith(args[0]):
                diff_dict[command] = (old_loaded_help[command], new_loaded_help[command])

        print("Verifying that help objects are the same for {0}/_help.py and {0}/help.yaml.".format(args[0]))
        # verify that contents the same
        for old, new in diff_dict.values():
            assert_help_objs_equal(old, new)

        print("Running linter on {}.".format(args[0]))
        linter_args = ["azdev", "cli-lint", "--module", args[0]]
        completed_process = subprocess.run(linter_args, stderr=subprocess.STDOUT)
        if completed_process.returncode != 0:
            if failed:
                print("{} assertion(s) failed.".format(failed))

            print("Done. Linter failed for {}/help.yaml.".format(args[0]))
            exit(1)

        if not failed:
            print("Done! Successfully tested and generated {0}/help.yaml in {0} module".format(args[0]))
        else:
            print("Done. {} assertion(s) failed.".format(failed))
            exit(1)

    else:
        print("Generating help.yaml file...")
        out_file, result = convert(target_mod, args[0])
        with open(out_file, "w") as f:
            yaml.dump(result, f)
        print("Done! Successfully generated {0}/help.yaml in {0} module.".format(args[0]))
