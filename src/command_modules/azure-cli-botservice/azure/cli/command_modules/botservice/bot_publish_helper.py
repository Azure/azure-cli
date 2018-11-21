# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import requests
import zipfile

from knack.util import CLIError


class BotPublishHelper:
    @staticmethod
    def create_upload_zip(code_dir, include_node_modules=True):
        file_excludes = ['upload.zip', 'db.lock', '.env']
        folder_excludes = ['packages', 'bin', 'obj']
        if not include_node_modules:
            folder_excludes.append('node_modules')
        zip_filepath = os.path.abspath('upload.zip')
        save_cwd = os.getcwd()
        os.chdir(code_dir)
        try:
            with zipfile.ZipFile(zip_filepath, 'w',
                                 compression=zipfile.ZIP_DEFLATED) as zf:
                path = os.path.normpath(os.curdir)
                for dirpath, dirnames, filenames in os.walk(os.curdir, topdown=True):
                    for item in folder_excludes:
                        if item in dirnames:
                            dirnames.remove(item)
                    for name in sorted(dirnames):
                        path = os.path.normpath(os.path.join(dirpath, name))
                        zf.write(path, path)
                    for name in filenames:
                        if name in file_excludes:
                            continue
                        path = os.path.normpath(os.path.join(dirpath, name))
                        if os.path.isfile(path):
                            zf.write(path, path)
        finally:
            os.chdir(save_cwd)
        return zip_filepath

    @staticmethod
    def find_proj(proj_file):
        for root, _, files in os.walk(os.curdir):
            for file_name in files:
                if proj_file == file_name.lower():
                    return os.path.relpath(os.path.join(root, file_name))
        raise CLIError('project file not found. Please pass a valid --proj-file.')

    @staticmethod
    def prepare_publish_v4(code_dir, proj_file):
        save_cwd = os.getcwd()
        os.chdir(code_dir)
        try:
            # TODO: Improve JS SDK detection logic, instead of only looking for package.json, look for botbuilder in package.json
            if not os.path.exists(os.path.join('.', 'package.json')):
                if proj_file is None:
                    raise CLIError('expected --proj-file parameter for csharp v4 project.')
                with open('.deployment', 'w') as f:
                    f.write('[config]\n')
                    proj_file = proj_file.lower()
                    proj_file = proj_file if proj_file.endswith('.csproj') else proj_file + '.csproj'
                    f.write('SCM_SCRIPT_GENERATOR_ARGS=--aspNetCore {0}\n'.format(BotPublishHelper.find_proj(proj_file)))

            else:
                # put iisnode.yml and web.config
                response = requests.get('https://icscratch.blob.core.windows.net/bot-packages/node_v4_publish.zip')
                with open('temp.zip', 'wb') as f:
                    f.write(response.content)

                zip_ref = zipfile.ZipFile('temp.zip')
                zip_ref.extractall()
                zip_ref.close()
                os.remove('temp.zip')
        finally:
            os.chdir(save_cwd)
