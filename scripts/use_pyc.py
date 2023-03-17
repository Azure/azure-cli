# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import logging
import glob
import os
import platform
import re
import sys
from pathlib import Path
import shutil

_LOGGER = logging.getLogger(__name__)


def calculate_folder_size(start_path):
    """Calculate total size of a folder and file count."""
    # https://stackoverflow.com/questions/1392413/calculating-a-directorys-size-using-python
    total_size = 0
    total_count = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_count += 1
                total_size += os.path.getsize(fp)

    return total_size, total_count


def _print_folder_size(folder):
    size, count = calculate_folder_size(folder)
    size_in_mb = size / 1048576  # 1 MB = 1024 * 1024 B = 1048576 B
    _LOGGER.info(f"{size_in_mb:.2f} MB, {count} files")


def main(folder, version=None):
    _LOGGER.info(f'Replace .py with .pyc, base folder: {folder}')
    _print_folder_size(folder)
    if version is None:
        version = re.search(r'python(\d\.\d+)', folder).group(1)
    else:
        # 3.10.10
        version = '.'.join(version.split('.')[:2])
    # invoke==1.2.0 has a weird file: invoke/completion/__pycache__/__init__.cpython-36.pyc
    # define pyc suffix to skip it
    pyc_suffix = f'cpython-{version.replace(".", "")}.pyc'
    _LOGGER.info(f'pyc suffix: {pyc_suffix}')
    for file in glob.glob(f'{folder}/**/__pycache__/*{pyc_suffix}', recursive=True):
        # If pip's py files are also removed, the following error will occur when use pip install.
        # For example: /opt/az/bin/python3 -m pip install --no-cache  pgcli==3.4.1
        #   × pip subprocess to install build dependencies did not run successfully.
        #   │ exit code: 2
        #   ╰─> [1 lines of output]
        #       /opt/az/bin/python3: can't open file '/opt/az/lib/python3.10/site-packages/pip/__pip-runner__.py': [Errno 2] No such file or directory
        #       [end of output]
        #
        #   note: This error originates from a subprocess, and is likely not a problem with pip.
        # error: subprocess-exited-with-error
        if 'site-packages/pip' in file:
            continue

        # file is /opt/az/lib/python3.10/site-packages/websocket/__pycache__/_app.cpython-310.pyc
        # py_filename is _app.py
        py_filename = Path(file).name[:-len('cpython-310.pyc')] + 'py'
        # py_path is /opt/az/lib/python3.10/site-packages/websocket/_app.py
        py_path = Path(file).parent.parent / py_filename
        if py_path.exists():
            py_path.unlink()
            shutil.move(file, py_path.with_suffix('.pyc'))

    for f in glob.glob(f'{folder}/**/__pycache__', recursive=True):
        # Remove pip __pycache__ folder for Windows only to save more space
        if 'site-packages/pip' in f and not platform.system() == 'Windows':
            continue
        shutil.rmtree(f)

    _LOGGER.info('Finish processing')
    _print_folder_size(folder)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        main(sys.argv[1], sys.argv[2])
