# AZURE CLI RESOURCE TEST DEFINITIONS

ENV_VAR = {}

TEST_DEF = [
    {
        'test_name': 'resource_group_list',
        'command': 'resource group list --output json'
    },
    {
        'test_name': 'resource_show_under_group',
        'command': 'resource show XPLATTESTGEXTENSION9085 xplatvmExt1314 --resource-type Microsoft.Compute/virtualMachines --output json'
    }
]

