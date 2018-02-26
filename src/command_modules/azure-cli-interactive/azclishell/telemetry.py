# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import datetime
import azure.cli.core.telemetry as telemetry_core


class Telemetry(object):
    """ Handles Interactive Telemetry """

    def __init__(self):
        self.core = telemetry_core
        self.interactive_start_time = datetime.datetime.now()
        self.interactive_end_time = None
        self.num_outside_gesture = 0
        self.num_exit_code_gesture = 0
        self.num_query_gesture = 0
        self.num_scope_changes = 0
        self.num_ran_tutorial = 0
        self.num_scroll_examples = 0
        self.num_open_config = 0
        self.num_toggle_default = 0
        self.num_toggle_symbol_bindings = 0
        self.num_cli_commands_used = 0

    def get_interactive_session_properties(self):
        properties = {}
        telemetry_core.set_custom_properties(properties, 'StartTime', str(self.interactive_start_time))
        telemetry_core.set_custom_properties(properties, 'EndTime', str(self.interactive_end_time))
        telemetry_core.set_custom_properties(properties, 'OutsideGestures', self.num_outside_gesture)
        telemetry_core.set_custom_properties(properties, 'ExitGestures', self.num_exit_code_gesture)
        telemetry_core.set_custom_properties(properties, 'QueryGestures', self.num_query_gesture)
        telemetry_core.set_custom_properties(properties, 'ScopeChanges', self.num_scope_changes)
        telemetry_core.set_custom_properties(properties, 'TutorialRuns', self.num_ran_tutorial)
        telemetry_core.set_custom_properties(properties, 'ExampleScrollingActions', self.num_scroll_examples)
        telemetry_core.set_custom_properties(properties, 'ConfigurationChanges', self.num_open_config)
        telemetry_core.set_custom_properties(properties, 'DefaultToggles', self.num_toggle_default)
        telemetry_core.set_custom_properties(properties, 'SymbolBindingToggles', self.num_toggle_symbol_bindings)
        telemetry_core.set_custom_properties(properties, 'CliCommandsUsed', self.num_cli_commands_used)
        return properties


_session = Telemetry()


# core telemetry operations
def start():
    telemetry_core.start()


def flush():
    telemetry_core.flush()


def conclude():
    _session.interactive_end_time = datetime.datetime.now()
    interactive_session_properties = _session.get_interactive_session_properties()
    telemetry_core.add_event('interactive', interactive_session_properties)
    telemetry_core.suppress_new_events()


def set_failure(summary=None):
    telemetry_core.set_failure(summary=summary)


def set_success(summary=None):
    telemetry_core.set_success(summary=summary)


# operations for aggregating data
def track_outside_gesture():
    _session.num_outside_gesture += 1


def track_exit_code_gesture():
    _session.num_exit_code_gesture += 1


def track_query_gesture():
    _session.num_query_gesture += 1


def track_scope_changes():
    _session.num_scope_changes += 1


def track_ran_tutorial():
    _session.num_ran_tutorial += 1


def track_scroll_examples():
    _session.num_scroll_examples += 1


def track_open_config():
    _session.num_open_config += 1


def track_toggle_default():
    _session.num_toggle_default += 1


def track_toggle_symbol_bindings():
    _session.num_toggle_symbol_bindings += 1


def track_cli_commands_used():
    _session.num_cli_commands_used += 1
