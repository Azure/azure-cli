# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-few-public-methods, protected-access

import json

from azure.core.exceptions import ClientAuthenticationError, ResourceExistsError, ResourceNotFoundError, \
    HttpResponseError

from ._arg_browser import AAZArgBrowser
from ._base import AAZUndefined, AAZBaseValue, AAZBaseType
from ._content_builder import AAZContentBuilder
from ._field_type import AAZSimpleType, AAZObjectType, AAZDictType, AAZListType

try:
    from urllib import quote  # type: ignore
except ImportError:
    from urllib.parse import quote  # type: ignore


class AAZOperation:

    def __init__(self, ctx):
        self.ctx = ctx


class AAZHttpOperation(AAZOperation):
    """ Http Operation
    """

    CLIENT_TYPE = None  # http client registered, its value should be in the keys of aaz._client.registered_clients

    def __init__(self, ctx):
        super().__init__(ctx)
        self.client = ctx.get_http_client(self.CLIENT_TYPE)
        # common http errors by status code
        self.error_map = {
            401: ClientAuthenticationError,
            404: ResourceNotFoundError,
            409: ResourceExistsError,
        }

    def __call__(self, *args, **kwargs):
        raise NotImplementedError()

    @staticmethod
    def serialize_url_param(name, value, required=True, skip_quote=False, **kwargs):  # pylint: disable=unused-argument
        if isinstance(value, AAZBaseValue):
            value = value.to_serialized_data()

        if value == AAZUndefined or value == None:  # noqa: E711, pylint: disable=singleton-comparison
            if required:
                raise ValueError(f"url parameter {name} is required.")
            return {}  # return empty dict

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
        if isinstance(value, AAZBaseValue):
            value = value.to_serialized_data()

        if value == AAZUndefined:
            if required:
                raise ValueError(f"query parameter {name} is required.")
            return {}

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
                     for v in value if v != AAZUndefined]
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
    def serialize_header_param(name, value, required=False, **kwargs):  # pylint: disable=unused-argument
        if isinstance(value, AAZBaseValue):
            value = value.to_serialized_data()

        if value == AAZUndefined:
            if required:
                raise ValueError(f"query parameter {name} is required.")
            return {}

        def process_element(e):
            if isinstance(e, (list, dict)):
                raise NotImplementedError(f"Not support {type(e)} type element")

            if isinstance(e, bool):
                e = json.dumps(e)
            elif e is None:
                e = ""
            return e

        if isinstance(value, list):
            value = [process_element(v) for v in value if v != AAZUndefined]
        else:
            value = process_element(value)
        value = str(value)
        return {name: value}

    @staticmethod
    def serialize_content(value, required=False):

        def processor(schema, result):
            if schema._flags.get('read_only', False):
                # ignore read_only fields when serialize content
                return AAZUndefined
            if result == AAZUndefined or result is None:
                return result

            if isinstance(schema, AAZObjectType):
                assert isinstance(result, dict)
                for _schema in [schema, schema.get_discriminator(result)]:
                    if not _schema:
                        continue
                    for _field_name, _field_schema in _schema._fields.items():
                        # verify required and not read only property
                        _name = _field_schema._serialized_name or _field_name  # prefer using serialized name first
                        if _name in result:
                            continue
                        if _field_schema._flags.get('read_only', False):
                            continue
                        if not _field_schema._flags.get('required', False):
                            continue

                        if isinstance(_field_schema, AAZObjectType):
                            # use an empty dict as data for required object property, and process it's sub properties
                            _field_result = processor(_field_schema, {})
                            assert _field_result != AAZUndefined
                            result[_name] = _field_result
                        elif isinstance(_field_schema, AAZDictType):
                            # use an empty dict for required dict property
                            result[_name] = {}
                        elif isinstance(_field_schema, AAZListType):
                            # use an empty dict for required list property
                            result[_name] = []
                        else:
                            raise ValueError(f"Missing a required field in request content: {_name}")

            return result

        if isinstance(value, AAZBaseValue):
            data = value.to_serialized_data(processor=processor)
            flags = value._schema._flags
            required = required or flags.get('required', False) and not flags.get('read_only', False)
            if data == AAZUndefined and required:
                if isinstance(value._schema, AAZObjectType):
                    # use an empty dict as data for required object, and process it's properties
                    data = processor(value._schema, {})
                    assert data != AAZUndefined
                elif isinstance(value._schema, AAZDictType):
                    # use an empty dict for required dict
                    data = {}
                elif isinstance(value._schema, AAZListType):
                    # use an empty list for required list
                    data = []
                else:
                    raise ValueError("Missing request content")
        else:
            data = value

        if data == AAZUndefined or data == None:  # noqa: E711, pylint: disable=singleton-comparison
            if required:
                raise ValueError("Missing request content")
            return None
        return data

    @staticmethod
    def deserialize_http_content(session):
        from azure.core.pipeline.policies import ContentDecodePolicy
        if ContentDecodePolicy.CONTEXT_NAME in session.context:
            return session.context[ContentDecodePolicy.CONTEXT_NAME]
        if session.context.options['stream']:
            # Cannot handle stream response now
            raise NotImplementedError()
        raise ValueError("This pipeline didn't have the ContentDecode Policy; can't deserialize")

    @staticmethod
    def new_content_builder(arg_value, value=None, typ=None, typ_kwargs=None):
        """ Create a Content Builder
        """
        assert isinstance(arg_value, AAZBaseValue)
        arg_data = arg_value.to_serialized_data(keep_undefined_in_list=True)
        if value is None:
            assert issubclass(typ, AAZBaseType)
            schema = typ(**typ_kwargs) if typ_kwargs else typ()

            if isinstance(schema, AAZSimpleType):
                value = typ._ValueCls(
                    schema=schema,
                    data=schema.process_data(arg_data)
                )
            else:
                value = typ._ValueCls(
                    schema=schema,
                    data=schema.process_data(None)
                )
        else:
            assert isinstance(value, AAZBaseValue), f"Unknown value type: {type(value)}"

        builder = AAZContentBuilder(
            values=[value],
            args=[AAZArgBrowser(arg_value=arg_value, arg_data=arg_data)]
        )
        return value, builder

    # properties

    @property
    def url(self):
        return None

    @property
    def method(self):
        return None

    @property
    def url_parameters(self):
        return {}

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
        # value should be in the keys of aaz._error_format.registered_error_formats
        return None

    def make_request(self):
        """ Make http request based on the properties.
        """
        if self.ctx.next_link:
            # support making request for next link
            request = self.client._request(
                "GET", self.ctx.next_link, {}, self.header_parameters,
                self.content, self.form_content, None)

        elif self.method in ("GET",):
            request = self.client._request(
                self.method, self.url, self.query_parameters, self.header_parameters,
                self.content, self.form_content, None)

        elif self.method in ("DELETE", "MERGE", "OPTIONS"):
            request = self.client._request(
                self.method, self.url, self.query_parameters, self.header_parameters,
                self.content, self.form_content, None)

        elif self.method in ("PUT", "POST", "HEAD", "PATCH",):
            request = self.client._request(
                self.method, self.url, self.query_parameters, self.header_parameters,
                self.content, self.form_content, self.stream_content)
        else:
            raise ValueError(f"Invalid request method {self.method}")
        return request

    def on_error(self, response):
        """ handle errors in response
        """
        # raise common http errors
        error_type = self.error_map.get(response.status_code)
        if error_type:
            raise error_type(response=response)
        # raise HttpResponseError
        error_format = self.ctx.get_error_format(self.error_format)
        raise HttpResponseError(response=response, error_format=error_format)


class AAZJsonInstanceUpdateOperation(AAZOperation):
    """ Instance Update Operation
    """

    def __call__(self, *args, **kwargs):
        raise NotImplementedError()

    @staticmethod
    def new_content_builder(arg_value, value=None, typ=None, typ_kwargs=None):
        """ Create a Content Builder
        """
        assert isinstance(arg_value, AAZBaseValue)
        arg_data = arg_value.to_serialized_data(keep_undefined_in_list=True)
        if value is None:
            assert issubclass(typ, AAZBaseType)
            schema = typ(**typ_kwargs) if typ_kwargs else typ()

            if isinstance(schema, AAZSimpleType):
                value = typ._ValueCls(
                    schema=schema,
                    data=schema.process_data(arg_data)
                )
            else:
                value = typ._ValueCls(
                    schema=schema,
                    data=schema.process_data(None)
                )
        else:
            assert isinstance(value, AAZBaseValue)

        builder = AAZContentBuilder(
            values=[value],
            args=[AAZArgBrowser(arg_value=arg_value, arg_data=arg_data)]
        )
        return value, builder


class AAZGenericInstanceUpdateOperation(AAZOperation):
    """ Generic Instance Update Operation
    """

    def __call__(self, *args, **kwargs):
        raise NotImplementedError()

    @staticmethod
    def _update_instance_by_generic(instance, args):  # pylint: disable=unused-argument
        # TODO: implement generic instance update
        return instance
