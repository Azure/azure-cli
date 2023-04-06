from knack.util import CLIError

def get_default_region(cmd):
    cloud_name = cmd.cli_ctx.cloud.name
    if cloud_name.lower() == 'azurechinacloud':
        raise CLIError("Azure China Cloud is not supported for the Azure Monitor Metrics addon")
    if cloud_name.lower() == 'azureusgovernment':
        return "usgovvirginia"
    return "eastus"