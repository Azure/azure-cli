# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import typing as t

from requests.structures import CaseInsensitiveDict

import azure.mgmt.resource.deploymentstacks.models as StackModels
# from itertools import groupby

from ._formatters import _format_ext_resource_identifiers
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

    CHANGE_CERTAINTY_PRIORITIES = CaseInsensitiveDict(
        {
            StackModels.DeploymentStacksWhatIfChangeCertainty.DEFINITE: 0,
            StackModels.DeploymentStacksWhatIfChangeCertainty.POTENTIAL: 1
        })

    DIAGNOSTIC_LEVEL_PRIORITIES = CaseInsensitiveDict(
        {
            StackModels.DeploymentStacksDiagnosticLevel.INFO: 1,
            StackModels.DeploymentStacksDiagnosticLevel.WARNING: 2,
            StackModels.DeploymentStacksDiagnosticLevel.ERROR: 3,
        })

    DIAGNOSTIC_COLORS = CaseInsensitiveDict(
        {
            StackModels.DeploymentStacksDiagnosticLevel.WARNING: Color.DARK_YELLOW,
            StackModels.DeploymentStacksDiagnosticLevel.ERROR: Color.RED,
        })

    def __init__(self, enable_color=True):
        self.builder: ColoredStringBuilder = ColoredStringBuilder(enable_color)
        self.what_if_result: t.Optional[StackModels.DeploymentStacksWhatIfResult] = None
        self.what_if_props: t.Optional[StackModels.DeploymentStacksWhatIfResultProperties] = None
        self.what_if_changes: t.Optional[StackModels.DeploymentStacksWhatIfChange] = None

    def format(self, what_if_result: StackModels.DeploymentStacksWhatIfResult) -> str:
        self.builder.clear()

        self.what_if_result = what_if_result
        self.what_if_props = what_if_result.properties
        self.what_if_changes = self.what_if_props.changes if self.what_if_props else None

        if self._format_change_type_legend():
            self._format_section_spacer()
        if self._format_stack_changes():
            self._format_section_spacer()
        if self._format_resource_changes_and_deletion_summary():
            self._format_section_spacer()
        self._format_diagnostics()

        result = self.builder.build()
        self.what_if_result = self.what_if_props = self.what_if_changes = None

        return result

    def _format_section_spacer(self):
        self.builder.ensure_num_new_lines(2)

    def _format_change_type_legend(self) -> bool:
        change_type_max_length = 20

        self.builder.append_line("Resource and property changes are indicated with these symbols:")
        self._push_indent()

        for i, change_type in enumerate(ALL_WHAT_IF_TOP_LEVEL_CHANGE_TYPES):
            change_type_label = change_type[0].upper() + change_type[1:]
            symbol, color = self._get_change_type_formatting(change_type)

            self.builder.append(symbol, color).append(" ").append(change_type_label)

            if i % 2 == 0:
                remaining_indent = max(1, change_type_max_length - len(change_type_label))
                self.builder.append(" " * remaining_indent)
            elif i < len(ALL_WHAT_IF_TOP_LEVEL_CHANGE_TYPES) - 1:
                self.builder.append_line()

        self._pop_indent()

        return True

    def _format_stack_changes(self) -> bool:
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

    def _format_resource_changes_and_deletion_summary(self) -> bool:
        if not self.what_if_changes or not self.what_if_changes.resource_changes:
            return False

        printed = False
        resource_changes_sorted = sorted(
            self.what_if_changes.resource_changes,
            key=lambda x: (
                0 if x.id else 1,  # sort Azure resources before extension resources
                DeploymentStacksWhatIfResultFormatter.CHANGE_CERTAINTY_PRIORITIES.get(
                    x.change_certainty, 1) if x.id else 0,  # Azure resources: then by certainty
                x.id.lower() if x.id else "",  # Azure resources: then by ID
                # Extension resources: then by (ext name, ext version, config id)
                x.extension.name if x.extension else "",
                x.extension.version if x.extension else "",
                (x.extension.config_id if x.extension else "") or "",
                DeploymentStacksWhatIfResultFormatter.CHANGE_CERTAINTY_PRIORITIES.get(
                    x.change_certainty, 1) if not x.id else 0,  # Extension resources: then by certainty
                x.type if x.extension else "",  # Extension resources: then by type
                # Extension resources: then by identifiers
                _format_ext_resource_identifiers(x.identifiers) if x.identifiers else ""
            ))

        if self._format_resource_changes(resource_changes_sorted):
            printed = True
        if self._format_resource_deletions_summary(resource_changes_sorted):
            printed = True

        return printed

    def _format_resource_changes(
        self, resource_changes_sorted: list[StackModels.DeploymentStacksWhatIfResourceChange]
    ) -> bool:
        if resource_changes_sorted is None or len(resource_changes_sorted) == 0:
            return False

        # Print the definite resource changes, followed by the potential changes
        last_group: t.Optional[str] = None
        has_potential_changes = False

        self.builder.append_line("Changes to Managed Resources:", Color.DARK_YELLOW)

        for change in resource_changes_sorted:
            # check if a new section should be started
            group = self._format_resource_class_header(change)

            if group != last_group:
                last_group = group
                has_potential_changes = False
                self._format_section_spacer()
                self.builder.append_line(group)

            if not has_potential_changes and str_lower_eq(
                    change.change_certainty, StackModels.DeploymentStacksWhatIfChangeCertainty.POTENTIAL):
                self.builder.append(">> ").append_line(
                    "Potential Resource Changes (Learn more at https://aka.ms/whatIfPotentialChanges)",
                    Color.PURPLE)
                has_potential_changes = True

            self._format_resource_change(change)

        return True

    def _format_resource_change(self, resource_change: StackModels.DeploymentStacksWhatIfResourceChange) -> bool:
        # print the resource heading line
        self._format_resource_heading_line(resource_change)

        # print stack management related changes
        self._push_indent()
        all_resource_changes = {
            "Management Status": resource_change.management_status_change,
            "Deny Status": resource_change.deny_status_change,
        }

        for path, change in all_resource_changes.items():
            self._format_change(change, path)

        # print resource property changes
        self._format_resource_property_changes(resource_change.resource_configuration_changes)
        self._pop_indent()

        return True

    def _format_resource_deletions_summary(
        self, resource_changes_sorted: list[StackModels.DeploymentStacksWhatIfResourceChange]
    ) -> bool:
        # Summarize the deletions, if any
        printed = False
        delete_changes = list(
            filter(
                lambda x: str_lower_eq(x.change_type, StackModels.DeploymentStacksWhatIfChangeType.DELETE),
                resource_changes_sorted))

        if len(delete_changes) > 0:
            self._format_section_spacer()
            self.builder.append("Deleting - ", Color.RED)
            self.builder.append_line(f"Resources Marked for Deletion {len(delete_changes)} total:")
            printed = True

        last_group: t.Optional[str] = None
        has_potential_deletions = False

        for i, delete_change in enumerate(delete_changes):
            group = self._format_resource_class_header(delete_change)

            if group != last_group:
                self._format_section_spacer()
                self.builder.append_line(group)
                last_group = group
                has_potential_deletions = False

            if not has_potential_deletions and str_lower_eq(
                    delete_change.change_certainty, StackModels.DeploymentStacksWhatIfChangeCertainty.POTENTIAL):
                self.builder.append(">> ").append_line(
                    f"Potential Deletions {self._get_num_potential_resource_changes(delete_changes, i)} total"
                    " (Learn more at https://aka.ms/whatIfPotentialChanges)",
                    Color.RED)
                has_potential_deletions = True

            self._format_resource_heading_line(delete_change)

        return printed

    def _format_resource_heading_line(self, resource_change: StackModels.DeploymentStacksWhatIfResourceChange):
        symbol, color = self._get_change_type_formatting(resource_change.change_type)

        is_potential_change = str_lower_eq(
            resource_change.change_certainty, StackModels.DeploymentStacksWhatIfChangeCertainty.POTENTIAL)

        # print the change type and resource ID
        if is_potential_change:
            self.builder.append("?", Color.CYAN)
        self.builder.append(f"{symbol} ", color)
        if is_potential_change:
            self.builder.append("[Potential] ", Color.CYAN)

        api_version_suffix = f" [{resource_change.api_version}]" if resource_change.api_version else ""
        resource_id = resource_change.id if resource_change.id else\
            f"{resource_change.type} {_format_ext_resource_identifiers(resource_change.identifiers)}"
        self.builder.append_line(f"{resource_id}{api_version_suffix}", color)

    def _format_resource_property_changes(
        self, property_changes: t.Optional[StackModels.DeploymentStacksChangeDeltaRecord]
    ) -> bool:
        if not property_changes or not property_changes.delta:
            return False

        printed = False

        for property_change in property_changes.delta:
            if self._format_change(property_change):
                printed = True

        return printed

    def _format_diagnostics(self) -> bool:
        if not self.what_if_props or not self.what_if_props.diagnostics or len(self.what_if_props.diagnostics) == 0:
            return False

        diagnostics_sorted = sorted(
            self.what_if_props.diagnostics,
            key=lambda x: (
                DeploymentStacksWhatIfResultFormatter.DIAGNOSTIC_LEVEL_PRIORITIES.get(x.level, 0),
                x.code or ""))

        self.builder.append_line(f"Diagnostics ({len(diagnostics_sorted)}):")

        for diagnostic in diagnostics_sorted:
            self._format_diagnostic(diagnostic)

        return True

    def _format_diagnostic(self, diagnostic: StackModels.DeploymentStacksDiagnostic):
        self.builder.append_line(
            f"{diagnostic.level.upper()}: [{diagnostic.code}] {diagnostic.message}",
            DeploymentStacksWhatIfResultFormatter.DIAGNOSTIC_COLORS.get(diagnostic.level, None))

    def _format_change(
        self,
        change: t.Optional[t.Union[
            StackModels.DeploymentStacksChangeBase,
            StackModels.DeploymentStacksChangeDeltaRecord,
            StackModels.DeploymentStacksWhatIfPropertyChange]],
        parent_path: t.Optional[str] = None,
        is_array_item: bool = False
    ) -> bool:
        if not change:
            return False

        value_type = self._get_value_type_from_change(change)

        if value_type is str or value_type is bool or value_type is int or value_type is float:
            if self._format_primitive_change(change, parent_path, is_array_item):
                return True
        elif value_type is list:
            if self._format_array_changes(change, parent_path):
                return True
        elif value_type is dict:
            if self._format_object_change(change, parent_path):
                return True

        return False

    def _format_object_change(
        self,
        object_change: t.Optional[t.Union[
            StackModels.DeploymentStacksChangeDeltaRecord, StackModels.DeploymentStacksWhatIfPropertyChange]],
        parent_path: t.Optional[str] = None
    ) -> bool:
        if not object_change:
            return False

        children = object_change.delta if hasattr(object_change, "delta") else (
            object_change.children if hasattr(object_change, "children") else None)

        if not children or len(children) == 0:
            return False

        printed = False

        for child in children:
            if self._format_change(child, parent_path):
                printed = True

        return printed

    def _format_array_changes(
        self, array_change: StackModels.DeploymentStacksWhatIfPropertyChange, parent_path: t.Optional[str] = None
    ) -> bool:
        if not str_lower_eq(array_change.change_type, StackModels.DeploymentStacksWhatIfPropertyChangeType.ARRAY):
            return False

        children = array_change.children

        if not children or len(children) == 0:
            return False

        property_path = self._get_change_path(array_change, parent_path)
        symbol, color = self._get_change_type_formatting(StackModels.DeploymentStacksWhatIfPropertyChangeType.MODIFY)

        self.builder.append_line(f"{symbol} {property_path}: ", color)
        self._push_indent()

        print_array_indices = all(c.path for c in children)
        sorted_children = sorted(
            children,
            key=lambda x: int(x.path)) if print_array_indices else children

        for i, item_change in enumerate(sorted_children):
            if print_array_indices:
                child_symbol, child_color = self._get_change_type_formatting(item_change.change_type)
                self.builder.append(child_symbol, child_color).append_line(f" {item_change.path}:")
                self._push_indent()

            if self._format_change(item_change, is_array_item=True) and i < len(array_change.children) - 1:
                self.builder.ensure_num_new_lines(1)

            if print_array_indices:
                self._pop_indent()

        self._pop_indent()

        return True

    def _format_primitive_change(
        self,
        primitive_change: t.Optional[
            t.Union[StackModels.DeploymentStacksChangeBase, StackModels.DeploymentStacksWhatIfPropertyChange]],
        parent_path: t.Optional[str] = None,
        is_array_item: bool = False
    ) -> bool:
        if not primitive_change:
            return False

        change_type = primitive_change.change_type if hasattr(primitive_change, "change_type") else None
        change_type = (change_type or (StackModels.DeploymentStacksWhatIfPropertyChangeType.NO_EFFECT
                                       if primitive_change.before == primitive_change.after
                                       else StackModels.DeploymentStacksWhatIfPropertyChangeType.MODIFY))

        property_path = self._get_change_path(primitive_change, parent_path)
        symbol, color = self._get_change_type_formatting(change_type)

        self.builder.append(f"{symbol} " if is_array_item else f"{symbol} {property_path}: ", color)
        if str_lower_eq(change_type, StackModels.DeploymentStacksWhatIfPropertyChangeType.MODIFY):
            self.builder.append_line(
                f"{self._format_primitive_value(primitive_change.before)}"
                f" => {self._format_primitive_value(primitive_change.after)}")
        else:
            value = primitive_change.before if str_lower_eq(
                change_type, StackModels.DeploymentStacksWhatIfPropertyChangeType.DELETE) else primitive_change.after
            self.builder.append_line(
                self._format_primitive_value(value), color if is_array_item else None)

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
            StackModels.DeploymentStacksWhatIfChangeType, StackModels.DeploymentStacksWhatIfPropertyChangeType, str]
    ) -> t.Tuple[t.Optional[str], t.Optional[Color]]:
        if change_type is None:
            return None, None

        symbol = DeploymentStacksWhatIfResultFormatter.CHANGE_TYPE_SYMBOLS.get(change_type, None)
        color = DeploymentStacksWhatIfResultFormatter.CHANGE_TYPE_COLORS.get(change_type, None)

        return symbol, color

    @staticmethod
    def _get_change_path(change, parent_path: t.Optional[str] = None) -> str:
        if hasattr(change, "path"):
            return '.'.join([parent_path, change.path]) if parent_path else change.path
        return parent_path

    @staticmethod
    def _get_value_type_from_change(  # pylint: disable=too-many-return-statements
        change: t.Union[
            StackModels.DeploymentStacksChangeBase,
            StackModels.DeploymentStacksChangeDeltaRecord,
            StackModels.DeploymentStacksWhatIfPropertyChange]
    ) -> t.Optional[t.Type]:
        if hasattr(change, "change_type"):
            if str_lower_eq(StackModels.DeploymentStacksWhatIfPropertyChangeType.ARRAY, change.change_type):
                return list
            if hasattr(change, "children") and change.children and len(change.children) > 0:
                return dict
        elif hasattr(change, "delta"):
            return dict

        before_type = type(change.before)
        after_type = type(change.after)

        if before_type == after_type:
            return before_type
        if after_type is not type(None):
            return after_type
        if before_type is not type(None):
            return before_type

        return None

    @staticmethod
    def _get_num_potential_resource_changes(
        resource_changes: t.List[StackModels.DeploymentStacksWhatIfResourceChange], start_index: int
    ) -> int:
        count = 0
        for i in range(start_index, len(resource_changes)):
            if str_lower_eq(
                    resource_changes[i].change_certainty, StackModels.DeploymentStacksWhatIfChangeCertainty.POTENTIAL):
                count += 1
            else:
                break
        return count

    @staticmethod
    def _format_resource_class_header(change: StackModels.DeploymentStacksWhatIfResourceChange) -> str:
        if change.id:
            return "Azure"

        result = "Unknown"
        if change.extension:
            result = f"{change.extension.name}@{change.extension.version}"

            if change.extension.config:
                # Print the config. Eventually this can be substituted with an optional user-provided "comparison ID"
                # for brevity.
                config_items = sorted(
                    change.extension.config.items(),
                    key=lambda ci: ((ci[1] or {}).get('keyVaultReference', None) is not None, ci[0]))

                if len(config_items) > 0:
                    config_parts = []

                    for prop, item in config_items:
                        if not item:
                            continue

                        if item.get('keyVaultReference', None):
                            secret_name = item['keyVaultReference'].get('secretName', None)
                            secret_version = item['keyVaultReference'].get('secretVersion', None)
                            kv_id = item['keyVaultReference'].get('keyVault', {}).get('id', None)
                            version_suffix = f"@{secret_version}" if secret_version else ""

                            config_parts.append(
                                f"{prop}=<Secret '{secret_name}'{version_suffix} in key vault '{kv_id}'>")
                        else:
                            config_parts.append(f"{prop}={json.dumps(item.get('value', None))}")

                    result += f" {', '.join(config_parts)}"

        return result
