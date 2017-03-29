# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import paramiko

import azure.cli.command_modules.project.settings as settings
import azure.cli.command_modules.project.utils as utils
from azure.cli.command_modules.project.deployments import DeployableResource
import azure.cli.core.azlogging as azlogging  # pylint: disable=invalid-name
import tempfile
import hashlib
logger = azlogging.get_az_logger(__name__)  # pylint: disable=invalid-name

# pylint: disable=line-too-long, too-many-arguments,
# too-many-instance-attributes


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
        self._install_kubectl()
        self._create_kube_config()
        self._add_ci_job()
        self._add_cd_job()
        # TODO: We should unsecure the instance first
        # and then setup everything without using username/password
        # Current script requires a username and password, that's why we
        # are running unsecure script at the end.
        self._unsecure_instance()
        utils.writeline('Jenkins configuration completed.')

    def _get_hostname(self):
        """
        Gets the Jenkins hostname
        """
        return '{}.{}.cloudapp.azure.com'.format(self.dns_prefix, self.location)

    def _get_kube_config(self):
        """
        Gets the .kube/config file from Kubernetes master
        """
        project_settings = settings.Project()
        dns_prefix = project_settings.cluster_name
        location = project_settings.location
        user = project_settings.admin_username

        local_kube_config = tempfile.NamedTemporaryFile().name
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('{}.{}.cloudapp.azure.com'.format(
            dns_prefix, location), username=user)
        scp = paramiko.SFTPClient.from_transport(ssh.get_transport())
        scp.get('.kube/config', local_kube_config)
        scp.close()
        ssh.close()

        return local_kube_config

    def _create_kube_config(self):
        """
        Creates the .kube/config file
        """
        local_kube_config = self._get_kube_config()
        # Copy the local kube config to Jenkins VM
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        hostname = self._get_hostname()
        ssh.connect(hostname,
                    username=self.admin_username,
                    password=self.admin_password)
        scp = paramiko.SFTPClient.from_transport(ssh.get_transport())
        ssh.exec_command('sudo mkdir -p /var/lib/jenkins/.kube')
        scp.put(local_kube_config, '/home/azureuser/config')
        ssh.exec_command(
            'sudo cp /home/azureuser/config /var/lib/jenkins/.kube && sudo chown --from root jenkins /var/lib/jenkins/.kube')

    def _install_kubectl(self):
        """
        Installs kubectl on the Jenkins VM
        """
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
        # TODO: Remove -x once we figure out proper naming
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
        # TODO: Make sure this is right
        return self.pipeline_name

    def _get_jenkins_url(self):
        """
        Gets the Jenkins URL
        """
        return 'http://127.0.0.1:8080'

    def _add_cd_job(self):
        """
        Adds the CD job to Jenkins instance
        """
        add_cd_job_script = \
            'https://raw.githubusercontent.com/PeterJausovec/azure-devops-utils/master/jenkins/add-cd-job.sh'
        args = ' '.join([
            '-j {}'.format(self._get_jenkins_url()),
            '-ju {}'.format('admin'),
            '-g {}'.format(self.git_repo_url),
            '-cin {}'.format(self._get_ci_job_name()),
            '-cdn {}'.format(self._get_cd_job_name()),
            '-cddn "{}"'.format(self._get_cd_job_display_name())
        ])
        command = 'curl {} | bash -s -- {}'.format(add_cd_job_script, args)
        utils.writeline(command)
        self._run_remote_command(command)

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
        add_build_job_script_url = \
            'https://raw.githubusercontent.com/PeterJausovec/azure-devops-utils/master/jenkins/add-docker-build-job.sh'
        args = ' '.join([
            '-j {}'.format(self._get_jenkins_url()),
            '-ju {}'.format('admin'),
            '-g {}'.format(self.git_repo_url),
            '-r {}'.format(self.container_registry_url),
            '-ru {}'.format(self.client_id),
            '-rp {}'.format(self.client_secret),
            '-jsn {}'.format(self._get_ci_job_name()),
            '-jdn "{}"'.format(self._get_ci_job_display_name()),
            '-cdn {}'.format(self._get_cd_job_name()),
            '-sn {}'.format(self.service_name),
            '-rr {}'.format(self._get_image_repo_name()),
            '-sps {}'.format('"* * * * *"'),
            '-al {}'.format(
                'https://raw.githubusercontent.com/PeterJausovec/azure-devops-utils/master'),
            '-rr {}/{}'.format(self.admin_username, self.service_name)])
        command = 'curl --silent {} | sudo bash -s -- {}'.format(
            add_build_job_script_url, args)
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
            'https://raw.githubusercontent.com/Azure/azure-devops-utils/{}/jenkins/unsecure-jenkins-instance.sh'.format(
                self.scripts_version)
        command = 'curl --silent {} | sudo bash -s --'.format(
            unsecure_script_url)
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
            utils.writeline(line)
        for line in stderr_lines:
            utils.writeline(line)
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
