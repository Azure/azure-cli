# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import platform
import shutil
import tempfile


def get_test_data_file_path(filename):
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(curr_dir, "data", filename)


def create_kubelogin_zip(file_url, download_path):
    import zipfile

    try:
        cwd = os.getcwd()
        temp_dir = os.path.realpath(tempfile.mkdtemp())
        os.chdir(temp_dir)
        bin_dir = "bin"
        system = platform.system()
        if system == "Windows":
            bin_dir += "/windows_amd64"
        elif system == "Linux":
            bin_dir += "/linux_amd64"
        elif system == "Darwin":
            bin_dir += "/darwin_amd64"
        os.makedirs(bin_dir)
        bin_location = os.path.join(bin_dir, "kubelogin")
        open(bin_location, "a").close()
        with zipfile.ZipFile(download_path, "w", zipfile.ZIP_DEFLATED) as outZipFile:
            outZipFile.write(bin_location)
    finally:
        os.chdir(cwd)
        shutil.rmtree(temp_dir)
