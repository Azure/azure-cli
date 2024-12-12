# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from knack.log import get_logger

from azure.cli.core.azclierror import RequiredArgumentMissingError
from ._util import import_aaz_by_profile
from azure.cli.core.aaz import has_value

logger = get_logger(__name__)

_Sig = import_aaz_by_profile("sig")

