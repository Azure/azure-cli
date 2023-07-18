# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
from importlib import import_module
import os

from logging import getLogger

logger = getLogger(__name__)

from knack.util import CLIError
from knack.help_files import helps
from azure.cli.core.mock import DummyCli
from azure.cli.core.util import get_installed_cli_distributions
from azure.cli.core._help import CliCommandHelpFile, CliGroupHelpFile
from azure.cli.core.file_util import _store_parsers, _is_group

try:
    from ruamel.yaml import YAML
    yaml = YAML()
    yaml.width = 1000 # prevents wrapping around in dumper.
    yaml.allow_duplicate_keys = True # TODO: allow duplicate keys within help entries. see az container create. Remove this.
except ImportError as e:
    msg = "{}\npip install ruamel.Yaml to use this script.".format(e)
    exit(msg)

PACKAGE_PREFIX = "azure.cli.command_modules"
CLI_PACKAGE_NAME = 'azure-cli'
COMPONENT_PREFIX = 'azure-cli-'

failed = 0

loaded_helps = {}

def get_all_help(cli_ctx):
    invoker = cli_ctx.invocation
    help_ctx = cli_ctx.help_cls(cli_ctx)
    if not invoker:
        raise CLIError('CLI context does not contain invocation.')

    parser_keys = []
    parser_values = []
    sub_parser_keys = []
    sub_parser_values = []
    _store_parsers(invoker.parser, parser_keys, parser_values, sub_parser_keys, sub_parser_values)
    for cmd, parser in zip(parser_keys, parser_values):
        if cmd not in sub_parser_keys:
            sub_parser_keys.append(cmd)
            sub_parser_values.append(parser)
    help_files = []
    for cmd, parser in zip(sub_parser_keys, sub_parser_values):
        if cmd in loaded_helps:
            try:
                help_file = CliGroupHelpFile(help_ctx, cmd, parser) if _is_group(parser) \
                    else CliCommandHelpFile(help_ctx, cmd, parser)
                help_file.load(parser)
                help_files.append(help_file)
            except Exception as ex:  # pylint: disable=broad-except
                print("Skipped '{}' due to '{}'".format(cmd, ex))
    help_files = sorted(help_files, key=lambda x: x.command)
    assert {help_file.command for help_file in help_files} == set(loaded_helps.keys())
    print("Loaded {} help files".format(len(help_files)))
    return help_files


def create_invoker_and_load_cmds_and_args(cli_ctx):
    global loaded_helps
    from knack import events
    from azure.cli.core.commands import register_cache_arguments
    from azure.cli.core.commands.arm import register_global_subscription_argument, register_ids_argument

    invoker = cli_ctx.invocation_cls(cli_ctx=cli_ctx, commands_loader_cls=cli_ctx.commands_loader_cls,
                                     parser_cls=cli_ctx.parser_cls, help_cls=cli_ctx.help_cls)
    cli_ctx.invocation = invoker
    invoker.commands_loader.skip_applicability = True
    temp_help = helps.copy()
    invoker.commands_loader.load_command_table(None) # this ends up loading all the helpfiles, which could be problematic with duplicate key commands like acs create
    helps.clear()
    helps.update(temp_help)

    # turn off applicability check for applicable loaders
    new_cmd_to_loader_map = {}
    new_command_group_table = {}
    new_command_table = {}
    for cmd in loaded_helps.keys():
        if cmd in invoker.commands_loader.cmd_to_loader_map: # if a command from help, then update commands_loader
            new_cmd_to_loader_map[cmd] = invoker.commands_loader.cmd_to_loader_map[cmd]
            new_command_table[cmd] = invoker.commands_loader.command_table[cmd]
        else: # else a group then update
            new_command_group_table[cmd] = invoker.commands_loader.command_group_table[cmd]

    # include commands of groups in help.py, even though the commands themselves might not be in help.py, so their subparsers can be added.
    for cmd in new_command_group_table.keys():
        all_cmds = invoker.commands_loader.cmd_to_loader_map.keys()
        for old_cmd in all_cmds:
            if old_cmd.startswith(cmd) and old_cmd != cmd:
                new_cmd_to_loader_map[old_cmd] = invoker.commands_loader.cmd_to_loader_map[old_cmd]
                new_command_table[old_cmd] = invoker.commands_loader.command_table[old_cmd]

    invoker.commands_loader.cmd_to_loader_map = new_cmd_to_loader_map
    invoker.commands_loader.command_table = new_command_table
    invoker.commands_loader.command_group_table = new_command_group_table

    for loaders in invoker.commands_loader.cmd_to_loader_map.values():
        for loader in loaders:
            loader.skip_applicability = True

    for command in invoker.commands_loader.command_table:
        invoker.commands_loader.load_arguments(command)

    assert len(new_command_table) == len(new_cmd_to_loader_map)
    assert set(list(new_command_table.keys()) + list(new_command_group_table.keys())) >= set(loaded_helps.keys())

    register_global_subscription_argument(cli_ctx)
    register_ids_argument(cli_ctx)  # global subscription must be registered first!
    register_cache_arguments(cli_ctx)
    cli_ctx.raise_event(events.EVENT_INVOKER_POST_CMD_TBL_CREATE, commands_loader=invoker.commands_loader)
    invoker.parser.load_command_table(invoker.commands_loader)

# this must be called before loading any command modules. Otherwise helps object will have every help.py file's contents
def convert(target_mod_or_file, mod_name, test=False):
    global loaded_helps

    if os.path.exists(target_mod_or_file):
        out_file = target_mod_or_file
        target_mod = import_module("{}.{}._help".format(PACKAGE_PREFIX, mod_name))

    else: # else not a file, but a mod.
        try:
            target_mod = import_module(target_mod_or_file)
        except ModuleNotFoundError as e: # azure.cli.command_modules.core
            logger.warning(e)
            return None, None
        loader_file_path = os.path.abspath(target_mod.__file__)
        out_file = os.path.join(os.path.dirname(loader_file_path), "help.yaml")

    if test and os.path.exists(out_file):
        print("{}/help.yaml already exists. Will remove and rewrite: {}\n".format(mod_name, out_file))
        os.remove(out_file)

    # the modules keys are keys added to helps object from fresh import....
    help_dict = target_mod.helps
    result = _get_new_yaml_dict(help_dict)

    # clear modules help from knack.helps, store help.py info
    for key, value in help_dict.items():
        loaded_helps[key] = value

    return out_file, result

def delete(target_mods):
    for mod_name in target_mods:
        try:
            target_mod = import_module(mod_name)
        except ModuleNotFoundError as e:  # azure.cli.command_modules.core
            print(e)
            print("SKIPPING...")
            continue
        loader_file_path = os.path.abspath(target_mod.__file__)
        yaml_file = os.path.join(os.path.dirname(loader_file_path), "help.yaml")
        if os.path.exists(yaml_file):
            print("Removing {}".format(yaml_file))
            os.remove(yaml_file)

def get_all_mod_names():
    installed_dists = get_installed_cli_distributions()
    mod_name_list = list(sorted(dist.key.replace(COMPONENT_PREFIX, '') for dist in installed_dists if dist.key.startswith(COMPONENT_PREFIX)))
    return mod_name_list


def _get_new_yaml_dict(help_dict):

    result = dict(version=1, content=[])
    content = result['content']

    for command_or_group, yaml_text in help_dict.items():
        help_dict = yaml.safe_load(yaml_text)

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
                    new_param["name"] = max(options, key=lambda x: len(x))
                _convert_summaries(old_dict=param, new_dict=new_param)

                if "populator-commands" in param:
                    new_param["value-sources"] = []
                    for item in param["populator-commands"]:
                        new_param["value-sources"].append({"link": {"command" : item}})
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
                supported_profiles, unsupported_profiles = "supported-profiles", "unsupported-profiles"
                if supported_profiles in ex:
                    new_ex[supported_profiles] = ex[supported_profiles]
                if unsupported_profiles in ex:
                    new_ex[unsupported_profiles] = ex[unsupported_profiles]
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

    old_examples = sorted(old_help.examples, key=lambda x: x.short_summary)
    new_examples = sorted(new_help.examples, key=lambda x: x.short_summary)
    assert_true_or_warn(len(old_examples), len(new_examples))
    # note: this cannot test if min / max version were added as these fields weren't stored in helpfile objects previously.
    for old_ex, new_ex in zip(old_examples, new_examples):
        assert_true_or_warn (old_ex.short_summary, new_ex.short_summary)
        assert_true_or_warn (old_ex.command, new_ex.command)
        assert_true_or_warn (old_ex.long_summary, new_ex.long_summary)

    # group and not command, we are done checking.
    if old_help.type == "group":
        return

    old_parameters = sorted(old_help.parameters, key=lambda x: x.name_source)
    new_parameters = sorted(new_help.parameters, key=lambda x: x.name_source)
    assert_true_or_warn(len(old_parameters), len(new_parameters))
    assert_params_equal(old_parameters, new_parameters)


def assert_params_equal(old_parameters, new_parameters):
    for old, new in zip(old_parameters, new_parameters):
        assert_true_or_warn(old.short_summary, new.short_summary)
        assert_true_or_warn(old.long_summary, new.long_summary)
        assert_true_or_warn(old.value_sources, new.value_sources)


def assert_true_or_warn(x, y):
    try:
        assert x == y

    except AssertionError:
        # if is list try to find exactly where there is failure
        if isinstance(x, list) and len(x) == len(y):
            for x_1, y_1 in zip(x, y):
                assert_true_or_warn(x_1, y_1)
        else:
            msg = "\nvalues:\n\n{}\n\nand\n\n{}\n\nare not equal.\n".format(x, y)

            global failed
            failed+=1
            if failed:
                msg = "{}{}".format(msg, "-------------------\nAssertion Failed!!!\nExiting test.\n-------------------\n")
                exit(msg)


if __name__ == "__main__":
    if sys.version_info[0] < 3:
        raise Exception("This script requires Python 3")

    args = [arg.strip() for arg in sys.argv[1:]]
    test = False

    msg = 'Usage: python help_convert.py (MOD | --test | --delete | --all | MOD --test | path/help.py --package {myext.package})\n'

    if "--help" in args or "-h" in args:
        print(msg)
        exit(0)

    if len(args) > 3 or len(args) == 0:
        exit(msg)

    if len(args) == 2:
        if args[1].lower() != "--test":
            exit(msg)
        else:
            test = True
    if len(args) == 3:
        if not args[0].lower().endswith("_help.py") or args[1].lower() != "--package":
            exit(msg)
        else:
            raise NotImplementedError

    target_mods = None
    # if args[0].lower() in ["--test", "--all"]:
    #     # convert all modules and test
    #     mod_names = get_all_mod_names()
    #     target_mods = ["{}.{}._help".format(PACKAGE_PREFIX, mod) for mod in mod_names]
    #     if args[0].lower() == "--test":
    #         test = True
    if args[0].lower() == "--delete":
        mod_names = get_all_mod_names()
        mod_names.append("sqlvm")
        target_mods = ["{}.{}._help".format(PACKAGE_PREFIX, mod) for mod in mod_names]
        delete(target_mods)
        exit(0)
    elif args[0].lower() == "--get-all-mods":
        mod_names = get_all_mod_names()
        with open("mod.txt", "w") as f:
            for name in mod_names:
                f.write(name + "\n")
        exit(0)
    else:
        mod_names = [args[0]]
        # attempt to find and load the desired module.
        if "_help.py" not in mod_names[0]:
            target_mods = ["{}.{}._help".format(PACKAGE_PREFIX, mod_names[0])]
        else:
            target_mods = [mod_names[0]]
            mod_names = [os.path.split(os.path.split(mod_names[0])[0])[1]] # if help.py, get mod name

    if test:
        # convert _help.py contents to help.yaml. Write out help.yaml
        print("Generating new help.yaml file contents. Holding off on writing contents...")
        file_to_help = {}

        for mod, mod_name in zip(target_mods, mod_names):
            file, help_dict = convert(mod, mod_name, test=True)
            if file is None or help_dict is None:
                continue
            file_to_help[file] = help_dict

        if not file_to_help:
            exit("No help.yaml file generated for {}.".format(", ".join(mod_names)))

        print("Loading Commands...")
        # setup CLI
        az_cli = DummyCli()
        create_invoker_and_load_cmds_and_args(az_cli)

        print("Loading all old help...")
        all_cli_help = get_all_help(az_cli)
        old_loaded_help = {data.command: data for data in all_cli_help}

        print("Now writing out new help.yaml file contents...")
        for file, help_dict in file_to_help.items():
            logger.warning("Writing {} ...".format(file))
            with open(file, "w") as f:
                yaml.safe_dump(help_dict, f)

        print("Loading all help again...")
        all_cli_help = get_all_help(az_cli)
        new_loaded_help = {data.command: data for data in all_cli_help}

        assert len(old_loaded_help) == len(new_loaded_help)

        diff_dict = {}
        for command in old_loaded_help:
            diff_dict[command] = (old_loaded_help[command], new_loaded_help[command])

        logger.warning("Loaded {} help objects".format(len(new_loaded_help)))
        logger.warning("Verifying that help objects are the same for _help.py and help.yaml.")
        assert len(diff_dict) == len(loaded_helps)
        for old, new in diff_dict.values():
            assert_help_objs_equal(old, new)

    else:
        if len(target_mods) == 1:
            print("Generating help.yaml file...")
            out_file, result = convert(target_mods[0], mod_names[0])
            with open(out_file, "w") as f:
                yaml.safe_dump(result, f)
            print("Done! Successfully generated {0}/help.yaml in {0} module.".format(mod_names[0]))
        else:
            print("Generating help.yaml files...")
            for mod, mod_name in zip(target_mods, mod_names):
                out_file, result = convert(mod, mod_name)
                if out_file is None or result is None:
                    continue
                with open(out_file, "w") as f:
                    yaml.safe_dump(result, f)
                print("Successfully generated {0}/help.yaml in {0} module.".format(mod_name))

