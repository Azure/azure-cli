# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import subprocess
import argparse
from knack.log import get_logger
from azure.cli.core.extension import get_extensions

logger = get_logger(__name__)

def get_profiles():
    try:
        profiles_str = subprocess.check_output(["az", "cloud", "list-profiles", "-o", "tsv"]).decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        raise SystemExit("Failed to get profiles with err: {}".format(e))

    return profiles_str.splitlines()

def set_profile(profile):
    try:
        logger.warning("Setting the profile to %s", profile)
        subprocess.check_call(['az', 'cloud', 'update', '--profile', profile])
    except subprocess.CalledProcessError as e:
        raise SystemExit("Failed to set profile {} due to err:\n{}".format(profile, e))

def get_current_profile():
    try:
        return subprocess.check_output(['az', 'cloud', 'show', '--query', '"profile"', '-otsv']).decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        raise SystemExit("Failed to get profiles with err: {}".format(e))

def main(args):
    if get_extensions():
        raise SystemExit("Extensions are installed. Please uninstall them to generate core CLI docs.")

    output_dir = args.output_dir if args.output_dir else "_build"
    output_dir = os.path.abspath(output_dir)
    if not os.path.exists(output_dir):

        logger.warning("%s does not exist. Will create it.", output_dir)
        os.mkdir(output_dir)
    output_type = args.output_type if args.output_type else "xml"
    original_profile = get_current_profile()

    profiles = get_profiles()

    for profile in profiles:
        try:
            # build cmd
            profile_output_dir = os.path.join(output_dir, profile)
            cmd = ['azdev', 'cli', 'generate-docs', '--output-type', output_type, '--output-dir', profile_output_dir]

            # set profile
            set_profile(profile)
            logger.warning("Executing: %s", " ".join(cmd))

            # call cmd
            subprocess.call(cmd)
            logger.warning("Finished. The %s files are in %s", output_type, profile_output_dir)
        except SystemExit as e:
            set_profile(original_profile)
            logger.warning("Error when attempting to generate docs for profile %s", profile)
            raise e

    # always set the profile back to the original profile
    set_profile(original_profile)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", dest="output_dir", help="The directory to place the generated ref docs in. Default: _build")
    parser.add_argument("--output-type", dest="output_type", help="The sphinx output / builder type of the generated ref docs. Default: xml")
    args = parser.parse_args()
    main(args)