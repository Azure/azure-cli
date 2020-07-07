# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import re
import time
import uuid

try:
    from urllib.parse import quote, urlparse
except ImportError:
    from urllib import quote  #pylint: disable=no-name-in-module
    from urlparse import urlparse  #pylint: disable=import-error
from vsts_info_provider import VstsInfoProvider
from continuous_delivery import ContinuousDelivery
from continuous_delivery.models import (AuthorizationInfo, AuthorizationInfoParameters, BuildConfiguration,
                                        CiArtifact, CiConfiguration, ProvisioningConfiguration,
                                        ProvisioningConfigurationSource, ProvisioningConfigurationTarget,
                                        SlotSwapConfiguration, SourceRepository, CreateOptions)
from aex_accounts import Account

# Use this class to setup or remove continuous delivery mechanisms for Azure web sites using VSTS build and release
class ContinuousDeliveryManager(object):
    def __init__(self, progress_callback):
        """
        Use this class to setup or remove continuous delivery mechanisms for Azure web sites using VSTS build and release
        :param progress_callback: method of the form func(count, total, message)
        """
        self._update_progress = progress_callback or self._skip_update_progress
        self._azure_info = _AzureInfo()
        self._repo_info = _RepositoryInfo()

    def get_vsts_app_id(self):
        """
        Use this method to get the 'resource' value for creating an Azure token to be used by VSTS
        :return: App id for VSTS
        """
        return '499b84ac-1321-427f-aa17-267ca6975798'

    def set_azure_web_info(self, resource_group_name, website_name, credentials,
                           subscription_id, subscription_name, tenant_id, webapp_location):
        """
        Call this method before attempting to setup continuous delivery to setup the azure settings
        :param resource_group_name:
        :param website_name:
        :param credentials:
        :param subscription_id:
        :param subscription_name:
        :param tenant_id:
        :param webapp_location:
        :return:
        """
        self._azure_info.resource_group_name = resource_group_name
        self._azure_info.website_name = website_name
        self._azure_info.credentials = credentials
        self._azure_info.subscription_id = subscription_id
        self._azure_info.subscription_name = subscription_name
        self._azure_info.tenant_id = tenant_id
        self._azure_info.webapp_location = webapp_location

    def set_repository_info(self, repo_url, branch, git_token, private_repo_username, private_repo_password):
        """
        Call this method before attempting to setup continuous delivery to setup the source control settings
        :param repo_url: URL of the code repo
        :param branch: repo branch
        :param git_token: git token
        :param private_repo_username: private repo username
        :param private_repo_password: private repo password
        :return:
        """
        self._repo_info.url = repo_url
        self._repo_info.branch = branch
        self._repo_info.git_token = git_token
        self._repo_info._private_repo_username = private_repo_username
        self._repo_info._private_repo_password = private_repo_password

    def remove_continuous_delivery(self):
        """
        To be Implemented
        :return:
        """
        # TODO: this would be called by appservice web source-control delete
        return

    def setup_continuous_delivery(self, swap_with_slot, app_type_details, cd_project_url, create_account,
                                  vsts_app_auth_token, test, webapp_list):
        """
        Use this method to setup Continuous Delivery of an Azure web site from a source control repository.
        :param swap_with_slot: the slot to use for deployment
        :param app_type_details: the details of app that will be deployed. i.e. app_type = Python, python_framework = Django etc.
        :param cd_project_url: CD Project url in the format of https://<accountname>.visualstudio.com/<projectname> 
        :param create_account: Boolean value to decide if account need to be created or not
        :param vsts_app_auth_token: Authentication token for vsts app
        :param test: Load test webapp name
        :param webapp_list: Existing webapp list
        :return: a message indicating final status and instructions for the user
        """

        branch = self._repo_info.branch or 'refs/heads/master'
        self._validate_cd_project_url(cd_project_url)
        vsts_account_name = self._get_vsts_account_name(cd_project_url)

        # Verify inputs before we start generating tokens
        source_repository, account_name, team_project_name = self._get_source_repository(self._repo_info.url,
            self._repo_info.git_token, branch, self._azure_info.credentials, 
            self._repo_info._private_repo_username, self._repo_info._private_repo_password)
        self._verify_vsts_parameters(vsts_account_name, source_repository)
        vsts_account_name = vsts_account_name or account_name
        cd_project_name = team_project_name or self._azure_info.website_name
        account_url = 'https://{}.visualstudio.com'.format(quote(vsts_account_name))
        portalext_account_url = 'https://{}.portalext.visualstudio.com'.format(quote(vsts_account_name))

        # VSTS Account using AEX APIs
        account_created = False
        if create_account:
            self.create_vsts_account(self._azure_info.credentials, vsts_account_name)
            account_created = True
        
        # Create ContinuousDelivery client
        cd = ContinuousDelivery('3.2-preview.1', portalext_account_url, self._azure_info.credentials)

        # Construct the config body of the continuous delivery call
        build_configuration = self._get_build_configuration(app_type_details)
        source = ProvisioningConfigurationSource('codeRepository', source_repository, build_configuration)
        auth_info = AuthorizationInfo('Headers', AuthorizationInfoParameters('Bearer ' + vsts_app_auth_token))
        target = self.get_provisioning_configuration_target(auth_info, swap_with_slot, test, webapp_list)
        ci_config = CiConfiguration(CiArtifact(name=cd_project_name))
        config = ProvisioningConfiguration(None, source, target, ci_config)

        # Configure the continuous deliver using VSTS as a backend
        response = cd.provisioning_configuration(config)
        if response.ci_configuration.result.status == 'queued':
            final_status = self._wait_for_cd_completion(cd, response)
            return self._get_summary(final_status, account_url, vsts_account_name, account_created, self._azure_info.subscription_id,
                                     self._azure_info.resource_group_name, self._azure_info.website_name)
        else:
            raise RuntimeError('Unknown status returned from provisioning_configuration: ' + response.ci_configuration.result.status)
    
    def create_vsts_account(self, creds, vsts_account_name):
        aex_url = 'https://app.vsaex.visualstudio.com'
        accountClient = Account('4.0-preview.1', aex_url, creds)
        self._update_progress(0, 100, 'Creating or getting Team Services account information')            
        regions = accountClient.regions()
        if regions.count == 0:
            raise RuntimeError('Region details not found.')
        region_name = regions.value[0].name
        create_account_reponse = accountClient.create_account(vsts_account_name, region_name)
        if create_account_reponse.id:
            self._update_progress(5, 100, 'Team Services account created')
        else:
            raise RuntimeError('Account creation failed.')
        
    def _validate_cd_project_url(self, cd_project_url):
        if -1 == cd_project_url.find('visualstudio.com') or -1 == cd_project_url.find('https://'):
            raise RuntimeError('Project URL should be in format https://<accountname>.visualstudio.com/<projectname>')

    def _get_vsts_account_name(self, cd_project_url):
        return (cd_project_url.split('.visualstudio.com', 1)[0]).split('https://', 1)[1]

    def get_provisioning_configuration_target(self, auth_info, swap_with_slot, test, webapp_list):
        swap_with_slot_config = None if swap_with_slot is None else SlotSwapConfiguration(swap_with_slot)
        slotTarget = ProvisioningConfigurationTarget('azure', 'windowsAppService', 'production', 'Production',
                                                 self._azure_info.subscription_id, self._azure_info.subscription_name, 
                                                 self._azure_info.tenant_id, self._azure_info.website_name, 
                                                 self._azure_info.resource_group_name, self._azure_info.webapp_location, 
                                                 auth_info, swap_with_slot_config)
        target = [slotTarget]
        if test is not None:
            create_options = None
            if webapp_list is not None and not any(s.name == test for s in webapp_list) :
                app_service_plan_name = 'ServicePlan'+ str(uuid.uuid4())[:13]
                create_options = CreateOptions(app_service_plan_name, 'Standard', self._azure_info.website_name)
            testTarget = ProvisioningConfigurationTarget('azure', 'windowsAppService', 'test', 'Load Test',
                                                    self._azure_info.subscription_id,
                                                    self._azure_info.subscription_name, self._azure_info.tenant_id,
                                                    test, self._azure_info.resource_group_name,
                                                    self._azure_info.webapp_location, auth_info, None, create_options)
            target.append(testTarget)
        return target        

    def _verify_vsts_parameters(self, cd_account, source_repository):
        # if provider is vsts and repo is not vsts then we need the account name
        if source_repository.type in ['Github', 'ExternalGit'] and not cd_account:
            raise RuntimeError('You must provide a value for cd-account since your repo-url is not a Team Services repository.')

    def _get_build_configuration(self, app_type_details):
        accepted_app_types = ['AspNet', 'AspNetCore', 'NodeJS', 'PHP', 'Python']
        accepted_nodejs_task_runners = ['None', 'Gulp', 'Grunt']
        accepted_python_frameworks = ['Bottle', 'Django', 'Flask']
        accepted_python_versions = ['Python 2.7.12 x64', 'Python 2.7.12 x86', 'Python 2.7.13 x64', 'Python 2.7.13 x86', 'Python 3.5.3 x64', 'Python 3.5.3 x86', 'Python 3.6.0 x64', 'Python 3.6.0 x86', 'Python 3.6.2 x64', 'Python 3.6.1 x86']
        
        build_configuration = None
        working_directory = app_type_details.get('app_working_dir')
        app_type = app_type_details.get('cd_app_type')
        if (app_type == 'AspNet') :
            build_configuration = BuildConfiguration('AspNetWap', working_directory)
        elif (app_type == 'AspNetCore') or (app_type == 'PHP') :
            build_configuration = BuildConfiguration(app_type, working_directory)
        elif app_type == 'NodeJS' :
            nodejs_task_runner = app_type_details.get('nodejs_task_runner')
            if any(s == nodejs_task_runner for s in accepted_nodejs_task_runners) :
                build_configuration = BuildConfiguration(app_type, working_directory, nodejs_task_runner)
            else:
                raise RuntimeError("The nodejs_task_runner %s was not understood. Accepted values: %s." % (nodejs_task_runner, accepted_nodejs_task_runners))
        elif app_type == 'Python' :
            python_framework = app_type_details.get('python_framework')
            python_version = app_type_details.get('python_version')
            django_setting_module = 'DjangoProjectName.settings'
            flask_project_name = 'FlaskProjectName'
            if any(s == python_framework for s in accepted_python_frameworks) :
                if any(s == python_version for s in accepted_python_versions) :
                    python_version = python_version.replace(" ", "").replace(".", "")
                    build_configuration = BuildConfiguration(app_type, working_directory, None, python_framework, python_version, django_setting_module, flask_project_name)
                else :
                    raise RuntimeError("The python_version %s was not understood. Accepted values: %s." % (python_version, accepted_python_versions))
            else:
                raise RuntimeError("The python_framework %s was not understood. Accepted values: %s." % (python_framework, accepted_python_frameworks))
        else:
            raise RuntimeError("The app_type %s was not understood. Accepted values: %s." % (app_type, accepted_app_types))
        return build_configuration

    def _get_source_repository(self, uri, token, branch, cred, username, password):
        # Determine the type of repository (TfsGit, github, tfvc, externalGit)
        # Find the identifier and set the properties.
        # Default is externalGit
        type = 'Git'
        identifier = uri
        account_name = None
        team_project_name = None
        auth_info = AuthorizationInfo('UsernamePassword', AuthorizationInfoParameters(None, None, username, password))
        
        match = re.match(r'[htps]+\:\/\/(.+)\.visualstudio\.com.*\/_git\/(.+)', uri, re.IGNORECASE)
        if match:
            type = 'TfsGit'
            account_name = match.group(1)
            # we have to get the repo id as the identifier
            info = self._get_vsts_info(uri, cred)
            identifier = info.repository_info.id
            team_project_name = info.repository_info.project_info.name
            auth_info = None
        else:
            match = re.match(r'[htps]+\:\/\/github\.com\/(.+)', uri, re.IGNORECASE)
            if match:
                if token is not None:                    
                    type = 'Github'
                    identifier = match.group(1).replace(".git", "")
                    auth_info = AuthorizationInfo('PersonalAccessToken', AuthorizationInfoParameters(None, token))
            else:
                match = re.match(r'[htps]+\:\/\/(.+)\.visualstudio\.com\/(.+)', uri, re.IGNORECASE)
                if match:
                    type = 'TFVC'
                    identifier = match.group(2)
                    account_name = match.group(1)
                    auth_info = None
        sourceRepository = SourceRepository(type, identifier, branch, auth_info)
        return sourceRepository, account_name, team_project_name

    def _get_vsts_info(self, vsts_repo_url, cred):
        vsts_info_client = VstsInfoProvider('3.2-preview', vsts_repo_url, cred)
        return vsts_info_client.get_vsts_info()

    def _wait_for_cd_completion(self, cd, response):
        # Wait for the configuration to finish and report on the status
        step = 5
        max = 100
        self._update_progress(step, max, 'Setting up Team Services continuous deployment')
        config = cd.get_provisioning_configuration(response.id)
        while config.ci_configuration.result.status == 'queued' or config.ci_configuration.result.status == 'inProgress':
            step += 5 if step + 5 < max else 0
            self._update_progress(step, max, 'Setting up Team Services continuous deployment (' + config.ci_configuration.result.status + ')')
            time.sleep(2)
            config = cd.get_provisioning_configuration(response.id)
        if config.ci_configuration.result.status == 'failed':
            self._update_progress(max, max, 'Setting up Team Services continuous deployment (FAILED)')
            raise RuntimeError(config.ci_configuration.result.status_message)
        self._update_progress(max, max, 'Setting up Team Services continuous deployment (SUCCEEDED)')
        return config

    def _get_summary(self, provisioning_configuration, account_url, account_name, account_created, subscription_id, resource_group_name, website_name):
        summary = '\n'
        if not provisioning_configuration: return None

        # Add the vsts account info
        if not account_created:
            summary += "The Team Services account '{}' was updated to handle the continuous delivery.\n".format(account_url)
        else:
            summary += "The Team Services account '{}' was created to handle the continuous delivery.\n".format(account_url)

        # Add the subscription info
        website_url = 'https://portal.azure.com/#resource/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Web/sites/{}/vstscd'.format(
            quote(subscription_id), quote(resource_group_name), quote(website_name))
        summary += 'You can check on the status of the Azure web site deployment here:\n'
        summary += website_url + '\n'

        # setup the build url and release url
        build_url = ''
        release_url = ''
        if provisioning_configuration.ci_configuration and provisioning_configuration.ci_configuration.project:
            project_id = provisioning_configuration.ci_configuration.project.id
            if provisioning_configuration.ci_configuration.build_definition:
                build_url = '{}/{}/_build?_a=simple-process&definitionId={}'.format(
                    account_url, quote(project_id), quote(provisioning_configuration.ci_configuration.build_definition.id))
            if provisioning_configuration.ci_configuration.release_definition:
                release_url = '{}/{}/_apps/hub/ms.vss-releaseManagement-web.hub-explorer?definitionId={}&_a=releases'.format(
                    account_url, quote(project_id), quote(provisioning_configuration.ci_configuration.release_definition.id))

        return ContinuousDeliveryResult(account_created, account_url, resource_group_name,
                                        subscription_id, website_name, website_url, summary,
                                        build_url, release_url, provisioning_configuration)

    def _skip_update_progress(self, count, total, message):
        return


class _AzureInfo(object):
    def __init__(self):
        self.resource_group_name = None
        self.website_name = None
        self.credentials = None
        self.subscription_id = None
        self.subscription_name = None
        self.tenant_id = None
        self.webapp_location = None


class _RepositoryInfo(object):
    def __init__(self):
        self.url = None
        self.branch = None
        self.git_token = None
        self.private_repo_username = None
        self.private_repo_password = None


class ContinuousDeliveryResult(object):
    def __init__(self, account_created, account_url, resource_group, subscription_id, website_name, cd_url, message, build_url, release_url, final_status):
        self.vsts_account_created = account_created
        self.vsts_account_url = account_url
        self.vsts_build_def_url = build_url
        self.vsts_release_def_url = release_url
        self.azure_resource_group = resource_group
        self.azure_subscription_id = subscription_id
        self.azure_website_name = website_name
        self.azure_continuous_delivery_url = cd_url
        self.status = 'SUCCESS'
        self.status_message = message
        self.status_details = final_status
