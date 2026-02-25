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

ALL_WHAT_IF_TOP_LEVEL_CHANGE_TYPES = [
    StackModels.DeploymentStacksWhatIfChangeType.CREATE,
    StackModels.DeploymentStacksWhatIfChangeType.UNSUPPORTED,
    StackModels.DeploymentStacksWhatIfChangeType.MODIFY,
    StackModels.DeploymentStacksWhatIfChangeType.DELETE,
    StackModels.DeploymentStacksWhatIfChangeType.NO_CHANGE,
    StackModels.DeploymentStacksWhatIfChangeType.DETACH
]


class DeploymentStacksWhatIfResultFormatter:  # pylint: disable=too-few-public-methods
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
            StackModels.DeploymentStacksWhatIfChangeType.MODIFY: Color.PURPLE
        })

    CHANGE_CERTAINTY_WEIGHTS = CaseInsensitiveDict(
        {
            StackModels.DeploymentStacksWhatIfChangeCertainty.DEFINITE: 0,
            StackModels.DeploymentStacksWhatIfChangeCertainty.POTENTIAL: 1
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
        self._format_diagnostics()

        result = self.builder.build()
        self.what_if_result = self.what_if_props = None

        return result


    def _format_new_section(self):
        self.builder.append("\n\n")


    def _format_change_type_legend(self):
        change_type_max_length = 20

        self.builder.append_line("Resource and property changes are indicated with these symbols:")
        self._push_indent()

        for i, change_type in enumerate(ALL_WHAT_IF_TOP_LEVEL_CHANGE_TYPES):
            change_type_label = change_type[0].upper() + change_type[1:]
            symbol, color = self._get_change_type_formatting(change_type)

            self.builder.append(symbol, color).append(" ", no_indent=True).append(change_type_label, no_indent=True)

            if i % 2 == 0:
                remaining_indent = max(1, change_type_max_length - len(change_type_label))
                self.builder.append(" " * remaining_indent, no_indent=True)
            elif i < len(ALL_WHAT_IF_TOP_LEVEL_CHANGE_TYPES) - 1:
                self.builder.append_line(no_indent=True)

        self._pop_indent()

        return True


    def _format_stack_changes(self):
        if not self.what_if_changes:
            return False

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
            self.builder.insert_line(
                title_index, f"Changes to Stack {self.what_if_props.deployment_stack_resource_id}:", Color.DARK_YELLOW)

        return printed


    def _format_resource_changes(self):
        if not self.what_if_changes or not self.what_if_changes.resource_changes:
            return False

        printed = False
        title_index = self.builder.get_current_index()

        resource_changes_sorted = sorted(
            self.what_if_changes.resource_changes,
            key=lambda x: (DeploymentStacksWhatIfResultFormatter.CHANGE_CERTAINTY_WEIGHTS.get(x.change_certainty, 1), x.id))

        # Print the definite resource changes, followed by the potential changes
        first_potential_change_index = None
        for change in resource_changes_sorted:
            if first_potential_change_index is None and str_lower_eq(
                change.change_certainty, StackModels.DeploymentStacksWhatIfChangeCertainty.POTENTIAL):
                first_potential_change_index = self.builder.get_current_index()

            if self._format_resource_change(change):
                printed = True

        if first_potential_change_index is not None:
            self.builder.insert_line(first_potential_change_index, "Potential Resource Changes (Learn more at https://aka.ms/whatIfPotentialChanges)", Color.PURPLE)
            self.builder.insert(first_potential_change_index, ">> ")

        if printed:
            self.builder.insert_line(title_index, "Changes to Managed Resources:", Color.DARK_YELLOW)

        # Summarize the deletions, if any
        delete_changes = list(filter(
            lambda x: str_lower_eq(x.change_type, StackModels.DeploymentStacksWhatIfChangeType.DELETE),
            resource_changes_sorted))

        if len(delete_changes) > 0:
            self._format_new_section()
            self.builder.append("Deleting - ", Color.RED)
            self.builder.append_line(f"Resources Marked for Deletion {len(delete_changes)} total:", no_indent=True)

        first_potential_change_index = None
        num_potential_deletions = 0
        for delete_change in delete_changes:
            if first_potential_change_index is None and str_lower_eq(
                delete_change.change_certainty, StackModels.DeploymentStacksWhatIfChangeCertainty.POTENTIAL):
                first_potential_change_index = self.builder.get_current_index()
                num_potential_deletions += 1

            self._format_resource_heading_line(delete_change)

        if first_potential_change_index is not None:
            self.builder.insert_line(
                first_potential_change_index,
                f"Potential Deletions {num_potential_deletions} total (Learn more at https://aka.ms/whatIfPotentialChanges)",
                Color.RED)
            self.builder.insert(first_potential_change_index, ">> ")

        return printed


    def _format_resource_change(self, resource_change: StackModels.DeploymentStacksWhatIfResourceChange):
        if not resource_change.id:  # is an extensible resource
            return False  # not yet supported

        # print the resource heading line
        self._format_resource_heading_line(resource_change)

        # print stack management related changes
        self._push_indent()
        all_resource_changes = {
            "Management Status Change": resource_change.management_status_change,
            "Deny Status Change": resource_change.deny_status_change,
        }

        for path, change in all_resource_changes.items():
            self._format_change(change, path)

        # print resource property changes
        self._format_resource_property_changes(resource_change.resource_configuration_changes)
        self._pop_indent()

        return True


    def _format_resource_heading_line(self, resource_change: StackModels.DeploymentStacksWhatIfResourceChange):
        symbol, color = self._get_change_type_formatting(resource_change.change_type)

        is_potential_change = str_lower_eq(
            resource_change.change_certainty, StackModels.DeploymentStacksWhatIfChangeCertainty.POTENTIAL)

        # print the change type and resource ID
        if is_potential_change:
            self.builder.append("?", Color.CYAN)
        self.builder.append(f"{symbol} ", color, no_indent=is_potential_change)
        if is_potential_change:
            self.builder.append("Potential ?", Color.CYAN, no_indent=True).append(f"{symbol} ", color, no_indent=True)

        api_version_suffix = f" [{resource_change.api_version}]" if resource_change.api_version else ""
        self.builder.append_line(f"{resource_change.id}{api_version_suffix}", color, no_indent=True)


    def _format_resource_property_changes(
        self, property_changes: t.Optional[StackModels.DeploymentStacksChangeDeltaRecord]
    ):
        if not property_changes or not property_changes.delta:
            return False

        printed = False

        for property_change in property_changes.delta:
            if self._format_change(property_change):
                printed = True

        return printed


    def _format_resource_deletions_summary(self):
        if not self.what_if_changes or not self.what_if_changes.resource_changes:
            return False


    def _format_diagnostics(self):
        pass


    def _format_change(
        self,
        change: t.Optional[t.Union[
            StackModels.DeploymentStacksChangeBase,
            StackModels.DeploymentStacksChangeDeltaRecord,
            StackModels.DeploymentStacksWhatIfPropertyChange]],
        parent_path: t.Optional[str] = None
    ):
        if not change:
            return False

        value_type = self._get_value_type_from_change(change)

        if value_type is str or value_type is bool or value_type is int or value_type is float:
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
        self, object_change: t.Optional[StackModels.DeploymentStacksChangeDeltaRecord],
        parent_path: t.Optional[str] = None
    ):
        if not object_change or not object_change.delta:
            return False

        printed = False

        for delta in object_change.delta:
            if self._format_change(delta, parent_path):
                printed = True

        return printed


    def _format_array_changes(
        self, array_change: StackModels.DeploymentStacksWhatIfPropertyChange, parent_path: t.Optional[str] = None
    ):
        if not str_lower_eq(array_change.change_type, StackModels.DeploymentStacksWhatIfPropertyChangeType.ARRAY):
            return False

        property_path = self._get_change_path(array_change, parent_path)
        symbol, color = self._get_change_type_formatting(StackModels.DeploymentStacksWhatIfPropertyChangeType.MODIFY)

        self.builder.append_line(f"{symbol} {property_path}: ", color)
        self._push_indent()

        for i, item_change in enumerate(array_change.children or []):
            if self._format_array_child_change(item_change) and i < len(array_change.children) - 1:
                self.builder.append_line(no_indent=True)

        self._pop_indent()

        return True


    def _format_array_child_change(self, array_change: StackModels.DeploymentStacksWhatIfPropertyChange):
        symbol, color = self._get_change_type_formatting(array_change.change_type)

        # TODO(kylealbert): handle non-primitive
        if str_lower_eq(array_change.change_type, StackModels.DeploymentStacksWhatIfPropertyChangeType.CREATE) or \
            str_lower_eq(array_change.change_type, StackModels.DeploymentStacksWhatIfPropertyChangeType.NO_EFFECT):
            self.builder.append(f"{symbol} {self._format_primitive_value(array_change.after)}", color)
            return True
        if str_lower_eq(array_change.change_type, StackModels.DeploymentStacksWhatIfPropertyChangeType.DELETE):
            self.builder.append(f"{symbol} {self._format_primitive_value(array_change.before)}", color)
            return True

        return False


    def _format_primitive_change(
        self,
        primitive_change: t.Optional[
            t.Union[StackModels.DeploymentStacksChangeBase, StackModels.DeploymentStacksWhatIfPropertyChange]],
        parent_path: t.Optional[str] = None
    ):
        if not primitive_change:
            return False

        property_path = self._get_change_path(primitive_change, parent_path)
        symbol, color = self._get_change_type_formatting(
            StackModels.DeploymentStacksWhatIfPropertyChangeType.NO_EFFECT if primitive_change.before == primitive_change.after \
                else StackModels.DeploymentStacksWhatIfPropertyChangeType.MODIFY)

        self.builder.append(f"{symbol} {property_path}: ", color)
        self.builder.append_line(
            f"{self._format_primitive_value(primitive_change.before)} => {self._format_primitive_value(primitive_change.after)}",
            no_indent=True)

        return True


    def _push_indent(self, indent_size=INDENT_SIZE):
        self.builder.push_indent(" " * indent_size)


    def _pop_indent(self):
        self.builder.pop_indent()


    @staticmethod
    def _format_primitive_value(value: t.Optional[t.Union[str, bool, int, float]]):
        if value is None:
            return "null"
        return f'"{value}"' if isinstance(value, str) else str(value)


    @staticmethod
    def _get_change_type_formatting(
        change_type: t.Union[
            StackModels.DeploymentStacksWhatIfChangeType, StackModels.DeploymentStacksWhatIfPropertyChangeType]
    ):
        symbol = DeploymentStacksWhatIfResultFormatter.CHANGE_TYPE_SYMBOLS.get(change_type, None)
        color = DeploymentStacksWhatIfResultFormatter.CHANGE_TYPE_COLORS.get(change_type, None)

        return symbol, color


    @staticmethod
    def _get_change_path(change, parent_path: t.Optional[str] = None):
        if hasattr(change, "path"):
            return '.'.join([parent_path, change.path]) if parent_path else change.path
        return parent_path


    @staticmethod
    def _get_value_type_from_change(
        change: t.Union[
            StackModels.DeploymentStacksChangeBase,
            StackModels.DeploymentStacksChangeDeltaRecord,
            StackModels.DeploymentStacksWhatIfPropertyChange]
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
