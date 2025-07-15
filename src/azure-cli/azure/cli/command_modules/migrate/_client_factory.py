# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def cf_migrate(cli_ctx, *_):
    """
    Client factory for migrate commands.
    Since we're using PowerShell cmdlets directly, we don't need a traditional Azure SDK client.
    """
    # Return a simple object that can be used by custom commands
    return type('MigrateClient', (), {
        'cli_ctx': cli_ctx
    })()
