from azure.core.credentials import TokenCredential
from azure.cli.core.auth.util import resource_to_scopes

# Enable passing in custom token audience that takes precedence over SDK's hardcoded audience.
# Users can configure an audience based on their cloud.
class AppConfigurationCliCredential(TokenCredential):

    def __init__(self, credential: TokenCredential, resource: str = None):
        self._impl = credential
        self._resource = resource
    
    def get_token(self, *scopes, **kwargs):

        if self._resource is not None:
            scopes = resource_to_scopes(self._resource)

        return self._impl.get_token(*scopes, **kwargs)