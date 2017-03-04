# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.core.azlogging as azlogging
logger = azlogging.get_az_logger(__name__)

def create_continuous_deployment(remote_access_token):
    """
    Provisions Jenkins and Spinnaker, configures CI and CD pipelines, kicks off initial build-deploy
    and saves the CI/CD information to a local project file.
    """
    pass

