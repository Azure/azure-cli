# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from ._transformers import (transform_budget_show_output,
                            transform_budget_create_update_output)
from ._validators import (validate_budget_parameters)


def load_command_table(self, _):
    with self.command_group('consumption usage'):
        from azure.cli.command_modules.consumption.custom import ConsumptionUsageList
        self.command_table["consumption usage list"] = ConsumptionUsageList(loader=self)

    with self.command_group('consumption reservation summary'):
        from azure.cli.command_modules.consumption.custom import ConsumptionReservationSummaryList
        self.command_table["consumption reservation summary list"] = ConsumptionReservationSummaryList(loader=self)

    with self.command_group('consumption reservation detail'):
        from azure.cli.command_modules.consumption.custom import ConsumptionReservationDetailList
        self.command_table["consumption reservation detail list"] = ConsumptionReservationDetailList(loader=self)

    with self.command_group('consumption pricesheet'):
        from azure.cli.command_modules.consumption.custom import ConsumptionPricesheetShow
        self.command_table["consumption pricesheet show"] = ConsumptionPricesheetShow(loader=self)

    with self.command_group('consumption marketplace'):
        from azure.cli.command_modules.consumption.custom import ConsumptionMarketplaceList
        self.command_table["consumption marketplace list"] = ConsumptionMarketplaceList(loader=self)

    with self.command_group('consumption budget') as p:
        from azure.cli.command_modules.consumption.custom import ConsumptionBudgetsList
        self.command_table["consumption budget list"] = ConsumptionBudgetsList(loader=self)

        p.custom_show_command('show', 'cli_consumption_show_budget', transform=transform_budget_show_output)

        p.custom_command('create', 'cli_consumption_create_budget', transform=transform_budget_create_update_output, validator=validate_budget_parameters)

        p.custom_command('delete', 'cli_consumption_delete_budget')

    with self.command_group('consumption', is_preview=True):
        pass
