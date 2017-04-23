# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import hashlib
import tempfile

import azure.cli.command_modules.project.settings as settings
import azure.cli.command_modules.project.sshconnect as ssh
import azure.cli.command_modules.project.utils as utils
from azure.cli.command_modules.project.deployments import DeployableResource
import azure.cli.core.azlogging as azlogging  # pylint: disable=invalid-name
logger = azlogging.get_az_logger(__name__)  # pylint: disable=invalid-name

# pylint: disable=line-too-long, too-many-arguments
# pylint: disable=too-many-instance-attributes


class Jenkins(DeployableResource):
    """
    Deals with creating and configuring Jenkins
    """
    scripts_version = 'v0.4.0'

    def __init__(self, resource_group,
                 admin_username, admin_password,
                 client_id, client_secret,
                 git_repo_url, dns_prefix, location, container_registry_url,
                 service_name, project_name, pipeline_name):
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
        self.pipeline_name = pipeline_name

    def deploy(self):
        """
        Creates a VM, installs Jenkins on it and configures it
        """
        logger.info('Deploying Jenkins...')
        parameters = self._create_params()
        template_url = \
            'https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/101-jenkins/azuredeploy.json'
        deployment = self.deploy_template(template_url, parameters)
        deployment.add_done_callback(self._deployment_completed)
        return deployment

    def _deployment_completed(self, completed_deployment):
        """
        Called when deployment is completed
        """
        # TODO: We could check the completed_deployment to see
        # if it failed or succeeded
        logger.info('Jenkins deployment completed.')
        self._configure()

    def _configure(self):
        """
        Configures Jenkins instance to work with the
        Azure registry and polls the GitHub repo
        """
        logger.info('Configuring Jenkins...')
        self._install_docker()
        self._install_kubectl()
        self._create_kube_config()
        self.create_pipelines()
        self._unsecure_instance()
        logger.info('Jenkins configuration completed.')

    def create_pipelines(self):
        """
        Create CI and CD pipelines
        """
        self._add_ci_job()
        self._add_cd_job()

    def _get_kube_config(self):
        """
        Gets the .kube/config file from Kubernetes master
        """
        project_settings = settings.Project()
        dns_prefix = project_settings.cluster_name
        location = project_settings.location
        user = project_settings.admin_username

        local_kube_config = tempfile.NamedTemporaryFile().name
        ssh_client = ssh.SSHConnect(
            dns_prefix, location, user, ssh_private_key=project_settings.ssh_private_key)
        ssh_client.get('.kube/config', local_kube_config)
        return local_kube_config

    def _create_kube_config(self):
        """
        Creates the .kube/config file
        """
        logger.info('Creating .kube/config file...')
        local_kube_config = self._get_kube_config()
        # Copy the local kube config to Jenkins VM
        with ssh.SSHConnect(self.dns_prefix, self.location, user_name=self.admin_username, password=self.admin_password) as ssh_client:
            ssh_client.run_command('sudo mkdir -p /var/lib/jenkins/.kube')
            ssh_client.put(local_kube_config, '/home/azureuser/config')
            ssh_client.run_command(
                'sudo cp /home/azureuser/config /var/lib/jenkins/.kube && sudo chown --from root jenkins /var/lib/jenkins/.kube && sudo chown --from root jenkins /var/lib/jenkins/.kube/config')

    def _install_kubectl(self):
        """
        Installs kubectl on the Jenkins VM
        """
        logger.info('Installing kubectl...')
        command = 'curl -sSLO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl | sh && chmod +x ./kubectl && sudo mv ./kubectl /usr/local/bin/kubectl'
        self._run_remote_command(command)

    def _get_hash(self):
        """
        Gets the hashed string
        """
        input_string = '{}-{}-{}'.format(self.project_name,
                                         self.service_name, self.git_repo_url)
        hash_value = hashlib.sha1(input_string.encode('utf-8'))
        digest = hash_value.hexdigest()
        return digest[:8]

    def _get_ci_job_name(self):
        """
        Gets the name for the CI job
        """
        return '{}-{}-build'.format(self.pipeline_name, self._get_hash())

    def _get_ci_job_display_name(self):
        """
        Gets the display name for CI job
        """
        return '{} build'.format(self.pipeline_name)

    def _get_cd_job_name(self):
        """
        Gets the name for the CD job
        """
        return '{}-{}-deploy'.format(self.pipeline_name, self._get_hash())

    def _get_cd_job_display_name(self):
        """
        Gets the display name for CD job
        """
        return '{} deploy'.format(self.pipeline_name)

    def _get_image_repo_name(self):
        """
        Gets the image repository name
        """
        return self.pipeline_name.lower()

    def _get_jenkins_url(self):
        """
        Gets the Jenkins URL
        """
        return 'http://127.0.0.1:8080'

    def _add_cd_job(self):
        """
        Adds the CD job to Jenkins instance
        """
        logger.info('Adding CD job...')
        add_cd_job_script = \
            'https://raw.githubusercontent.com/PeterJausovec/azure-devops-utils/master/jenkins/add-cd-job.sh'
        args = ' '.join([
            '-j {}'.format(self._get_jenkins_url()),
            '-ju {}'.format('admin'),
            '-cdn {}'.format(self._get_cd_job_name()),
            '-cddn "{}"'.format(self._get_cd_job_display_name())
        ])
        command = 'curl {} | sudo bash -s -- {}'.format(
            add_cd_job_script, args)
        self._run_remote_command(command)

    def _install_docker(self):
        """
        Installs Docker on the Jenkins VM
        and ensures Jenkins has access to it
        """
        logger.info('Installing Docker...')
        command = 'sudo curl -sSL https://get.docker.com/ | sh && sudo gpasswd -a jenkins docker && skill -KILL -u jenkins && sudo service jenkins restart'
        self._run_remote_command(command)

    def _add_ci_job(self):
        """
        Adds the CI job to Jenkins instance
        """
        logger.info('Adding CI job...')
        add_build_job_script_url = \
            'https://raw.githubusercontent.com/PeterJausovec/azure-devops-utils/master/jenkins/add-docker-build-job.sh'
        args = ' '.join([
            '-j {}'.format(self._get_jenkins_url()),
            '-ju {}'.format('admin'),
            '-g {}'.format(self.git_repo_url),
            '-r {}'.format(self.container_registry_url),
            '-ru {}'.format(self.client_id),
            '-rp {}'.format(self.client_secret),
            '-rr {}'.format(self._get_image_repo_name()),
            '-jsn {}'.format(self._get_ci_job_name()),
            '-jdn "{}"'.format(self._get_ci_job_display_name()),
            '-cdn {}'.format(self._get_cd_job_name()),
            '-sn {}'.format(self.service_name),
            '-sps {}'.format('"* * * * *"'),
            '-al {}'.format(
                'https://raw.githubusercontent.com/PeterJausovec/azure-devops-utils/master')])
        command = 'curl --silent {} | sudo bash -s -- {}'.format(
            add_build_job_script_url, args)
        self._run_remote_command(command)

    def _unsecure_instance(self):
        """
        Unsecures the Jenkins instance by setting
        the useSecurity tag in config.xml to false
        """
        logger.info('Unsecuring Jenkins instance...')
        unsecure_script_url = \
            'https://raw.githubusercontent.com/Azure/azure-devops-utils/{}/jenkins/unsecure-jenkins-instance.sh'.format(
                self.scripts_version)
        command = 'curl --silent {} | sudo bash -s --'.format(
            unsecure_script_url)
        self._run_remote_command(command)

    def _run_remote_command(self, command):
        """
        Runs a command on Jenkins instance
        """
        with ssh.SSHConnect(self.dns_prefix, self.location, user_name=self.admin_username, password=self.admin_password) as ssh_client:
            ssh_client.run_command(command)

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
            'jenkinsDnsPrefix': {
                'value': self.dns_prefix
            }
        }
