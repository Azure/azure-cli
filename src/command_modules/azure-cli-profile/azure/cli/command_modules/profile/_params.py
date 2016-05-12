from azure.cli.commands import COMMON_PARAMETERS as GLOBAL_COMMON_PARAMETERS
from azure.cli._locale import L

# BASIC PARAMETER CONFIGURATION

PARAMETER_ALIASES = GLOBAL_COMMON_PARAMETERS.copy()
PARAMETER_ALIASES.update({
    'password': {
        'name': '--password -p',
        'help': L('User password or client secret. Will prompt if not given.'),
    },
    'service_principal': {
        'name': '--service-principal',
        'action': 'store_true',
        'help': L('The credential representing a service principal.')
    },
    'subscription_name_or_id': {
        'name': '--subscription-name-or-id -n',
        'metavar': 'SUBSCRIPTION_NAME_OR_ID',
        'help': L('Subscription id. Unique name also works.')
    },
    'tenant': {
        'name': '--tenant -t',
        'help': L('The tenant associated with the service principal.')
    },
    'username': {
        'name': '--username -u',
        'help': L('Organization Id or service principal.')
    }
})
