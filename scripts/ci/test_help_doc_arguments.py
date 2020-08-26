#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import xmltodict
import subprocess
import logging
import re
import sys
import os

logger = logging.getLogger('az-publish')

pattern = r".*?\s+(( --\S+)+( -\S)*).*?:"
# meaning:  escape ansi color codes then
#           match one or more long options ('--') followed by an (optional) short option ('-')
#           and then the first semicolon after 0 or more chars (':')
#           Also handles cases where there are multiple long options see --edition in az sql mi
COMPILED_RE = re.compile(pattern)
GLOBAL_ARGS = ["debug", "help", "output", "query", "subscription", "verbose"]


def main(xml_file, commands=[]):

    if commands is None:
        commands = ["vm create"]
    with open(xml_file, 'r') as f:
        doc_contents = xmltodict.parse(f.read(), process_namespaces=True)

    entries = doc_contents['document']['desc']
    cmd_to_content_dict = {entry['desc_signature']['desc_addname']['#text']: entry['desc_content'] for entry in
                           entries if entry['@objtype'] == "clicommand"}
    for cmd in commands:
        logger.warning("Testing %s help...", cmd)
        help_args = get_args_from_help_text(cmd)
        doc_args = get_args_from_doc_dict(cmd, cmd_to_content_dict)
        try:
            assert help_args == doc_args
        except AssertionError as e:
            logger.error("Test failed. Help args are different.\n")
            logger.error("CLI help args:%s\n\nDoc help args: %s.\n", ", ".join(help_args), ", ".join(doc_args))
            logger.error(e)
            exit(1)


    logger.info("Doc help arguments match CLI help arguments.")



def get_args_from_help_text(cmd_name):
    cmd = "az {} -h".format(cmd_name)
    cmd_args = cmd.split()
    completedprocess = subprocess.run(cmd_args, stdout=subprocess.PIPE, encoding="utf-8")

    if completedprocess.returncode != 0:
        logger.error("Error running %s", " ".join(cmd))
        exit(1)

    lines = completedprocess.stdout.splitlines()
    arguments = set()
    for line in lines:
        match = COMPILED_RE.search(line)
        if match:
            options = match.group(1).strip()
            if _get_long_option(options) not in GLOBAL_ARGS:
                arguments.add(options)
    return arguments


def get_args_from_doc_dict(cmd_name, cmd_to_content_dict):
    try:
        arg_info_dict = {possible_arg['desc_signature']['desc_addname']['#text']: possible_arg['desc_content']['field_list']['field']
                for possible_arg in cmd_to_content_dict[cmd_name]['desc'] if possible_arg['@objtype'] == "cliarg" and
                _get_long_option(possible_arg['desc_signature']['desc_addname']['#text']) not in GLOBAL_ARGS}
    except KeyError:
        return set()

    arguments = set()
    # Only add arguments that don't have the deprecated field. #todo: tidy up logic.
    for arg, arg_fields in arg_info_dict.items():
        is_deprecated = False
        for field in arg_fields:
            if field['field_name'].lower() == 'deprecated':
                is_deprecated = True
                break
        if not is_deprecated:
            arguments.add(arg)
    return arguments



def _get_long_option(options):
    return options.strip().split()[0].lstrip("-")


if __name__ == "__main__":
    usage_msg = "USAGE: PATH-TO-DOC-XML [optional command (without az)]"

    # very rudimentary arg parsing TODO: update to argparse so list of commands can be passed in.
    if len(sys.argv) < 2:
        logger.warning(usage_msg)
        exit(1)

    if not os.path.isfile(sys.argv[1]):
        logger.warning(usage_msg)
        exit(1)

    default_commands = [
        "vm", "network vnet", "storage", # these groups should not fail as command groups do not have parameters.
       "keyvault secret set", "vm create", "sql mi create", "aks create", "webapp deployment slot list"]

    test_commands = [sys.argv[2]] if len(sys.argv) > 2 else default_commands
    main(sys.argv[1], test_commands)