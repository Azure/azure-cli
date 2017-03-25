# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# coding: utf-8
# pylint: skip-file
from msrest.serialization import Model


class ExportLabResourceUsageParameters(Model):
    """ExportLabResourceUsageParameters.

    :param blob_storage_absolute_sas_uri: The blob storage absolute sas uri
     with write permission to the container which the usage data needs to be
     uploaded to.
    :type blob_storage_absolute_sas_uri: str
    :param usage_start_date: The start time of the usage.
    :type usage_start_date: str
    """

    _attribute_map = {
        'blob_storage_absolute_sas_uri': {'key': 'blobStorageAbsoluteSasUri', 'type': 'str'},
        'usage_start_date': {'key': 'usageStartDate', 'type': 'str'},
    }

    def __init__(self, blob_storage_absolute_sas_uri=None, usage_start_date=None):
        self.blob_storage_absolute_sas_uri = blob_storage_absolute_sas_uri
        self.usage_start_date = usage_start_date
