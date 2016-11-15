#!/usr/bin/env python

# common utilities for scripts

from __future__ import print_function


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

