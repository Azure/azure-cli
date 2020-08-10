import vsts.service_endpoint.v4_1.models as models
from vsts.exceptions import VstsServiceError
from ..base.base_manager import BaseManager
from .service_endpoint_utils import sanitize_github_repository_fullname

class GithubServiceEndpointManager(BaseManager):
    def __init__(self, organization_name, project_name, creds):
        super(GithubServiceEndpointManager, self).__init__(
            creds, organization_name=organization_name, project_name=project_name
        )

    def get_github_service_endpoints(self, repository_fullname):
        service_endpoint_name = self._get_service_github_endpoint_name(repository_fullname)
        try:
            result = self._service_endpoint_client.get_service_endpoints_by_names(
                self._project_name,
                [service_endpoint_name],
                type="github"
            )
        except VstsServiceError:
            return []
        return result

    def create_github_service_endpoint(self, repository_fullname, github_pat):
        data = {}
        auth = models.endpoint_authorization.EndpointAuthorization(
            parameters={
                "accessToken": github_pat
            },
            scheme="PersonalAccessToken"
        )
        service_endpoint_name = self._get_service_github_endpoint_name(repository_fullname)
        service_endpoint = models.service_endpoint.ServiceEndpoint(
            administrators_group=None,
            authorization=auth,
            data=data,
            name=service_endpoint_name,
            type="github",
            url="http://github.com"
        )

        return self._service_endpoint_client.create_service_endpoint(service_endpoint, self._project_name)

    def _get_service_github_endpoint_name(self, repository_name):
        return sanitize_github_repository_fullname(repository_name)
