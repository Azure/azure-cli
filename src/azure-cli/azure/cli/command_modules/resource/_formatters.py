# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from itertools import groupby

from azure.mgmt.resource.resources.models import ChangeType, PropertyChangeType

from ._symbol import Symbol
from ._color import Color, ColoredStringBuilder
from ._utils import split_resource_id

_change_type_to_color = {
    ChangeType.create: Color.GREEN,
    ChangeType.delete: Color.ORANGE,
    ChangeType.modify: Color.PURPLE,
    ChangeType.deploy: Color.BLUE,
    ChangeType.no_change: Color.RESET,
    ChangeType.ignore: Color.GRAY,
}

_property_change_type_to_color = {
    PropertyChangeType.create: Color.GREEN,
    PropertyChangeType.delete: Color.ORANGE,
    PropertyChangeType.modify: Color.PURPLE,
    PropertyChangeType.array: Color.PURPLE,
}

_change_type_to_symbol = {
    ChangeType.create: Symbol.PLUS,
    ChangeType.delete: Symbol.MINUS,
    ChangeType.modify: Symbol.TILDE,
    ChangeType.deploy: Symbol.EXCLAMATION_POINT,
    ChangeType.no_change: Symbol.EQUAL,
    ChangeType.ignore: Symbol.ASTERISK,
}

_property_change_type_to_symbol = {
    PropertyChangeType.create: Symbol.PLUS,
    PropertyChangeType.delete: Symbol.MINUS,
    PropertyChangeType.modify: Symbol.TILDE,
    PropertyChangeType.array: Symbol.TILDE,
}

_change_type_to_weight = {
    ChangeType.delete: 0,
    ChangeType.create: 1,
    ChangeType.deploy: 2,
    ChangeType.modify: 3,
    ChangeType.no_change: 4,
    ChangeType.ignore: 5,
}

_property_change_type_to_weight = {
    PropertyChangeType.delete: 0,
    PropertyChangeType.create: 1,
    PropertyChangeType.modify: 2,
    PropertyChangeType.array: 2,
}


def format_what_if_operation_result(what_if_operation_result, enable_color=True):
    builder = ColoredStringBuilder(enable_color)
    _format_noise_notice(builder)
    _format_change_type_legend(builder, what_if_operation_result.changes)
    _format_resource_changes(builder, what_if_operation_result.changes)
    _format_resource_changes_stats(builder, what_if_operation_result.changes)
    return builder.build()


def _format_noise_notice(builder):
    builder.append_line(
        """Note: The result may contain false positive predictions (noise).
You can help us improve the accuracy of the result by opening an issue here: https://aka.ms/WhatIfIssues."""
    )
    builder.append_line()


def _format_change_type_legend(builder, resource_changes):
    if not resource_changes:
        return

    def populate_change_type_set(property_changes):
        if not property_changes:
            return

        for property_change in property_changes:
            property_change_type = property_change.property_change_type
            change_type_set.add(
                ChangeType.modify if property_change_type == PropertyChangeType.array else property_change_type
            )
            populate_change_type_set(property_change.children)

    change_type_set = set()

    for resource_change in resource_changes:
        change_type_set.add(resource_change.change_type)
        populate_change_type_set(resource_change.delta)

    change_types = sorted(change_type_set, key=lambda x: _change_type_to_weight[x])

    builder.append("Resource and property changes are indicated with ")
    builder.append_line("this symbol:" if len(change_types) == 1 else "these symbols:")

    for change_type in change_types:
        change_type_symbol = _change_type_to_symbol[change_type]
        change_type_color = _change_type_to_color[change_type]
        _format_indent(builder)
        builder.append(change_type_symbol, change_type_color).append(Symbol.WHITE_SPACE)
        builder.append_line(change_type.value.title())


def _format_resource_changes_stats(builder, resource_changes):
    builder.append_line().append("Resource changes: ")

    if not resource_changes:
        builder.append("no change.")
        return

    sorted_resource_changes = sorted(resource_changes, key=lambda x: _change_type_to_weight[x.change_type])
    resource_changes_by_change_type = groupby(sorted_resource_changes, lambda x: x.change_type)
    count_by_change_type = map(lambda x: (x[0], len(list(x[1]))), resource_changes_by_change_type)
    count_by_change_type = filter(lambda x: x[1] > 0, count_by_change_type)
    change_type_stats = map(lambda x: _format_change_type_count(x[0], x[1]), count_by_change_type)

    builder.append(", ".join(change_type_stats)).append(".")


def _format_change_type_count(change_type, count):
    if change_type == ChangeType.create:
        return f"{count} to create"
    if change_type == ChangeType.delete:
        return f"{count} to delete"
    if change_type == ChangeType.deploy:
        return f"{count} to deploy"
    if change_type == ChangeType.modify:
        return f"{count} to modify"
    if change_type == ChangeType.ignore:
        return f"{count} to ignore"
    if change_type == ChangeType.no_change:
        return f"{count} no change"

    raise ValueError(f"Invalid ChangeType: {change_type}")


def _format_resource_changes(builder, resource_changes):
    if not resource_changes:
        return

    num_scopes = len(set(map(_get_scope_uppercase, resource_changes)))
    resource_changes_by_scope = groupby(sorted(resource_changes, key=_get_scope_uppercase), _get_scope_uppercase)

    builder.append_line()
    builder.append_line(f"The deployment will update the following {'scope:' if num_scopes == 1 else 'scopes'}")

    for _, resource_changes_in_scope in resource_changes_by_scope:
        resource_changes_in_scope_list = list(resource_changes_in_scope)
        scope = _get_scope(resource_changes_in_scope_list[0])
        _format_resource_changes_in_scope(builder, scope, resource_changes_in_scope_list)


def _format_resource_changes_in_scope(builder, scope, resource_changes_in_scope):
    builder.append_line().append_line(f"Scope: {scope}")

    sorted_resource_changes = sorted(
        resource_changes_in_scope,
        # Sort by change_type and then by relative_resource_id.
        key=lambda x: (_change_type_to_weight[x.change_type], _get_relative_resource_id(x)),
    )

    for change_type, resource_changes in groupby(sorted_resource_changes, lambda x: x.change_type):
        with builder.new_color_scope(_change_type_to_color[change_type]):
            for resource_change in resource_changes:
                is_last = resource_change == sorted_resource_changes[-1]
                _format_resource_change(builder, resource_change, is_last)


def _format_resource_change(builder, resource_change, is_last):
    change_type = resource_change.change_type
    relative_resource_id = _get_relative_resource_id(resource_change)
    api_version = _get_api_version(resource_change)

    builder.append_line()
    _format_resource_change_path(builder, change_type, relative_resource_id, api_version)

    if change_type == ChangeType.create and resource_change.after:
        _format_json(builder, resource_change.after, indent_level=2)

    elif change_type == ChangeType.delete and resource_change.before:
        _format_json(builder, resource_change.before, indent_level=2)

    elif change_type == ChangeType.modify and resource_change.delta:
        with builder.new_color_scope(Color.RESET):
            builder.append_line()
            _format_property_changes(
                builder,
                sorted(
                    resource_change.delta,
                    key=lambda x: (_property_change_type_to_weight[x.property_change_type], x.path),
                ),
            )

    elif is_last:
        builder.append_line()


def _format_resource_change_path(builder, change_type, resource_change_id, api_version):
    return _format_path(
        builder,
        resource_change_id,
        0,
        1,
        lambda builder: _format_resource_change_type(builder, change_type),
        lambda builder: _format_resource_change_api_verion(builder, api_version),
    )


def _format_resource_change_type(builder, change_type):
    change_symbol = _change_type_to_symbol[change_type]
    builder.append(change_symbol).append(Symbol.WHITE_SPACE)


def _format_resource_change_api_verion(builder, api_version):
    if not api_version:
        return

    with builder.new_color_scope(Color.RESET):
        builder.append(Symbol.WHITE_SPACE)
        builder.append(Symbol.LEFT_SQUARE_BRACKET)
        builder.append(api_version)
        builder.append(Symbol.RIGHT_SQUARE_BRACKET)


def _format_property_changes(builder, property_changes, indent_level=2):
    max_path_length = _get_max_path_length_from_property_changes(property_changes)

    for property_change in property_changes:
        _format_property_change(builder, property_change, max_path_length, indent_level)
        builder.append_line()


def _format_property_change(builder, property_change, max_path_length, indent_level):
    property_change_type = property_change.property_change_type
    before, after, children = property_change.before, property_change.after, property_change.children

    if property_change_type == PropertyChangeType.create:
        _format_property_change_path(builder, property_change, "after", max_path_length, indent_level)
        _format_property_create(builder, after, indent_level + 1)
    elif property_change_type == PropertyChangeType.delete:
        _format_property_change_path(builder, property_change, "before", max_path_length, indent_level)
        _format_property_delete(builder, before, indent_level + 1)
    elif property_change_type == PropertyChangeType.modify:
        _format_property_change_path(builder, property_change, "before", max_path_length, indent_level)
        _format_property_modify(builder, before, after, children, indent_level + 1)
    elif property_change_type == PropertyChangeType.array:
        _format_property_change_path(builder, property_change, "children", max_path_length, indent_level)
        _format_property_array_change(builder, children, indent_level + 1)
    else:
        raise ValueError(f"Unknown property change type: {property_change_type}.")


def _format_property_change_path(builder, property_change, value_name, max_path_length, indent_level):
    path, property_change_type = property_change.path, property_change.property_change_type
    value = getattr(property_change, value_name)

    padding_width = max_path_length - len(path) + 1

    if _is_non_empty_array(value):
        padding_width = 1
    if _is_non_empty_object(value):
        padding_width = 0
    if property_change_type == PropertyChangeType.modify and property_change.children:
        # Has nested changes.
        padding_width = 0

    _format_path(
        builder,
        path,
        padding_width,
        indent_level,
        format_head=lambda builder: _format_property_change_type(builder, property_change_type),
        format_tail=_format_colon,
    )


def _format_property_change_type(builder, property_change_type):
    property_change_symbol = _property_change_type_to_symbol[property_change_type]
    property_change_color = _property_change_type_to_color[property_change_type]
    builder.append(property_change_symbol, property_change_color).append(Symbol.WHITE_SPACE)


def _format_property_create(builder, value, indent_level):
    with builder.new_color_scope(_property_change_type_to_color[PropertyChangeType.create]):
        _format_json(builder, value, indent_level=indent_level)


def _format_property_delete(builder, value, indent_level):
    with builder.new_color_scope(_property_change_type_to_color[PropertyChangeType.delete]):
        _format_json(builder, value, indent_level=indent_level)


def _format_property_modify(builder, before, after, children, indent_level):
    if children:
        # Has nested changes.
        builder.append_line().append_line()
        _format_property_changes(
            builder,
            sorted(children, key=lambda x: (_property_change_type_to_weight[x.property_change_type], x.path)),
            indent_level,
        )
    else:
        _format_property_delete(builder, before, indent_level)

        # Space before =>
        if _is_non_empty_object(before):
            builder.append_line()
            _format_indent(indent_level)
        else:
            builder.append(Symbol.WHITE_SPACE)

        builder.append("=>")

        # Space after =>
        if not _is_non_empty_object(after):
            builder.append(Symbol.WHITE_SPACE)

        _format_property_create(builder, after, indent_level)

        if not _is_leaf(before) and _is_leaf(after):
            builder.append_line()


def _format_property_array_change(builder, property_changes, indent_level):
    if not property_changes:
        builder.append_line("[]")
        return

    # [
    builder.append(Symbol.LEFT_SQUARE_BRACKET).append_line()

    _format_property_changes(
        builder,
        sorted(property_changes, key=lambda x: (int(x.path), _property_change_type_to_weight[x.property_change_type])),
        indent_level,
    )

    # ]
    _format_indent(builder, indent_level)
    builder.append(Symbol.RIGHT_SQUARE_BRACKET)


def _get_api_version(resource_change):
    if resource_change.before:
        return resource_change.before.get("apiVersion")
    if resource_change.after:
        return resource_change.after.get("apiVersion")
    return None


def _get_scope(resource_change):
    scope, _ = split_resource_id(resource_change.resource_id)
    return scope


def _get_scope_uppercase(resource_change):
    return _get_scope(resource_change).upper()


def _get_relative_resource_id(resource_change):
    _, relative_resource_id = split_resource_id(resource_change.resource_id)
    return relative_resource_id


def _get_max_path_length_from_property_changes(property_changes):
    if not property_changes:
        return 0

    filtered_property_changes = filter(_should_consider_property_change_path, property_changes)
    path_lengths = map(lambda x: len(x.path), filtered_property_changes)

    return max(path_lengths, default=0)


def _should_consider_property_change_path(property_change):
    property_change_type = property_change.property_change_type

    if property_change_type == PropertyChangeType.create:
        return _is_leaf(property_change.after)

    if property_change_type in (PropertyChangeType.delete, PropertyChangeType.modify):
        return _is_leaf(property_change.before)

    return not property_change.children


def format_json(value, enable_color=True):
    builder = ColoredStringBuilder(enable_color)
    _format_json(builder, value)
    return builder.build()


def _format_json(builder, value, path="", max_path_length=0, indent_level=0):
    if _is_leaf(value):
        _format_json_path(builder, path, max_path_length - len(path) + 1, indent_level)
        _format_leaf(builder, value)
    elif _is_non_empty_array(value):
        _format_json_path(builder, path, 1, indent_level)
        _format_non_empty_array(builder, value, indent_level)
    elif _is_non_empty_object(value):
        _format_non_empty_object(builder, value, path, max_path_length, indent_level)
    else:
        raise ValueError(f"Invalid JSON value: {value}")


def _format_leaf(builder, value):
    if value is None:
        builder.append("null")
    elif isinstance(value, bool):
        builder.append(str(value).lower())
    elif isinstance(value, str):
        builder.append(Symbol.QUOTE).append(value).append(Symbol.QUOTE)
    else:
        builder.append(value)


def _format_non_empty_array(builder, value, indent_level):
    builder.append(Symbol.LEFT_SQUARE_BRACKET, Color.RESET).append_line()

    max_path_length = _get_max_path_length_from_array(value)

    for index, child_value in enumerate(value):
        child_path = str(index)

        if _is_non_empty_object(child_value):
            _format_json_path(builder, child_path, 0, indent_level + 1)
            _format_non_empty_object(builder, child_value, indent_level=indent_level + 1)
        else:
            _format_json(builder, child_value, child_path, max_path_length, indent_level + 1)

        builder.append_line()

    _format_indent(builder, indent_level)
    builder.append(Symbol.RIGHT_SQUARE_BRACKET, Color.RESET)


def _format_non_empty_object(builder, value, path=None, max_path_length=0, indent_level=0):
    is_root = not path

    if not path:
        # root object.
        builder.append_line().append_line()
        max_path_length = _get_max_path_length_from_object(value)
        indent_level += 1

    for child_path, child_value in value.items():
        child_path = child_path if is_root else f"{path}{Symbol.DOT}{child_path}"
        _format_json(builder, child_value, child_path, max_path_length, indent_level)

        # if _is_non_empty_array(child_value) or _is_leaf(child_value):
        if not _is_non_empty_object(child_value):
            builder.append_line()


def _format_json_path(builder, path, padding_width, indent_level):
    return _format_path(builder, path, padding_width, indent_level, format_tail=_format_colon)


def _format_path(builder, path, padding_width, indent_level, format_head=None, format_tail=None):
    if not path:
        return

    _format_indent(builder, indent_level)

    if format_head:
        format_head(builder)

    builder.append(path)

    if format_tail:
        format_tail(builder)

    builder.append(str(Symbol.WHITE_SPACE) * padding_width)


def _format_colon(builder):
    builder.append(Symbol.COLON, Color.RESET)


def _format_indent(builder, indent_level=1):
    builder.append(str(Symbol.WHITE_SPACE) * 2 * indent_level)


def _get_max_path_length_from_array(value):
    maxLengthIndex = 0

    for index, child_value in enumerate(value):
        if _is_leaf(child_value):
            maxLengthIndex = index

    return len(str(maxLengthIndex))


def _get_max_path_length_from_object(value):
    max_path_length = 0

    for key, child_value in value.items():
        if _is_non_empty_array(child_value):
            # Ignoring array paths to avoid long padding like this:
            #
            #   short.path:                   "foo"
            #   another.short.path:           "bar"
            #   very.very.long.path.to.array: [
            #     ...
            #   ]
            #   path.after.array:             "foobar"
            #
            # The following is what we want:
            #
            #   short.path:         "foo"
            #   another.short.path: "bar"
            #   very.very.long.path.to.array: [
            #     ...
            #   ]
            #   path.after.array:   "foobar"
            #
            continue

        current_path_length = (
            # Add one for dot.
            len(key) + 1 + _get_max_path_length_from_object(child_value)
            if _is_non_empty_object(child_value)
            else len(key)
        )

        max_path_length = max(max_path_length, current_path_length)

    return max_path_length


def _is_leaf(value):
    return (
        isinstance(value, (type(None), bool, int, float, str)) or
        (isinstance(value, list) and not value) or
        (isinstance(value, dict) and not value)
    )


def _is_non_empty_array(value):
    return isinstance(value, list) and value


def _is_non_empty_object(value):
    return isinstance(value, dict) and value
