# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
from azure.cli.core.azclierror import RequiredArgumentMissingError


def validate_ip_rule(namespace):
    if not namespace.ip_rule:
        raise RequiredArgumentMissingError('IP rule should be set.')
