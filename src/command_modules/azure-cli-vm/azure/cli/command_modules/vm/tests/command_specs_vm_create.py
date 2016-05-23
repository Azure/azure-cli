# AZURE CLI VM CREATE TEST DEFINITIONS
import tempfile
from azure.cli.utils.command_test_script import CommandTestScript, JMESPathComparator

#pylint: disable=method-hidden
class VMCreateUbuntuScenarioTest(CommandTestScript): #pylint: disable=too-many-instance-attributes

    TEST_SSH_KEY_PUB = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCbIg1guRHbI0lV11wWDt1r2cUdcNd27CJsg+SfgC7miZeubtwUhbsPdhMQsfDyhOWHq1+ZL0M+nJZV63d/1dhmhtgyOqejUwrPlzKhydsbrsdUor+JmNJDdW01v7BXHyuymT8G4s09jCasNOwiufbP/qp72ruu0bIA1nySsvlf9pCQAuFkAnVnf/rFhUlOkhtRpwcq8SUNY2zRHR/EKb/4NWY1JzR4sa3q2fWIJdrrX0DvLoa5g9bIEd4Df79ba7v+yiUBOS0zT2ll+z4g9izHK3EO5d8hL4jYxcjKs+wcslSYRWrascfscLgMlMGh0CdKeNTDjHpGPncaf3Z+FwwwjWeuiNBxv7bJo13/8B/098KlVDl4GZqsoBCEjPyJfV6hO0y/LkRGkk7oHWKgeWAfKtfLItRp00eZ4fcJNK9kCaSMmEugoZWcI7NGbZXzqFWqbpRI7NcDP9+WIQ+i9U5vqWsqd/zng4kbuAJ6UuKqIzB0upYrLShfQE3SAck8oaLhJqqq56VfDuASNpJKidV+zq27HfSBmbXnkR/5AK337dc3MXKJypoK/QPMLKUAP5XLPbs+NddJQV7EZXd29DLgp+fRIg3edpKdO7ZErWhv7d+3Kws+e1Y+ypmR2WIVSwVyBEUfgv2C8Ts9gnTF4pNcEY/S2aBicz5Ew2+jdyGNQQ== test@example.com\n" #pylint: disable=line-too-long

    def __init__(self):
        self.deployment_name = 'azurecli-test-deployment-vm-create-ubuntu'
        self.resource_group = 'cliTestRg_VMCreate_Ubuntu'
        self.admin_username = 'ubuntu'
        self.location = 'westus'
        self.vm_names = ['cli-test-vm1']
        self.vm_image = 'UbuntuLTS'
        self.auth_type = 'ssh'
        self.pub_ssh_filename = None
        super(VMCreateUbuntuScenarioTest, self).__init__(
            self.set_up,
            self.test_body,
            self.tear_down)

    def set_up(self):
        _, pathname = tempfile.mkstemp()
        with open(pathname, 'w') as key_file:
            key_file.write(VMCreateUbuntuScenarioTest.TEST_SSH_KEY_PUB)
        self.pub_ssh_filename = pathname
        self.run('resource group create --location {} --name {}'.format(
            self.location,
            self.resource_group))

    def test_body(self):
        self.test('vm create --resource-group {rg} --admin-username {admin} --name {vm_name} --authentication-type {auth_type} --image {image} --ssh-key-value {ssh_key} --location {location} --deployment-name {deployment}'.format( #pylint: disable=line-too-long
            rg=self.resource_group,
            admin=self.admin_username,
            vm_name=self.vm_names[0],
            image=self.vm_image,
            auth_type=self.auth_type,
            ssh_key=self.pub_ssh_filename,
            location=self.location,
            deployment=self.deployment_name,
        ), [
            JMESPathComparator('type(@)', 'object'),
            JMESPathComparator('vm.value.provisioningState', 'Succeeded'),
            JMESPathComparator('vm.value.osProfile.adminUsername', self.admin_username),
            JMESPathComparator('vm.value.osProfile.computerName', self.vm_names[0]),
            JMESPathComparator(
                'vm.value.osProfile.linuxConfiguration.disablePasswordAuthentication',
                True),
            JMESPathComparator(
                'vm.value.osProfile.linuxConfiguration.ssh.publicKeys[0].keyData',
                VMCreateUbuntuScenarioTest.TEST_SSH_KEY_PUB),
        ])

    def tear_down(self):
        self.run('resource group delete --name {}'.format(self.resource_group))

ENV_VAR = {}

TEST_DEF = [
    #{
    #    'test_name': 'vm_create_ubuntu',
    #    'command': VMCreateUbuntuScenarioTest()
    #},
]


