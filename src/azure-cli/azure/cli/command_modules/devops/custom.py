# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError

from azure.cli.command_modules.devops._artifacttool import ArtifactToolInvoker

logger = get_logger(__name__)


def _resolve_organization(organization, project, scope, detect):
    """Resolve organization and optionally project from arguments or defaults."""
    if not organization:
        # Try to detect organization from git remote or az devops configuration
        try:
            from azext_devops.dev.common.services import (  # pylint: disable=import-outside-toplevel
                resolve_instance, resolve_instance_and_project)
            if scope == 'project':
                return resolve_instance_and_project(detect=detect, organization=organization, project=project)
            return resolve_instance(detect=detect, organization=organization), project
        except ImportError:
            pass
        raise CLIError("--organization is required. Please provide the organization URL or "
                       "install the azure-devops extension (az extension add --name azure-devops) "
                       "to use automatic detection.")
    if scope == 'project' and not project:
        raise CLIError("--project is required when --scope is 'project'.")
    return organization, project


def download_package(feed,
                     name,
                     version,
                     path,
                     file_filter=None,
                     no_hardlinks=False,
                     scope='organization',
                     organization=None,
                     project=None,
                     detect=None):
    """Download a Universal Package.

    :param scope: Scope of the feed: 'project' if the feed was created in a project,
                  and 'organization' otherwise.
    :type scope: str
    :param feed: Name or ID of the feed.
    :type feed: str
    :param name: Name of the package, e.g. 'foo-package'.
    :type name: str
    :param version: Version of the package, e.g. '1.0.0'.
    :type version: str
    :param path: Directory to place the package contents.
    :type path: str
    :param file_filter: Wildcard filter for file download.
    :type file_filter: str
    :param no_hardlinks: Disable the use of hard links when downloading. Use on file systems
                         that do not support hard linking.
    :type no_hardlinks: bool
    """
    if scope == 'project':
        organization, project = _resolve_organization(organization, project, scope, detect)
    else:
        if project is not None:
            raise CLIError("--scope 'project' is required when specifying a value in --project")
        organization, _ = _resolve_organization(organization, None, scope, detect)

    artifact_tool = ArtifactToolInvoker()
    return artifact_tool.download_universal(organization, project, feed, name, version, path,
                                            file_filter, no_hardlinks)


def publish_package(feed,
                    name,
                    version,
                    path,
                    description=None,
                    scope='organization',
                    organization=None,
                    project=None,
                    detect=None):
    """Publish a Universal Package.

    :param scope: Scope of the feed: 'project' if the feed was created in a project,
                  and 'organization' otherwise.
    :type scope: str
    :param feed: Name or ID of the feed.
    :type feed: str
    :param name: Name of the package, e.g. 'foo-package'.
    :type name: str
    :param version: Version of the package, e.g. '1.0.0'.
    :type version: str
    :param description: Description of the package.
    :type description: str
    :param path: Directory containing the package contents.
    :type path: str
    """
    if scope == 'project':
        organization, project = _resolve_organization(organization, project, scope, detect)
    else:
        if project is not None:
            raise CLIError("--scope 'project' is required when specifying a value in --project")
        organization, _ = _resolve_organization(organization, None, scope, detect)

    artifact_tool = ArtifactToolInvoker()
    return artifact_tool.publish_universal(organization, project, feed, name, version, description, path)
