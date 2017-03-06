# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


class RecordingProcessor(object):
    def process_request(self, request):
        return request

    def process_response(self, response):
        return response


class SubscriptionRecordingProcessor(RecordingProcessor):
    def __init__(self, replacement):
        self._replacement = replacement

    def process_request(self, request):
        request.uri = self._replace_subscription_id(request.uri)
        return request

    def process_response(self, response):
        try:
            raw = response['body']['string']
            response['body']['string'] = self._replace_subscription_id(raw)
            response['headers']['location'] = \
                [self._replace_subscription_id(l) for l in response['headers']['location']]
        except (KeyError, AttributeError):
            pass

        return response

    def _replace_subscription_id(self, val):
        import re
        return re.sub('/subscriptions/([^/]+)/',
                      '/subscriptions/{}/'.format(self._replacement),
                      val)


class OAuthRequestResponsesFilter(RecordingProcessor):
    """Remove oauth authentication requests and responses from recording."""
    def process_request(self, request):
        # filter request like:
        # GET https://login.microsoftonline.com/72f988bf-86f1-41af-91ab-2d7cd011db47/oauth2/token
        import re
        if not re.match('https://login.microsoftonline.com/([^/]+)/oauth2/token', request.uri):
            return request

    def process_response(self, response):
        import json
        try:
            body = json.loads(response['body']['string'])
            if 'token_type' in body and 'access_token' in body:
                return None
        except (KeyError, AttributeError, ValueError):
            pass

        return response


class GeneralNameReplacer(RecordingProcessor):
    def __init__(self):
        self.names_name = []

    def register_name_pair(self, old, new):
        self.names_name.append((old, new))

    def process_request(self, request):
        for old, new in self.names_name:
            try:
                request.uri = request.uri.replace(old, new)
            except (KeyError, AttributeError, TypeError):
                pass

            try:
                request.body = request.body.replace(old, new)
            except (KeyError, AttributeError, TypeError):
                pass

        return request

    def process_response(self, response):
        for old, new in self.names_name:
            try:
                response['body']['string'] = response['body']['string'].replace(old, new)
            except (KeyError, AttributeError, TypeError):
                pass

            self._replace_in_header(response, 'location', old, new)
            self._replace_in_header(response, 'azure-asyncoperation', old, new)

        return response

    @classmethod
    def _replace_in_header(cls, response, header_name, old, new):
        try:
            response['headers'][header_name] = \
                [l.replace(old, new) for l in response['headers'][header_name]]
        except (KeyError, AttributeError, TypeError):
            pass
