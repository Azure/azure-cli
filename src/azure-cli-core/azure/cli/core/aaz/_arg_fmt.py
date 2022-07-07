# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, too-few-public-methods

import abc
import re
import math

from knack.log import get_logger

from ._command_ctx import AAZCommandCtx
from ._field_type import AAZSimpleType
from ._field_value import AAZUndefined, AAZSimpleValue, AAZDict, AAZList, AAZObject
from .exceptions import AAZInvalidArgValueError

logger = get_logger(__name__)


class AAZBaseArgFormat:

    @abc.abstractmethod
    def __call__(self, ctx: AAZCommandCtx, value):
        raise NotImplementedError()


class AAZStrArgFormat(AAZBaseArgFormat):

    def __init__(self, pattern=None, max_length=None, min_length=None):
        self._pattern = pattern
        self._max_length = max_length
        self._min_length = min_length
        if self._pattern is not None:
            self._compiled_pattern = re.compile(pattern)
        else:
            self._compiled_pattern = None

    def __call__(self, ctx, value):
        assert isinstance(value, AAZSimpleValue)
        data = value._data
        if data == AAZUndefined or data is None or value._is_patch:
            return value

        assert isinstance(data, str)
        if self._min_length is not None and len(data) < self._min_length:
            raise AAZInvalidArgValueError(
                f"FormatError: '{data}' length is less than {self._min_length} ")
        if self._max_length is not None and len(data) > self._max_length:
            raise AAZInvalidArgValueError(
                f"FormatError: '{data}' length is greater than {self._min_length}")
        if self._pattern is not None and not self._compiled_pattern.fullmatch(data):
            raise AAZInvalidArgValueError(
                f"FormatError: '{data}' does not fully match regular expression pattern '{self._pattern}'")

        return value


class AAZIntArgFormat(AAZBaseArgFormat):

    def __init__(self, multiple_of=None, maximum=None, minimum=None):
        self._multiple_of = multiple_of
        self._maximum = maximum
        self._minimum = minimum

    def __call__(self, ctx, value):
        assert isinstance(value, AAZSimpleValue)
        data = value._data
        if data == AAZUndefined or data is None or value._is_patch:
            return value

        assert isinstance(data, int)
        if self._multiple_of is not None and data % self._multiple_of != 0:
            raise AAZInvalidArgValueError(
                f"FormatError: '{data}' is not multiple of {self._multiple_of}")
        if self._minimum is not None and data < self._minimum:
            raise AAZInvalidArgValueError(
                f"FormatError: '{data}' is less than {self._minimum}")
        if self._maximum is not None and data > self._maximum:
            raise AAZInvalidArgValueError(
                f"FormatError: '{data}' is greater than {self._maximum}")
        return value


class AAZFloatArgFormat(AAZBaseArgFormat):

    def __init__(self, multiple_of=None, maximum=None, exclusive_maximum=None, minimum=None, exclusive_minimum=None,
                 rel_tol=1e-09):
        self._multiple_of = multiple_of
        self._maximum = maximum
        self._minimum = minimum
        self._exclusive_maximum = exclusive_maximum
        self._exclusive_minimum = exclusive_minimum
        self._rel_tol = rel_tol

    def __call__(self, ctx, value):
        assert isinstance(value, AAZSimpleValue)
        data = value._data
        if data == AAZUndefined or data is None or value._is_patch:
            return value

        assert isinstance(data, float)

        if self._multiple_of is not None:
            q = int(data / self._multiple_of)
            if not math.isclose(data, q * self._multiple_of, rel_tol=self._rel_tol) and \
                    not math.isclose(data, (q + 1) * self._multiple_of, rel_tol=self._rel_tol):
                raise AAZInvalidArgValueError(
                    f"FormatError: '{data}' is not multiple of {self._multiple_of}")

        if self._minimum is not None:
            if math.isclose(data, self._minimum, rel_tol=self._rel_tol):
                data = self._minimum

            if self._exclusive_minimum:
                if data <= self._minimum:
                    raise AAZInvalidArgValueError(
                        f"FormatError: '{data}' is not greater than {self._minimum}")
            elif data < self._minimum:
                raise AAZInvalidArgValueError(
                    f"FormatError: '{data}' is less than {self._minimum}")

        if self._maximum is not None:
            if math.isclose(data, self._maximum, rel_tol=self._rel_tol):
                data = self._maximum

            if self._exclusive_maximum:
                if data >= self._maximum:
                    raise AAZInvalidArgValueError(
                        f"FormatError: '{data}' is not less than {self._maximum}")
            elif data > self._maximum:
                raise AAZInvalidArgValueError(
                    f"FormatError: '{data}' is greater than {self._maximum}")

        value._data = data
        return value


class AAZBoolArgFormat(AAZBaseArgFormat):

    def __init__(self, reverse=False):
        self._reverse = reverse  # reverse it's value

    def __call__(self, ctx, value):
        assert isinstance(value, AAZSimpleValue)
        data = value._data
        if data == AAZUndefined or data is None or value._is_patch:
            return value

        assert isinstance(data, bool)
        if self._reverse:
            data = not data

        value._data = data
        return value


class AAZObjectArgFormat(AAZBaseArgFormat):

    def __init__(self, max_properties=None, min_properties=None):
        self._max_properties = max_properties
        self._min_properties = min_properties

    def __call__(self, ctx, value):
        assert isinstance(value, AAZObject)
        data = value._data
        if data == AAZUndefined or data is None:
            return value

        assert isinstance(data, dict)

        # Because _fields of object schema is OrderedDict
        # aaz-dev should register arguments in order of their interdependence.
        for field_name, field_schema in value._schema._fields.items():
            if not field_schema._fmt:
                continue
            if field_name in data:
                try:
                    value[field_name] = field_schema._fmt(ctx, value[field_name])
                except AAZInvalidArgValueError as err:
                    err.indexes = [f'{field_name}', *err.indexes]
                    raise err from err
            else:
                # build AAZUndefined value and fmt it.
                v = field_schema._ValueCls(field_schema, AAZUndefined)
                try:
                    v = field_schema._fmt(ctx, v)
                except AAZInvalidArgValueError as err:
                    err.indexes = [f'{field_name}', *err.indexes]
                    raise err from err
                if v._data != AAZUndefined:
                    # when result has real data, assign it
                    value[field_name] = v

        if value._is_patch:
            return value

        if self._min_properties and len(data) < self._min_properties:
            raise AAZInvalidArgValueError(
                f"FormatError: object length is less than {self._min_properties}")

        if self._max_properties and len(data) > self._max_properties:
            raise AAZInvalidArgValueError(
                f"FormatError: object length is greater than {self._max_properties}")

        return value


class AAZDictArgFormat(AAZBaseArgFormat):

    def __init__(self, max_properties=None, min_properties=None):
        self._max_properties = max_properties
        self._min_properties = min_properties

    def __call__(self, ctx, value):
        assert isinstance(value, AAZDict)
        data = value._data
        if data == AAZUndefined or data is None:
            return value

        assert isinstance(data, dict)
        element_schema = value._schema.Element
        element_fmt = element_schema._fmt
        if element_fmt:
            for key in data:
                try:
                    value[key] = element_fmt(ctx, value[key])
                except AAZInvalidArgValueError as err:
                    err.indexes = [f'[{key}]', *err.indexes]
                    raise err from err

        if value._is_patch:
            return value

        if self._min_properties and len(value) < self._min_properties:
            raise AAZInvalidArgValueError(
                f"FormatError: dict length is less than {self._min_properties}")

        if self._max_properties and len(value) > self._max_properties:
            raise AAZInvalidArgValueError(
                f"FormatError: dict length is greater than {self._max_properties}")

        return value


class AAZListArgFormat(AAZBaseArgFormat):

    def __init__(self, unique=None, max_length=None, min_length=None):
        self._unique = unique
        self._max_length = max_length
        self._min_length = min_length

    def __call__(self, ctx, value):
        assert isinstance(value, AAZList)
        data = value._data
        if data == AAZUndefined or data is None:
            return value

        assert isinstance(data, dict)
        element_schema = value._schema.Element
        element_fmt = element_schema._fmt
        if element_fmt:
            for idx in data:
                try:
                    value[idx] = element_fmt(ctx, value[idx])
                except AAZInvalidArgValueError as err:
                    err.indexes = [f'[{idx}]', *err.indexes]
                    raise err from err

        if value._is_patch:
            return value

        if self._unique and isinstance(element_schema, AAZSimpleType):
            unique_elements = set()
            for idx in data:
                e = value[idx]
                if e._is_patch:
                    continue
                if e._data in unique_elements:
                    raise AAZInvalidArgValueError(
                        f"FormatError: '{e._data}' duplicate in list.",
                        indexes=[f'[{idx}]']
                    )
                unique_elements.add(e._data)

        if self._min_length is not None and len(value) < self._min_length:
            raise AAZInvalidArgValueError(
                f"FormatError: list length is less than {self._min_length} ")

        if self._max_length is not None and len(value) > self._max_length:
            raise AAZInvalidArgValueError(
                f"FormatError: list length is greater than {self._max_length}")

        return value


class AAZResourceLocationArgFormat(AAZBaseArgFormat):

    def __init__(self, resource_group_arg=None):
        self._resource_group_arg = resource_group_arg

    def __call__(self, ctx, value):
        from ._command_ctx import get_subscription_locations
        assert isinstance(value, AAZSimpleValue)

        data = value._data
        if data is None or value._is_patch:
            return value

        if data == AAZUndefined:
            data = self.get_location_from_resource_group(ctx)

        if data == AAZUndefined:
            return value

        assert isinstance(data, str)
        if ' ' in data:
            for location in get_subscription_locations(ctx):
                if location.display_name.lower() == data.lower():
                    # if display name is provided, attempt to convert to short form name
                    data = location.name
                    break

        value._data = data
        return value

    def get_location_from_resource_group(self, ctx):
        from ._command_ctx import get_resource_group_location

        if not self._resource_group_arg:
            return AAZUndefined

        rg_name = ctx.args[self._resource_group_arg].to_serialized_data()
        if rg_name == AAZUndefined:
            return AAZUndefined

        location = get_resource_group_location(ctx, rg_name)
        if location != AAZUndefined:
            logger.debug("using location '%s' from resource group '%s'",location, rg_name)

        return location


class AAZResourceIdArgFormat(AAZBaseArgFormat):

    class _Template:
        """
        Example template:
            /subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{vnet_name}/subnets/{}

        A template string is consisted of several segments joined by '/'.
        Placeholder segment is wrapped by '{}'.

        """

        def __init__(self, template):
            self._template = template
            self._segments = template.split('/')
            blank_placeholders = 0
            for segment in self._segments:
                if segment.startswith('{') != segment.endswith('}'):
                    raise ValueError(f"Invalid segment: {segment}")
                if segment == '{}':
                    blank_placeholders += 1

            # when there's only one '{}' in placeholder, user can only pass the value of that segment.
            self.support_name_segment_only = blank_placeholders == 1

        def __call__(self, ctx, data):
            data_segments = data.split('/')
            if len(data_segments) != len(self._segments) and len(data_segments) == 1 and self.support_name_segment_only:
                # build resource_id by template
                data_segments = []
                for segment in self._segments:
                    if segment == '{}':
                        data_segments.append(data)
                    elif segment.startswith('{'):
                        # use argument value
                        arg_name = segment[1:-1]
                        if arg_name == 'subscription':
                            arg_data = ctx.subscription_id
                        else:
                            arg_data = ctx.args[arg_name].to_serialized_data()

                        if arg_data == AAZUndefined or arg_data is None:
                            raise AAZInvalidArgValueError(
                                f"FormatError: Failed to construct resource id: argument '{arg_name}' is not defined")
                        if not isinstance(arg_data, str):
                            raise AAZInvalidArgValueError(
                                f"FormatError: Failed to construct resource id: argument '{arg_name}' is not string")

                        data_segments.append(arg_data)
                    else:
                        data_segments.append(segment)
                data = '/'.join(data_segments)
                # return data

            # verify resource id
            if len(data_segments) != len(self._segments):
                raise AAZInvalidArgValueError(
                    f"FormatError: resource id should be in '{self._template}' format."
                )
            for data_segment, segment in zip(data_segments, self._segments):
                if not segment.startswith('{') and data_segment.lower() != segment.lower():
                    raise AAZInvalidArgValueError(
                        f"FormatError: resource id should be in '{self._template}' format."
                    )

            return data

    def __init__(self, template=None):
        """

        :param template: template property is used to verify a resource Id or construct resource Id.
        """
        self._template = None
        if template:
            self._template = self._Template(template)

    def __call__(self, ctx, value):
        from azure.mgmt.core.tools import parse_resource_id

        assert isinstance(value, AAZSimpleValue)

        data = value._data
        if data == AAZUndefined or data is None or value._is_patch:
            return value

        if self._template:
            data = self._template(ctx, data)

        parsed_id = parse_resource_id(data)
        subscription_id = parsed_id.get('subscription', None)
        if subscription_id:
            # update subscription_id to support cross tenants
            ctx.update_aux_subscriptions(subscription_id)

        value._data = data
        return value


class AAZSubscriptionIdArgFormat(AAZBaseArgFormat):

    def __call__(self, ctx, value):
        assert isinstance(value, AAZSimpleValue)

        data = value._data
        if data == AAZUndefined or data is None or value._is_patch:
            return value

        assert isinstance(data, str)
        # convert subscription name to id
        subscriptions_list = ctx.profile.load_cached_subscriptions()
        sub_id = None
        match_val = data.lower()
        for sub in subscriptions_list:
            # match by id
            if sub['id'].lower() == match_val:
                sub_id = sub['id']
                break
        if not sub_id:
            for sub in subscriptions_list:
                # match by name
                if sub['name'].lower() == match_val:
                    sub_id = sub['id']
                    break
        if sub_id:
            ctx.update_aux_subscriptions(sub_id)
            value._data = sub_id
        else:
            logger.warning("Subscription '%s' not recognized.", value._data)
        return value
