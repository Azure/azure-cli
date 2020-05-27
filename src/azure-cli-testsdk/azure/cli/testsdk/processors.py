# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure_devtools.scenario_tests import RecordingProcessor
from azure_devtools.scenario_tests.utilities import is_text_payload


class SubscriptionRecordingProcessor(RecordingProcessor):
    """
    This processor supports multiple subscriptions
    """

    def __init__(self, test_instance):
        self.test_instance = test_instance
        if not hasattr(test_instance, 'subs_count'):
            # Mapping between real subscription and moniker
            test_instance.subs_map = {}

    def process_request(self, request):
        request.uri = self._replace_subscription_id(request.uri, True)

        if is_text_payload(request) and request.body:
            request.body = self._replace_subscription_id(request.body.decode(), True).encode()

        return request

    def process_response(self, response):
        if is_text_payload(response) and response['body']['string']:
            response['body']['string'] = self._replace_subscription_id(response['body']['string'])

        self.replace_header_fn(response, 'location', self._replace_subscription_id)
        self.replace_header_fn(response, 'azure-asyncoperation', self._replace_subscription_id)

        return response

    def _replace_subscription_id(self, val, request=None):
        import re

        subs_map = self.test_instance.subs_map

        if request:
            pattern = '/subscriptions/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
            subs = re.findall(pattern, val)
            pattern = 'https://graph.windows.net/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
            subs.extend(re.findall(pattern, val))
            for sub in subs:
                if sub not in subs_map and sub.count('0') < 20:
                    size = len(subs_map)
                    moniker = sub[:-36] + '00000000-0000-0000-0000-' + '%012d' % size
                    subs_map[sub] = moniker

        for sub in subs_map:
            val = val.replace(sub, subs_map[sub])

        return val

        # subscription presents in all api call
        retval = re.sub('/(subscriptions)/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
                        r'/\1/{}'.format(self._replacement),
                        val,
                        flags=re.IGNORECASE)

        # subscription is also used in graph call
        retval = re.sub('https://(graph.windows.net)/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
                        r'https://\1/{}'.format(self._replacement),
                        retval,
                        flags=re.IGNORECASE)
        return retval