# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


class RecordingProcessor(object):
    def process_request(self, request):  # pylint: disable=no-self-use
        return request

    def process_response(self, response):  # pylint: disable=no-self-use
        return response

    @classmethod
    def replace_header(cls, entity, header, old, new):
        cls.replace_header_fn(entity, header, lambda v: v.replace(old, new))

    @classmethod
    def replace_header_fn(cls, entity, header, replace_fn):
        try:
            header = header.lower()
            values = entity['headers'][header]
            entity['headers'][header] = [replace_fn(v) for v in values]
        except KeyError:
            pass


class SubscriptionRecordingProcessor(RecordingProcessor):
    def __init__(self, replacement):
        self._replacement = replacement

    def process_request(self, request):
        request.uri = self._replace_subscription_id(request.uri)
        return request

    def process_response(self, response):
        if response['body']['string']:
            response['body']['string'] = self._replace_subscription_id(response['body']['string'])

        self.replace_header_fn(response, 'location', self._replace_subscription_id)
        self.replace_header_fn(response, 'azure-asyncoperation', self._replace_subscription_id)

        return response

    def _replace_subscription_id(self, val):
        import re
        return re.sub('/subscriptions/([^/]+)/', '/subscriptions/{}/'.format(self._replacement),
                      val)


class OAuthRequestResponsesFilter(RecordingProcessor):
    """Remove oauth authentication requests and responses from recording."""

    def process_request(self, request):
        # filter request like:
        # GET https://login.microsoftonline.com/72f988bf-86f1-41af-91ab-2d7cd011db47/oauth2/token
        import re
        if not re.match('https://login.microsoftonline.com/([^/]+)/oauth2/token', request.uri):
            return request


class GeneralNameReplacer(RecordingProcessor):
    def __init__(self):
        self.names_name = []

    def register_name_pair(self, old, new):
        self.names_name.append((old, new))

    def process_request(self, request):
        for old, new in self.names_name:
            request.uri = request.uri.replace(old, new)

            if request.body:
                body = str(request.body)
                if old in body:
                    request.body = body.replace(old, new)

        return request

    def process_response(self, response):
        for old, new in self.names_name:
            if response['body']['string']:
                response['body']['string'] = response['body']['string'].replace(old, new)

            self.replace_header(response, 'location', old, new)
            self.replace_header(response, 'azure-asyncoperation', old, new)

        return response
