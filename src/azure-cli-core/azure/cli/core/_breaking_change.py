from azure.cli.core.breaking_change import register_conditional_breaking_change, AzCLIOtherChange


register_conditional_breaking_change('MANAGED_IDENTITY_WITH_USERNAME', AzCLIOtherChange(
    cmd='login',
    message='Passing the managed identity ID with --username is deprecated and will be removed in a future release. '
            'Please use --client-id, --object-id or --resource-id instead.'))
