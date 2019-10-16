# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=no-name-in-module,import-error
from azure.mgmt.containerservice.v2019_08_01.models import ManagedClusterAPIServerAccessProfile


def _populate_api_server_access_profile(api_server_authorized_ip_ranges):
    access_profile = None
    if api_server_authorized_ip_ranges:
        access_profile = ManagedClusterAPIServerAccessProfile(
            authorized_ip_ranges=api_server_authorized_ip_ranges.split(",")
        )
    return access_profile
