# AZURE CLI RESOURCE TEST DEFINITIONS

ENV_VAR = {}

TEST_DEF = [
    {
        'test_name': 'resource_group_list',
        'command': 'resource group list --output json'
    },
    {
        'test_name': 'resource_show_under_group',
        'command': 'resource show -n xplatvmExt1314 --resource-group XPLATTESTGEXTENSION9085 --resource-type Microsoft.Compute/virtualMachines --output json'
    }
]

