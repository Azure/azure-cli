# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ..base.base_manager import BaseManager
from vsts.exceptions import VstsClientRequestError

class ArtifactManager(BaseManager):
    """ Manage DevOps Artifacts

    Attributes:
        See BaseManager
    """

    def __init__(self, organization_name="", project_name="", creds=None):
        """Inits ArtifactManager as per BaseManager and includes relevant clients"""
        super(ArtifactManager, self).__init__(creds, organization_name=organization_name, project_name=project_name)

    def list_artifacts(self, build_id):
        """Lists artifacts from a build"""
        project = self._get_project_by_name(self._project_name)
        try:
            result = self._build_client.get_artifacts(build_id, project.id)
        except VstsClientRequestError:
            return []
        return result
