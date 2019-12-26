# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure_devtools.scenario_tests import RecordingProcessor


class TimeSpanProcessor(RecordingProcessor):
    def __init__(self, replacement):
        self._replacement = replacement

    def process_request(self, request):
        request.uri = self._replace_timespan(request.uri)

        return request

    def _replace_timespan(self, val):
        import re
        # subscription presents in all api call
        retval = re.sub('timespan=((.*?)(&|$))',
                        r'timespan={}\3'.format(self._replacement),
                        val,
                        flags=re.IGNORECASE)
        return retval


class DataSourceProcessor(RecordingProcessor):
    def __init__(self):
        self.test_guid_count = 0

    def process_request(self, request):
        request.uri = self._replace_data_source(request.uri)

        return request

    def _replace_data_source(self, val):
        import re
        self.test_guid_count += 1
        moniker = '88888888-0000-0000-0000-00000000' + ("%0.4X" % self.test_guid_count)
        retval = re.sub('DataSource_(.*?)_([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})',
                        r'DataSource_\1_{}'.format(moniker),
                        val,
                        flags=re.IGNORECASE)
        return retval
