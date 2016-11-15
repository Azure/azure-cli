#!/usr/bin/env python

# Remove the UTF-8 BOM from all python files

from __future__ import print_function
from _common import get_repo_root

import codecs
import os

def remove_bom(file_path):
    file_size = os.path.getsize(file_path)
    if file_size < 32:
        return False

    content = None
    with open(file_path, 'rb') as f:
        first_32 = f.read(32)
        if not first_32.startswith(codecs.BOM_UTF8):
            return

        content = bytearray(first_32 + f.read(file_size))

    with open(file_path, 'wb') as f:
        f.write(content[len(codecs.BOM_UTF8):])


if __name__ == '__main__':
    repo_root = get_repo_root()
    for root, dirs, files in os.walk(repo_root):
        if root[len(repo_root):len(repo_root) + 5] == '/.git':
            continue

        for f in (os.path.join(root, f) for f in files if f[-3:] == '.py'):
            remove_bom(f)

