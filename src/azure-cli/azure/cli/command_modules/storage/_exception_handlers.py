from azure.cli.core.profiles import ResourceType, get_sdk
from knack.util import CLIError


def account_key_exception_handler(ex):
    from azure.common import AzureException
    from azure.core.exceptions import ClientAuthenticationError
    if isinstance(ex, AzureException) and 'incorrect padding' in ex.exc_msg:
        raise CLIError('incorrect usage: the given account key may be not valid.')
