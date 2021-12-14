from azure.core.exceptions import ClientAuthenticationError, ResourceExistsError, \
    ResourceNotFoundError, HttpResponseError
from ._base import AAZUndefined, AAZBaseValue
import json

try:
    from urllib import quote  # type: ignore
except ImportError:
    from urllib.parse import quote  # type: ignore


class AAZOperation:

    def __init__(self, ctx):
        self.ctx = ctx


class AAZHttpOperation(AAZOperation):
    CLIENT_TYPE = None
    ERROR_FORMAT = None

    def __init__(self, ctx):
        super().__init__(ctx)
        self.client = ctx.get_http_client(self.CLIENT_TYPE)
        self.error_map = {
            401: ClientAuthenticationError,
            404: ResourceNotFoundError,
            409: ResourceExistsError,
        }

    @staticmethod
    def serialize_url_param(name, value, required=True, skip_quote=False, **kwargs):
        if value == AAZUndefined or value == None:
            if required:
                raise ValueError(f"url parameter {name} is required.")
            return {}

        if isinstance(value, AAZBaseValue):
            value = value.to_serialized_data()

        if isinstance(value, (list, dict)):
            raise NotImplementedError(f"not support type {type(value)} for url parameter")

        if isinstance(value, bool):
            value = json.dumps(value)

        if skip_quote is True:
            value = str(value)
        else:
            value = quote(str(value), safe='')

        return {name: value}

    @staticmethod
    def serialize_query_param(name, value, required=False, skip_quote=False, **kwargs):
        if value == AAZUndefined:
            if required:
                raise ValueError(f"query parameter {name} is required.")
            return {}

        if isinstance(value, AAZBaseValue):
            value = value.to_serialized_data()

        def process_element(e):
            if isinstance(e, (list, dict)):
                raise NotImplementedError(f"Not support {type(e)} type element")

            if isinstance(e, bool):
                e = json.dumps(e)
            elif e is None:
                e = ""

            if skip_quote is True:
                e = str(e)
            else:
                e = quote(str(e), safe='')
            return e

        if isinstance(value, list):
            value = [process_element(v)
                     for v in value]
            # Determines the format of the array. Possible formats are:
            #   csv - comma separated values 'foo,bar'
            #   ssv - space separated values 'foo bar'
            #   tsv - tab separated values 'foo\tbar'
            #   pipes - pipe separated values 'foo|bar'
            # default is csv format
            div = kwargs.get('div', ',')
            if div:
                value = div.join(value)
            value = str(value)
        else:
            # Not a list
            value = process_element(value)
        return {name: value}

    @staticmethod
    def serialize_header_param(name, value, required=False, **kwargs):
        if value == AAZUndefined:
            if required:
                raise ValueError(f"query parameter {name} is required.")
            return {}

        if isinstance(value, AAZBaseValue):
            value = value.to_serialized_data()

        def process_element(e):
            if isinstance(e, (list, dict)):
                raise NotImplementedError(f"Not support {type(e)} type element")

            if isinstance(e, bool):
                e = json.dumps(e)
            elif e is None:
                e = ""
            return e

        if isinstance(value, list):
            value = [process_element(v) for v in value]
        else:
            value = process_element(value)
        value = str(value)
        return {name: value}

    @staticmethod
    def deserialize_http_content(session):
        from azure.core.pipeline.policies import ContentDecodePolicy
        if ContentDecodePolicy.CONTEXT_NAME in session.context:
            return session.context[ContentDecodePolicy.CONTEXT_NAME]
        elif session.context.options['stream']:
            # Cannot handle stream response now
            raise NotImplementedError()
        else:
            raise ValueError("This pipeline didn't have the ContentDecode Policy; can't deserialize")

    @property
    def url(self):
        return None

    @property
    def method(self):
        return None

    @property
    def query_parameters(self):
        return {}

    @property
    def header_parameters(self):
        return {}

    @property
    def content(self):
        return None

    @property
    def form_content(self):
        return None

    @property
    def stream_content(self):
        return None

    @property
    def error_format(self):
        if self.ERROR_FORMAT:
            return self.ctx.get_error_format(self.ERROR_FORMAT)
        return None

    def make_request(self):
        if self.method in ("GET", "DELETE", "MERGE", "OPTIONS"):
            request = self.client._request(
                self.method, self.url, self.query_parameters, self.header_parameters,
                self.content, self.form_content, None)
        elif self.method in ("PUT", "POST", "HEAD", "PATCH", ):
            request = self.client._request(
                self.method, self.url, self.query_parameters, self.header_parameters,
                self.content, self.form_content, self.stream_content)
        else:
            raise ValueError(f"Invalid request method {self.method}")
        return request

    def __call__(self, *args, **kwargs):
        raise NotImplementedError()

    def on_error(self, session):
        response = session.http_response
        error_type = self.error_map.get(response.status_code)
        if error_type:
            raise error_type(response=response)
        raise HttpResponseError(response=response, error_format=self.error_format)


class AAZInstanceUpdateOperation(AAZOperation):
    pass
