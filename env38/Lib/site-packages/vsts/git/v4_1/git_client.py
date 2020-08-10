# coding=utf-8
# --------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is
# regenerated.
# --------------------------------------------------------------------------


from msrest.universal_http import ClientRequest
from .git_client_base import GitClientBase


class GitClient(GitClientBase):
    """Git
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(GitClient, self).__init__(base_url, creds)

    def get_vsts_info(self, relative_remote_url):
        url = self._client.format_url(relative_remote_url.rstrip('/') + '/vsts/info')
        request = ClientRequest(method='GET', url=url)
        headers = {'Accept': 'application/json'}
        if self._suppress_fedauth_redirect:
            headers['X-TFS-FedAuthRedirect'] = 'Suppress'
        if self._force_msa_pass_through:
            headers['X-VSS-ForceMsaPassThrough'] = 'true'
        response = self._send_request(request, headers)
        return self._deserialize('VstsInfo', response)

    @staticmethod
    def get_vsts_info_by_remote_url(remote_url, credentials,
                                    suppress_fedauth_redirect=True,
                                    force_msa_pass_through=True):
        request = ClientRequest(method='GET', url=remote_url.rstrip('/') + '/vsts/info')
        headers = {'Accept': 'application/json'}
        if suppress_fedauth_redirect:
            headers['X-TFS-FedAuthRedirect'] = 'Suppress'
        if force_msa_pass_through:
            headers['X-VSS-ForceMsaPassThrough'] = 'true'
        git_client = GitClient(base_url=remote_url, creds=credentials)
        response = git_client._send_request(request, headers)
        return git_client._deserialize('VstsInfo', response)
