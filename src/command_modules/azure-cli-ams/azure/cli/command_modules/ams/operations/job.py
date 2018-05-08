# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError


def create_job(client, resource_group_name, account_name, transform_name, job_name,
               output_asset_names, input_asset_name=None,
               description=None, priority=None, files=None, base_uri=None):
    from azure.mgmt.media.models import (Job, JobInputAsset, JobInputHttp, JobOutputAsset)

    if input_asset_name:
        job_input = JobInputAsset(asset_name=input_asset_name, files=files)
    else:
        if base_uri is None and files is None:
            raise CLIError("Missing required arguments.\nEither --input-asset-name, "
                           "or both --files or --base-uri must be specified.")
        else:
            job_input = JobInputHttp(files=files, base_uri=base_uri)

    job_outputs = list(map(lambda x: JobOutputAsset(asset_name=x), output_asset_names))

    job = Job(input=job_input, outputs=job_outputs, description=description, priority=priority)

    return client.create(resource_group_name, account_name, transform_name, job_name, job)


def cancel_job(client, resource_group_name, account_name,
               transform_name, job_name, delete=False):
    cancel_result = client.cancel_job(resource_group_name, account_name,
                                      transform_name, job_name)

    if delete:
        return client.delete(resource_group_name, account_name,
                             transform_name, job_name)

    return cancel_result
