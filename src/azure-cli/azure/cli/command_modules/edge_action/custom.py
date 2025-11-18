# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines
# pylint: disable=too-many-statements

import base64
import os
import zipfile
import tempfile
from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.aaz import AAZStrArg, has_value, register_command
from azure.cli.command_modules.edge_action.aaz.latest.edge_action.version._deploy_version_code import (
    DeployVersionCode as _DeployVersionCode
)


logger = get_logger(__name__)


@register_command(
    "edge-action version deploy-version-code",
)
class EdgeActionVersionDeployFromFile(_DeployVersionCode):
    """Deploy Edge Action version code from file or base64 content"""

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        # Add file-based arguments
        args_schema.file_path = AAZStrArg(
            options=['--file-path'],
            help='Path to the file or directory to deploy. Mutually exclusive with --content.',
            required=False,
        )
        args_schema.file_type = AAZStrArg(
            options=['--file-type'],
            help='Type of file deployment: "zip" (compress if needed) or "file" (deploy as-is). Default is "file".',
            required=False,
        )

        # Make content and name optional when file-path is provided
        args_schema.content._required = False  # pylint: disable=protected-access
        args_schema.name._required = False  # pylint: disable=protected-access

        return args_schema

    def pre_operations(self):
        args = self.ctx.args

        # Validation: Either content or file-path must be provided
        if not has_value(args.content) and not has_value(args.file_path):
            raise CLIError('Either --content or --file-path must be provided.')

        if has_value(args.content) and has_value(args.file_path):
            raise CLIError('Cannot specify both --content and --file-path. Use one or the other.')

        # If using file-path, process the file
        if has_value(args.file_path):
            file_path = args.file_path.to_serialized_data()
            file_type = args.file_type.to_serialized_data() if has_value(args.file_type) else 'file'

            # Validate file type
            if file_type not in ['zip', 'file']:
                raise CLIError('--file-type must be either "zip" or "file".')

            # Check if file/directory exists
            if not os.path.exists(file_path):
                raise CLIError(f'File or directory not found: {file_path}')

            # Process based on file type
            if file_type == 'zip':
                content = self._process_zip_file(file_path)
            else:
                content = self._process_single_file(file_path)

            # Set content for API call
            args.content = content

            # Set name from version if not provided
            if not has_value(args.name):
                args.name = args.version.to_serialized_data()
                logger.info("--name not provided, using version name: %s", args.name)
        else:
            # Using --content mode, name is required
            if not has_value(args.name):
                raise CLIError('--name is required when using --content.')

    def _process_zip_file(self, file_path):
        """Process zip file - verify it's a zip or create one from file/directory"""
        if os.path.isfile(file_path) and zipfile.is_zipfile(file_path):
            # Already a zip file, just encode it
            logger.info("File is already a zip, encoding: %s", file_path)
            with open(file_path, 'rb') as f:
                zip_content = f.read()
        elif os.path.isfile(file_path):
            # Single file, create zip containing it
            logger.info("Creating zip from file: %s", file_path)
            zip_content = self._create_zip_from_file(file_path)
        elif os.path.isdir(file_path):
            # Directory, create zip from all contents
            logger.info("Creating zip from directory: %s", file_path)
            zip_content = self._create_zip_from_directory(file_path)
        else:
            raise CLIError(f'Invalid path: {file_path}')

        encoded = base64.b64encode(zip_content).decode('utf-8')
        logger.info("Zip file encoded to base64 (length: %d)", len(encoded))
        return encoded

    def _process_single_file(self, file_path):
        """Process single file - encode without zipping"""
        if os.path.isdir(file_path):
            raise CLIError(
                f'--file-type "file" cannot be used with directories: {file_path}\n'
                'Use --file-type "zip" to compress the directory first.'
            )

        if not os.path.isfile(file_path):
            raise CLIError(f'File not found: {file_path}')

        logger.info("Reading and encoding file: %s", file_path)
        with open(file_path, 'rb') as f:
            file_content = f.read()

        encoded = base64.b64encode(file_content).decode('utf-8')
        logger.info("File encoded to base64 (length: %d)", len(encoded))
        return encoded

    def _create_zip_from_file(self, file_path):
        """Create a zip file containing a single file"""
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')

        try:
            with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(file_path, os.path.basename(file_path))

            with open(temp_zip.name, 'rb') as f:
                zip_content = f.read()

            return zip_content
        finally:
            if os.path.exists(temp_zip.name):
                os.unlink(temp_zip.name)

    def _create_zip_from_directory(self, directory_path):
        """Create a zip file from all files in a directory"""
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')

        try:
            with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(directory_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, directory_path)
                        zipf.write(file_path, arcname)
                        logger.debug("Added to zip: %s", arcname)

            with open(temp_zip.name, 'rb') as f:
                zip_content = f.read()

            return zip_content
        finally:
            if os.path.exists(temp_zip.name):
                os.unlink(temp_zip.name)
