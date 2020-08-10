# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PublishedExtension(Model):
    """PublishedExtension.

    :param categories:
    :type categories: list of str
    :param deployment_type:
    :type deployment_type: object
    :param display_name:
    :type display_name: str
    :param extension_id:
    :type extension_id: str
    :param extension_name:
    :type extension_name: str
    :param flags:
    :type flags: object
    :param installation_targets:
    :type installation_targets: list of :class:`InstallationTarget <gallery.v4_0.models.InstallationTarget>`
    :param last_updated:
    :type last_updated: datetime
    :param long_description:
    :type long_description: str
    :param published_date: Date on which the extension was first uploaded.
    :type published_date: datetime
    :param publisher:
    :type publisher: :class:`PublisherFacts <gallery.v4_0.models.PublisherFacts>`
    :param release_date: Date on which the extension first went public.
    :type release_date: datetime
    :param shared_with:
    :type shared_with: list of :class:`ExtensionShare <gallery.v4_0.models.ExtensionShare>`
    :param short_description:
    :type short_description: str
    :param statistics:
    :type statistics: list of :class:`ExtensionStatistic <gallery.v4_0.models.ExtensionStatistic>`
    :param tags:
    :type tags: list of str
    :param versions:
    :type versions: list of :class:`ExtensionVersion <gallery.v4_0.models.ExtensionVersion>`
    """

    _attribute_map = {
        'categories': {'key': 'categories', 'type': '[str]'},
        'deployment_type': {'key': 'deploymentType', 'type': 'object'},
        'display_name': {'key': 'displayName', 'type': 'str'},
        'extension_id': {'key': 'extensionId', 'type': 'str'},
        'extension_name': {'key': 'extensionName', 'type': 'str'},
        'flags': {'key': 'flags', 'type': 'object'},
        'installation_targets': {'key': 'installationTargets', 'type': '[InstallationTarget]'},
        'last_updated': {'key': 'lastUpdated', 'type': 'iso-8601'},
        'long_description': {'key': 'longDescription', 'type': 'str'},
        'published_date': {'key': 'publishedDate', 'type': 'iso-8601'},
        'publisher': {'key': 'publisher', 'type': 'PublisherFacts'},
        'release_date': {'key': 'releaseDate', 'type': 'iso-8601'},
        'shared_with': {'key': 'sharedWith', 'type': '[ExtensionShare]'},
        'short_description': {'key': 'shortDescription', 'type': 'str'},
        'statistics': {'key': 'statistics', 'type': '[ExtensionStatistic]'},
        'tags': {'key': 'tags', 'type': '[str]'},
        'versions': {'key': 'versions', 'type': '[ExtensionVersion]'}
    }

    def __init__(self, categories=None, deployment_type=None, display_name=None, extension_id=None, extension_name=None, flags=None, installation_targets=None, last_updated=None, long_description=None, published_date=None, publisher=None, release_date=None, shared_with=None, short_description=None, statistics=None, tags=None, versions=None):
        super(PublishedExtension, self).__init__()
        self.categories = categories
        self.deployment_type = deployment_type
        self.display_name = display_name
        self.extension_id = extension_id
        self.extension_name = extension_name
        self.flags = flags
        self.installation_targets = installation_targets
        self.last_updated = last_updated
        self.long_description = long_description
        self.published_date = published_date
        self.publisher = publisher
        self.release_date = release_date
        self.shared_with = shared_with
        self.short_description = short_description
        self.statistics = statistics
        self.tags = tags
        self.versions = versions
