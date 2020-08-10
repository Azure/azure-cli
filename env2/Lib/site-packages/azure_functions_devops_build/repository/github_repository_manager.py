# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import base64
from ..exceptions import (
    GithubContentNotFound,
    GithubIntegrationRequestError,
    GithubUnauthorizedError,
)
from ..base.base_github_manager import BaseGithubManager


class GithubRepositoryManager(BaseGithubManager):

    def check_github_repository(self, repository_fullname):
        header_parameters = self.construct_github_request_header()
        request = self._client.get('/repos/{repo}'.format(repo=repository_fullname))
        response = self._client.send(request, header_parameters)
        if response.status_code // 100 == 2:
            return True
        return False

    def check_github_file(self, repository_fullname, file_path):
        header_parameters = self.construct_github_request_header()
        request = self._client.get('/repos/{repo}/contents/{path}'.format(
            repo=repository_fullname,
            path=file_path
        ))
        response = self._client.send(request, header_parameters)
        return response.status_code // 100 == 2

    def get_content(self, repository_fullname, file_path, get_metadata=True):
        header_parameters = self.construct_github_request_header()

        if get_metadata:  # Get files metadata
            header_parameters['Content-Type'] = 'application/json'
        else:  # Get files content
            header_parameters['Accept'] = 'application/vnd.github.v3.raw'

        request = self._client.get('/repos/{repo}/contents/{path}'.format(
            repo=repository_fullname,
            path=file_path
        ))
        response = self._client.send(request, header_parameters)

        # The response is a Json content
        if response.status_code // 100 == 2:
            return response.json()

        if response.status_code == 401:
            raise GithubUnauthorizedError('Failed to read {repo}/{path}'.format(
                repo=repository_fullname,
                path=file_path
            ))

        if response.status_code == 404:
            raise GithubContentNotFound('Failed to find {repo}/{path}'.format(
                repo=repository_fullname,
                path=file_path
            ))

        raise GithubIntegrationRequestError(response.status_code)

    def put_content(self, repository_fullname, file_path, data):
        header_parameters = self.construct_github_request_header()
        header_parameters['Content-Type'] = 'Application/Json'
        request = self._client.put(
            url='/repos/{repo}/contents/{path}'.format(repo=repository_fullname, path=file_path),
            headers=header_parameters,
            content=data
        )

        response = self._client.send(request)
        if response.status_code // 100 == 2:
            return response

        if response.status_code == 401:
            raise GithubUnauthorizedError('Failed to write {repo}/{path}'.format(
                repo=repository_fullname,
                path=file_path
            ))

        if response.status_code == 404:
            raise GithubContentNotFound('Failed to find {repo}/{path}'.format(
                repo=repository_fullname,
                path=file_path
            ))

        raise GithubIntegrationRequestError("{res.status_code} {res.url}".format(res=response))

    def commit_file(self, repository_fullname, file_path, commit_message, file_data, sha=None, encode='utf-8'):
        data = {
            "branch": "master",
            "message": "{message}".format(message=commit_message),
            "content": base64.b64encode(bytes(file_data.encode(encode))).decode('ascii'),
        }

        if sha:
            data["sha"] = sha

        return self.put_content(
            repository_fullname=repository_fullname,
            file_path=file_path,
            data=data
        )
