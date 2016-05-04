# AZURE CLI VM TEST DEFINITIONS
from azure.cli.utils.command_test_script import CommandTestScript

#pylint: disable=method-hidden
class VMImageListByAliasesScenarioTest(CommandTestScript):

    def test_body(self):
        result = self.run('vm image list --offer ubuntu -o tsv')
        assert result.index('14.04.4-LTS') >= 0

    def __init__(self):
        super(VMImageListByAliasesScenarioTest, self).__init__(None, self.test_body, None)

class VMImageListThruServiceScenarioTest(CommandTestScript):

    def test_body(self):
        cmd = ('vm image list -l westus --publisher Canonical --offer '
               'Ubuntu_Snappy_Core -o tsv --all')
        result = self.run(cmd)
        assert result.index('15.04') >= 0

    def __init__(self):
        super(VMImageListThruServiceScenarioTest, self).__init__(None, self.test_body, None)


ENV_VAR = {}

TEST_DEF = [
    {
        'test_name': 'vm_usage_list_westus',
        'command': 'vm usage list --location westus --output json',
    },
    {
        'test_name': 'vm_list_from_group',
        'command': 'vm list --resource-group XPLATTESTGEXTENSION9085',
    },
    {
        'test_name': 'vm_images_list_by_aliases',
        'command': VMImageListByAliasesScenarioTest()
    },
    {
        'test_name': 'vm_images_list_thru_services',
        'command': VMImageListThruServiceScenarioTest()
    }
]


