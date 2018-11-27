# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import zipfile
import requests

from knack.util import CLIError


class BotPublishPrep:

    @staticmethod
    def create_upload_zip(logger, code_dir, include_node_modules=True):
        file_excludes = ['upload.zip', 'db.lock', '.env']
        folder_excludes = ['packages', 'bin', 'obj']

        logger.info('Creating upload zip file, code directory %s.', code_dir)

        if not include_node_modules:

            logger.info('Adding node_modules to folders to exclude from zip file.')
            folder_excludes.append('node_modules')

        zip_filepath = os.path.abspath('upload.zip')
        logger.info('Compressing bot source into %s.', zip_filepath)

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
    def prepare_publish_v4(logger, code_dir, proj_file):
        save_cwd = os.getcwd()
        os.chdir(code_dir)

        logger.info('Preparing Bot Builder SDK v4 bot for publish, with code directory %s and project file %s.',
                    code_dir, proj_file or '')

        try:
            if not os.path.exists(os.path.join('.', 'package.json')):

                logger.info('Detected bot language C#, Bot Builder version v4.')

                if proj_file is None:
                    raise CLIError('Expected --proj-file argument provided with the full path to the '
                                   'bot csproj file for csharp bot with Bot Builder SDK v4 project.')
                with open('.deployment', 'w') as f:
                    f.write('[config]\n')
                    proj_file = proj_file.lower()
                    proj_file = proj_file if proj_file.endswith('.csproj') else proj_file + '.csproj'
                    f.write('SCM_SCRIPT_GENERATOR_ARGS=--aspNetCore {0}\n'
                            .format(BotPublishPrep.__find_proj(proj_file)))

            else:

                logger.info('Detected bot language Node, Bot Builder version v4.')

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

    @staticmethod
    def __find_proj(proj_file):
        for root, _, files in os.walk(os.curdir):
            for file_name in files:
                if proj_file == file_name.lower():
                    return os.path.relpath(os.path.join(root, file_name))
        raise CLIError('project file not found. Please pass a valid --proj-file.')
