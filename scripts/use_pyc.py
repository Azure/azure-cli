# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import logging
import os
import re
import sys
import glob
from pathlib import Path
import shutil

_LOGGER = logging.getLogger(__name__)


def get_folder_size(folder):
    total_size = 0
    for path, dirs, files in os.walk(folder):
        for f in files:
            fp = os.path.join(path, f)
            total_size += os.path.getsize(fp)
    return total_size


def main(folder, version=None):
    _LOGGER.info(f'Replace .py with .pyc, base folder: {folder}')
    _LOGGER.info(f'Base folder size: {get_folder_size(folder)}')
    if version is None:
        version = re.search(r'python(\d\.\d+)', folder).group(1)
    else:
        # 3.10.10
        version = version.split('.')[:2].join('.')
    # invoke==1.2.0 has a weird file: invoke/completion/__pycache__/__init__.cpython-36.pyc
    # define pyc suffix to skip it
    pyc_suffix = f'cpython-{version.replace(".", "")}.pyc'
    _LOGGER.info(f'pyc suffix: {pyc_suffix}')
    for file in glob.glob(f'{folder}/**/__pycache__/*{pyc_suffix}.pyc', recursive=True):
        # file is /opt/az/lib/python3.10/site-packages/websocket/__pycache__/_app.cpython-310.pyc
        # py_filename is _app.py
        py_filename = Path(file).name[:-len('cpython-310.pyc')] + 'py'
        # py_path is /opt/az/lib/python3.10/site-packages/websocket/_app.py
        py_path = Path(file).parent.parent / py_filename
        if py_path.exists():
            py_path.unlink()
            shutil.move(file, py_path.with_suffix('.pyc'))

    for folder in glob.glob(f'{folder}/**/__pycache__', recursive=True):
        shutil.rmtree(folder)

    _LOGGER.info('Finish processing')
    _LOGGER.info(f'Base folder size: {get_folder_size(folder)}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        main(sys.argv[1], sys.argv[2])
