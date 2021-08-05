#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# common utilities for scripts

def get_repo_root():
    """
    Returns the root path to this repository. The root is where .git folder is.
    """
    import os.path
    here = os.path.dirname(os.path.realpath(__file__))

    while not os.path.exists(os.path.join(here, '.git')):
        here = os.path.dirname(here)

    return here


if __name__ == '__main__':
    print(get_repo_root())

