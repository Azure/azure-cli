# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import logging
from msrest.service_client import ServiceClient
from msrest import Configuration, Deserializer
from msrest.exceptions import HttpOperationError
from vsts.exceptions import VstsServiceError
import vsts.core.v4_1.models.team_project as team_project
from ..user.user_manager import UserManager
from ..base.base_manager import BaseManager
from . import models


class ProjectManager(BaseManager):
    """ Manage DevOps projects

    Create or list existing projects

    Attributes:
        config: url configuration
        client: authentication client
        dserialize: deserializer to process http responses into python classes
        Otherwise see BaseManager
    """

    def __init__(self, base_url='https://{}.visualstudio.com', organization_name="", creds=None,
                 create_project_url='https://dev.azure.com'):
        """Inits Project as per BaseManager and adds relevant other needed fields"""
        super(ProjectManager, self).__init__(creds, organization_name=organization_name)
        base_url = base_url.format(organization_name)
        self._config = Configuration(base_url=base_url)
        self._client = ServiceClient(creds, self._config)
        self._credentials = creds
        # Need to make a secondary client for the creating project as it uses a different base url
        self._create_project_config = Configuration(base_url=create_project_url)
        self._create_project_client = ServiceClient(creds, self._create_project_config)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._deserialize = Deserializer(client_models)
        self._user_mgr = UserManager(creds=self._creds)

    def create_project(self, projectName):
        """Create a new project for an organization"""
        try:
            capabilities = dict()
            capabilities['versioncontrol'] = {"sourceControlType": "Git"}
            capabilities['processTemplate'] = {"templateTypeId": "adcc42ab-9882-485e-a3ed-7678f01f66bc"}
            project = team_project.TeamProject(
                description="Azure Functions Devops Build created project",
                name=projectName,
                visibility=0,
                capabilities=capabilities
            )
            queue_object = self._core_client.queue_create_project(project)
            queue_id = queue_object.id
            self._poll_project(queue_id)
            # Sleep as there is normally a gap between project finishing being made and when we can retrieve it
            time.sleep(1)
            project = self._get_project_by_name(projectName)
            project.valid = True
            return project
        except VstsServiceError as e:
            return models.ProjectFailed(e)

    def list_projects(self):
        """Lists the current projects within an organization"""
        url = '/_apis/projects'

        # First pass without X-VSS-ForceMsaPassThrough header
        response = self._list_projects_request(url)

        deserialized = None
        if response.status_code // 100 != 2:
            logging.error("GET %s", response.url)
            logging.error("response: %s", response.status_code)
            logging.error(response.text)
            raise HttpOperationError(self._deserialize, response)
        else:
            deserialized = self._deserialize('Projects', response)

        return deserialized

    def _list_projects_request(self, url):
        query_paramters = {}
        query_paramters['includeCapabilities'] = 'true'

        header_paramters = {}
        if self._user_mgr.is_msa_account():
            header_paramters['X-VSS-ForceMsaPassThrough'] = 'true'

        request = self._client.get(url, params=query_paramters)
        response = self._client.send(request, headers=header_paramters)
        return response

    def _poll_project(self, project_id):
        """Helper function to poll the project"""
        project_created = False
        while not project_created:
            time.sleep(1)
            res = self._is_project_created(project_id)
            logging.info('project creation is: %s', res.status)
            if res.status == 'succeeded':
                project_created = True

    def _is_project_created(self, project_id):
        """Helper function to see the status of a project"""
        url = '/' + self._organization_name + '/_apis/operations/' + project_id
        query_paramters = {}

        header_paramters = {}
        header_paramters['Accept'] = 'application/json'
        if self._user_mgr.is_msa_account():
            header_paramters['X-VSS-ForceMsaPassThrough'] = 'true'

        request = self._create_project_client.get(url, params=query_paramters)
        response = self._create_project_client.send(request, headers=header_paramters)

        # Handle Response
        deserialized = None
        if response.status_code // 100 != 2:
            logging.error("GET %s", request.url)
            logging.error("response: %s", response.status_code)
            logging.error(response.text)
            raise HttpOperationError(self._deserialize, response)
        else:
            deserialized = self._deserialize('ProjectPoll', response)

        return deserialized
