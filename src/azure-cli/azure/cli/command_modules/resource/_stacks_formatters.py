# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import typing as t
from requests.structures import CaseInsensitiveDict

import azure.mgmt.resource.deploymentstacks.models as StackModels
#from itertools import groupby

#from azure.mgmt.resource.deployments.models import ChangeType, PropertyChangeType, Level

from ._color import Color, ColoredStringBuilder
#from ._utils import split_resource_id

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
    INDENT = " " * INDENT_SIZE

    # NOTE(kylealbert): Some of these overlap with property change types
    CHANGE_TYPE_SYMBOLS = CaseInsensitiveDict({
        StackModels.DeploymentStacksWhatIfPropertyChangeType.ARRAY: '~',
        StackModels.DeploymentStacksWhatIfChangeType.CREATE: '+',
        StackModels.DeploymentStacksWhatIfChangeType.DELETE: '-',
        StackModels.DeploymentStacksWhatIfChangeType.DETACH: 'v',
        StackModels.DeploymentStacksWhatIfChangeType.MODIFY: '~',
        StackModels.DeploymentStacksWhatIfChangeType.NO_CHANGE: '=',
        StackModels.DeploymentStacksWhatIfPropertyChangeType.NO_EFFECT: '=',
        StackModels.DeploymentStacksWhatIfChangeType.UNSUPPORTED: '!',
    })

    CHANGE_TYPE_COLORS = CaseInsensitiveDict({
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
        self.what_if_changes = self.what_if_props and self.what_if_props.changes or None

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

        if self._format_primitive_change(self.what_if_changes.deployment_scope_change, "DeploymentScope"):
            printed = True
        if self._format_object_change(self.what_if_changes.deny_settings_change, "DenySettings"):
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

    def _format_object_change(
        self, object_change: t.Optional[StackModels.DeploymentStacksChangeDeltaRecord], parent_path: t.Optional[str] = None
    ):
        if not object_change:
            return False

        printed = False
        delta = object_change.delta

        for delta in delta or []:
            if delta.change_type == StackModels.DeploymentStacksWhatIfPropertyChangeType.MODIFY:
                if delta
            if self._format_property_change(delta, parent_path):
               printed = True

        return printed

    def _format_property_change(
        self, property_change: t.Optional[StackModels.DeploymentStacksWhatIfPropertyChange], parent_path: t.Optional[str] = None
    ):
        if not property_change:
            return False

        symbol = DeploymentStacksWhatIfResultFormatter.CHANGE_TYPE_SYMBOLS.get(property_change.change_type, None)
        property_color = DeploymentStacksWhatIfResultFormatter.CHANGE_TYPE_COLORS.get(property_change.change_type, None)
        property_path = '.'.join([parent_path, property_change.path]) if parent_path else property_change.path

        self.builder.append_line(f"{symbol} {property_path}:", property_color)
        self.builder.append_line()

        return True

    def _format_primitive_change(self, primitive_change: t.Optional[StackModels.DeploymentStacksChangeBase], property_path: str):
        if not primitive_change:
            return False

        self.builder.append(
            f"~ {property_path}: ",
            DeploymentStacksWhatIfResultFormatter.CHANGE_TYPE_COLORS[StackModels.DeploymentStacksWhatIfPropertyChangeType.MODIFY])
        self.builder.append_line(f"{primitive_change.before} => {primitive_change.after}")  # TODO(kylealbert): correct arrow symbol?

        return True

    def _get_type_from_delta(self, delta: StackModels.DeploymentStacksChangeBase):

