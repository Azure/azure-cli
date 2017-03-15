# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import paramiko

import azure.cli.command_modules.project.utils as utils
from azure.cli.command_modules.project.deployments import DeployableResource
import azure.cli.core.azlogging as azlogging  # pylint: disable=invalid-name
logger = azlogging.get_az_logger(__name__) # pylint: disable=invalid-name
# pylint: disable=line-too-long, too-many-arguments

class Jenkins(DeployableResource):
    """
    Deals with creating and configuring Jenkins
    """

    def __init__(self, resource_group,
                 admin_username, admin_password,
                 client_id, client_secret,
                 git_repo_url, dns_prefix, container_registry_url):
        # TODO: admin_password should be replaced with the SSH key once quickstart
        # template is updated to use SSH instead of username/password
        super(Jenkins, self).__init__(resource_group)
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.client_id = client_id
        self.client_secret = client_secret
        # Git repo URL of the service
        self.git_repo_url = git_repo_url
        self.dns_prefix = dns_prefix
        self.container_registry_url = container_registry_url

    def deploy(self):
        """
        Creates a VM, installs Jenkins on it and configures it
        """
        parameters = self._create_params()
        template_url = \
            'https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/101-jenkins-master-on-ubuntu/azuredeploy.json'
        return self.deploy_template(template_url, parameters)

    def configure(self):
        """
        Configures Jenkins instance to work with the
        Azure registry and polls the GitHub repo
        """
        self._add_docker_build_job()
        # TODO: We should unsecure the instance first
        # and then setup everything without using username/password
        # Current script requires a username and password, that's why we
        # are running unsecure script at the end.
        self._unsecure_instance()

    def _add_docker_build_job(self):
        """
        Adds a docker build job to Jenkins instance
        """
        initial_password = self._get_initial_password()
        add_build_job_script_url = \
            'https://raw.githubusercontent.com/Azure/azure-devops-utils/v0.2.0/jenkins/add-docker-build-job.sh'
        args = ' '.join([
            '-j {}'.format('http://127.0.0.1:8080'),
            '-ju {}'.format('admin'),
            '-jp {}'.format(initial_password),
            '-g {}'.format(self.git_repo_url),
            '-r {}'.format(self.container_registry_url),
            '-ru {}'.format(self.client_id),
            '-rp {}'.format(self.client_secret),
            '-sps {}'.format('"* * * * *"'),
            # TODO: Pull the registry repository name out of here 
            '-rr {}/{}'.format(self.admin_username, 'myfirstapp')])
        command = 'curl --silent {} | sudo bash -s -- {}'.format(add_build_job_script_url, args)
        self._run_remote_command(command)

    def _get_initial_password(self):
        """
        Gets the initial Jenkins password from
        """
        command = 'sudo cat /var/lib/jenkins/secrets/initialAdminPassword'
        stdout, _ = self._run_remote_command(command, False)
        return stdout[0].strip()

    def _unsecure_instance(self):
        """
        Unsecures the Jenkins instance by setting
        the useSecurity tag in config.xml to false
        """
        unsecure_script_url = \
            'https://raw.githubusercontent.com/Azure/azure-devops-utils/v0.2.0/jenkins/unsecure-jenkins-instance.sh'
        command = 'curl --silent {} | sudo bash -s --'.format(unsecure_script_url)
        self._run_remote_command(command)

    def _run_remote_command(self, command, output=True):
        """
        Runs a command on remote Jenkins instance
        """
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('{}.westus.cloudapp.azure.com'.format(self.dns_prefix),
                    username=self.admin_username,
                    password=self.admin_password)

        _, stdout, stderr = ssh.exec_command(command)
        stdout_lines = stdout.readlines()
        stderr_lines = stderr.readlines()
        if output:
            for line in stdout_lines:
                utils.writeline(line)
            for line in stderr_lines:
                logger.debug(line)
        return stdout_lines, stderr_lines

    def _create_params(self):
        """
        Creates parameters for ARM deployment
        """
        return {
            'adminUsername': {
                'value': self.admin_username
            },
            'adminPassword': {
                'value': self.admin_password
            },
            'jenkinsDnsLabelPrefix': {
                'value': self.dns_prefix
            }
        }
