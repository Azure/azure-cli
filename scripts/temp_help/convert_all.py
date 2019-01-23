# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import os
import subprocess

if __name__ == "__main__":
    args = sys.argv[1:]

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
