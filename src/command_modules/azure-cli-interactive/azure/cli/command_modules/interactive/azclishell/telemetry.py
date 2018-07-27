# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import datetime
import azure.cli.core.telemetry as telemetry_core


# pylint:disable=too-few-public-methods
class Telemetry(object):
    """ Handles Interactive Telemetry """

    def __init__(self):
        self.core = telemetry_core
        self.interactive_start_time = datetime.datetime.utcnow()
        self.interactive_end_time = None
        self.tracked_data = {
            'outside_gesture': 0,
            'exit_code_gesture': 0,
            'query_gesture': 0,
            'scope_changes': 0,
            'ran_tutorial': 0,
            'scroll_examples': 0,
            'open_config': 0,
            'toggle_default': 0,
            'toggle_symbol_bindings': 0,
            'cli_commands_used': 0
        }

    def get_interactive_session_properties(self):
        properties = {}
        telemetry_core.set_custom_properties(properties, 'StartTime', str(self.interactive_start_time))
        telemetry_core.set_custom_properties(properties, 'EndTime', str(self.interactive_end_time))
        telemetry_core.set_custom_properties(properties, 'OutsideGestures', self.tracked_data['outside_gesture'])
        telemetry_core.set_custom_properties(properties, 'ExitGestures', self.tracked_data['exit_code_gesture'])
        telemetry_core.set_custom_properties(properties, 'QueryGestures', self.tracked_data['query_gesture'])
        telemetry_core.set_custom_properties(properties, 'ScopeChanges', self.tracked_data['scope_changes'])
        telemetry_core.set_custom_properties(properties, 'TutorialRuns', self.tracked_data['ran_tutorial'])
        telemetry_core.set_custom_properties(properties, 'ExampleScrollingActions',
                                             self.tracked_data['scroll_examples'])
        telemetry_core.set_custom_properties(properties, 'ConfigurationChanges', self.tracked_data['open_config'])
        telemetry_core.set_custom_properties(properties, 'DefaultToggles', self.tracked_data['toggle_default'])
        telemetry_core.set_custom_properties(properties, 'SymbolBindingToggles',
                                             self.tracked_data['toggle_symbol_bindings'])
        telemetry_core.set_custom_properties(properties, 'CliCommandsUsed', self.tracked_data['cli_commands_used'])
        return properties


_session = Telemetry()


# core telemetry operations
def start():
    telemetry_core.start(mode='interactive')


def flush():
    telemetry_core.flush()


def conclude():
    _session.interactive_end_time = datetime.datetime.utcnow()
    interactive_session_properties = _session.get_interactive_session_properties()
    telemetry_core.add_interactive_event(interactive_session_properties)
    telemetry_core.suppress_new_events()


def set_failure(summary=None):
    telemetry_core.set_failure(summary=summary)


def set_success(summary=None):
    telemetry_core.set_success(summary=summary)


# operations for aggregating data
def track_outside_gesture():
    _session.tracked_data['outside_gesture'] += 1


def track_exit_code_gesture():
    _session.tracked_data['exit_code_gesture'] += 1


def track_query_gesture():
    _session.tracked_data['query_gesture'] += 1


def track_scope_changes():
    _session.tracked_data['scope_changes'] += 1


def track_ran_tutorial():
    _session.tracked_data['ran_tutorial'] += 1


def track_scroll_examples():
    _session.tracked_data['scroll_examples'] += 1


def track_open_config():
    _session.tracked_data['open_config'] += 1


def track_toggle_default():
    _session.tracked_data['toggle_default'] += 1


def track_toggle_symbol_bindings():
    _session.tracked_data['toggle_symbol_bindings'] += 1


def track_cli_commands_used():
    _session.tracked_data['cli_commands_used'] += 1
