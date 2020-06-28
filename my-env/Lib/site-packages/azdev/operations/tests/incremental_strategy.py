# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import abc
from knack.util import CLIError

from azdev.utilities import get_path_table, git_util


# @wrapt.decorator
# def cli_release_scenario(wrapped, _, args, kwargs):
#     """
#     Filter out those files in Azure CLI release stage
#     """
#     # TODO
#     # if instance.resolved:
#     #     return instance

#     return wrapped(*args, **kwargs)


class AzureDevOpsContext(abc.ABC):
    def __init__(self, git_repo, git_source, git_target):
        """
        :param git_source: could be commit id, branch name or any valid value for git diff
        :param git_target: could be commit id, branch name or any valid value for git diff
        """
        self.git_repo = git_repo
        self.git_source = git_source
        self.git_target = git_target

    @abc.abstractmethod
    def filter(self, test_index):
        pass


class CLIAzureDevOpsContext(AzureDevOpsContext):
    """
    Assemble strategy of incremental test on Azure DevOps Environment for Azure CLI
    """
    def __init__(self, git_repo, git_source, git_target):
        super().__init__(git_repo, git_source, git_target)

        if not any([self.git_source, self.git_target, self.git_repo]):
            raise CLIError('usage error: [--src NAME]  --tgt NAME --repo PATH --cli-ci')

        if not all([self.git_target, self.git_repo]):
            raise CLIError('usage error: [--src NAME]  --tgt NAME --repo PATH --cli-ci')

    @property
    def modified_files(self):
        modified_files = git_util.diff_branches(self.git_repo, self.git_source, self.git_target)
        return [f for f in modified_files if f.startswith('src/')]

    def filter(self, test_index):
        """
        Strategy on Azure CLI pull request verification stage.

        :return: a list of modified packages
        """

        modified_packages = git_util.summarize_changed_mods(self.modified_files)

        if any(core_package in modified_packages for core_package in ['core', 'testsdk', 'telemetry']):
            path_table = get_path_table()

            # tests under all packages
            return list(path_table['mod'].keys()) + list(path_table['core'].keys()) + list(path_table['ext'].keys())

        return modified_packages
