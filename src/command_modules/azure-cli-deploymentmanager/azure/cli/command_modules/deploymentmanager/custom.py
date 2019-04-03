# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError

from azure.mgmt.deploymentmanager.models import (SasAuthentication, ArtifactSource)

logger = get_logger(__name__)

allowed_c_family_sizes = ['c0', 'c1', 'c2', 'c3', 'c4', 'c5', 'c6']
allowed_p_family_sizes = ['p1', 'p2', 'p3', 'p4', 'p5']
wrong_vmsize_error = CLIError('Invalid VM size. Example for Valid values: '
                              'For Standard Sku : (C0, C1, C2, C3, C4, C5, C6), '
                              'for Premium Sku : (P1, P2, P3, P4, P5)')

# pylint: disable=unused-argument
def cli_artifact_source_create(
    cmd,
    client,
    resource_group_name,
    location,
    artifact_source_name,
    sas_uri,
    artifact_root=None,
    tags=None):
    pass