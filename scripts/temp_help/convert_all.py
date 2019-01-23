# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import os
import subprocess


def get_repo_root():
    """
    Returns the root path to this repository. The root is where .git folder is.
    """
    import os.path
    here = os.path.dirname(os.path.realpath(__file__))

    while not os.path.exists(os.path.join(here, '.git')):
        here = os.path.dirname(here)

    return here


if __name__ == "__main__":
    args = sys.argv[1:]

    if args:
        if args[0].lower() == "--core":
            subprocess.run(["python", "./help_convert.py", "--get-all-mods"])

            module_names = []
            with open("mod.txt", "r") as f:
                for line in f:
                    module_names.append(line)
            os.remove("mod.txt")
            successes = 0
            with open(os.devnull, 'w') as devnull: # silence stdout by redirecting to devnull
                for mod in module_names:
                    args = ["python", "./help_convert.py", mod, "--test"]
                    completed_process = subprocess.run(args, stdout=devnull)
                    if completed_process.returncode == 0:
                        successes += 1

            if successes:
                print("\n----------------------------------------------------------"
                        "Successfuly converted {} help.py files to help.yaml files."
                      "\n----------------------------------------------------------".format(successes))

        elif args[0].lower() == "--extensions":
            pass

        elif args[0].lower() == "--count":
            # Get info about help.py modules and converted help.yaml modules.

            src_root = os.path.join(get_repo_root(), "src", "command_modules")

            py_count = 0
            yaml_count = 0

            for root, dirs, files in os.walk(src_root):
                for file in files:
                    if file.endswith("_help.py") and os.path.dirname(root).endswith("command_modules") and os.path.join("build", "lib") not in root:
                        print("Found {}\n".format(os.path.join(root, file)))
                        py_count +=1
                    if file.endswith("help.yaml") and os.path.dirname(root).endswith("command_modules"):
                        print("Found {}\n".format(os.path.join(root, file)))
                        yaml_count +=1

            print("Found {} _help.py files\n".format(py_count))
            print("Found {} help.yaml files\n".format(yaml_count))
