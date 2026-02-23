# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import typing as t

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
    WHAT_IF_CHANGE_TYPE_SYMBOLS = {
        StackModels.DeploymentStacksWhatIfChangeType.CREATE: '+',
        StackModels.DeploymentStacksWhatIfChangeType.DELETE: '-',
        StackModels.DeploymentStacksWhatIfChangeType.DETACH: 'v',
        StackModels.DeploymentStacksWhatIfChangeType.MODIFY: '~',
        StackModels.DeploymentStacksWhatIfChangeType.NO_CHANGE: '=',
        StackModels.DeploymentStacksWhatIfChangeType.UNSUPPORTED: '!'
    }

    WHAT_IF_CHANGE_TYPE_COLORS = {
        StackModels.DeploymentStacksWhatIfChangeType.CREATE: Color.GREEN,
        StackModels.DeploymentStacksWhatIfChangeType.DELETE: Color.RED,
        StackModels.DeploymentStacksWhatIfChangeType.DETACH: Color.BLUE,
        StackModels.DeploymentStacksWhatIfChangeType.MODIFY: Color.PURPLE,
        StackModels.DeploymentStacksWhatIfChangeType.NO_CHANGE: Color.GRAY,
        StackModels.DeploymentStacksWhatIfChangeType.UNSUPPORTED: Color.GRAY
    }

    def __init__(self, enable_color=True):
        self.builder: ColoredStringBuilder = ColoredStringBuilder(enable_color)
        self.what_if_result: t.Optional[StackModels.DeploymentStacksWhatIfResult] = None
        self.what_if_props: t.Optional[StackModels.DeploymentStacksWhatIfResultProperties] = None

    def format(self, what_if_result: StackModels.DeploymentStacksWhatIfResult):
        self.builder.clear()

        self.what_if_result = what_if_result
        self.what_if_props = what_if_result.properties

        self._format_change_type_legend()
        self._format_stack_changes()
        self._format_resource_changes()
        self._format_resource_deletions()
        self._format_diagnostics()

        result = self.builder.build()
        self.what_if_result = self.what_if_props = None

        return result

    def _format_change_type_legend(self):
        change_type_max_length = 20
        indent_size = 2

        self.builder.append_line("Resource and property changes are indicated with these symbols:")

        for i, change_type in enumerate(ALL_WHAT_IF_CHANGE_TYPES):
            if i % 2 == 0:
                self.builder.append(" " * indent_size)

            change_type_label = change_type[0].upper() + change_type[1:]

            (self.builder.append(
                DeploymentStacksWhatIfResultFormatter.WHAT_IF_CHANGE_TYPE_SYMBOLS[change_type],
                DeploymentStacksWhatIfResultFormatter.WHAT_IF_CHANGE_TYPE_COLORS[change_type])
             .append(" ").append(change_type_label))

            if i % 2 == 0:
                remaining_indent = max(1, change_type_max_length - len(change_type_label))
                self.builder.append(" " * remaining_indent)
            elif i < len(ALL_WHAT_IF_CHANGE_TYPES) - 1:
                self.builder.append_line()

    def _format_stack_changes(self):
        pass

    def _format_resource_changes(self):
        pass

    def _format_resource_deletions(self):
        pass

    def _format_diagnostics(self):
        pass
