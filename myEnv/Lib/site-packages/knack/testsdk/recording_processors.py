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


class LargeRequestBodyProcessor(RecordingProcessor):
    def __init__(self, max_request_body=128):
        self._max_request_body = max_request_body

    def process_request(self, request):
        if request.body and len(request.body) > self._max_request_body * 1024:
            request.body = '!!! The request body has been omitted from the recording because its ' \
                           'size {} is larger than {}KB. !!!'.format(len(request.body),
                                                                     self._max_request_body)

        return request


class LargeResponseBodyProcessor(RecordingProcessor):
    control_flag = '<CTRL-REPLACE>'

    def __init__(self, max_response_body=256):
        self._max_response_body = max_response_body

    def process_response(self, response):
        length = len(response['body']['string'] or '')
        if length > self._max_response_body * 1024:
            response['body']['string'] = \
                "!!! The response body has been omitted from the recording because it is larger " \
                "than {max} KB. It will be replaced with blank content of {length} bytes while replay. " \
                "{flag}{length}".format(max=self._max_response_body, length=length, flag=self.control_flag)

        return response


class LargeResponseBodyReplacer(RecordingProcessor):
    def process_response(self, response):
        import six
        body = response['body']['string']

        # backward compatibility. under 2.7 response body is unicode, under 3.5 response body is
        # bytes. when set the value back, the same type must be used.
        body_is_string = isinstance(body, six.string_types)

        content_in_string = (response['body']['string'] or b'').decode('utf-8')
        index = content_in_string.find(LargeResponseBodyProcessor.control_flag)

        if index > -1:
            length = int(content_in_string[index + len(LargeResponseBodyProcessor.control_flag):])
            if body_is_string:
                response['body']['string'] = '0' * length
            else:
                response['body']['string'] = bytes([0] * length)

        return response


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

        return response
