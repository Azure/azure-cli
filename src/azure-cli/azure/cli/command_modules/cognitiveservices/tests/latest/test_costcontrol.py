# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""CRUD scenarios for account and project cost controls using API version 2026-11-15-preview.

Record these scenarios with:
    azdev test cognitiveservices.test_costcontrol --discover --live --series
"""

from datetime import datetime, timezone

from azure.cli.testsdk import ResourceGroupPreparer, ScenarioTest


class CognitiveServicesCostControlScenarioTests(ScenarioTest):

    def _prepare_test_parameters(self, resource_group):
        start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(year=start.year + 1)
        self.kwargs.update({
            'resource_group': resource_group,
            'account_name': self.create_random_name('test-account-', 23),
            'cost_control_name_1': 'test-1',
            'cost_control_name_2': 'test-2',
            'location': 'westus2',
            'start_date': start.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'end_date': end.strftime('%Y-%m-%dT%H:%M:%SZ'),
        })

    @ResourceGroupPreparer(
        name_prefix='dcohen-az-cli-account-costcontrol-rg-',
        location='westus2',
        random_name_length=47,
    )
    def test_cognitiveservices_account_costcontrol_crud(self, resource_group):
        self._prepare_test_parameters(resource_group)

        self.cmd(
            'cognitiveservices account create '
            '--resource-group {resource_group} --name {account_name} '
            '--kind AIServices --sku S0 --location {location} --yes',
            checks=[self.check('name', '{account_name}')],
        )

        first = self.cmd(
            'cognitiveservices account costcontrol create '
            '--resource-group {resource_group} --account-name {account_name} '
            '--cost-control-name {cost_control_name_1} '
            '--category Cost --amount 200 --time-grain Monthly '
            '--time-period start-date={start_date} end-date={end_date}',
            checks=[
                self.check('name', '{cost_control_name_1}'),
                self.check('properties.category', 'Cost'),
                self.check('properties.amount', 200),
                self.check('properties.timeGrain', 'Monthly'),
            ],
        ).get_output_in_json()
        time_period = first['properties']['timePeriod']

        self.cmd(
            'cognitiveservices account costcontrol create '
            '--resource-group {resource_group} --account-name {account_name} '
            '--cost-control-name {cost_control_name_2} '
            '--category Cost --amount 500 --time-grain Monthly '
            '--time-period start-date={start_date} end-date={end_date}',
            checks=[
                self.check('name', '{cost_control_name_2}'),
                self.check('properties.category', 'Cost'),
                self.check('properties.amount', 500),
                self.check('properties.timeGrain', 'Monthly'),
            ],
        )

        self.cmd(
            'cognitiveservices account costcontrol list '
            '--resource-group {resource_group} --account-name {account_name}',
            checks=[
                self.check('length(@)', 2),
                self.check("length([?name=='{cost_control_name_1}'])", 1),
                self.check("length([?name=='{cost_control_name_2}'])", 1),
            ],
        )
        self.cmd(
            'cognitiveservices account costcontrol head '
            '--resource-group {resource_group} --account-name {account_name} '
            '--cost-control-name {cost_control_name_1}',
            checks=[self.is_empty()],
        )
        self.cmd(
            'cognitiveservices account costcontrol show '
            '--resource-group {resource_group} --account-name {account_name} '
            '--cost-control-name {cost_control_name_1}',
            checks=[
                self.check('name', '{cost_control_name_1}'),
                self.check('properties.amount', 200),
                self.check('properties.category', 'Cost'),
                self.check('properties.timeGrain', 'Monthly'),
                self.check('properties.timePeriod', time_period),
            ],
        )

        self.cmd(
            'cognitiveservices account costcontrol update '
            '--resource-group {resource_group} --account-name {account_name} '
            '--cost-control-name {cost_control_name_1} --amount 300',
            checks=[
                self.check('name', '{cost_control_name_1}'),
                self.check('properties.amount', 300),
                self.check('properties.category', 'Cost'),
                self.check('properties.timeGrain', 'Monthly'),
                self.check('properties.timePeriod', time_period),
            ],
        )
        self.cmd(
            'cognitiveservices account costcontrol show '
            '--resource-group {resource_group} --account-name {account_name} '
            '--cost-control-name {cost_control_name_1}',
            checks=[
                self.check('properties.amount', 300),
                self.check('properties.category', 'Cost'),
                self.check('properties.timeGrain', 'Monthly'),
                self.check('properties.timePeriod', time_period),
            ],
        )
        self.cmd(
            'cognitiveservices account costcontrol show '
            '--resource-group {resource_group} --account-name {account_name} '
            '--cost-control-name {cost_control_name_2}',
            checks=[self.check('properties.amount', 500)],
        )

        self.cmd(
            'cognitiveservices account costcontrol delete '
            '--resource-group {resource_group} --account-name {account_name} '
            '--cost-control-name {cost_control_name_1} --yes',
            checks=[self.is_empty()],
        )
        self.cmd(
            'cognitiveservices account costcontrol list '
            '--resource-group {resource_group} --account-name {account_name}',
            checks=[
                self.check('length(@)', 1),
                self.check("length([?name=='{cost_control_name_1}'])", 0),
                self.check("length([?name=='{cost_control_name_2}'])", 1),
            ],
        )
        self.cmd(
            'cognitiveservices account costcontrol delete '
            '--resource-group {resource_group} --account-name {account_name} '
            '--cost-control-name {cost_control_name_2} --yes',
            checks=[self.is_empty()],
        )
        self.cmd(
            'cognitiveservices account costcontrol list '
            '--resource-group {resource_group} --account-name {account_name}',
            checks=[self.check('length(@)', 0)],
        )
        self.cmd(
            'cognitiveservices account delete '
            '--resource-group {resource_group} --name {account_name}',
        )

    @ResourceGroupPreparer(
        name_prefix='dcohen-az-cli-project-costcontrol-rg-',
        location='westus2',
        random_name_length=47,
    )
    def test_cognitiveservices_project_costcontrol_crud(self, resource_group):
        self._prepare_test_parameters(resource_group)
        self.kwargs.update({
            'project_name': self.create_random_name('test-project-', 23),
            'custom_domain': self.create_random_name('cli-costcontrol-', 26),
        })

        self.cmd(
            'cognitiveservices account create '
            '--resource-group {resource_group} --name {account_name} '
            '--kind AIServices --sku S0 --location {location} --yes '
            '--assign-identity --allow-project-management true --custom-domain {custom_domain}',
            checks=[
                self.check('name', '{account_name}'),
                self.check('properties.allowProjectManagement', True),
            ],
        )
        self.cmd(
            'cognitiveservices account project create '
            '--resource-group {resource_group} --name {account_name} '
            '--project-name {project_name} --location {location} '
            '--assign-identity --display-name "Cost control CRUD test"',
            checks=[
                self.check('properties.provisioningState', 'Succeeded'),
                self.check('properties.displayName', 'Cost control CRUD test'),
            ],
        )

        first = self.cmd(
            'cognitiveservices account project costcontrol create '
            '--resource-group {resource_group} --account-name {account_name} --project-name {project_name} '
            '--cost-control-name {cost_control_name_1} '
            '--category Tokens --amount 1000000 --time-grain Monthly '
            '--time-period start-date={start_date} end-date={end_date}',
            checks=[
                self.check('name', '{cost_control_name_1}'),
                self.check('properties.category', 'Tokens'),
                self.check('properties.amount', 1000000),
                self.check('properties.timeGrain', 'Monthly'),
            ],
        ).get_output_in_json()
        time_period = first['properties']['timePeriod']

        self.cmd(
            'cognitiveservices account project costcontrol create '
            '--resource-group {resource_group} --account-name {account_name} --project-name {project_name} '
            '--cost-control-name {cost_control_name_2} '
            '--category Tokens --amount 2000000 --time-grain Monthly '
            '--time-period start-date={start_date} end-date={end_date}',
            checks=[
                self.check('name', '{cost_control_name_2}'),
                self.check('properties.category', 'Tokens'),
                self.check('properties.amount', 2000000),
                self.check('properties.timeGrain', 'Monthly'),
            ],
        )

        self.cmd(
            'cognitiveservices account project costcontrol list '
            '--resource-group {resource_group} --account-name {account_name} --project-name {project_name}',
            checks=[
                self.check('length(@)', 2),
                self.check("length([?name=='{cost_control_name_1}'])", 1),
                self.check("length([?name=='{cost_control_name_2}'])", 1),
            ],
        )
        self.cmd(
            'cognitiveservices account project costcontrol head '
            '--resource-group {resource_group} --account-name {account_name} --project-name {project_name} '
            '--cost-control-name {cost_control_name_1}',
            checks=[self.is_empty()],
        )
        self.cmd(
            'cognitiveservices account project costcontrol show '
            '--resource-group {resource_group} --account-name {account_name} --project-name {project_name} '
            '--cost-control-name {cost_control_name_1}',
            checks=[
                self.check('name', '{cost_control_name_1}'),
                self.check('properties.amount', 1000000),
                self.check('properties.category', 'Tokens'),
                self.check('properties.timeGrain', 'Monthly'),
                self.check('properties.timePeriod', time_period),
            ],
        )

        self.cmd(
            'cognitiveservices account project costcontrol update '
            '--resource-group {resource_group} --account-name {account_name} --project-name {project_name} '
            '--cost-control-name {cost_control_name_1} --amount 1500000',
            checks=[
                self.check('name', '{cost_control_name_1}'),
                self.check('properties.amount', 1500000),
                self.check('properties.category', 'Tokens'),
                self.check('properties.timeGrain', 'Monthly'),
                self.check('properties.timePeriod', time_period),
            ],
        )
        self.cmd(
            'cognitiveservices account project costcontrol show '
            '--resource-group {resource_group} --account-name {account_name} --project-name {project_name} '
            '--cost-control-name {cost_control_name_1}',
            checks=[
                self.check('properties.amount', 1500000),
                self.check('properties.category', 'Tokens'),
                self.check('properties.timeGrain', 'Monthly'),
                self.check('properties.timePeriod', time_period),
            ],
        )
        self.cmd(
            'cognitiveservices account project costcontrol show '
            '--resource-group {resource_group} --account-name {account_name} --project-name {project_name} '
            '--cost-control-name {cost_control_name_2}',
            checks=[self.check('properties.amount', 2000000)],
        )

        self.cmd(
            'cognitiveservices account project costcontrol delete '
            '--resource-group {resource_group} --account-name {account_name} --project-name {project_name} '
            '--cost-control-name {cost_control_name_1} --yes',
            checks=[self.is_empty()],
        )
        self.cmd(
            'cognitiveservices account project costcontrol list '
            '--resource-group {resource_group} --account-name {account_name} --project-name {project_name}',
            checks=[
                self.check('length(@)', 1),
                self.check("length([?name=='{cost_control_name_1}'])", 0),
                self.check("length([?name=='{cost_control_name_2}'])", 1),
            ],
        )
        self.cmd(
            'cognitiveservices account project costcontrol delete '
            '--resource-group {resource_group} --account-name {account_name} --project-name {project_name} '
            '--cost-control-name {cost_control_name_2} --yes',
            checks=[self.is_empty()],
        )
        self.cmd(
            'cognitiveservices account project costcontrol list '
            '--resource-group {resource_group} --account-name {account_name} --project-name {project_name}',
            checks=[self.check('length(@)', 0)],
        )
        self.cmd(
            'cognitiveservices account project delete '
            '--resource-group {resource_group} --name {account_name} --project-name {project_name}',
        )
        self.cmd(
            'cognitiveservices account delete '
            '--resource-group {resource_group} --name {account_name}',
        )
