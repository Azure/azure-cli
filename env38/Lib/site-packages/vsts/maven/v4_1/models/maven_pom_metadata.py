# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .maven_pom_gav import MavenPomGav


class MavenPomMetadata(MavenPomGav):
    """MavenPomMetadata.

    :param artifact_id:
    :type artifact_id: str
    :param group_id:
    :type group_id: str
    :param version:
    :type version: str
    :param build:
    :type build: :class:`MavenPomBuild <maven.v4_1.models.MavenPomBuild>`
    :param ci_management:
    :type ci_management: :class:`MavenPomCi <maven.v4_1.models.MavenPomCi>`
    :param contributors:
    :type contributors: list of :class:`MavenPomPerson <maven.v4_1.models.MavenPomPerson>`
    :param dependencies:
    :type dependencies: list of :class:`MavenPomDependency <maven.v4_1.models.MavenPomDependency>`
    :param dependency_management:
    :type dependency_management: :class:`MavenPomDependencyManagement <maven.v4_1.models.MavenPomDependencyManagement>`
    :param description:
    :type description: str
    :param developers:
    :type developers: list of :class:`MavenPomPerson <maven.v4_1.models.MavenPomPerson>`
    :param inception_year:
    :type inception_year: str
    :param issue_management:
    :type issue_management: :class:`MavenPomIssueManagement <maven.v4_1.models.MavenPomIssueManagement>`
    :param licenses:
    :type licenses: list of :class:`MavenPomLicense <maven.v4_1.models.MavenPomLicense>`
    :param mailing_lists:
    :type mailing_lists: list of :class:`MavenPomMailingList <maven.v4_1.models.MavenPomMailingList>`
    :param model_version:
    :type model_version: str
    :param modules:
    :type modules: list of str
    :param name:
    :type name: str
    :param organization:
    :type organization: :class:`MavenPomOrganization <maven.v4_1.models.MavenPomOrganization>`
    :param packaging:
    :type packaging: str
    :param parent:
    :type parent: :class:`MavenPomParent <maven.v4_1.models.MavenPomParent>`
    :param prerequisites:
    :type prerequisites: dict
    :param properties:
    :type properties: dict
    :param scm:
    :type scm: :class:`MavenPomScm <maven.v4_1.models.MavenPomScm>`
    :param url:
    :type url: str
    """

    _attribute_map = {
        'artifact_id': {'key': 'artifactId', 'type': 'str'},
        'group_id': {'key': 'groupId', 'type': 'str'},
        'version': {'key': 'version', 'type': 'str'},
        'build': {'key': 'build', 'type': 'MavenPomBuild'},
        'ci_management': {'key': 'ciManagement', 'type': 'MavenPomCi'},
        'contributors': {'key': 'contributors', 'type': '[MavenPomPerson]'},
        'dependencies': {'key': 'dependencies', 'type': '[MavenPomDependency]'},
        'dependency_management': {'key': 'dependencyManagement', 'type': 'MavenPomDependencyManagement'},
        'description': {'key': 'description', 'type': 'str'},
        'developers': {'key': 'developers', 'type': '[MavenPomPerson]'},
        'inception_year': {'key': 'inceptionYear', 'type': 'str'},
        'issue_management': {'key': 'issueManagement', 'type': 'MavenPomIssueManagement'},
        'licenses': {'key': 'licenses', 'type': '[MavenPomLicense]'},
        'mailing_lists': {'key': 'mailingLists', 'type': '[MavenPomMailingList]'},
        'model_version': {'key': 'modelVersion', 'type': 'str'},
        'modules': {'key': 'modules', 'type': '[str]'},
        'name': {'key': 'name', 'type': 'str'},
        'organization': {'key': 'organization', 'type': 'MavenPomOrganization'},
        'packaging': {'key': 'packaging', 'type': 'str'},
        'parent': {'key': 'parent', 'type': 'MavenPomParent'},
        'prerequisites': {'key': 'prerequisites', 'type': '{str}'},
        'properties': {'key': 'properties', 'type': '{str}'},
        'scm': {'key': 'scm', 'type': 'MavenPomScm'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, artifact_id=None, group_id=None, version=None, build=None, ci_management=None, contributors=None, dependencies=None, dependency_management=None, description=None, developers=None, inception_year=None, issue_management=None, licenses=None, mailing_lists=None, model_version=None, modules=None, name=None, organization=None, packaging=None, parent=None, prerequisites=None, properties=None, scm=None, url=None):
        super(MavenPomMetadata, self).__init__(artifact_id=artifact_id, group_id=group_id, version=version)
        self.build = build
        self.ci_management = ci_management
        self.contributors = contributors
        self.dependencies = dependencies
        self.dependency_management = dependency_management
        self.description = description
        self.developers = developers
        self.inception_year = inception_year
        self.issue_management = issue_management
        self.licenses = licenses
        self.mailing_lists = mailing_lists
        self.model_version = model_version
        self.modules = modules
        self.name = name
        self.organization = organization
        self.packaging = packaging
        self.parent = parent
        self.prerequisites = prerequisites
        self.properties = properties
        self.scm = scm
        self.url = url
