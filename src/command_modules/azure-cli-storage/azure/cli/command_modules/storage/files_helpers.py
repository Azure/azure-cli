# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

""""
Define the utility methods which are used in blob and file upload command to deal with local file
system
"""


def glob_files_locally(folder_path, pattern):
    """glob files in local folder based on the given pattern"""
    import os.path
    from fnmatch import fnmatch
    pattern = os.path.join(folder_path, pattern.lstrip('/')) if pattern else None

    from os import walk
    len_folder_path = len(folder_path) + 1
    for root, _, files in walk(folder_path):
        for f in files:
            full_path = os.path.join(root, f)
            if pattern and fnmatch(full_path, pattern):
                yield (full_path, full_path[len_folder_path:])
            elif not pattern:
                yield (full_path, full_path[len_folder_path:])


def glob_files_remotely(client, share_name, pattern):
    """glob the files in remote file share based on the given pattern"""
    import os.path
    from fnmatch import fnmatch
    from collections import deque
    from azure.storage.file.models import Directory, File

    queue = deque([""])
    while len(queue) > 0:
        current_dir = queue.pop()
        for f in client.list_directories_and_files(share_name, current_dir):
            if isinstance(f, File):
                if (pattern and fnmatch(os.path.join(current_dir, f.name), pattern)) or \
                   (not pattern):
                    yield current_dir, f.name
            elif isinstance(f, Directory):
                queue.appendleft(os.path.join(current_dir, f.name))


def mkdir_p(path):
    import errno
    import os
    try:
        os.makedirs(path)
    except OSError as exc:  # Python <= 2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
