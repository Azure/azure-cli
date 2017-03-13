
import os
import tempfile

import paramiko
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.mgmt.compute import ComputeManagementClient

from deployments import DeployableResource


class Spinnaker(DeployableResource):
    """
    Deals with creating and configuring Spinnaker
    """
    script_version = 'v0.2.0'

    def __init__(self, resource_group,
                 admin_username, public_ssh_key_filename, dns_prefix):
        super(Spinnaker, self).__init__(resource_group)
        self.admin_username = admin_username
        self.public_ssh_key_filename = public_ssh_key_filename
        self.dns_prefix = dns_prefix

    def deploy(self):
        """
        Creates a VM, installs Spinnaker on it and configures it
        """
        parameters = self._create_params()
        template_url = \
            'https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/spinnaker-vm-simple/azuredeploy.json'
        return self.deploy_template(template_url, parameters)

    def configure(self, spinnaker_hostname, acs_info,
                  registry_url, registry_repository,
                  client_id, client_secret):
        """
        Configures Spinnaker instance to work
        with the registry and Kubernetes cluster
        """
        self._copy_kube_config(spinnaker_hostname, acs_info)
        self._configure_registry(
            spinnaker_hostname, registry_url, client_id, client_secret)
        self._create_pipeline(spinnaker_hostname,
                              registry_url, registry_repository)

    def _create_pipeline(self, spinnaker_hostname, registry_url, registry_repository):
        """
        Creates the pipeline
        """
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(spinnaker_hostname, username=self.admin_username,
                    key_filename=self.public_ssh_key_filename)

        # This is the same name used in clouddriver-local under
        # dockerRegistry account
        registry_account_name = 'azure-container-registry'
        add_pipeline_script_url = \
            'https://raw.githubusercontent.com/Azure/azure-devops-utils/{}/spinnaker/add_k8s_pipeline/add_k8s_pipeline.sh'.format(
                self.script_version)
        command = 'curl --silent {} | sudo bash -s -- -an {} -rg {} -rp {}'.format(
            add_pipeline_script_url, registry_account_name, registry_url, registry_repository)
        _, stdout, stderr = ssh.exec_command(command)
        print 'COMMAND: ', command
        for line in stdout.readlines():
            print line
        for line in stderr.readlines():
            print 'ERR: ' + line
        ssh.close()

    def _configure_registry(self, spinnaker_hostname, registry_url, client_id, client_secret):
        """
        Runs the configure_k8s script to set up Spinnaker to use provided
        registry.
        """
        # Run the script
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(spinnaker_hostname, username=self.admin_username,
                    key_filename=self.public_ssh_key_filename)
        args = ' '.join([
            '-rg {}'.format(registry_url),
            '-ci {}'.format(client_id),
            '-ck {}'.format(client_secret)])

        configure_k8s_script_url = \
            'https://raw.githubusercontent.com/Azure/azure-devops-utils/{}/spinnaker/configure_k8s/configure_k8s.sh'.format(
                self.script_version)
        command = self._create_script_execute_command(
            configure_k8s_script_url, args)
        _, stdout, stderr = ssh.exec_command(command)
        for line in stdout.readlines():
            print line
        for line in stderr.readlines():
            print 'ERR: ' + line
        ssh.close()

    def _create_script_execute_command(self, script_url, args):
        """
        Creates a command that when executed will download the script,
        make it executable, and run it with the provided arguments.
        """
        local_script = script_url.strip('/').split('/')[-1]
        curl_command = 'curl -s {} -o {}'.format(script_url, local_script)
        run_script_command = 'chmod +x {} && sudo ./{}'.format(
            local_script, local_script)
        return '{} && {} {}'.format(curl_command, run_script_command, args)

    def _copy_kube_config(self, spinnaker_hostname, acs_info):
        """
        Copies .kube/config file from the Kubernetes master
        to Spinnaker home folder
        """
        # TODO: get the spinnaker_hostname from within this class, instead
        # of passing it in
        dns_prefix = acs_info.master_profile.dns_prefix
        location = acs_info.location
        user = acs_info.linux_profile.admin_username
        public_ssh_key = self.public_ssh_key_filename

        # HACK: Copy the .kube/config to local machine first and then to the Spinnaker VM
        # We should do this directly from the Spinnaker VM (assuming we have the
        # private key...)
        local_kube_config = tempfile.NamedTemporaryFile().name
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('{}.{}.cloudapp.azure.com'.format(dns_prefix, location), username=user,
                    key_filename=public_ssh_key)
        scp = paramiko.SFTPClient.from_transport(ssh.get_transport())
        scp.get('.kube/config', local_kube_config)
        scp.close()
        ssh.close()

        # Copy .kube to Spinnaker
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(spinnaker_hostname,
                    username=self.admin_username, key_filename=public_ssh_key)
        scp = paramiko.SFTPClient.from_transport(ssh.get_transport())
        scp.mkdir('/home/azureuser/.kube')
        scp.put(local_kube_config, '/home/azureuser/.kube/config')
        scp.close()
        ssh.close()

    def _create_params(self):
        """
        Creates parameters for ARM deployment
        """
        return {
            'adminUsername': {
                'value': self.admin_username
            },
            'sshPublicKey': {
                'value': self._get_public_ssh_key_contents()
            },
            'dnsLabelPrefix': {
                'value': self.dns_prefix
            }
        }

    def _get_public_ssh_key_contents(self):
        """
        Gets the public SSH key file contents
        """
        ssh_filename = self.public_ssh_key_filename
        contents = None
        with open(ssh_filename) as ssh_file:
            contents = ssh_file.read()
        return contents
