# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import runpy


def main():
    """Run the complete CLI module from the interpreter-bound Windows launcher."""
    runpy.run_module('azure.cli.__main__', run_name='__main__', alter_sys=True)
