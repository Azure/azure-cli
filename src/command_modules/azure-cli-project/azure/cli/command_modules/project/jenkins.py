# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import paramiko

from azure.cli.command_modules.project.deployments import DeployableResource
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
        add_build_job_script_url = \
            'https://raw.githubusercontent.com/Azure/azure-devops-utils/v0.2.0/jenkins/add-docker-build-job.sh'
        args = ' '.join([
            '-j {}'.format('http://localhost:8080'),
            '-ju {}'.format('admin'),
            '-jp {}'.format(self._get_initial_password()),
            '-g {}'.format(self.git_repo_url),
            '-r {}'.format(self.container_registry_url),
            '-ru {}'.format(self.client_id),
            '-rp {}'.format(self.client_secret),
            '-rr {}/{}'.format(self.admin_username, 'myfirstapp')])
        command = 'curl --silent {} | sudo bash -s -- {}'.format(add_build_job_script_url, args)
        self._run_remote_command(command)

    def _get_initial_password(self):
        """
        Gets the initial Jenkins password from
        """
        command = 'sudo cat /var/lib/jenkins/secrets/initialAdminPassword'
        stdout, _ = self._run_remote_command(command, False)
        return stdout.readline().strip()

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
        ssh.connect('{}@{}.westus.cloudapp.com'.format(self.dns_prefix, self.admin_username),
                    username=self.admin_username,
                    password=self.admin_password)
        if output:
            _, stdout, stderr = ssh.exec_command(command)
            for line in stdout.readlines():
                print line
            for line in stderr.readlines():
                print 'ERR: ' + line
        ssh.close()
        return stdout, stderr

    def _create_params(self):
        """
        Creates parameters for ARM deployment
        """
        # TODO: USE BASIC ARM TEMPLATE!!
        return {
            'adminUsername': {
                'value': self.admin_username
            },
            'adminPassword': {
                'value': self.admin_password
            },
            'jenkinsDnsLabelPrefix': {
                'value': self.dns_prefix
            },
            'servicePrincipalClientId': {
                'value': self.client_id
            },
            'servicePrincipalClientSecret': {
                'value': self.client_secret
            },
            'gitRepository': {
                'value': self.git_repo_url
            }
        }
