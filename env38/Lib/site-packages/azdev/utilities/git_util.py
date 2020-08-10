# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os

from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)


def filter_by_git_diff(selected_modules, git_source, git_target, git_repo):
    if not any([git_source, git_target, git_repo]):
        return selected_modules

    if not all([git_target, git_repo]):
        raise CLIError('usage error: [--src NAME]  --tgt NAME --repo PATH')

    files_changed = diff_branches(git_repo, git_target, git_source)
    mods_changed = summarize_changed_mods(files_changed)

    repo_path = str(os.path.abspath(git_repo)).lower()
    to_remove = {'mod': [], 'core': [], 'ext': []}
    for key in selected_modules:
        for name, path in selected_modules[key].items():
            path = path.lower()
            if path.startswith(repo_path):
                if name in mods_changed:
                    # has changed, so do not filter out
                    continue
            # if not in the repo or has not changed, filter out
            to_remove[key].append(name)

    # remove the unchanged modules
    for key in to_remove:
        for name in to_remove[key]:
            selected_modules[key].pop(name)
    logger.info('Filtered out: %s', to_remove)

    return selected_modules


def summarize_changed_mods(files_changed):
    from azdev.utilities import extract_module_name

    mod_set = set()
    for f in files_changed:
        try:
            mod_name = extract_module_name(f)
        except CLIError:
            # some files aren't part of a module
            continue
        mod_set.add(mod_name)
    return list(mod_set)


def diff_branches(repo, target, source):
    """ Returns a list of files that have changed in a given repo
        between two branches. """
    try:
        import git  # pylint: disable=unused-import,unused-variable
        import git.exc as git_exc
        import gitdb
    except ImportError as ex:
        raise CLIError(ex)

    from git import Repo
    try:
        git_repo = Repo(repo)
    except (git_exc.NoSuchPathError, git_exc.InvalidGitRepositoryError):
        raise CLIError('invalid git repo: {}'.format(repo))

    def get_commit(branch):
        try:
            return git_repo.commit(branch)
        except gitdb.exc.BadName:
            raise CLIError('usage error, invalid branch: {}'.format(branch))

    if source:
        source_commit = get_commit(source)
    else:
        source_commit = git_repo.head.commit
    target_commit = get_commit(target)

    logger.info('Filtering down to modules which have changed based on:')
    logger.info('cd %s', repo)
    logger.info('git --no-pager diff %s..%s --name-only -- .\n', target_commit, source_commit)

    diff_index = target_commit.diff(source_commit)

    return [diff.b_path for diff in diff_index]
