# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Generate CLITest.yml in ./
"""


import os

from jinja2 import Environment, FileSystemLoader

# If include extensions
EXTENSION = False


def main():
    env = Environment(loader=FileSystemLoader('/home/vsts/work/1/s/scripts/live_test/'))
    template = env.get_template('template.yml')
    config = {}
    config['modules'] = get_modules()
    result = template.render(config)
    with open('CLITest.yml', 'w') as f:
        f.write(result)


def get_modules():
    """
    :return: str[]
    """
    path = 'azure-cli/src/azure-cli/azure/cli/command_modules'
    modules = [m for m in os.listdir(path) if os.path.isdir(os.path.join(path, m))]
    if EXTENSION:
        path = 'azure-cli-extensions/src'
        modules.extend(m for m in os.listdir(path) if os.path.isdir(os.path.join(path, m)))
    return modules


if __name__ == '__main__':
    main()
