# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class UnpackagedExtensionData(Model):
    """UnpackagedExtensionData.

    :param categories:
    :type categories: list of str
    :param description:
    :type description: str
    :param display_name:
    :type display_name: str
    :param draft_id:
    :type draft_id: str
    :param extension_name:
    :type extension_name: str
    :param installation_targets:
    :type installation_targets: list of :class:`InstallationTarget <gallery.v4_1.models.InstallationTarget>`
    :param is_converted_to_markdown:
    :type is_converted_to_markdown: bool
    :param pricing_category:
    :type pricing_category: str
    :param product:
    :type product: str
    :param publisher_name:
    :type publisher_name: str
    :param qn_aEnabled:
    :type qn_aEnabled: bool
    :param referral_url:
    :type referral_url: str
    :param repository_url:
    :type repository_url: str
    :param tags:
    :type tags: list of str
    :param version:
    :type version: str
    :param vsix_id:
    :type vsix_id: str
    """

    _attribute_map = {
        'categories': {'key': 'categories', 'type': '[str]'},
        'description': {'key': 'description', 'type': 'str'},
        'display_name': {'key': 'displayName', 'type': 'str'},
        'draft_id': {'key': 'draftId', 'type': 'str'},
        'extension_name': {'key': 'extensionName', 'type': 'str'},
        'installation_targets': {'key': 'installationTargets', 'type': '[InstallationTarget]'},
        'is_converted_to_markdown': {'key': 'isConvertedToMarkdown', 'type': 'bool'},
        'pricing_category': {'key': 'pricingCategory', 'type': 'str'},
        'product': {'key': 'product', 'type': 'str'},
        'publisher_name': {'key': 'publisherName', 'type': 'str'},
        'qn_aEnabled': {'key': 'qnAEnabled', 'type': 'bool'},
        'referral_url': {'key': 'referralUrl', 'type': 'str'},
        'repository_url': {'key': 'repositoryUrl', 'type': 'str'},
        'tags': {'key': 'tags', 'type': '[str]'},
        'version': {'key': 'version', 'type': 'str'},
        'vsix_id': {'key': 'vsixId', 'type': 'str'}
    }

    def __init__(self, categories=None, description=None, display_name=None, draft_id=None, extension_name=None, installation_targets=None, is_converted_to_markdown=None, pricing_category=None, product=None, publisher_name=None, qn_aEnabled=None, referral_url=None, repository_url=None, tags=None, version=None, vsix_id=None):
        super(UnpackagedExtensionData, self).__init__()
        self.categories = categories
        self.description = description
        self.display_name = display_name
        self.draft_id = draft_id
        self.extension_name = extension_name
        self.installation_targets = installation_targets
        self.is_converted_to_markdown = is_converted_to_markdown
        self.pricing_category = pricing_category
        self.product = product
        self.publisher_name = publisher_name
        self.qn_aEnabled = qn_aEnabled
        self.referral_url = referral_url
        self.repository_url = repository_url
        self.tags = tags
        self.version = version
        self.vsix_id = vsix_id
