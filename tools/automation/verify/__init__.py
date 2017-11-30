# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from automation.verify.doc_source_map import verify_doc_source_map
from automation.verify.default_modules import verify_default_modules
import automation.verify.verify_packages
import automation.verify.verify_commands
import automation.verify.verify_dependencies


def verify_license(_):
    import sys
    import os
    from automation.utilities.path import get_repo_root

    license_header = """# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
"""

    env_path = os.path.join(get_repo_root(), 'env')

    files_without_header = []
    for current_dir, _, files in os.walk(get_repo_root()):
        if current_dir.startswith(env_path):
            continue

        file_itr = (os.path.join(current_dir, p) for p in files if p.endswith('.py') and p != 'azure_bdist_wheel.py')
        for python_file in file_itr:
            with open(python_file, 'r') as f:
                file_text = f.read()

                if file_text and license_header not in file_text:
                    files_without_header.append(os.path.join(current_dir, python_file))

    if files_without_header:
        sys.stderr.write("Error: The following files don't have the required license headers: \n{}".format(
            '\n'.join(files_without_header)))

        sys.exit(1)


def init_args(root):
    parser = root.add_parser('verify')
    parser.set_defaults(func=lambda _: parser.print_help())
    sub_parser = parser.add_subparsers(title='sub commands')

    license_verify = sub_parser.add_parser('license', help='Verify license headers.')
    license_verify.set_defaults(func=verify_license)

    doc_map = sub_parser.add_parser('document-map', help='Verify documentation map.')
    doc_map.set_defaults(func=verify_doc_source_map)

    def_modules = sub_parser.add_parser('default-modules', help='Verify default modules.')
    def_modules.add_argument('build_folder', help='The path to the folder contains all wheel files.')
    def_modules.set_defaults(func=verify_default_modules)

    automation.verify.verify_packages.init(sub_parser)
    automation.verify.verify_commands.init(sub_parser)
    automation.verify.verify_dependencies.init(sub_parser)
