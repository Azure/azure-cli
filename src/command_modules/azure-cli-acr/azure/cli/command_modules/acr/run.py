# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError

import os
import tempfile

from .sdk.models import (
    FileTaskRunRequest,
    PlatformProperties,
    OS
)

from ._utils import validate_managed_registry

from ._client_factory import cf_acr_registries_build

RUN_NOT_SUPPORTED = 'Run is only available for managed registries.'

RUN_OS_NOT_SUPPORTED = 'Run is only supported on Linux'

from azure.cli.core.commands import LongRunningOperation

logger = get_logger(__name__)


def acr_run(cmd,
            client,
            registry_name,
            source_location,
            task_file_path,
            values_file_path,
            encoded_task_content,
            encoded_values_content,
            values,
            no_format=False,
            no_logs=False,
            timeout=None,
            resource_group_name=None,
            os_type=OS.linux):

    if os_type != OS.linux:
        raise CLIError(RUN_OS_NOT_SUPPORTED)
