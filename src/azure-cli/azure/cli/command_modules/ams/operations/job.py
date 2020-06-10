# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError

from azure.cli.command_modules.ams._utils import show_child_resource_not_found_message


def create_job(client, resource_group_name, account_name, transform_name, job_name,
               output_assets, input_asset_name=None,
               label=None, correlation_data=None,
               description=None, priority=None, files=None, base_uri=None):
    from azure.mgmt.media.models import (Job, JobInputAsset, JobInputHttp)

    if input_asset_name:
        job_input = JobInputAsset(asset_name=input_asset_name, files=files, label=label)
    else:
        if base_uri is not None and files is not None:
            job_input = JobInputHttp(files=files, base_uri=base_uri, label=label)
        else:
            raise CLIError("Missing required arguments.\nEither --input-asset-name, "
                           "or both --files or --base-uri must be specified.")

    job_outputs = output_assets

    job = Job(input=job_input, outputs=job_outputs, correlation_data=correlation_data,
              description=description, priority=priority)

    return client.create(resource_group_name, account_name, transform_name, job_name, job)


def update_job(instance, description=None, priority=None):
    if not instance:
        raise CLIError('The job resource was not found.')

    if description is not None:
        instance.description = description

    if priority is not None:
        instance.priority = priority

    return instance


def cancel_job(client, resource_group_name, account_name,
               transform_name, job_name, delete=False):
    cancel_result = client.cancel_job(resource_group_name, account_name,
                                      transform_name, job_name)

    if delete:
        return client.delete(resource_group_name, account_name,
                             transform_name, job_name)

    return cancel_result


def get_job(client, resource_group_name, account_name,
            transform_name, job_name):
    job = client.get(resource_group_name, account_name, transform_name, job_name)
    if not job:
        show_child_resource_not_found_message(
            resource_group_name, account_name, 'transforms', transform_name, 'jobs', job_name)

    return job
