# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path as path
import logging
from jinja2 import Environment, PackageLoader, select_autoescape
from ..constants import (WINDOWS, PYTHON, NODE, DOTNET, JAVA)


class YamlManager(object):  # pylint: disable=too-few-public-methods
    """ Generate yaml files for devops

    Attributes:
        language: the language of the functionapp you are creating
        app_type: the type of functionapp that you are creating
    """

    def __init__(self, language, app_type):
        """Inits YamlManager as to be able generate the yaml files easily"""
        self._language = language
        self._app_type = app_type

    def create_yaml(self):
        """Create the yaml to be able to create build in the azure-pipelines.yml file"""
        if self._language == PYTHON:
            language_str = 'python'
            package_route = '$(System.DefaultWorkingDirectory)'
            dependencies = _python_dependencies()
        elif self._language == NODE:
            language_str = 'node'
            package_route = '$(System.DefaultWorkingDirectory)'
            dependencies = _node_dependencies()
        elif self._language == DOTNET:
            language_str = 'dotnet'
            package_route = '$(System.DefaultWorkingDirectory)/publish_output/s'
            dependencies = _dotnet_dependencies()
        elif self._language == JAVA:
            language_str = 'java'
            package_route = '$(System.DefaultWorkingDirectory)'
            dependencies = _java_dependencies()
            # ADD NEW DEPENDENCIES FOR LANGUAGES HERE
        else:
            logging.warning("valid app type not found")
            dependencies = ""

        if self._app_type == WINDOWS:
            platform_str = 'windows'
            yaml = _generate_yaml(dependencies, 'VS2017-Win2016', language_str, platform_str, package_route)
        else:
            platform_str = 'linux'
            yaml = _generate_yaml(dependencies, 'ubuntu-16.04', language_str, platform_str, package_route)

        with open('azure-pipelines.yml', 'w') as f:
            f.write(yaml)


def _requires_extensions():
    return True if path.exists('extensions.csproj') else False


def _generate_yaml(dependencies, vmImage, language_str, platform_str, package_route):
    env = Environment(
        loader=PackageLoader('azure_functions_devops_build.yaml', 'templates'),
        autoescape=select_autoescape(['html', 'xml', 'jinja'])
    )
    template = env.get_template('build.jinja')
    outputText = template.render(dependencies=dependencies, vmImage=vmImage,
                                 language=language_str, platform=platform_str,
                                 package_route=package_route)
    return outputText


def _python_dependencies():
    """Helper to create the standard python dependencies"""
    dependencies = []
    dependencies.append('- task: UsePythonVersion@0')
    dependencies.append('  displayName: "Setting python version to 3.6 as required by functions"')
    dependencies.append('  inputs:')
    dependencies.append('    versionSpec: \'3.6\'')
    dependencies.append('    architecture: \'x64\'')
    dependencies.append('- script: |')
    if _requires_extensions():
        # We need to add the dependencies for the extensions if the functionapp has them
        dependencies.append('    dotnet restore')
        dependencies.append('    dotnet build --runtime ubuntu.16.04-x64 --output \'./bin/\'')
    dependencies.append('    python3.6 -m venv worker_venv')
    dependencies.append('    source worker_venv/bin/activate')
    dependencies.append('    pip3.6 install setuptools')
    dependencies.append('    pip3.6 install -r requirements.txt')
    return dependencies


def _node_dependencies():
    """Helper to create the standard node dependencies"""
    dependencies = []
    dependencies.append('- script: |')
    if _requires_extensions():
        dependencies.append('    dotnet restore')
        dependencies.append('    dotnet build --output \'./bin/\'')
    dependencies.append('    npm install')
    dependencies.append('    npm run build')
    return dependencies


def _dotnet_dependencies():
    """Helper to create the standard dotnet dependencies"""
    dependencies = []
    dependencies.append('- script: |')
    dependencies.append('    dotnet restore')
    dependencies.append('    dotnet build --configuration Release')
    dependencies.append("- task: DotNetCoreCLI@2")
    dependencies.append("  inputs:")
    dependencies.append("    command: publish")
    dependencies.append("    arguments: '--configuration Release --output publish_output'")
    dependencies.append("    projects: '*.csproj'")
    dependencies.append("    publishWebProjects: false")
    dependencies.append("    modifyOutputPath: true")
    dependencies.append("    zipAfterPublish: false")
    return dependencies


def _java_dependencies():
    """Helper to create the standard java dependencies"""
    dependencies = ['- script: |', '    dotnet restore', '    dotnet build', '   mvn clean deploy']
    logging.critical("java dependencies are currently not implemented")
    return dependencies


def _powershell_dependencies():
    # TODO
    exit(1)
