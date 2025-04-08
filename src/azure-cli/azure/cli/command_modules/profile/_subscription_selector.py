# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core._profile import (_SUBSCRIPTION_NAME, _SUBSCRIPTION_ID, _TENANT_DISPLAY_NAME, _TENANT_ID,
                                     _IS_DEFAULT_SUBSCRIPTION)
from knack.log import get_logger

logger = get_logger(__name__)


class SubscriptionSelector:  # pylint: disable=too-few-public-methods
    DEFAULT_ROW_MARKER = '*'

    def __init__(self, subscriptions):
        self._subscriptions = subscriptions
        self._active_one = None
        self._format_subscription_table()

    def _format_subscription_table(self):
        from azure.cli.core.style import format_styled_text, Style
        index_to_subscription_map = {}
        table_data = []
        subscription_name_length_limit = 36

        # Sort by subscription name
        subscriptions_sorted = sorted(self._subscriptions, key=lambda s: s[_SUBSCRIPTION_NAME].lower())

        def highlight_text(text, row_is_default):
            return format_styled_text((Style.HIGHLIGHT, text)) if row_is_default else text

        for index, sub in enumerate(subscriptions_sorted, start=1):
            # There is no need to use int, as int requires parsing. str match is sufficient.
            index_str = str(index)  # '1', '2', ...
            index_to_subscription_map[index_str] = sub

            is_default = sub[_IS_DEFAULT_SUBSCRIPTION]
            if is_default:
                self._active_one = sub

            # Trim subscription name if it is too long
            subscription_name = sub[_SUBSCRIPTION_NAME]
            if len(subscription_name) > subscription_name_length_limit:
                subscription_name = subscription_name[:subscription_name_length_limit - 3] + '...'

            row = {
                'No': (highlight_text(f'[{index_str}]', is_default) +
                       (' ' + self.DEFAULT_ROW_MARKER if is_default else '')),
                'Subscription name': highlight_text(subscription_name, is_default),
                'Subscription ID': highlight_text(sub[_SUBSCRIPTION_ID], is_default),
                'Tenant': highlight_text(self._get_tenant_string(sub), is_default)
            }
            table_data.append(row)

        from tabulate import tabulate
        self._table_str = tabulate(table_data, headers="keys", tablefmt="simple", disable_numparse=True)

        self._index_to_subscription_map = index_to_subscription_map

    def __call__(self):
        """Select a subscription.
        NOTE: The original subscription list (isDefault property) is not modified. Call
        Profile.set_active_subscription to modify it.
        """
        from knack.prompting import prompt

        print(f'\n[Tenant and subscription selection]\n\n{self._table_str}\n')
        tenant_string = self._get_tenant_string(self._active_one)
        print(f"The default is marked with an {self.DEFAULT_ROW_MARKER}; "
              f"the default tenant is '{tenant_string}' and subscription is "
              f"'{self._active_one[_SUBSCRIPTION_NAME]}' ({self._active_one[_SUBSCRIPTION_ID]}).\n")

        selected = self._active_one
        # Keep prompting until the user inputs a valid index
        while True:
            select_index = prompt('Select a subscription and tenant (Type a number or Enter for no changes): ')

            # Nothing is typed, keep current selection
            if select_index == '':
                break

            if select_index in self._index_to_subscription_map:
                selected = self._index_to_subscription_map[select_index]
                break

            logger.warning("Invalid selection.")
            # Let retry

        # Echo the selection
        tenant_string = self._get_tenant_string(selected)
        print(f"\nTenant: {tenant_string}\n"
              f"Subscription: {selected[_SUBSCRIPTION_NAME]} ({selected[_SUBSCRIPTION_ID]})\n")
        return selected

    @staticmethod
    def _get_tenant_string(subscription):
        if tenant_display_name := subscription.get(_TENANT_DISPLAY_NAME):
            return tenant_display_name
        # If _TENANT_DISPLAY_NAME doesn't exist or is None, return _TENANT_ID
        return subscription[_TENANT_ID]
