# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
from knack.util import CLIError


def get_blob_info(blob_sas_url):
    match = re.search((r"http(s)?://(?P<account_name>.*?)\.blob\.(?P<endpoint_suffix>.*?)/(?P<container_name>.*?)/"
                       r"(?P<blob_name>.*?)\?(?P<sas_token>.*)"), blob_sas_url)
    account_name = match.group('account_name')
    endpoint_suffix = match.group('endpoint_suffix')
    container_name = match.group('container_name')
    blob_name = match.group('blob_name')
    sas_token = match.group('sas_token')

    if not account_name or not container_name or not blob_name or not sas_token:
        raise CLIError("Failed to parse the SAS URL: '{!s}'.".format(blob_sas_url))

    return account_name, endpoint_suffix, container_name, blob_name, sas_token
