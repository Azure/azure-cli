from azure.cli.testsdk import ScenarioTest

class ProviderTests(ScenarioTest):

    def test_register(self):

        self.kwargs = {
            'namespace': "Microsoft.PolicyInsights"
        }

        self.cmd('provider unregister -n {namespace}')
        self.cmd('provider register -n {namespace} --consent-to-authorization')
        self.cmd('provider permission list -n {namespace}')
        self.cmd('provider unregister -n {namespace}')
        self.cmd('provider register -n {namespace}')
