# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path as path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from ..constants import (WINDOWS, PYTHON, NODE, DOTNET, POWERSHELL)
from ..exceptions import LanguageNotSupportException


class YamlManager(object):
    """ Generate yaml files for devops

    Attributes:
        language: the language of the functionapp you are creating
        app_type: the type of functionapp that you are creating
    """

    def __init__(self, language, app_type):
        """Inits YamlManager as to be able generate the yaml files easily"""
        self._language = language
        self._app_type = app_type
        self.jinja_env = Environment(
            loader=FileSystemLoader(path.join(path.abspath(path.dirname(__file__)), 'templates')),
            autoescape=select_autoescape(['jinja'])
        )

    def create_yaml(self):
        """Create the yaml to be able to create build in the azure-pipelines.yml file"""
        if self._language == PYTHON:
            language_str = 'python'
            package_route = '$(System.DefaultWorkingDirectory)'
            dependencies = self._python_dependencies()
        elif self._language == NODE:
            language_str = 'node'
            package_route = '$(System.DefaultWorkingDirectory)'
            dependencies = self._node_dependencies()
        elif self._language == DOTNET:
            language_str = 'dotnet'
            package_route = '$(System.DefaultWorkingDirectory)/publish_output/s'
            dependencies = self._dotnet_dependencies()
        elif self._language == POWERSHELL:
            language_str = 'powershell'
            package_route = '$(System.DefaultWorkingDirectory)'
            dependencies = self._powershell_dependencies()
        else:
            raise LanguageNotSupportException(self._language)

        if self._app_type == WINDOWS:
            platform_str = 'windows'
            yaml = self._generate_yaml(dependencies, 'VS2017-Win2016', language_str, platform_str, package_route)
        else:
            platform_str = 'linux'
            yaml = self._generate_yaml(dependencies, 'ubuntu-16.04', language_str, platform_str, package_route)

        with open('azure-pipelines.yml', 'w') as f:
            f.write(yaml)

    def _generate_yaml(self, dependencies, vmImage, language_str, platform_str, package_route):
        template = self.jinja_env.get_template('build.jinja')
        outputText = template.render(dependencies=dependencies, vmImage=vmImage,
                                     language=language_str, platform=platform_str,
                                     package_route=package_route)
        return outputText

    def _requires_extensions(self):
        return path.exists('extensions.csproj')

    def _requires_pip(self):
        return path.exists('requirements.txt')

    def _requires_npm(self):
        return path.exists('package.json')

    def _inject_extensions_build(self, dependencies):
        if self._app_type == WINDOWS:
            runtime = 'win10-x64'
        else:
            runtime = 'ubuntu.16.04-x64'

        dependencies.append("- task: DotNetCoreCLI@2")
        dependencies.append("  displayName: '.NET Core build extensions'")
        dependencies.append("  inputs:")
        dependencies.append("    projects: extensions.csproj")
        dependencies.append("    arguments: '--runtime {runtime} --output bin/'".format(runtime=runtime))

    def _python_dependencies(self):
        """Helper to create the standard python dependencies"""
        dependencies = []
        if self._requires_extensions():
            self._inject_extensions_build(dependencies)
        dependencies.append('- task: UsePythonVersion@0')
        dependencies.append('  displayName: "Setting python version to 3.6 as required by functions"')
        dependencies.append('  inputs:')
        dependencies.append('    versionSpec: \'3.6\'')
        dependencies.append('    architecture: \'x64\'')
        dependencies.append('- script: |')
        dependencies.append('    python3.6 -m venv worker_venv')
        dependencies.append('    source worker_venv/bin/activate')
        dependencies.append('    pip3.6 install setuptools')
        if self._requires_pip():
            dependencies.append('    pip3.6 install -r requirements.txt')
        return dependencies

    def _node_dependencies(self):
        """Helper to create the standard node dependencies"""
        dependencies = []
        if self._requires_extensions():
            self._inject_extensions_build(dependencies)
        if self._requires_npm():
            dependencies.append('- script: |')
            dependencies.append('    npm install')
            dependencies.append('    npm run build --if-present')
            dependencies.append('    npm prune --production')

        return dependencies

    def _dotnet_dependencies(self):
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

    def _powershell_dependencies(self):
        dependencies = []
        if self._requires_extensions():
            self._inject_extensions_build(dependencies)

        return dependencies
