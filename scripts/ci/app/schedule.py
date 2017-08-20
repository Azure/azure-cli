# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys


# REFERENCE:

# shared virtualenv                 AZ_BATCH_NODE_SHARED_DIR/venv/bin/activate
# batch account name                AZ_BATCH_ACCOUNT_NAME
# batch account key                 AZURE_BATCH_KEY
# batch account endpoint            AZURE_BATCH_ENDPOINT
# current job id                    AZ_BATCH_JOB_ID
# logging container url with SAS    AUTOMATION_OUTPUT_CONTAINER

# https://docs.microsoft.com/en-us/azure/batch/batch-compute-node-environment-variables

def create_batch_client():
    from azure.batch import BatchServiceClient
    from azure.batch.batch_auth import SharedKeyCredentials
    cred = SharedKeyCredentials(os.environ['AZ_BATCH_ACCOUNT_NAME'], os.environ['AZURE_BATCH_KEY'])
    return BatchServiceClient(cred, os.environ['AZURE_BATCH_ENDPOINT'])


def get_command_string(*args):
    return "/bin/bash -c 'set -e; set -o pipefail; {}; wait'".format(';'.join(args))


def get_output_log_list(test_id):
    from azure.batch.models import (OutputFile, OutputFileDestination, OutputFileBlobContainerDestination,
                                    OutputFileUploadOptions, OutputFileUploadCondition)

    build_container_url = os.environ['AUTOMATION_OUTPUT_CONTAINER']
    return [OutputFile('../std*.*',
                       OutputFileDestination(OutputFileBlobContainerDestination(build_container_url, test_id)),
                       OutputFileUploadOptions(OutputFileUploadCondition.task_completion))]


def main():
    from azure.batch.models import TaskAddParameter, BatchErrorException
    input_file = sys.argv[1]

    bs = create_batch_client()
    fail_to_schedule = []
    for index, line in enumerate(open(input_file, 'r')):
        try:
            test_class, test_method = line.split()
            commands = ['$AZ_BATCH_NODE_SHARED_DIR/app/run_test.sh {} {}'.format(test_class, test_method)]
            test_id = '{:04}{}'.format(index, test_method)[:64]
            bs.task.add(job_id=os.environ['AZ_BATCH_JOB_ID'],
                        task=TaskAddParameter(id=test_id,
                                              command_line=get_command_string(*commands),
                                              display_name='test {} ({})'.format(test_method, test_class),
                                              output_files=get_output_log_list(test_id)))
        except (BatchErrorException, ValueError):
            fail_to_schedule.append(line)

    if not fail_to_schedule:
        sys.exit(0)
    else:
        for line in fail_to_schedule:
            print('FAIL: {}'.format(line))
        sys.exit(1)


if __name__ == '__main__':
    main()
