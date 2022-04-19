# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ManagedApplicationPreparer, ResourceGroupPreparer, ScenarioTest, live_only
# flake8: noqa


class AzureOpenShiftServiceScenarioTest(ScenarioTest):

    # It works in --live mode but fails in replay mode.get rid off @live_only attribute once this resolved
    @live_only()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitestosa', location='eastus')
    @ManagedApplicationPreparer()
    def test_openshift_create_default_service(self, resource_group, resource_group_location, aad_client_app_id, aad_client_app_secret):
        # kwargs for string formatting
        osa_name = self.create_random_name('clitestosa', 15)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': osa_name,
            'location': resource_group_location,
            'aad_client_app_id': aad_client_app_id,
            'aad_client_app_secret': aad_client_app_secret,
            'resource_type': "Microsoft.ContainerService/OpenShiftManagedClusters"
        })

        # create
        create_cmd = 'openshift create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--compute-count=1 ' \
                     '--aad-client-app-id {aad_client_app_id} --aad-client-app-secret {aad_client_app_secret}'
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.check('provisioningState', 'Succeeded')
        ])

        # show
        self.cmd('openshift show -g {resource_group} -n {name}', checks=[
            self.check('type', '{resource_type}'),
            self.check('name', '{name}'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_D4s_v3'),
            self.exists('openShiftVersion')
        ])

        # scale up
        self.cmd('openshift scale -g {resource_group} -n {name} --compute-count 3', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # show again
        self.cmd('openshift show -g {resource_group} -n {name}', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # delete
        self.cmd('openshift delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    # It works in --live mode but fails in replay mode.get rid off @live_only attribute once this resolved
    @live_only()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitestosa', location='eastus')
    @ManagedApplicationPreparer()
    def test_openshift_create_service_no_wait(self, resource_group, resource_group_location, aad_client_app_id, aad_client_app_secret):
        # kwargs for string formatting
        osa_name = self.create_random_name('clitestosa', 15)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': osa_name,
            'location': resource_group_location,
            'aad_client_app_id': aad_client_app_id,
            'aad_client_app_secret': aad_client_app_secret
        })

        # create --no-wait
        create_cmd = 'openshift create -g {resource_group} -n {name} ' \
                     '-l {location} -c 1 --aad-client-app-id {aad_client_app_id} ' \
                     '--aad-client-app-secret {aad_client_app_secret} ' \
                     '--tags scenario_test --no-wait'
        self.cmd(create_cmd, checks=[self.is_empty()])

        # wait
        self.cmd('openshift wait -g {resource_group} -n {name} --created', checks=[self.is_empty()])

        # show
        self.cmd('openshift show -g {resource_group} -n {name}', checks=[
            self.check('name', '{name}'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_D4s_v3'),
            self.check('provisioningState', 'Succeeded'),
            self.exists('openShiftVersion')
        ])

        # delete
        self.cmd('openshift delete -g {resource_group} -n {name} --yes', checks=[self.is_empty()])

        # show again and expect failure
        self.cmd('openshift show -g {resource_group} -n {name}', expect_failure=True)

    # It works in --live mode but fails in replay mode.get rid off @live_only attribute once this resolved
    @live_only()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitestosa', location='eastus')
    def test_openshift_create_default_service_no_aad(self, resource_group, resource_group_location):
        # kwargs for string formatting
        osa_name = self.create_random_name('clitestosa', 15)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': osa_name,
            'location': resource_group_location,
            'resource_type': 'Microsoft.ContainerService/OpenShiftManagedClusters'
        })

        # create
        create_cmd = 'openshift create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--compute-count=1 '
        self.cmd(create_cmd, checks=[
            self.exists('fqdn'),
            self.check('provisioningState', 'Succeeded')
        ])

        # show
        self.cmd('openshift show -g {resource_group} -n {name}', checks=[
            self.check('type', '{resource_type}'),
            self.check('name', '{name}'),
            self.check('resourceGroup', '{resource_group}'),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_D4s_v3'),
            self.exists('openShiftVersion')
        ])

        # scale up
        self.cmd('openshift scale -g {resource_group} -n {name} --compute-count 3', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # show again
        self.cmd('openshift show -g {resource_group} -n {name}', checks=[
            self.check('agentPoolProfiles[0].count', 3)
        ])

        # delete
        self.cmd('openshift delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])
    # It works in --live mode but fails in replay mode.get rid off @live_only attribute once this resolved
    @live_only()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitestosa', location='eastus')
    @ManagedApplicationPreparer()
    def test_openshift_create_with_monitoring(self, resource_group, resource_group_location, aad_client_app_id, aad_client_app_secret):
        # kwargs for string formatting
        osa_name = self.create_random_name('clitestosa', 15)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': osa_name,
            'location': resource_group_location,
            'aad_client_app_id': aad_client_app_id,
            'aad_client_app_secret': aad_client_app_secret
        })
        workspace = self.cmd("monitor log-analytics workspace create -g {resource_group} -n {name}").get_output_in_json()
        workspace_id = workspace["id"]
        account = self.cmd("account show").get_output_in_json()
        tenant_id = account["tenantId"]
        self.kwargs.update({
            'workspace_id': workspace_id,
            'tenant_id': tenant_id
        })
        # create
        create_cmd = 'openshift create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--compute-count=1 ' \
                     '--aad-client-app-id {aad_client_app_id} --aad-client-app-secret {aad_client_app_secret} ' \
                     '--aad-tenant-id {tenant_id} --workspace-id {workspace_id}'

        self.cmd(create_cmd, checks=[self.is_empty()])
        # show
        self.cmd('openshift show -g {resource_group} -n {name}', checks=[
            self.check('name', '{name}'),
            self.check('resourceGroup', '{resource_group}'),
            self.exists('openShiftVersion'),
            self.exists('monitorProfile')
        ])
        # delete
        self.cmd('openshift delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])

    @live_only()
    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitestosa', location='eastus')
    @ManagedApplicationPreparer()
    def test_openshift_monitoring_enable(self, resource_group, resource_group_location, aad_client_app_id, aad_client_app_secret):
        # kwargs for string formatting
        osa_name = self.create_random_name('clitestosa', 15)
        self.kwargs.update({
            'resource_group': resource_group,
            'name': osa_name,
            'location': resource_group_location,
            'aad_client_app_id': aad_client_app_id,
            'aad_client_app_secret': aad_client_app_secret
        })
        account = self.cmd("account show").get_output_in_json()
        tenant_id = account["tenantId"]
        self.kwargs.update({
            'tenant_id': tenant_id
        })

        # create without monitoring
        create_cmd = 'openshift create --resource-group={resource_group} --name={name} --location={location} ' \
                     '--compute-count=1 ' \
                     '--aad-client-app-id {aad_client_app_id} --aad-client-app-secret {aad_client_app_secret} ' \
                     '--aad-tenant-id {tenant_id}'
        self.cmd(create_cmd, checks=[self.is_empty()])

        # show
        self.cmd('openshift show -g {resource_group} -n {name}', checks=[
            self.check('name', '{name}'),
            self.check('resourceGroup', '{resource_group}'),
            self.exists('openShiftVersion'),
        ])

        workspace = self.cmd("monitor log-analytics workspace create -g {resource_group} -n {name}").get_output_in_json()
        workspace_id = workspace["id"]
        self.kwargs.update({
            'workspace_id': workspace_id,
        })
        monitor_enable_cmd = 'openshift monitor enable --resource-group={resource_group} --name={name} --location={location} ' \
                     '--workspace-id {workspace_id}'

        self.cmd(monitor_enable_cmd, checks=[self.is_empty()])

        self.cmd('openshift show -g {resource_group} -n {name}', checks=[
            self.exists('monitorProfile')
        ])

        # delete
        self.cmd('openshift delete -g {resource_group} -n {name} --yes --no-wait', checks=[self.is_empty()])
