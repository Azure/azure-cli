# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from subprocess import check_output, CalledProcessError
import time
import re
import json
from knack.prompting import prompt_choice_list, prompt_y_n, prompt
from azure_functions_devops_build.constants import (LINUX_CONSUMPTION, LINUX_DEDICATED, WINDOWS,
                                                    PYTHON, NODE, DOTNET, JAVA)
from .azure_devops_build_provider import AzureDevopsBuildProvider
from .custom import list_function_app, show_webapp, get_app_settings

# pylint: disable=too-many-instance-attributes


def str2bool(v):
    if v == 'true':
        retval = True
    elif v == 'false':
        retval = False
    else:
        retval = None
    return retval


class AzureDevopsBuildInteractive(object):
    """Implement the basic user flow for a new user wanting to do an Azure DevOps build for Azure Functions

    Attributes:
        cmd : the cmd input from the command line
        logger : a knack logger to log the info/error messages
    """

    def __init__(self, cmd, logger, functionapp_name, organization_name, project_name,
                 overwrite_yaml, use_local_settings, local_git):
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
        self.repository_name = None
        self.service_endpoint_name = None
        self.build_definition_name = None
        self.release_definition_name = None
        self.build_pool_name = "Default"
        self.release_pool_name = "Hosted VS2017"
        self.artifact_name = "drop"

        self.settings = []
        self.build = None
        self.release = None
        # These are used to tell if we made new objects
        self.created_organization = False
        self.created_project = False
        self.overwrite_yaml = str2bool(overwrite_yaml)
        self.use_local_settings = str2bool(use_local_settings)
        self.local_git = local_git

    def interactive_azure_devops_build(self):
        """Main interactive flow which is the only function that should be used outside of this
        class (the rest are helpers)
        """
        self.pre_checks()
        self.process_functionapp()
        self.process_organization()
        self.process_project()

        # Set up the default names for the rest of the things we need to create
        self.repository_name = self.project_name
        self.service_endpoint_name = self.organization_name + self.project_name
        self.build_definition_name = self.project_name + " INITIAL AZ CLI BUILD"
        self.release_definition_name = self.project_name + " INITIAL AZ CLI RELEASE"

        self.process_yaml()
        self.process_repository()

        self.process_service_endpoint()
        self.process_extensions()

        self.process_build()
        self.process_release()

        return_dict = {}
        return_dict['functionapp_name'] = self.functionapp_name
        return_dict['storage_name'] = self.storage_name
        return_dict['resource_group_name'] = self.resource_group_name
        return_dict['functionapp_language'] = self.functionapp_language
        return_dict['functionapp_type'] = self.functionapp_type
        return_dict['organization_name'] = self.organization_name
        return_dict['project_name'] = self.project_name
        return_dict['repository_name'] = self.repository_name
        return_dict['service_endpoint_name'] = self.service_endpoint_name
        return_dict['build_definition_name'] = self.build_definition_name
        return_dict['release_definition_name'] = self.release_definition_name

        return return_dict

    def pre_checks(self):
        if not os.path.exists('host.json'):
            self.logger.critical("FATAL: There is no host.json in the current directory. Functionapps must contain a host.json in their root.")  # pylint: disable=line-too-long
            exit(1)

    def process_functionapp(self):
        """Helper to retrieve information about a functionapp"""
        if self.functionapp_name is None:
            functionapp = self._select_functionapp()
            # We now know the functionapp name so can set it
            self.functionapp_name = functionapp.name
        else:
            functionapp = self.cmd_selector.cmd_functionapp(self.functionapp_name)

        kinds = show_webapp(self.cmd, functionapp.resource_group, functionapp.name).kind.split(',')
        app_settings = get_app_settings(self.cmd, functionapp.resource_group, functionapp.name)

        self.resource_group_name = functionapp.resource_group
        self.functionapp_type = self._find_type(kinds)
        self.functionapp_language, self.storage_name = self._find_language_and_storage_name(app_settings)

    def process_organization(self):
        """Helper to retrieve information about an organization / create a new one"""
        if self.organization_name is None:
            response = prompt_y_n('Would you like to use an existing organization? ')
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
            use_existing_project = prompt_y_n('Would you like to use an existing project? ')
            if use_existing_project:
                self._select_project()
            else:
                self._create_project()
        else:
            self.cmd_selector.cmd_project(self.organization_name, self.project_name)

    def process_yaml(self):
        """Helper to create the local azure-pipelines.yml file"""
        # Try and get what the app settings are
        with open('local.settings.json') as f:
            data = json.load(f)

        default = ['FUNCTIONS_WORKER_RUNTIME', 'AzureWebJobsStorage']
        settings = []
        for key, value in data['Values'].items():
            if key not in default:
                settings.append((key, value))

        if settings:
            if self.use_local_settings is None:
                use_local_settings = prompt_y_n('Would you like to transfer your local.settings.json to the host settings of your application running on Azure?')  # pylint: disable=line-too-long
            else:
                use_local_settings = self.use_local_settings
            if not use_local_settings:
                settings = []

        self.settings = settings

        if os.path.exists('azure-pipelines.yml'):
            if self.overwrite_yaml is None:
                self.logger.warning("There is already an azure pipelines yaml file.")
                self.logger.warning("If you are using a yaml file that was not configured through this command this process may fail.")  # pylint: disable=line-too-long
                response = prompt_y_n("Do you want to delete it and create a new one? ")
            else:
                response = self.overwrite_yaml
        if (not os.path.exists('azure-pipelines.yml')) or response:
            self.logger.info('Creating new yaml')
            self.adbp.create_yaml(self.functionapp_language, self.functionapp_type)

    def process_repository(self):
        """Helper to process for setting up the azure devops build repository to use for the build"""
        if os.path.exists(".git"):
            self.process_git_exists()
        else:
            self.process_git_doesnt_exist()

    def process_extensions(self):
        self.logger.info("Installing the required extensions for the build and release")
        self.adbp.create_extension(self.organization_name, 'AzureAppServiceSetAppSettings', 'hboelman')
        self.adbp.create_extension(self.organization_name, 'PascalNaber-Xpirit-CreateSasToken', 'pascalnaber')

    def process_service_endpoint(self):
        service_endpoints = self.adbp.list_service_endpoints(self.organization_name, self.project_name)
        service_endpoint_match = \
            [service_endpoint for service_endpoint in service_endpoints
             if service_endpoint.name == self.service_endpoint_name]

        if len(service_endpoint_match) != 1:
            service_endpoint = self.adbp.create_service_endpoint(self.organization_name, self.project_name,
                                                                 self.service_endpoint_name)
        else:
            service_endpoint = service_endpoint_match[0]
        return service_endpoint

    def process_build(self):
        # need to check if the build definition already exists
        build_definitions = self.adbp.list_build_definitions(self.organization_name, self.project_name)
        build_definition_match = \
            [build_definition for build_definition in build_definitions
             if build_definition.name == self.build_definition_name]

        if len(build_definition_match) != 1:
            self.adbp.create_build_definition(self.organization_name, self.project_name,
                                              self.repository_name, self.build_definition_name,
                                              self.build_pool_name)

        build = self.adbp.create_build_object(self.organization_name, self.project_name,
                                              self.build_definition_name, self.build_pool_name)

        url = "https://dev.azure.com/" + self.organization_name + "/" \
            + self.project_name + "/_build/results?buildId=" + str(build.id)
        self.logger.info("To follow the build process go to %s", url)
        self.build = build

    def process_release(self):
        # wait for artifacts / build to complete
        artifacts = []
        counter = 0
        while artifacts == []:
            time.sleep(1.5)
            self.logger.info("waiting for artifacts ... %s", counter)
            build = self._get_build_by_id(self.organization_name, self.project_name, self.build.id)
            if build.status == 'completed':
                break
            artifacts = self.adbp.list_artifacts(self.organization_name, self.project_name, self.build.id)
            counter += 1

        if build.result == 'failed':
            url = "https://dev.azure.com/" + self.organization_name + "/" \
                  + self.project_name + "/_build/results?buildId=" + str(build.id)
            self.logger.critical("Your build has failed")
            self.logger.critical("To view details on why your build has failed please go to %s", url)
            exit(1)

        self.adbp.create_release_definition(self.organization_name, self.project_name,
                                            self.build_definition_name, self.artifact_name,
                                            self.release_pool_name, self.service_endpoint_name,
                                            self.release_definition_name, self.functionapp_type,
                                            self.functionapp_name, self.storage_name,
                                            self.resource_group_name, self.settings)
        release = self.adbp.create_release(self.organization_name, self.project_name,
                                           self.release_definition_name)
        url = "https://dev.azure.com/" + self.organization_name + "/" \
            + self.project_name + "/_releaseProgress?_a=release-environment-logs&releaseId=" + str(release.id)
        self.logger.info("To follow the release process go to %s", url)
        self.release = release

    def find_type_repository(self):  # pylint: disable=no-self-use
        lines = (check_output('git remote show origin'.split())).decode('utf-8').split('\n')
        for line in lines:
            if re.search('github', line):
                return 'github'
            elif re.search('visualstudio', line):
                return 'azure repos'
        return 'other'

    def process_remote(self):
        commits = self.adbp.list_commits(self.organization_name, self.project_name, self.repository_name)
        if commits:
            self.logger.warning("The default repository associated with your project already contains a commit. There needs to be a clean repository.")  # pylint: disable=line-too-long
            self.logger.warning("We will try and create a new repository instead")
            succeeded = False
            while not succeeded:
                repository_name = prompt('What would you like to call the new repository?')  # pylint: disable=line-too-long
                # Validate that the name does not already exist
                repositories = self.adbp.list_repositories(self.organization_name, self.project_name)
                repository_match = \
                    [repo for repo in repositories if repo.name == repository_name]
                if repository_match:
                    self.logger.error("A repository with that name already exists in this project.")
                else:
                    succeeded = True
            self.adbp.create_repository(self.organization_name, self.project_name, repository_name)
            self.repository_name = repository_name
            self.build_definition_name += repository_name
            self.release_definition_name += repository_name
        try:
            setup = self.adbp.setup_remote(self.organization_name, self.project_name, self.repository_name, 'devopsbuild')  # pylint: disable=line-too-long
        except CalledProcessError:
            self.logger.critical("error with the seting up of the remote")
            exit(1)
        if not setup.succeeded:
            self.logger.critical('It looks like you already have a remote called devopsbuild. This indicates that you already have a pipeline setup.')  # pylint: disable=line-too-long
            self.logger.critical('This command is only to setup a build|release pipeline.')
            self.logger.critical('If you want to run your existing pipeline just push your changes in git to the devopsbuild remote.')  # pylint: disable=line-too-long
            exit(1)

    def process_git_exists(self):
        self.logger.warning("There is a local git file.")

        if self.local_git is None:
            self.logger.warning("1. Chosing the add remote will create a new remote to the build repository but otherwise preserve your local git")  # pylint: disable=line-too-long
            self.logger.warning("2. Chosing the add new repository will delete your local git file and create a new one with a reference to the build repository.")  # pylint: disable=line-too-long
            self.logger.warning("3. Choosing the use existing will use the repository you are referencing to do the build. Only choose use existing if your local git file is referencing an azure repository that you can create a build with.")  # pylint: disable=line-too-long
            command_options = ['AddRemote', 'AddNewRepository', 'UseExisting']
            choice_index = prompt_choice_list('Please choose the action you would like to take: ', command_options)
            command = command_options[choice_index]
        else:
            command = self.local_git

        if command == 'AddNewRepository':
            self.logger.info("Removing your old, adding a new repository.")
            # https://docs.python.org/3/library/os.html#os.name (if os.name is nt it is windows)
            if os.name == 'nt':
                os.system("rmdir /s /q .git")
            else:
                os.system("rm -rf .git")
            self.process_git_doesnt_exist()
        elif command == 'AddRemote':
            self.process_remote()
        else:
            # default is to try and use the existing azure repo
            repository_type = self.find_type_repository()
            self.logger.info("We have detected that you have a %s type of repository", repository_type)
            if repository_type == 'azure repos':
                # Figure out what the repository information is for their current azure repos account
                lines = (check_output('git remote show origin'.split())).decode('utf-8').split('\n')
                for line in lines:
                    if re.search('Push', line):
                        m = re.search('http.*', line)
                        url = m.group(0)
                        segs = url.split('/')
                        organization_name = segs[2].split('.')[0]
                        project_name = segs[3]
                        repository_name = segs[5]
                # We don't need to push to it as it is all currently there
                self.organization_name = organization_name
                self.project_name = project_name
                self.repository_name = repository_name
            else:
                self.logger.critical("We don't support any other repositories except for azure repos. We cannot setup a build with these repositories.")  # pylint: disable=line-too-long
                exit(1)

    def process_git_doesnt_exist(self):
        # check if we need to make a repository
        repositories = self.adbp.list_repositories(self.organization_name, self.project_name)
        repository_match = \
            [repository for repository in repositories if repository.name == self.repository_name]

        if not repository_match:
            # Since we don't have a match for that repository we should just make it
            self.adbp.create_repository(self.organization_name, self.project_name, self.repository_name)
        else:
            commits = self.adbp.list_commits(self.organization_name, self.project_name, self.repository_name)
            if commits:
                self.logger.warning("The default repository associated with your project already contains a commit. There needs to be a clean repository.")  # pylint: disable=line-too-long
                succeeded = False
                while not succeeded:
                    repository_name = prompt('We will create that repository. What would you like to call the new repository?')  # pylint: disable=line-too-long
                    # Validate that the name does not already exist
                    repositories = self.adbp.list_repositories(self.organization_name, self.project_name)
                    repository_match = \
                        [repo for repo in repositories if repo.name == repository_name]
                    if repository_match:
                        self.logger.error("A repository with that name already exists in this project.")
                    else:
                        succeeded = True
                self.adbp.create_repository(self.organization_name, self.project_name, repository_name)
                self.repository_name = repository_name
                self.build_definition_name += repository_name
                self.release_definition_name += repository_name
        # Since they do not have a git file locally we can setup the git locally as is
        self.adbp.setup_repository(self.organization_name, self.project_name, self.repository_name)

    def _select_functionapp(self):
        self.logger.info("Retrieving functionapp names.")
        functionapps = list_function_app(self.cmd)
        functionapp_names = sorted([functionapp.name for functionapp in functionapps])
        if len(functionapp_names) < 1:
            self.logger.critical("You do not have any existing functionapps associated with this account subscription.")
            self.logger.critical("1. Please make sure you are logged into the right azure account by running `az account show` and checking the user.")  # pylint: disable=line-too-long
            self.logger.critical("2. If you are logged in as the right account please check the subscription you are using. Run `az account show` and view the name.")  # pylint: disable=line-too-long
            self.logger.critical("   If you need to set the subscription run `az account set --subscription \"{SUBSCRIPTION_NAME}\"`")  # pylint: disable=line-too-long
            self.logger.critical("3. If you do not have a functionapp please create one in the portal.")
            exit(1)
        choice_index = prompt_choice_list('Please choose the functionapp: ', functionapp_names)
        functionapp = [functionapp for functionapp in functionapps
                       if functionapp.name == functionapp_names[choice_index]][0]
        self.logger.info("Selected functionapp %s", functionapp.name)
        return functionapp

    def _find_local_language(self):
        # We want to check that locally the language that they are using matches the type of application they
        # are deploying to
        with open('local.settings.json') as f:
            settings = json.load(f)
        try:
            local_language = settings['Values']['FUNCTIONS_WORKER_RUNTIME']
        except KeyError:
            self.logger.critical('The app \'FUNCTIONS_WORKER_RUNTIME\' setting is not set in the local.settings.json file')  # pylint: disable=line-too-long
            exit(1)
        if local_language == '':
            self.logger.critical('The app \'FUNCTIONS_WORKER_RUNTIME\' setting is not set in the local.settings.json file')  # pylint: disable=line-too-long
            exit(1)
        return local_language

    def _find_language_and_storage_name(self, app_settings):
        local_language = self._find_local_language()
        for app_setting in app_settings:
            if app_setting['name'] == "FUNCTIONS_WORKER_RUNTIME":
                language_str = app_setting['value']
                if language_str != local_language:
                    # We should not deploy if the local runtime language is not the same as that of their functionapp
                    self.logger.critical("ERROR: The local language you are using (%s) does not match the language of your functionapp (%s)", local_language, language_str)  # pylint: disable=line-too-long
                    self.logger.critical("Please look at the FUNCTIONS_WORKER_RUNTIME both in your local.settings.json and in your application settings on your azure functionapp.")  # pylint: disable=line-too-long
                    exit(1)
                if language_str == "python":
                    self.logger.info("detected that language used by functionapp is python")
                    language = PYTHON
                elif language_str == "node":
                    self.logger.info("detected that language used by functionapp is node")
                    language = NODE
                elif language_str == "dotnet":
                    self.logger.info("detected that language used by functionapp is .net")
                    language = DOTNET
                elif language_str == "java":
                    self.logger.info("detected that language used by functionapp is java")
                    language = JAVA
                else:
                    self.logger.warning("valid language not found")
                    language = ""
            if app_setting['name'] == "AzureWebJobsStorage":
                storage_name = app_setting['value'].split(';')[1].split('=')[1]
                self.logger.info("detected that storage used by the functionapp is %s", storage_name)
        return language, storage_name

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
        if len(organization_names) < 1:
            self.logger.error("There are not any existing organizations, you need to create a new organization.")
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
        self.logger.info("The region for an Azure DevOps organization is where the organization will be located. Try locate it near your other resources and your location")  # pylint: disable=line-too-long
        choice_index = prompt_choice_list('Please select a region for the new organization: ', region_names)
        region = [region for region in regions.value if region.display_name == region_names[choice_index]][0]

        while True:
            organization_name = prompt("Please enter the name of the new organization: ")
            new_organization = self.adbp.create_organization(organization_name, region.name)
            if new_organization.valid is False:
                self.logger.warning(new_organization.message)
                self.logger.warning("Note: any name must be globally unique")
            else:
                break
        url = "https://dev.azure.com/" + new_organization.name + "/"
        self.logger.info("Finished creating the new organization. Click the link to see your new organization: %s", url)
        self.organization_name = new_organization.name

    def _select_project(self):
        projects = self.adbp.list_projects(self.organization_name)
        if projects.count > 0:
            project_names = sorted([project.name for project in projects.value])
            choice_index = prompt_choice_list('Please select your project: ', project_names)
            project = [project for project in projects.value if project.name == project_names[choice_index]][0]
            self.project_name = project.name
        else:
            self.logger.warning("There are no exisiting projects in this organization. You need to create a new project.")  # pylint: disable=line-too-long
            self._create_project()

    def _create_project(self):
        project_name = prompt("Please enter the name of the new project: ")
        project = self.adbp.create_project(self.organization_name, project_name)
        # Keep retrying to create a new project if it fails
        while not project.valid:
            self.logger.error(project.message)
            project_name = prompt("Please enter the name of the new project: ")
            project = self.adbp.create_project(self.organization_name, project_name)

        url = "https://dev.azure.com/" + self.organization_name + "/" + project.name + "/"
        self.logger.info("Finished creating the new project. Click the link to see your new project: %s", url)
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
            self.logger.error("""Error finding functionapp. Please check that the functionapp exists using 'az functionapp list'""")  # pylint: disable=line-too-long
            exit(1)
        else:
            functionapp = functionapp_match[0]
        return functionapp

    def cmd_organization(self, organization_name):
        organizations = self.adbp.list_organizations()
        organization_match = [organization for organization in organizations.value
                              if organization.accountName == organization_name]
        if not organization_match:
            self.logger.error("""Error finding organization. Please check that the organization exists by logging onto your dev.azure.com acocunt""")  # pylint: disable=line-too-long
            exit(1)
        else:
            organization = organization_match[0]
        return organization

    def cmd_project(self, organization_name, project_name):
        projects = self.adbp.list_projects(organization_name)
        project_match = \
            [project for project in projects.value if project.name == project_name]

        if not project_match:
            self.logger.error("Error finding project. Please check that the project exists by logging onto your dev.azure.com acocunt")  # pylint: disable=line-too-long
            exit(1)
        else:
            project = project_match[0]
        return project
