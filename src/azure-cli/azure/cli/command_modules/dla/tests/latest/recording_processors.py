# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk.scenario_tests import RecordingProcessor, mock_in_unit_test


MOCK_JOB_ID = '00000000-0000-0000-0000-000000000000'


class JobIdReplacer(RecordingProcessor):

    """Replace the random job id with a fixed mock name."""
    def process_request(self, request):
        import re
        request.uri = re.sub('/Jobs/([^/?]+)', '/Jobs/{}'.format(MOCK_JOB_ID), request.uri)
        return request

    def process_response(self, response):
        if response['body']['string']:
            response['body']['string'] = self._replace_job_id(response['body']['string'])
        return response

    # pylint: disable=no-self-use
    def _replace_job_id(self, val):
        import re
        if 'jobId' in val:
            return re.sub(r'"jobId":"([^"]+)"', r'"jobId":"{}"'.format(MOCK_JOB_ID), val, flags=re.IGNORECASE)
        return val


def patch_uuid_str(unit_test):

    def _mock_get_uuid_str(*args, **kwargs):  # pylint: disable=unused-argument
        return MOCK_JOB_ID

    mock_in_unit_test(unit_test, 'azure.cli.command_modules.dla.custom._get_uuid_str', _mock_get_uuid_str)
