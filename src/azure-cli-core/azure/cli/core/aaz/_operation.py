from azure.core.exceptions import ClientAuthenticationError, HttpResponseError, ResourceExistsError, \
    ResourceNotFoundError, map_error
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

    @property
    def url(self):
        return None

    @property
    def query_parameters(self):
        return {}

    @property
    def header_parameters(self):
        return {}

    @property
    def body(self):
        return None

    def __call__(self, *args, **kwargs):
        raise NotImplementedError()

    def map_error(self, status_code, response):
        if not self.error_map:
            return
        error_type = self.error_map.get(status_code)
        if not error_type:
            return
        error = error_type(response=response)
        raise error


class AAZInstanceUpdateOperation(AAZOperation):
    pass
