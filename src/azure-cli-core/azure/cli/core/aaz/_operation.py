# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-few-public-methods, protected-access, too-many-nested-blocks, too-many-branches

from urllib.parse import parse_qs, urljoin, urlparse, quote
import json

from azure.core.exceptions import ClientAuthenticationError, ResourceExistsError, ResourceNotFoundError, \
    HttpResponseError
from azure.cli.core.azclierror import InvalidArgumentValueError

from ._arg_browser import AAZArgBrowser
from ._base import AAZUndefined, AAZBaseValue, AAZBaseType, has_value
from ._content_builder import AAZContentBuilder
from ._field_type import AAZSimpleType, AAZObjectType, AAZBaseDictType, AAZListType
from ._field_value import AAZList, AAZObject, AAZBaseDictValue
from .exceptions import AAZInvalidValueError


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
                        elif isinstance(_field_schema, AAZBaseDictType):
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
                elif isinstance(value._schema, AAZBaseDictType):
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
            _parsed_next_link = urlparse(self.ctx.next_link)
            _next_request_params = {
                key: [quote(v) for v in value]
                for key, value in parse_qs(_parsed_next_link.query).items()
            }
            request = self.client._request(
                "GET", urljoin(self.ctx.next_link, _parsed_next_link.path), _next_request_params,
                self.header_parameters, self.content, self.form_content, None)

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


class AAZJsonInstanceOperationHelper:

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
            assert isinstance(value, AAZBaseValue), f"Unknown value type: {type(value)}"

        builder = AAZContentBuilder(
            values=[value],
            args=[AAZArgBrowser(arg_value=arg_value, arg_data=arg_data)]
        )
        return value, builder


class AAZJsonInstanceUpdateOperation(AAZJsonInstanceOperationHelper, AAZOperation):
    """ Instance Update Operation
    """

    def __call__(self, *args, **kwargs):
        raise NotImplementedError()


class AAZJsonInstanceCreateOperation(AAZJsonInstanceOperationHelper, AAZOperation):
    """ Json Instance Create Operation
    """

    def __call__(self, *args, **kwargs):
        raise NotImplementedError()


class AAZJsonInstanceDeleteOperation(AAZJsonInstanceOperationHelper, AAZOperation):
    """ Json Instance Delete Operation
    """

    def __call__(self, *args, **kwargs):
        raise NotImplementedError()

    def _delete_instance(self, *args, **kwargs):  # pylint: disable=unused-argument, no-self-use
        return AAZUndefined


class AAZGenericInstanceUpdateOperation(AAZOperation):
    """ Generic Instance Update Operation
    """

    def __call__(self, *args, **kwargs):
        raise NotImplementedError()

    def _update_instance_by_generic(self, instance, generic_update_args, client_flatten=True):  # pylint: disable=unused-argument
        from azure.cli.core.commands.arm import add_usage, remove_usage, set_usage
        if not generic_update_args or not generic_update_args['actions']:
            return instance
        assert isinstance(instance, AAZBaseValue)

        force_string = generic_update_args.get('force_string', False)
        for action_name, values in generic_update_args['actions']:
            if action_name == "set":
                try:
                    for expression in values:
                        self._set_properties(instance, expression, force_string, client_flatten)
                except ValueError:
                    raise InvalidArgumentValueError('invalid syntax: {}'.format(set_usage))
            elif action_name == "add":
                try:
                    self._add_properties(instance, values, force_string, client_flatten)
                except ValueError:
                    raise InvalidArgumentValueError('invalid syntax: {}'.format(add_usage))
            elif action_name == "remove":
                try:
                    self._remove_properties(instance, values, client_flatten)
                except ValueError:
                    raise InvalidArgumentValueError('invalid syntax: {}'.format(remove_usage))
        return instance

    def _set_properties(self, instance, expression, force_string, flatten):
        from azure.cli.core.commands.arm import _split_key_value_pair, shell_safe_json_parse, index_or_filter_regex
        key, value = _split_key_value_pair(expression)

        if key is None or key.strip() == '':
            raise InvalidArgumentValueError('Empty key in --set. Correct syntax: --set KEY=VALUE [KEY=VALUE ...]')

        if not force_string:
            try:
                value = shell_safe_json_parse(value)
            except (ValueError, InvalidArgumentValueError):
                pass

        path = self._get_internal_path(key)
        name = path.pop()
        instance = self._find_property(instance, path, flatten)  # find the parent instance

        match = index_or_filter_regex.match(name)
        index_value = int(match.group(1)) if match else None
        try:
            if index_value is not None:
                # instance is AAZList or list
                if not isinstance(instance, (AAZList, list)):
                    raise TypeError()
                if len(instance) <= index_value:
                    raise IndexError()
                instance[index_value] = value
            else:
                # instance is in AAZObject or AAZDict or dict
                if isinstance(instance, AAZObject):
                    parent = self._get_property_parent(instance, name, flatten)
                    if parent is None:
                        raise AttributeError()
                    instance = parent
                instance[name] = value
        except AAZInvalidValueError as err:
            raise InvalidArgumentValueError(err)
        except IndexError:
            raise InvalidArgumentValueError('index {} doesn\'t exist on {}'.format(index_value, path[-1]))
        except (AttributeError, KeyError, TypeError):
            self._throw_and_show_options(instance, name, key.split('.'), flatten)

    def _add_properties(self, instance, argument_values, force_string, flatten):
        from azure.cli.core.commands.arm import shell_safe_json_parse
        # The first argument indicates the path to the collection to add to.
        argument_values = list(argument_values)
        list_attribute_path = self._get_internal_path(argument_values.pop(0))
        list_to_add_to = self._find_property(instance, list_attribute_path, flatten)

        if not isinstance(list_to_add_to, (AAZList, list)):
            raise ValueError()

        try:
            dict_entry = {}
            for argument in argument_values:
                if '=' in argument:
                    # consecutive key=value entries get added to the same dictionary
                    split_arg = argument.split('=', 1)
                    argument = split_arg[1]
                    # Didn't convert argument by shell_safe_json_parse here to keep consist with the behavior in arm.py
                    dict_entry[split_arg[0]] = argument
                else:
                    if dict_entry:
                        # if an argument is supplied that is not key=value, append any dictionary entry
                        # to the list and reset. A subsequent key=value pair will be added to another
                        # dictionary.
                        list_to_add_to.append(dict_entry)
                        dict_entry = {}

                    if not force_string:
                        # attempt to convert anything else to JSON and fallback to string if error
                        try:
                            argument = shell_safe_json_parse(argument)
                        except (ValueError, InvalidArgumentValueError):
                            pass
                    list_to_add_to.append(argument)

            # if only key=value pairs used, must check at the end to append the dictionary
            if dict_entry:
                list_to_add_to.append(dict_entry)
        except AAZInvalidValueError as err:
            raise InvalidArgumentValueError(err)

    def _remove_properties(self, instance, argument_values, flatten):
        # The first argument indicates the path to the collection to remove from.
        argument_values = list(argument_values) if isinstance(argument_values, list) else [argument_values]

        list_attribute_path = self._get_internal_path(argument_values.pop(0))
        list_index = None
        try:
            list_index = argument_values.pop(0)
        except IndexError:
            pass

        if not list_index:
            # parent is in AAZObject or AAZDict or dict
            property_val = self._find_property(instance, list_attribute_path, flatten)
            parent = self._find_property(instance, list_attribute_path[:-1], flatten)
            if isinstance(parent, (AAZObject, AAZBaseDictValue)):
                if isinstance(parent, AAZObject):
                    parent = self._get_property_parent(parent, list_attribute_path[-1], flatten)
                if isinstance(property_val, (AAZList, list)):
                    if has_value(property_val):
                        # keep consist with the behavior in arm.py
                        parent[list_attribute_path[-1]] = []
                else:
                    parent[list_attribute_path[-1]] = AAZUndefined
            elif isinstance(parent, dict):
                del parent[list_attribute_path[-1]]
            else:
                # other types
                raise ValueError()
        else:
            list_to_remove_from = self._find_property(instance, list_attribute_path, flatten)
            try:
                if isinstance(list_to_remove_from, AAZList):
                    del list_to_remove_from[int(list_index)]
                elif isinstance(list_to_remove_from, list):
                    list_to_remove_from.pop(int(list_index))
                else:
                    raise IndexError()
            except IndexError:
                raise InvalidArgumentValueError('index {} doesn\'t exist on {}'
                                                .format(list_index, list_attribute_path[-1]))

    def _find_property(self, instance, path, flatten):
        from azure.cli.core.commands.arm import index_or_filter_regex, shell_safe_json_parse
        try:
            for part in path:
                index = index_or_filter_regex.match(part)
                if index and not isinstance(instance, (AAZList, list)):
                    raise AttributeError()

                if index and '=' in index.group(1):
                    key, value = index.group(1).split('=', 1)
                    try:
                        value = shell_safe_json_parse(value)
                    except (ValueError, InvalidArgumentValueError):
                        pass
                    matches = []
                    for x in instance:
                        if isinstance(x, dict) and x.get(key, None) == value:
                            matches.append(x)
                        elif isinstance(x, (AAZObject, AAZBaseDictValue)):
                            parent = x
                            if isinstance(parent, AAZObject):
                                parent = self._get_property_parent(parent, key, flatten)
                                if parent is None:
                                    continue
                            if parent[key].to_serialized_data() == value:
                                matches.append(x)  # should append `x` instead of `parent`

                    if len(matches) > 1:
                        raise InvalidArgumentValueError(
                            "non-unique key '{}' found multiple matches on {}. Key must be unique."
                            .format(key, path[-2]))
                    if len(matches) == 0:
                        raise InvalidArgumentValueError(
                            "item with value '{}' doesn\'t exist for key '{}' on {}".format(value, key, path[-2]))

                    instance = matches[0]

                elif index:
                    try:
                        index_value = int(index.group(1))
                        if isinstance(instance, AAZList):
                            if len(instance) <= index_value:
                                raise IndexError()

                        instance = instance[index_value]
                    except IndexError:
                        raise InvalidArgumentValueError('index {} doesn\'t exist on {}'.format(index_value, path[-2]))

                elif isinstance(instance, (dict, AAZBaseDictValue, AAZObject)):
                    parent = instance
                    if isinstance(instance, AAZObject):
                        parent = self._get_property_parent(parent, part, flatten)
                        if parent is None:
                            raise AttributeError()
                    instance = parent[part]
                else:
                    raise AttributeError()

        except (AttributeError, KeyError):
            self._throw_and_show_options(instance, part, path, flatten)

        return instance

    @staticmethod
    def _get_internal_path(path):
        from azure.cli.core.commands.arm import _get_internal_path
        return _get_internal_path(path)

    def _get_property_parent(self, instance, prop_name, flatten):
        if not isinstance(instance, AAZObject):
            return None

        # prop_name in current instance
        if hasattr(instance, prop_name):
            sub_instance = instance[prop_name]
            if not flatten or not sub_instance._schema._flags.get('client_flatten', False):
                # flatten property should be ignored
                return instance

        if not flatten:
            return None

        for key in self._iter_aaz_object_keys(instance):
            sub_instance = instance[key]
            if sub_instance._schema._flags.get('client_flatten', False):
                sub_instance = self._get_property_parent(sub_instance, prop_name, flatten)
                if sub_instance is not None:
                    return sub_instance

        return None

    @staticmethod
    def _iter_aaz_object_keys(instance):
        if not isinstance(instance, AAZObject):
            return
        schemas = [instance._schema]
        disc_schema = instance._schema.get_discriminator(instance)
        if disc_schema is not None:
            schemas.append(disc_schema)
        for schema in schemas:
            yield from schema._fields

    def _throw_and_show_options(self, instance, part, path, flatten):
        parent = '.'.join(path[:-1]).replace('.[', '[')
        error_message = "Couldn't find '{}' in '{}'.".format(part, parent)
        if isinstance(instance, AAZObject):
            options = []
            for key in self._iter_aaz_object_keys(instance):
                sub_instance = instance[key]
                if flatten and sub_instance._schema._flags.get('client_flatten', False):
                    options.extend(self._iter_aaz_object_keys(sub_instance))
                else:
                    options.append(key)
            options = sorted(options)
            error_message = '{} Available options: {}'.format(error_message, options)
        elif isinstance(instance, (AAZBaseDictValue, dict)):
            options = sorted(instance.keys())
            error_message = '{} Available options: {}'.format(error_message, options)
        elif isinstance(instance, (list, AAZList)):
            options = "index into the collection '{}' with [<index>] or [<key=value>]".format(parent)
            error_message = '{} Available options: {}'.format(error_message, options)
        else:
            error_message = "{} '{}' does not support further indexing.".format(error_message, parent)
        raise InvalidArgumentValueError(error_message)
