# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import paramiko

import azure.cli.command_modules.project.utils as utils
from azure.cli.command_modules.project.deployments import DeployableResource
import azure.cli.core.azlogging as azlogging  # pylint: disable=invalid-name
logger = azlogging.get_az_logger(__name__) # pylint: disable=invalid-name

# pylint: disable=line-too-long, too-many-arguments, too-many-instance-attributes
class Jenkins(DeployableResource):
    """
    Deals with creating and configuring Jenkins
    """
    scripts_version = 'v0.4.0'

    def __init__(self, resource_group,
                 admin_username, admin_password,
                 client_id, client_secret,
                 git_repo_url, dns_prefix, location, container_registry_url,
                 service_name, project_name):
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
        self.location = location
        self.container_registry_url = container_registry_url
        self.service_name = service_name
        self.project_name = project_name

    def deploy(self):
        """
        Creates a VM, installs Jenkins on it and configures it
        """
        parameters = self._create_params()
        template_url = \
            'https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/101-jenkins-master-on-ubuntu/azuredeploy.json'
        deployment = self.deploy_template(template_url, parameters)
        deployment.add_done_callback(self._deployment_completed)
        return deployment

    def _deployment_completed(self, completed_deployment):
        """
        Called when deployment is completed
        """
        # TODO: We could check the completed_deployment to see
        # if it failed or succeeded
        utils.writeline('Jenkins deployment completed.')
        self.configure()

    def configure(self):
        """
        Configures Jenkins instance to work with the
        Azure registry and polls the GitHub repo
        """
        utils.writeline('Configuring Jenkins...')
        self._install_docker()
        self._add_docker_build_job()
        # TODO: We should unsecure the instance first
        # and then setup everything without using username/password
        # Current script requires a username and password, that's why we
        # are running unsecure script at the end.
        self._unsecure_instance()
        utils.writeline('Jenkins configuration completed.')

    def _instal_kubectl(self):
        """
        Installs kubectl on the Jenkins VM
        """
        command = 'curl -sSLO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl | sh && chmod +x ./kubectl && sudo mv ./kubectl /usr/local/bin/kubectl'
        self._run_remote_command(command)

    def _get_ci_job_name(self):
        """
        Gets the name for the CI job
        """
        return '{}-CI'.format(self.service_name)

    def _get_cd_job_name(self):
        """
        Gets the name for the CD job
        """
        return '{}-CD'.format(self.service_name)

    def _get_image_repo_name(self):
        """
        Gets the image repository name
        """
        return '{}/{}'.format(self.project_name, self.service_name)

    def _add_cd_job(self):
        """
        Adds the CD job to Jenkins instance
        """
        pass

    def _install_docker(self):
        """
        Installs Docker on the Jenkins VM
        and ensures Jenkins has access to it
        """
        command = 'sudo curl -sSL https://get.docker.com/ | sh && sudo gpasswd -a jenkins docker && skill -KILL -u jenkins && sudo service jenkins restart'
        self._run_remote_command(command)

    def _add_ci_job(self):
        """
        Adds the CI job to Jenkins instance
        """
        initial_password = self._get_initial_password()
        add_build_job_script_url = \
            'https://raw.githubusercontent.com/PeterJausovec/azure-devops-utils/master/jenkins/add-docker-build-job.sh'
            # 'https://raw.githubusercontent.com/Azure/azure-devops-utils/{}/jenkins/add-docker-build-job.sh'.format(self.scripts_version)
        args = ' '.join([
            '-j {}'.format('http://127.0.0.1:8080'),
            '-ju {}'.format('admin'),
            '-jp {}'.format(initial_password),
            '-g {}'.format(self.git_repo_url),
            '-r {}'.format(self.container_registry_url),
            '-ru {}'.format(self.client_id),
            '-rp {}'.format(self.client_secret),
            '-jsn {}'.format(self._get_ci_job_name()),
            '-sn {}'.format(self.service_name),
            '-rr {}'.format(self._get_image_repo_name()),
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
        stdout, _ = self._run_remote_command(command)
        return stdout[0].strip()

    def _unsecure_instance(self):
        """
        Unsecures the Jenkins instance by setting
        the useSecurity tag in config.xml to false
        """
        unsecure_script_url = \
            'https://raw.githubusercontent.com/Azure/azure-devops-utils/{}/jenkins/unsecure-jenkins-instance.sh'.format(self.scripts_version)
        command = 'curl --silent {} | sudo bash -s --'.format(unsecure_script_url)
        self._run_remote_command(command)

    def _run_remote_command(self, command):
        """
        Runs a command on remote Jenkins instance
        """
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('{}.{}.cloudapp.azure.com'.format(self.dns_prefix, self.location),
                    username=self.admin_username,
                    password=self.admin_password)

        _, stdout, stderr = ssh.exec_command(command)
        stdout_lines = stdout.readlines()
        stderr_lines = stderr.readlines()
        for line in stdout_lines:
            logger.debug(line)
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
