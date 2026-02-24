# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import typing as t
from requests.structures import CaseInsensitiveDict

import azure.mgmt.resource.deploymentstacks.models as StackModels
# from itertools import groupby

from ._color import Color, ColoredStringBuilder
from ._utils import str_lower_eq

ALL_WHAT_IF_CHANGE_TYPES = [
    StackModels.DeploymentStacksWhatIfChangeType.CREATE,
    StackModels.DeploymentStacksWhatIfChangeType.UNSUPPORTED,
    StackModels.DeploymentStacksWhatIfChangeType.MODIFY,
    StackModels.DeploymentStacksWhatIfChangeType.DELETE,
    StackModels.DeploymentStacksWhatIfChangeType.NO_CHANGE,
    StackModels.DeploymentStacksWhatIfChangeType.DETACH
]


class DeploymentStacksWhatIfResultFormatter:
    INDENT_SIZE = 2

    # NOTE(kylealbert): Some of these overlap with property change types
    CHANGE_TYPE_SYMBOLS = CaseInsensitiveDict(
        {
            StackModels.DeploymentStacksWhatIfPropertyChangeType.ARRAY: '~',
            StackModels.DeploymentStacksWhatIfChangeType.CREATE: '+',
            StackModels.DeploymentStacksWhatIfChangeType.DELETE: '-',
            StackModels.DeploymentStacksWhatIfChangeType.DETACH: 'v',
            StackModels.DeploymentStacksWhatIfChangeType.MODIFY: '~',
            StackModels.DeploymentStacksWhatIfChangeType.NO_CHANGE: '=',
            StackModels.DeploymentStacksWhatIfPropertyChangeType.NO_EFFECT: '=',
            StackModels.DeploymentStacksWhatIfChangeType.UNSUPPORTED: '!',
        })

    CHANGE_TYPE_COLORS = CaseInsensitiveDict(
        {
            StackModels.DeploymentStacksWhatIfPropertyChangeType.ARRAY: Color.PURPLE,
            StackModels.DeploymentStacksWhatIfChangeType.CREATE: Color.GREEN,
            StackModels.DeploymentStacksWhatIfChangeType.DELETE: Color.RED,
            StackModels.DeploymentStacksWhatIfChangeType.DETACH: Color.BLUE,
            StackModels.DeploymentStacksWhatIfChangeType.MODIFY: Color.PURPLE,
            StackModels.DeploymentStacksWhatIfChangeType.NO_CHANGE: Color.GRAY,
            StackModels.DeploymentStacksWhatIfPropertyChangeType.NO_EFFECT: Color.GRAY,
            StackModels.DeploymentStacksWhatIfChangeType.UNSUPPORTED: Color.GRAY,
        })


    def __init__(self, enable_color=True):
        self.builder: ColoredStringBuilder = ColoredStringBuilder(enable_color)
        self.what_if_result: t.Optional[StackModels.DeploymentStacksWhatIfResult] = None
        self.what_if_props: t.Optional[StackModels.DeploymentStacksWhatIfResultProperties] = None
        self.what_if_changes: t.Optional[StackModels.DeploymentStacksWhatIfChange] = None


    def format(self, what_if_result: StackModels.DeploymentStacksWhatIfResult):
        self.builder.clear()

        self.what_if_result = what_if_result
        self.what_if_props = what_if_result.properties
        self.what_if_changes = self.what_if_props.changes if self.what_if_props else None

        if self._format_change_type_legend():
            self._format_new_section()
        if self._format_stack_changes():
            self._format_new_section()
        if self._format_resource_changes():
            self._format_new_section()
        if self._format_resource_deletions():
            self._format_new_section()
        self._format_diagnostics()

        result = self.builder.build()
        self.what_if_result = self.what_if_props = None

        return result


    def _format_new_section(self):
        self.builder.append("\n\n")


    def _format_change_type_legend(self):
        change_type_max_length = 20

        self.builder.append_line("Resource and property changes are indicated with these symbols:")

        for i, change_type in enumerate(ALL_WHAT_IF_CHANGE_TYPES):
            if i % 2 == 0:
                self.builder.append(" " * DeploymentStacksWhatIfResultFormatter.INDENT_SIZE)

            change_type_label = change_type[0].upper() + change_type[1:]

            (self.builder.append(
                DeploymentStacksWhatIfResultFormatter.CHANGE_TYPE_SYMBOLS[change_type],
                DeploymentStacksWhatIfResultFormatter.CHANGE_TYPE_COLORS[change_type])
             .append(" ").append(change_type_label))

            if i % 2 == 0:
                remaining_indent = max(1, change_type_max_length - len(change_type_label))
                self.builder.append(" " * remaining_indent)
            elif i < len(ALL_WHAT_IF_CHANGE_TYPES) - 1:
                self.builder.append_line()

        return True


    def _format_stack_changes(self):
        printed = False

        title_index = self.builder.get_current_index()

        all_stack_changes = {
            "DeploymentScope": self.what_if_changes.deployment_scope_change,
            "DenySettings": self.what_if_changes.deny_settings_change
        }

        for path, change in all_stack_changes.items():
            if self._format_change(change, path):
                printed = True

        if printed:
            self.builder.insert_line(title_index, f"Changes to Stack {self.what_if_props.deployment_stack_resource_id}:", Color.DARK_YELLOW)

        return printed


    def _format_resource_changes(self):
        pass


    def _format_resource_deletions(self):
        pass


    def _format_diagnostics(self):
        pass


    def _format_change(
        self, change: t.Union[
            StackModels.DeploymentStacksChangeBase, StackModels.DeploymentStacksChangeDeltaRecord, StackModels.DeploymentStacksWhatIfPropertyChange],
        parent_path: t.Optional[str] = None
    ):
        value_type = self._get_value_type_from_change(change)

        if value_type is str or value_type is bool or value_type is int:
            if self._format_primitive_change(change, parent_path):
                return True
        elif value_type is list:
            if self._format_array_changes(change, parent_path):
                return True
        elif value_type is dict:
            if self._format_object_change(change, parent_path):
                return True

        return False


    def _format_object_change(
        self, object_change: t.Optional[StackModels.DeploymentStacksChangeDeltaRecord], parent_path: t.Optional[str] = None
    ):
        if not object_change:
            return False

        printed = False
        delta = object_change.delta

        for delta in delta or []:
            if self._format_change(delta, parent_path):
                printed = True

        return printed


    def _format_array_changes(self, array_change: StackModels.DeploymentStacksWhatIfPropertyChange, parent_path: t.Optional[str] = None):
        if not str_lower_eq(array_change.change_type, StackModels.DeploymentStacksWhatIfPropertyChangeType.ARRAY):
            return False

        property_path = self._get_change_path(array_change, parent_path)
        color = DeploymentStacksWhatIfResultFormatter.CHANGE_TYPE_COLORS[StackModels.DeploymentStacksWhatIfPropertyChangeType.MODIFY]

        self.builder.append_line(f"~ {property_path}: ", color)

        for item_change in array_change.children or []:
            self._format_array_child_change(item_change)

        return True


    def _format_array_child_change(self, array_change: StackModels.DeploymentStacksWhatIfPropertyChange):
        symbol = DeploymentStacksWhatIfResultFormatter.CHANGE_TYPE_SYMBOLS.get(array_change.change_type, None)
        color = DeploymentStacksWhatIfResultFormatter.CHANGE_TYPE_COLORS.get(array_change.change_type, None)
        indent = self._get_indent(1)

        if str_lower_eq(array_change.change_type, StackModels.DeploymentStacksWhatIfPropertyChangeType.CREATE):
            self.builder.append_line(f"{indent}{symbol} {self._format_primitive_value(array_change.after)}", color)
        elif str_lower_eq(array_change.change_type, StackModels.DeploymentStacksWhatIfPropertyChangeType.DELETE):
            self.builder.append_line(f"{indent}{symbol} {self._format_primitive_value(array_change.before)}", color)
        elif str_lower_eq(array_change.change_type, StackModels.DeploymentStacksWhatIfPropertyChangeType.NO_EFFECT):
            self.builder.append_line(f"{indent}{symbol} {self._format_primitive_value(array_change.after)}", color)


    def _format_primitive_change(
        self,
        primitive_change: t.Optional[t.Union[StackModels.DeploymentStacksChangeBase, StackModels.DeploymentStacksWhatIfPropertyChange]],
        parent_path: t.Optional[str] = None
    ):
        if not primitive_change:
            return False

        property_path = self._get_change_path(primitive_change, parent_path)
        color = DeploymentStacksWhatIfResultFormatter.CHANGE_TYPE_COLORS[StackModels.DeploymentStacksWhatIfPropertyChangeType.MODIFY]

        self.builder.append(f"~ {property_path}: ", color)
        self.builder.append_line(
            f"{self._format_primitive_value(primitive_change.before)} => {self._format_primitive_value(primitive_change.after)}")  # TODO(kylealbert): correct arrow symbol?

        return True


    @staticmethod
    def _format_primitive_value(value: t.Union[str, bool, int]):
        return f'"{value}"' if isinstance(value, str) else str(value)


    @staticmethod
    def _get_change_path(change, parent_path: t.Optional[str] = None):
        if hasattr(change, "path"):
            return '.'.join([parent_path, change.path]) if parent_path else change.path
        return parent_path


    @staticmethod
    def _get_indent(indent_level: int, indent_size: int = INDENT_SIZE):
        return " " * indent_size * indent_level


    @staticmethod
    def _get_value_type_from_change(
        change: t.Union[
            StackModels.DeploymentStacksChangeBase, StackModels.DeploymentStacksChangeDeltaRecord, StackModels.DeploymentStacksWhatIfPropertyChange]
    ):
        if hasattr(change, "change_type"):
            if str_lower_eq(StackModels.DeploymentStacksWhatIfPropertyChangeType.ARRAY, change.change_type):
                return list
        elif hasattr(change, "delta"):
            return dict

        before_type = type(change.before)
        after_type = type(change.after)

        if before_type == after_type:
            return before_type
        if before_type is type(None) or after_type is type(None):
            return before_type or after_type

        return None
