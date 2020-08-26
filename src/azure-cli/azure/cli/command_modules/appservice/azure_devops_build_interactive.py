# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import time
import json
import logging
from knack.prompting import prompt_choice_list, prompt_y_n, prompt
from knack.util import CLIError
from azure_functions_devops_build.constants import (
    LINUX_CONSUMPTION,
    LINUX_DEDICATED,
    WINDOWS,
    PYTHON,
    NODE,
    DOTNET,
    POWERSHELL
)
from azure_functions_devops_build.exceptions import (
    GitOperationException,
    RoleAssignmentException,
    LanguageNotSupportException,
    BuildErrorException,
    ReleaseErrorException,
    GithubContentNotFound,
    GithubUnauthorizedError,
    GithubIntegrationRequestError
)
from .azure_devops_build_provider import AzureDevopsBuildProvider
from .custom import list_function_app, show_webapp, get_app_settings
from .utils import str2bool

# pylint: disable=too-many-instance-attributes,too-many-public-methods

SUPPORTED_SCENARIOS = ['AZURE_DEVOPS', 'GITHUB_INTEGRATION']
SUPPORTED_SOURCECODE_LOCATIONS = ['Current Directory', 'Github']
SUPPORTED_LANGUAGES = {
    'python': PYTHON,
    'node': NODE,
    'dotnet': DOTNET,
    'powershell': POWERSHELL,
}
BUILD_QUERY_FREQUENCY = 5  # sec
RELEASE_COMPOSITION_DELAY = 1  # sec


class AzureDevopsBuildInteractive(object):
    """Implement the basic user flow for a new user wanting to do an Azure DevOps build for Azure Functions

    Attributes:
        cmd : the cmd input from the command line
        logger : a knack logger to log the info/error messages
    """

    def __init__(self, cmd, logger, functionapp_name, organization_name, project_name, repository_name,
                 overwrite_yaml, allow_force_push, github_pat, github_repository):
        self.adbp = AzureDevopsBuildProvider(cmd.cli_ctx)
        self.cmd = cmd
        self.logger = logger
        self.cmd_selector = CmdSelectors(cmd, logger, self.adbp)
        self.functionapp_name = functionapp_name
        self.storage_name = None
        self.resource_group_name = None
        self.functionapp_language = None
        self.functionapp_type = None
        self.organization_name = organization_name
        self.project_name = project_name
        self.repository_name = repository_name

        self.github_pat = github_pat
        self.github_repository = github_repository
        self.github_service_endpoint_name = None

        self.repository_remote_name = None
        self.service_endpoint_name = None
        self.build_definition_name = None
        self.release_definition_name = None
        self.build_pool_name = "Default"
        self.release_pool_name = "Hosted VS2017"
        self.artifact_name = "drop"

        self.settings = []
        self.build = None
        # These are used to tell if we made new objects
        self.scenario = None  # see SUPPORTED_SCENARIOS
        self.created_organization = False
        self.created_project = False
        self.overwrite_yaml = str2bool(overwrite_yaml)
        self.allow_force_push = allow_force_push

    def interactive_azure_devops_build(self):
        """Main interactive flow which is the only function that should be used outside of this
        class (the rest are helpers)"""

        scenario = self.check_scenario()
        if scenario == 'AZURE_DEVOPS':
            return self.azure_devops_flow()
        if scenario == 'GITHUB_INTEGRATION':
            return self.github_flow()
        raise CLIError('Unknown scenario')

    def azure_devops_flow(self):
        self.process_functionapp()
        self.pre_checks_azure_devops()
        self.process_organization()
        self.process_project()
        self.process_yaml_local()
        self.process_local_repository()
        self.process_remote_repository()
        self.process_functionapp_service_endpoint('AZURE_DEVOPS')
        self.process_extensions()
        self.process_build_and_release_definition_name('AZURE_DEVOPS')
        self.process_build('AZURE_DEVOPS')
        self.wait_for_build()
        self.process_release()
        self.logger.warning("Pushing your code to {remote}:master will now trigger another build.".format(
            remote=self.repository_remote_name
        ))
        return {
            'source_location': 'local',
            'functionapp_name': self.functionapp_name,
            'storage_name': self.storage_name,
            'resource_group_name': self.resource_group_name,
            'functionapp_language': self.functionapp_language,
            'functionapp_type': self.functionapp_type,
            'organization_name': self.organization_name,
            'project_name': self.project_name,
            'repository_name': self.repository_name,
            'service_endpoint_name': self.service_endpoint_name,
            'build_definition_name': self.build_definition_name,
            'release_definition_name': self.release_definition_name
        }

    def github_flow(self):
        self.process_github_personal_access_token()
        self.process_github_repository()
        self.process_functionapp()
        self.pre_checks_github()
        self.process_organization()
        self.process_project()
        self.process_yaml_github()
        self.process_functionapp_service_endpoint('GITHUB_INTEGRATION')
        self.process_github_service_endpoint()
        self.process_extensions()
        self.process_build_and_release_definition_name('GITHUB_INTEGRATION')
        self.process_build('GITHUB_INTEGRATION')
        self.wait_for_build()
        self.process_release()
        self.logger.warning("Setup continuous integration between {github_repo} and Azure Pipelines".format(
            github_repo=self.github_repository
        ))
        return {
            'source_location': 'Github',
            'functionapp_name': self.functionapp_name,
            'storage_name': self.storage_name,
            'resource_group_name': self.resource_group_name,
            'functionapp_language': self.functionapp_language,
            'functionapp_type': self.functionapp_type,
            'organization_name': self.organization_name,
            'project_name': self.project_name,
            'repository_name': self.github_repository,
            'service_endpoint_name': self.service_endpoint_name,
            'build_definition_name': self.build_definition_name,
            'release_definition_name': self.release_definition_name
        }

    def check_scenario(self):
        if self.repository_name:
            self.scenario = 'AZURE_DEVOPS'
        elif self.github_pat or self.github_repository:
            self.scenario = 'GITHUB_INTEGRATION'
        else:
            choice_index = prompt_choice_list(
                'Please choose Azure function source code location: ',
                SUPPORTED_SOURCECODE_LOCATIONS
            )
            self.scenario = SUPPORTED_SCENARIOS[choice_index]
        return self.scenario

    def pre_checks_azure_devops(self):
        if not AzureDevopsBuildProvider.check_git():
            raise CLIError("The program requires git source control to operate, please install git.")

        if not os.path.exists('host.json'):
            raise CLIError("There is no host.json in the current directory.{ls}"
                           "Functionapps must contain a host.json in their root".format(ls=os.linesep))

        if not os.path.exists('local.settings.json'):
            raise CLIError("There is no local.settings.json in the current directory.{ls}"
                           "Functionapps must contain a local.settings.json in their root".format(ls=os.linesep))

        try:
            local_runtime_language = self._find_local_repository_runtime_language()
        except LanguageNotSupportException as lnse:
            raise CLIError("Sorry, currently we do not support {language}.".format(language=lnse.message))

        if local_runtime_language != self.functionapp_language:
            raise CLIError("The language stack setting found in your local repository ({setting}) does not match "
                           "the language stack of your Azure function app in Azure ({functionapp}).{ls}"
                           "Please look at the FUNCTIONS_WORKER_RUNTIME setting both in your local.settings.json file "
                           "and in your Azure function app's application settings, "
                           "and ensure they match.".format(
                               setting=local_runtime_language,
                               functionapp=self.functionapp_language,
                               ls=os.linesep,
                           ))

    def pre_checks_github(self):
        if not AzureDevopsBuildProvider.check_github_file(self.github_pat, self.github_repository, 'host.json'):
            raise CLIError("There is no host.json file in the provided Github repository {repo}.{ls}"
                           "Each function app must contain a host.json in their root.{ls}"
                           "Please ensure you have read permission to the repository.".format(
                               repo=self.github_repository,
                               ls=os.linesep,
                           ))
        try:
            github_runtime_language = self._find_github_repository_runtime_language()
        except LanguageNotSupportException as lnse:
            raise CLIError("Sorry, currently we do not support {language}.".format(language=lnse.message))

        if github_runtime_language is not None and github_runtime_language != self.functionapp_language:
            raise CLIError("The language stack setting found in the provided repository ({setting}) does not match "
                           "the language stack of your Azure function app ({functionapp}).{ls}"
                           "Please look at the FUNCTIONS_WORKER_RUNTIME setting both in your local.settings.json file "
                           "and in your Azure function app's application settings, "
                           "and ensure they match.".format(
                               setting=github_runtime_language,
                               functionapp=self.functionapp_language,
                               ls=os.linesep,
                           ))

    def process_functionapp(self):
        """Helper to retrieve information about a functionapp"""
        if self.functionapp_name is None:
            functionapp = self._select_functionapp()
            self.functionapp_name = functionapp.name
        else:
            functionapp = self.cmd_selector.cmd_functionapp(self.functionapp_name)

        kinds = show_webapp(self.cmd, functionapp.resource_group, functionapp.name).kind.split(',')

        # Get functionapp settings in Azure
        app_settings = get_app_settings(self.cmd, functionapp.resource_group, functionapp.name)

        self.resource_group_name = functionapp.resource_group
        self.functionapp_type = self._find_type(kinds)

        try:
            self.functionapp_language = self._get_functionapp_runtime_language(app_settings)
            self.storage_name = self._get_functionapp_storage_name(app_settings)
        except LanguageNotSupportException as lnse:
            raise CLIError("Sorry, currently we do not support {language}.".format(language=lnse.message))

    def process_organization(self):
        """Helper to retrieve information about an organization / create a new one"""
        if self.organization_name is None:
            response = prompt_y_n('Would you like to use an existing Azure DevOps organization? ')
            if response:
                self._select_organization()
            else:
                self._create_organization()
                self.created_organization = True
        else:
            self.cmd_selector.cmd_organization(self.organization_name)

    def process_project(self):
        """Helper to retrieve information about a project / create a new one"""
        # There is a new organization so a new project will be needed
        if (self.project_name is None) and (self.created_organization):
            self._create_project()
        elif self.project_name is None:
            use_existing_project = prompt_y_n('Would you like to use an existing Azure DevOps project? ')
            if use_existing_project:
                self._select_project()
            else:
                self._create_project()
        else:
            self.cmd_selector.cmd_project(self.organization_name, self.project_name)

        self.logger.warning("To view your Azure DevOps project, "
                            "please visit https://dev.azure.com/{org}/{proj}".format(
                                org=self.organization_name,
                                proj=self.project_name
                            ))

    def process_yaml_local(self):
        """Helper to create the local azure-pipelines.yml file"""

        if os.path.exists('azure-pipelines.yml'):
            if self.overwrite_yaml is None:
                self.logger.warning("There is already an azure-pipelines.yml file in your local repository.")
                self.logger.warning("If you are using a yaml file that was not configured "
                                    "through this command, this command may fail.")
                response = prompt_y_n("Do you want to delete it and create a new one? ")
            else:
                response = self.overwrite_yaml

        if (not os.path.exists('azure-pipelines.yml')) or response:
            self.logger.warning('Creating a new azure-pipelines.yml')
            try:
                self.adbp.create_yaml(self.functionapp_language, self.functionapp_type)
            except LanguageNotSupportException as lnse:
                raise CLIError("Sorry, currently we do not support {language}.".format(language=lnse.message))

    def process_yaml_github(self):
        does_yaml_file_exist = AzureDevopsBuildProvider.check_github_file(
            self.github_pat,
            self.github_repository,
            "azure-pipelines.yml"
        )
        if does_yaml_file_exist and self.overwrite_yaml is None:
            self.logger.warning("There is already an azure-pipelines.yml file in the provided Github repository.")
            self.logger.warning("If you are using a yaml file that was not configured "
                                "through this command, this command may fail.")
            self.overwrite_yaml = prompt_y_n("Do you want to generate a new one? "
                                             "(It will be committed to the master branch of the provided repository)")

        # Create and commit the new yaml file to Github without asking
        if not does_yaml_file_exist:
            if self.github_repository:
                self.logger.warning("Creating a new azure-pipelines.yml for Github repository")
            try:
                AzureDevopsBuildProvider.create_github_yaml(
                    pat=self.github_pat,
                    language=self.functionapp_language,
                    app_type=self.functionapp_type,
                    repository_fullname=self.github_repository
                )
            except LanguageNotSupportException as lnse:
                raise CLIError("Sorry, currently this command does not support {language}. To proceed, "
                               "you'll need to configure your build manually at dev.azure.com".format(
                                   language=lnse.message))
            except GithubContentNotFound:
                raise CLIError("Sorry, the repository you provided does not exist or "
                               "you do not have sufficient permissions to write to the repository. "
                               "Please provide an access token with the proper permissions.")
            except GithubUnauthorizedError:
                raise CLIError("Sorry, you do not have sufficient permissions to commit "
                               "azure-pipelines.yml to your Github repository.")

        # Overwrite yaml file
        if does_yaml_file_exist and self.overwrite_yaml:
            self.logger.warning("Overwrite azure-pipelines.yml file in the provided Github repository")
            try:
                AzureDevopsBuildProvider.create_github_yaml(
                    pat=self.github_pat,
                    language=self.functionapp_language,
                    app_type=self.functionapp_type,
                    repository_fullname=self.github_repository,
                    overwrite=True
                )
            except LanguageNotSupportException as lnse:
                raise CLIError("Sorry, currently this command does not support {language}. To proceed, "
                               "you'll need to configure your build manually at dev.azure.com".format(
                                   language=lnse.message))
            except GithubContentNotFound:
                raise CLIError("Sorry, the repository you provided does not exist or "
                               "you do not have sufficient permissions to write to the repository. "
                               "Please provide an access token with the proper permissions.")
            except GithubUnauthorizedError:
                raise CLIError("Sorry, you do not have sufficient permissions to overwrite "
                               "azure-pipelines.yml in your Github repository.")

    def process_local_repository(self):
        has_local_git_repository = AzureDevopsBuildProvider.check_git_local_repository()
        if has_local_git_repository:
            self.logger.warning("Detected a local Git repository already exists.")

        # Collect repository name on Azure Devops
        if not self.repository_name:
            self.repository_name = prompt("Push to which Azure DevOps repository (default: {repo}): ".format(
                repo=self.project_name
            ))
            if not self.repository_name:  # Select default value
                self.repository_name = self.project_name

        expected_remote_name = self.adbp.get_local_git_remote_name(
            self.organization_name,
            self.project_name,
            self.repository_name
        )
        expected_remote_url = self.adbp.get_azure_devops_repo_url(
            self.organization_name,
            self.project_name,
            self.repository_name
        )

        # If local repository already has a remote
        # Let the user to know s/he can push to the remote directly for context update
        # Or let s/he remove the git remote manually
        has_local_git_remote = self.adbp.check_git_remote(
            self.organization_name,
            self.project_name,
            self.repository_name
        )
        if has_local_git_remote:
            raise CLIError("There's a git remote bound to {url}.{ls}"
                           "To update the repository and trigger an Azure Pipelines build, please use "
                           "'git push {remote} master'".format(
                               url=expected_remote_url,
                               remote=expected_remote_name,
                               ls=os.linesep)
                           )

        # Setup a local git repository and create a new commit on top of this context
        try:
            self.adbp.setup_local_git_repository(self.organization_name, self.project_name, self.repository_name)
        except GitOperationException as goe:
            raise CLIError("Failed to setup local git repository when running '{message}'{ls}"
                           "Please ensure you have setup git user.email and user.name".format(
                               message=goe.message, ls=os.linesep
                           ))

        self.repository_remote_name = expected_remote_name
        self.logger.warning("Added git remote {remote}".format(remote=expected_remote_name))

    def process_remote_repository(self):
        # Create remote repository if it does not exist
        repository = self.adbp.get_azure_devops_repository(
            self.organization_name,
            self.project_name,
            self.repository_name
        )
        if not repository:
            self.adbp.create_repository(self.organization_name, self.project_name, self.repository_name)

        # Force push branches if repository is not clean
        remote_url = self.adbp.get_azure_devops_repo_url(
            self.organization_name,
            self.project_name,
            self.repository_name
        )
        remote_branches = self.adbp.get_azure_devops_repository_branches(
            self.organization_name,
            self.project_name,
            self.repository_name
        )
        is_force_push = self._check_if_force_push_required(remote_url, remote_branches)

        # Prompt user to generate a git credential
        self._check_if_git_credential_required()

        # If the repository does not exist, we will do a normal push
        # If the repository exists, we will do a force push
        try:
            self.adbp.push_local_to_azure_devops_repository(
                self.organization_name,
                self.project_name,
                self.repository_name,
                force=is_force_push
            )
        except GitOperationException:
            self.adbp.remove_git_remote(self.organization_name, self.project_name, self.repository_name)
            raise CLIError("Failed to push your local repository to {url}{ls}"
                           "Please check your credentials and ensure you are a contributor to the repository.".format(
                               url=remote_url, ls=os.linesep
                           ))

        self.logger.warning("Local branches have been pushed to {url}".format(url=remote_url))

    def process_github_personal_access_token(self):
        if not self.github_pat:
            self.logger.warning("If you need to create a Github Personal Access Token, "
                                "please follow the steps found at the following link:")
            self.logger.warning("https://help.github.com/en/articles/"
                                "creating-a-personal-access-token-for-the-command-line{ls}".format(ls=os.linesep))
            self.logger.warning("The required Personal Access Token permissions can be found here:")
            self.logger.warning("https://aka.ms/azure-devops-source-repos")

        while not self.github_pat or not AzureDevopsBuildProvider.check_github_pat(self.github_pat):
            self.github_pat = prompt(msg="Github Personal Access Token: ").strip()
        self.logger.warning("Successfully validated Github personal access token.")

    def process_github_repository(self):
        while (
                not self.github_repository or
                not AzureDevopsBuildProvider.check_github_repository(self.github_pat, self.github_repository)
        ):
            self.github_repository = prompt(msg="Github Repository Path (e.g. Azure/azure-cli): ").strip()
        self.logger.warning("Successfully found Github repository.")

    def process_build_and_release_definition_name(self, scenario):
        if scenario == 'AZURE_DEVOPS':
            self.build_definition_name = self.repository_remote_name.replace("_azuredevops_", "_build_", 1)[0:256]
            self.release_definition_name = self.repository_remote_name.replace("_azuredevops_", "_release_", 1)[0:256]
        if scenario == 'GITHUB_INTEGRATION':
            self.build_definition_name = "_build_github_" + self.github_repository.replace("/", "_", 1)[0:256]
            self.release_definition_name = "_release_github_" + self.github_repository.replace("/", "_", 1)[0:256]

    def process_github_service_endpoint(self):
        service_endpoints = self.adbp.get_github_service_endpoints(
            self.organization_name, self.project_name, self.github_repository
        )

        if not service_endpoints:
            service_endpoint = self.adbp.create_github_service_endpoint(
                self.organization_name, self.project_name, self.github_repository, self.github_pat
            )
        else:
            service_endpoint = service_endpoints[0]
            self.logger.warning("Detected a Github service endpoint already exists: {name}".format(
                                name=service_endpoint.name))

        self.github_service_endpoint_name = service_endpoint.name

    def process_functionapp_service_endpoint(self, scenario):
        repository = self.repository_name if scenario == "AZURE_DEVOPS" else self.github_repository
        service_endpoints = self.adbp.get_service_endpoints(
            self.organization_name, self.project_name, repository
        )

        # If there is no matching service endpoint, we need to create a new one
        if not service_endpoints:
            try:
                self.logger.warning("Creating a service principle (this may take a minute or two)")
                service_endpoint = self.adbp.create_service_endpoint(
                    self.organization_name, self.project_name, repository
                )
            except RoleAssignmentException:
                if scenario == "AZURE_DEVOPS":
                    self.adbp.remove_git_remote(self.organization_name, self.project_name, repository)
                raise CLIError("{ls}To create a build through Azure Pipelines,{ls}"
                               "The command will assign a contributor role to the "
                               "Azure function app release service principle.{ls}"
                               "Please ensure that:{ls}"
                               "1. You are the owner of the subscription, "
                               "or have roleAssignments/write permission.{ls}"
                               "2. You can perform app registration in Azure Active Directory.{ls}"
                               "3. The combined length of your organization name, project name and repository name "
                               "is under 68 characters.".format(ls=os.linesep))
        else:
            service_endpoint = service_endpoints[0]
            self.logger.warning("Detected a functionapp service endpoint already exists: {name}".format(
                                name=service_endpoint.name))

        self.service_endpoint_name = service_endpoint.name

    def process_extensions(self):
        if self.functionapp_type == LINUX_CONSUMPTION:
            self.logger.warning("Installing the required extensions for the build and release")
            self.adbp.create_extension(self.organization_name, 'AzureAppServiceSetAppSettings', 'hboelman')
            self.adbp.create_extension(self.organization_name, 'PascalNaber-Xpirit-CreateSasToken', 'pascalnaber')

    def process_build(self, scenario):
        # need to check if the build definition already exists
        build_definitions = self.adbp.list_build_definitions(self.organization_name, self.project_name)
        build_definition_match = [
            build_definition for build_definition in build_definitions
            if build_definition.name == self.build_definition_name
        ]

        if not build_definition_match:
            if scenario == "AZURE_DEVOPS":
                self.adbp.create_devops_build_definition(self.organization_name, self.project_name,
                                                         self.repository_name, self.build_definition_name,
                                                         self.build_pool_name)
            elif scenario == "GITHUB_INTEGRATION":
                try:
                    self.adbp.create_github_build_definition(self.organization_name, self.project_name,
                                                             self.github_repository, self.build_definition_name,
                                                             self.build_pool_name)
                except GithubIntegrationRequestError as gire:
                    raise CLIError("{error}{ls}{ls}"
                                   "Please ensure your Github personal access token has sufficient permissions.{ls}{ls}"
                                   "You may visit https://aka.ms/azure-devops-source-repos for more "
                                   "information.".format(
                                       error=gire.message, ls=os.linesep))
                except GithubContentNotFound:
                    raise CLIError("Failed to create a webhook for the provided Github repository or "
                                   "your repository cannot be accessed.{ls}{ls}"
                                   "You may visit https://aka.ms/azure-devops-source-repos for more "
                                   "information.".format(
                                       ls=os.linesep))
        else:
            self.logger.warning("Detected a build definition already exists: {name}".format(
                                name=self.build_definition_name))

        try:
            self.build = self.adbp.create_build_object(
                self.organization_name,
                self.project_name,
                self.build_definition_name,
                self.build_pool_name
            )
        except BuildErrorException as bee:
            raise CLIError("{error}{ls}{ls}"
                           "Please ensure your azure-pipelines.yml file matches Azure function app's "
                           "runtime operating system and language.{ls}"
                           "You may use 'az functionapp devops-build create --overwrite-yaml true' "
                           "to force generating an azure-pipelines.yml specifically for your build".format(
                               error=bee.message, ls=os.linesep))

        url = "https://dev.azure.com/{org}/{proj}/_build/results?buildId={build_id}".format(
            org=self.organization_name,
            proj=self.project_name,
            build_id=self.build.id
        )
        self.logger.warning("The build for the function app has been initiated (this may take a few minutes)")
        self.logger.warning("To follow the build process go to {url}".format(url=url))

    def wait_for_build(self):
        build = None
        prev_log_status = None

        self.logger.info("========== Build Log ==========")
        while build is None or build.result is None:
            time.sleep(BUILD_QUERY_FREQUENCY)
            build = self._get_build_by_id(self.organization_name, self.project_name, self.build.id)

            # Log streaming
            if self.logger.isEnabledFor(logging.INFO):
                curr_log_status = self.adbp.get_build_logs_status(
                    self.organization_name,
                    self.project_name,
                    self.build.id
                )
                log_content = self.adbp.get_build_logs_content_from_statuses(
                    organization_name=self.organization_name,
                    project_name=self.project_name,
                    build_id=self.build.id,
                    prev_log=prev_log_status,
                    curr_log=curr_log_status
                )
                if log_content:
                    self.logger.info(log_content)
                prev_log_status = curr_log_status

        if build.result == 'failed':
            url = "https://dev.azure.com/{org}/{proj}/_build/results?buildId={build_id}".format(
                org=self.organization_name,
                proj=self.project_name,
                build_id=build.id
            )
            raise CLIError("Sorry, your build has failed in Azure Pipelines.{ls}"
                           "To view details on why your build has failed please visit {url}".format(
                               url=url, ls=os.linesep
                           ))
        if build.result == 'succeeded':
            self.logger.warning("Your build has completed.")

    def process_release(self):
        # need to check if the release definition already exists
        release_definitions = self.adbp.list_release_definitions(self.organization_name, self.project_name)
        release_definition_match = [
            release_definition for release_definition in release_definitions
            if release_definition.name == self.release_definition_name
        ]

        if not release_definition_match:
            self.logger.warning("Composing a release definition...")
            self.adbp.create_release_definition(self.organization_name, self.project_name,
                                                self.build_definition_name, self.artifact_name,
                                                self.release_pool_name, self.service_endpoint_name,
                                                self.release_definition_name, self.functionapp_type,
                                                self.functionapp_name, self.storage_name,
                                                self.resource_group_name, self.settings)
        else:
            self.logger.warning("Detected a release definition already exists: {name}".format(
                                name=self.release_definition_name))

        # Check if a release is automatically triggered. If not, create a new release.
        time.sleep(RELEASE_COMPOSITION_DELAY)
        release = self.adbp.get_latest_release(self.organization_name, self.project_name, self.release_definition_name)
        if release is None:
            try:
                release = self.adbp.create_release(
                    self.organization_name,
                    self.project_name,
                    self.release_definition_name
                )
            except ReleaseErrorException:
                raise CLIError("Sorry, your release has failed in Azure Pipelines.{ls}"
                               "To view details on why your release has failed please visit "
                               "https://dev.azure.com/{org}/{proj}/_release".format(
                                   ls=os.linesep, org=self.organization_name, proj=self.project_name
                               ))

        self.logger.warning("To follow the release process go to "
                            "https://dev.azure.com/{org}/{proj}/_releaseProgress?"
                            "_a=release-environment-logs&releaseId={release_id}".format(
                                org=self.organization_name,
                                proj=self.project_name,
                                release_id=release.id
                            ))

    def _check_if_force_push_required(self, remote_url, remote_branches):
        force_push_required = False
        if remote_branches:
            self.logger.warning("The remote repository is not clean: {url}".format(url=remote_url))
            self.logger.warning("If you wish to continue, a force push will be commited and "
                                "your local branches will overwrite the remote branches!")
            self.logger.warning("Please ensure you have force push permission in {repo} repository.".format(
                repo=self.repository_name
            ))

            if self.allow_force_push is None:
                consent = prompt_y_n("I consent to force push all local branches to Azure DevOps repository")
            else:
                consent = str2bool(self.allow_force_push)

            if not consent:
                self.adbp.remove_git_remote(self.organization_name, self.project_name, self.repository_name)
                raise CLIError("Failed to obtain your consent.")

            force_push_required = True

        return force_push_required

    def _check_if_git_credential_required(self):
        # Username and password are not required if git credential manager exists
        if AzureDevopsBuildProvider.check_git_credential_manager():
            return

        # Manual setup alternative credential in Azure Devops
        self.logger.warning("Please visit https://dev.azure.com/{org}/_usersSettings/altcreds".format(
            org=self.organization_name,
        ))
        self.logger.warning('Check "Enable alternate authentication credentials" and save your username and password.')
        self.logger.warning("You may need to use this credential when pushing your code to Azure DevOps repository.")
        consent = prompt_y_n("I have setup alternative authentication credentials for {repo}".format(
            repo=self.repository_name
        ))
        if not consent:
            self.adbp.remove_git_remote(self.organization_name, self.project_name, self.repository_name)
            raise CLIError("Failed to obtain your consent.")

    def _select_functionapp(self):
        self.logger.info("Retrieving functionapp names.")
        functionapps = list_function_app(self.cmd)
        functionapp_names = sorted([functionapp.name for functionapp in functionapps])
        if not functionapp_names:
            raise CLIError("You do not have any existing function apps associated with this account subscription.{ls}"
                           "1. Please make sure you are logged into the right azure account by "
                           "running 'az account show' and checking the user.{ls}"
                           "2. If you are logged in as the right account please check the subscription you are using. "
                           "Run 'az account show' and view the name.{ls}"
                           "   If you need to set the subscription run "
                           "'az account set --subscription <subscription name or id>'{ls}"
                           "3. If you do not have a function app please create one".format(ls=os.linesep))
        choice_index = prompt_choice_list('Please select the target function app: ', functionapp_names)
        functionapp = [functionapp for functionapp in functionapps
                       if functionapp.name == functionapp_names[choice_index]][0]
        self.logger.info("Selected functionapp %s", functionapp.name)
        return functionapp

    def _find_local_repository_runtime_language(self):  # pylint: disable=no-self-use
        # We want to check that locally the language that they are using matches the type of application they
        # are deploying to
        with open('local.settings.json') as f:
            settings = json.load(f)

        runtime_language = settings.get('Values', {}).get('FUNCTIONS_WORKER_RUNTIME')
        if not runtime_language:
            raise CLIError("The 'FUNCTIONS_WORKER_RUNTIME' setting is not defined in the local.settings.json file")

        if SUPPORTED_LANGUAGES.get(runtime_language) is not None:
            return runtime_language

        raise LanguageNotSupportException(runtime_language)

    def _find_github_repository_runtime_language(self):
        try:
            github_file_content = AzureDevopsBuildProvider.get_github_content(
                self.github_pat,
                self.github_repository,
                "local.settings.json"
            )
        except GithubContentNotFound:
            self.logger.warning("The local.settings.json is not commited to Github repository {repo}".format(
                repo=self.github_repository
            ))
            self.logger.warning("Set azure-pipeline.yml language to: {language}".format(
                language=self.functionapp_language
            ))
            return None

        runtime_language = github_file_content.get('Values', {}).get('FUNCTIONS_WORKER_RUNTIME')
        if not runtime_language:
            raise CLIError("The 'FUNCTIONS_WORKER_RUNTIME' setting is not defined in the local.settings.json file")

        if SUPPORTED_LANGUAGES.get(runtime_language) is not None:
            return runtime_language

        raise LanguageNotSupportException(runtime_language)

    def _get_functionapp_runtime_language(self, app_settings):  # pylint: disable=no-self-use
        functions_worker_runtime = [
            setting['value'] for setting in app_settings if setting['name'] == "FUNCTIONS_WORKER_RUNTIME"
        ]

        if functions_worker_runtime:
            functionapp_language = functions_worker_runtime[0]
            if SUPPORTED_LANGUAGES.get(functionapp_language) is not None:
                return SUPPORTED_LANGUAGES[functionapp_language]

            raise LanguageNotSupportException(functionapp_language)
        return None

    def _get_functionapp_storage_name(self, app_settings):  # pylint: disable=no-self-use
        functions_worker_runtime = [
            setting['value'] for setting in app_settings if setting['name'] == "AzureWebJobsStorage"
        ]

        if functions_worker_runtime:
            return functions_worker_runtime[0].split(';')[1].split('=')[1]
        return None

    def _find_type(self, kinds):  # pylint: disable=no-self-use
        if 'linux' in kinds:
            if 'container' in kinds:
                functionapp_type = LINUX_DEDICATED
            else:
                functionapp_type = LINUX_CONSUMPTION
        else:
            functionapp_type = WINDOWS
        return functionapp_type

    def _select_organization(self):
        organizations = self.adbp.list_organizations()
        organization_names = sorted([organization.accountName for organization in organizations.value])
        if not organization_names:
            self.logger.warning("There are no existing organizations, you need to create a new organization.")
            self._create_organization()
            self.created_organization = True
        else:
            choice_index = prompt_choice_list('Please choose the organization: ', organization_names)
            organization_match = [organization for organization in organizations.value
                                  if organization.accountName == organization_names[choice_index]][0]
            self.organization_name = organization_match.accountName

    def _get_organization_by_name(self, organization_name):
        organizations = self.adbp.list_organizations()
        return [organization for organization in organizations.value
                if organization.accountName == organization_name][0]

    def _create_organization(self):
        self.logger.info("Starting process to create a new Azure DevOps organization")
        regions = self.adbp.list_regions()
        region_names = sorted([region.display_name for region in regions.value])
        self.logger.info("The region for an Azure DevOps organization is where the organization will be located. "
                         "Try locate it near your other resources and your location")
        choice_index = prompt_choice_list('Please select a region for the new organization: ', region_names)
        region = [region for region in regions.value if region.display_name == region_names[choice_index]][0]

        while True:
            organization_name = prompt("Please enter a name for your new organization: ")
            new_organization = self.adbp.create_organization(organization_name, region.name)
            if new_organization.valid is False:
                self.logger.warning(new_organization.message)
                self.logger.warning("Note: all names must be globally unique")
            else:
                break

        self.organization_name = new_organization.name

    def _select_project(self):
        projects = self.adbp.list_projects(self.organization_name)
        if projects.count > 0:
            project_names = sorted([project.name for project in projects.value])
            choice_index = prompt_choice_list('Please select your project: ', project_names)
            project = [project for project in projects.value if project.name == project_names[choice_index]][0]
            self.project_name = project.name
        else:
            self.logger.warning("There are no existing projects in this organization. "
                                "You need to create a new project.")
            self._create_project()

    def _create_project(self):
        project_name = prompt("Please enter a name for your new project: ")
        project = self.adbp.create_project(self.organization_name, project_name)
        # Keep retrying to create a new project if it fails
        while not project.valid:
            self.logger.error(project.message)
            project_name = prompt("Please enter a name for your new project: ")
            project = self.adbp.create_project(self.organization_name, project_name)

        self.project_name = project.name
        self.created_project = True

    def _get_build_by_id(self, organization_name, project_name, build_id):
        builds = self.adbp.list_build_objects(organization_name, project_name)
        return next((build for build in builds if build.id == build_id))


class CmdSelectors(object):

    def __init__(self, cmd, logger, adbp):
        self.cmd = cmd
        self.logger = logger
        self.adbp = adbp

    def cmd_functionapp(self, functionapp_name):
        functionapps = list_function_app(self.cmd)
        functionapp_match = [functionapp for functionapp in functionapps
                             if functionapp.name == functionapp_name]
        if not functionapp_match:
            raise CLIError("Error finding functionapp. "
                           "Please check that the function app exists by calling 'az functionapp list'")

        return functionapp_match[0]

    def cmd_organization(self, organization_name):
        organizations = self.adbp.list_organizations()
        organization_match = [organization for organization in organizations.value
                              if organization.accountName == organization_name]
        if not organization_match:
            raise CLIError("Error finding organization. "
                           "Please check that the organization exists by "
                           "navigating to the Azure DevOps portal at dev.azure.com")

        return organization_match[0]

    def cmd_project(self, organization_name, project_name):
        projects = self.adbp.list_projects(organization_name)
        project_match = [project for project in projects.value if project.name == project_name]

        if not project_match:
            raise CLIError("Error finding project. "
                           "Please check that the project exists by "
                           "navigating to the Azure DevOps portal at dev.azure.com")

        return project_match[0]
