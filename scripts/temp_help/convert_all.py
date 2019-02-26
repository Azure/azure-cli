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


def comment_import_help(init_file, out_file):
    f_out =  open(out_file, "w")

    output = ""
    updated = False
    with open(init_file, "r") as f_in:
        for line in f_in:
            if "import" in line and "_help" in line and not updated:
                updated = True
                line = "# " + line
            output += line

    f_out.write(output)
    f_out.close()
    return updated

def decomment_import_help(init_file, out_file):
    f_out =  open(out_file, "w")

    output = ""
    updated = False
    with open(init_file, "r") as f_in:
        for line in f_in:
            if "import" in line and "_help" in line and not updated:
                updated = True
                line = line.lstrip("# ")
            output += line
    f_out.write(output)
    f_out.close()
    return updated

def install_extension(ext_name):
    command = "az extension add -n " + ext_name
    completed = subprocess.run(command.split())
    if completed.returncode == 0:
        print("{} was successfully installed.".format(ext_name))
        return True
    else:
        print("{} was not installed.".format(ext_name))
        return False

def uninstall_extension(ext_name):
    command = "az extension remove -n " + ext_name
    completed = subprocess.run(command.split())
    if completed.returncode == 0:
        print("{} was successfully uninstalled.".format(ext_name))
        return True
    else:
        print("{} was not uninstalled.".format(ext_name))
        return False

if __name__ == "__main__":
    args = sys.argv[1:]

    if args:
        if args[0].lower() == "--core":
            test = False
            try:
                if args[1].lower() == "--test":
                    test = True
            except IndexError:
                pass

            subprocess.run(["python", "./help_convert.py", "--get-all-mods"])

            module_names = []
            with open("mod.txt", "r") as f:
                for line in f:
                    module_names.append(line)
            if "sqlvm" not in module_names:
                module_names.append("sqlvm")
            os.remove("mod.txt")
            successes = 0
            with open(os.devnull, 'w') as devnull: # silence stdout by redirecting to devnull
                for mod in module_names:
                    args = ["python", "./help_convert.py", mod]
                    if test:
                        args.append("--test")
                    completed_process = subprocess.run(args, stdout=devnull)
                    if completed_process.returncode == 0:
                        successes += 1

            if successes:
                print("\n----------------------------------------------------------"
                      "\nSuccessfuly converted {} help.py files to help.yaml files."
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

        elif args[0].lower() == "--move-py":

            src_root = os.path.join(get_repo_root(), "src", "command_modules")

            py_count = 0
            yaml_count = 0
            failures = 0

            for root, dirs, files in os.walk(src_root):
                for file in files:
                    if file.endswith("_help.py") and os.path.dirname(root).endswith("command_modules") and os.path.join("build", "lib") not in root:
                        src = os.path.join(root, file)
                        dst = os.path.join(root, "foo.py")
                        print("Found {}\n".format(src))
                        print("Renaming {}\n\tto {}\n.".format(src, dst))
                        os.rename(src, dst)
                        py_count +=1

                        src = os.path.join(root, "__init__.py")
                        dst = os.path.join(root, "__init__2.py")

                        success = comment_import_help(src, dst)

                        if success:
                            os.remove(src)
                            os.rename(dst, src)
                            print("Commented out import in {}\n".format(src))
                        else:
                            os.remove(dst)
                            print("Failed to comment out import in {}\n".format(src))
                            failures+=1


            print("Renamed {} _help.py files to foo.py.\n".format(py_count))
            print("There were {} failures to decomment import statements\n".format(failures))

        elif args[0].lower() == "--move-foo":
            src_root = os.path.join(get_repo_root(), "src", "command_modules")

            py_count = 0
            yaml_count = 0
            failures = 0

            for root, dirs, files in os.walk(src_root):
                for file in files:
                    if file.endswith("foo.py") and os.path.dirname(root).endswith("command_modules") and os.path.join("build", "lib") not in root:
                        src = os.path.join(root, file)
                        dst = os.path.join(root, "_help.py")
                        print("Found {}\n".format(src))
                        print("Renaming {}\n\tto {}\n.".format(src, dst))
                        os.rename(src, dst)
                        py_count +=1

                        src = os.path.join(root, "__init__.py")
                        dst = os.path.join(root, "__init__2.py")

                        success = decomment_import_help(src, dst)

                        if success:
                            os.remove(src)
                            os.rename(dst, src)
                            print("De-commented out import in {}\n".format(src))
                        else:
                            os.remove(dst)
                            print("Failed to de-comment out import in {}\n".format(src))
                            failures+=1

            print("Renamed {} foo.py files to _help.py.\n".format(py_count))
            print("There were {} failures to decomment import statements\n".format(failures))

        elif args[0].lower() == "--add-extensions":
            command = "az extension list-available --query [].name -o tsv"
            completed = subprocess.run(command.split(), stdout=subprocess.PIPE, universal_newlines=True)
            if completed.returncode == 0:
                num_installed = 0
                extensions = completed.stdout.splitlines()
                for ext in extensions:
                    success = install_extension(ext)
                    if success:
                        num_installed += 1

                print("Installed {} extensions".format(num_installed))

        elif args[0].lower() == "--remove-extensions":
            command = "az extension list --query [].name -o tsv"
            completed = subprocess.run(command.split(), stdout=subprocess.PIPE, universal_newlines=True)
            if completed.returncode == 0:
                num_installed = 0
                extensions = completed.stdout.splitlines()
                for ext in extensions:
                    success = uninstall_extension(ext)
                    if success:
                        num_installed += 1

                print("Uninstalled {} extensions".format(num_installed))
