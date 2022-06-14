#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import fileinput
import logging
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

resource_type = sys.argv[1]
target_api_version = sys.argv[2]
shared_file_path = 'src/azure-cli-core/azure/cli/core/profiles/_shared.py'


def _parse_target_api():
    if len(target_api_version.split()) == 1 and "=" not in target_api_version:
        return False, target_api_version
    target = {}
    for single_api_version in target_api_version.split():
        operation, api_version = single_api_version.split("=")
        target[operation] = api_version
    return True, target


def _parse_original_api(api_version):
    return "SDKProfile" in api_version, api_version.split("'")[1]


def _replace_line(line, old_str, new_str):
    logger.info(f"Replacing line from:\n{line}")
    line = line.replace(old_str, new_str)
    logger.info(f"to:\n{line}")


def _replace_resource_type_line(line):
    target_sdk_profile, target = _parse_target_api()
    original_sdk_profile, original = _parse_original_api(line)
    if original_sdk_profile and not target_sdk_profile:
        raise ValueError(f"The type of AZURE_API_PROFILES[latest][ResourceType.{resource_type}] is SDKProfile."
                         f" Can't be replaced with string: {target_api_version}")
    if not original_sdk_profile and target_sdk_profile:
        raise ValueError(f"The type of AZURE_API_PROFILES[latest][ResourceType.{resource_type}] is string."
                         f" Can't be replaced with complex {target_api_version} ")
    if original_sdk_profile and target_sdk_profile:
        if target.get("default"):
            _replace_line(line, original, target.get('default'))
    if not original_sdk_profile and not target_sdk_profile:
        _replace_line(line, original, target)
    return line


def _replace_sdk_profile_line(line):
    _, target = _parse_target_api()
    parts = line.split("'")
    operation = parts[1]
    api_version = parts[3]
    if target.get(operation):
        _replace_line(line, api_version, target.get(operation))
    return line


def main():
    logger.info(f"Start updating api profile for {resource_type} to {target_api_version}\n")
    if not target_api_version:
        raise ValueError(f"'TARGET_API_VERSION' is required for RESOURCE_TYPE:{resource_type}")

    # 0: current line is before latest profile definition
    # 1: current line is within latest profile definition
    # 2: current line is after latest profile definition
    latest_profile_definition = 0
    # 0: current line is before resource type definition
    # 1: current line is within resource type definition
    # 2: current line is after resource type definition
    resource_type_definition = 0

    with fileinput.FileInput(shared_file_path, inplace=True) as file:
        for line in file:
            # check latest_profile_definition change
            if latest_profile_definition == 0 and "'latest':" in line:
                latest_profile_definition = 1
            elif latest_profile_definition == 1 and "}," in line:
                latest_profile_definition = 2
            # check resource_type_definition change and replace line
            if latest_profile_definition == 1:
                if resource_type_definition == 0:
                    if f"ResourceType.{resource_type}:" in line:
                        resource_type_definition = 1 if "SDKProfile" in line else 2
                        line = _replace_resource_type_line(line)
                elif resource_type_definition == 1:
                    if "})" in line:
                        resource_type_definition = 2
                    else:
                        line = _replace_sdk_profile_line(line)
            # fail quickly for invalid cases
            if latest_profile_definition == 2 and resource_type_definition != 2:
                raise ValueError(f"No API definition found in latest profile for ResourceType {resource_type}")

            print(line, end='')

        if latest_profile_definition != 2:
            raise ValueError(f"Did not find AZURE_API_PROFILES[latest] definition in {shared_file_path}")


if __name__ == '__main__':
    main()
