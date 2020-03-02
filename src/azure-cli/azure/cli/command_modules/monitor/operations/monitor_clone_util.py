# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from .._client_factory import cf_monitor
from ..util import _gen_guid
from azure.cli.core.commands.transform import _parse_id
from knack.log import get_logger
from knack.util import CLIError
from msrestazure.tools import parse_resource_id

logger = get_logger(__name__)
CLONED_NAME = "cloned-{}-{}"

