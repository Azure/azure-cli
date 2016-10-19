#!/usr/bin/env python

import re, sys
# from azure.cli.core._util import CLIError

def get_repo_info(repositoryUrl):
    # Parses the repository url to find account, project (for VSTS) and the repository name and repo_type.

    repo_parsers = {
        'vsts' : parse_vsts,
        'github' : parse_github
    }
    for parser in repo_parsers:
        result = repo_parsers[parser](repositoryUrl)
        if result:
            # merge successful parser name with result as repo_type

            repo_info = result.copy()
            repo_info.update({'repo_type' : parser})
            return repo_info

    raise CLIError("Only Visual Studio Team Services or GitHub repositories are currently supported.")

def parse_vsts(repositoryUrl):
    """ Parses a vsts git repo and returns object with filtered details
    # Testing VSTS parser for ssh urls
    >>> parse_vsts('ssh://myvstsaccountname@myvstsaccountname.visualstudio.com:22/_git/myvstsgit')
    {'repo': 'myvstsgit', 'vsts_account_name': 'myvstsaccountname', 'vsts_project_name': 'myvstsgit'}

    # Testing VSTS parser for caps
    >>> parse_vsts('ssh://myvstsaccountname@myvstsaccountname.visualSTUDIO.com:22/_git/myvstsGIT')
    {'repo': 'myvstsGIT', 'vsts_account_name': 'myvstsaccountname', 'vsts_project_name': 'myvstsGIT'}

    # Testing VSTS parser for ssh urls without ssh protocol
    >>> parse_vsts('myvstsaccountname@myvstsaccountname.visualstudio.com:22/_git/myvstsgit')
    {'repo': 'myvstsgit', 'vsts_account_name': 'myvstsaccountname', 'vsts_project_name': 'myvstsgit'}

    # Testing VSTS parser for ssh urls with numbers and strange characters
    >>> parse_vsts('ssh://myvstsaccountname_1234@myvstsaccountname_1234.visualstudio.com:22/_git/myvstsgit')
    {'repo': 'myvstsgit', 'vsts_account_name': 'myvstsaccountname_1234', 'vsts_project_name': 'myvstsgit'}

    # Testing VSTS parser for https
    >>> parse_vsts('https://myvstsaccountname.visualstudio.com/_git/myvstsgit')
    {'repo': 'myvstsgit', 'vsts_account_name': 'myvstsaccountname', 'vsts_project_name': 'myvstsgit'}

    # Testing VSTS parser for http
    >>> parse_vsts('http://myvstsaccountname.visualstudio.com/_git/myvstsgit')
    {'repo': 'myvstsgit', 'vsts_account_name': 'myvstsaccountname', 'vsts_project_name': 'myvstsgit'}

    # Testing VSTS parser for empty value
    >>> parse_vsts('') is None
    True

    # Testing VSTS parser for multiple git repos on same account for https
    >>> parse_vsts('https://myaccount.visualstudio.com/myproject/_git/myrepo')
    {'repo': 'myrepo', 'vsts_account_name': 'myaccount', 'vsts_project_name': 'myproject'}

    # Testing VSTS parser for multiple git repos on same account for ssh
    >>> parse_vsts('ssh://myaccount@myaccount.visualstudio.com/myproject/_git/myrepo')
    {'repo': 'myrepo', 'vsts_account_name': 'myaccount', 'vsts_project_name': 'myproject'}

    # Testing VSTS parser for completely wrong urls
    >>> parse_vsts('ssh://myaccount@myaccount.visualstudio.com////myproject/_git/myrepo') is None
    True

    # Testing VSTS parser for completely wrong urls
    >>> parse_vsts('httpmyaccount@msdiohjoadoajsdijasoijasiodioasjdoas') is None
    True
    """

    # Parse a vsts repo url
    # 1. ssh://vsts_account_name@{vsts_account_name}.visualstudio.com:22/_git/{vsts_project_name&repo}
    matches = reg_find_if_one(repositoryUrl, '^(?:ssh\:\/\/){0,1}[^@]+\@([^\.]+)\.[vV][iI][sS][uU][aA][lL][sS][tT][uU][dD][iI][oO]\.[cC][oO][mM]\:[0-9]+\/[^\/]+\/([^\s+]+)$')
    if matches:
        # one set of matches with two captures
        assert_friendly(len(matches) == 2, 'Invalid vsts repository URL')
        return {
            'vsts_account_name' : matches[0],
            'vsts_project_name' : matches[1],
            'repo' : matches[1]
        }

    # 2. https://{vsts_account_name}.visualstudio.com/_git/{vsts_project_name&repo}/
    matches = reg_find_if_one(repositoryUrl, '^http[s]{0,1}\:\/\/([^\.]+)\.[vV][iI][sS][uU][aA][lL][sS][tT][uU][dD][iI][oO]\.[cC][oO][mM]\/[^\/]+\/([^\/\s]+)$')
    if matches:
        # one set of matches with two captures
        assert_friendly( len(matches) == 2, 'Invalid vsts repository URL')
        return {
            'vsts_account_name' : matches[0],
            'vsts_project_name' : matches[1],
            'repo' : matches[1]
        }

    # 3. ssh://vsts_account_name@{vsts_account_name}.visualstudio.com:22/{vsts_project_name}/_git/{repo}
    matches = reg_find_if_one(repositoryUrl, '^(?:ssh\:\/\/){0,1}[^@]+\@([^\.]+)\.[vV][iI][sS][uU][aA][lL][sS][tT][uU][dD][iI][oO]\.[cC][oO][mM]\/([^\/]+)\/(?:\_git)\/([\S]+)$')
    if matches:
        # one set of matches with two captures
        assert_friendly( len(matches) == 3, 'Invalid vsts repository URL')
        return {
            'vsts_account_name' : matches[0],
            'vsts_project_name' : matches[1],
            'repo' : matches[2]
        }

    # 4. https://{vsts_account_name}.visualstudio.com:22/{vsts_project_name}/_git/{repo}
    matches = reg_find_if_one(repositoryUrl, '^http[s]{0,1}\:\/\/([^\.]+)\.[vV][iI][sS][uU][aA][lL][sS][tT][uU][dD][iI][oO]\.[cC][oO][mM]\/([^\/]+)\/(?:\_git)\/([\S]+)$')
    if matches:
        # one set of matches with two captures
        assert_friendly( len(matches) == 3, 'Invalid vsts repository URL')
        return {
            'vsts_account_name' : matches[0],
            'vsts_project_name' : matches[1],
            'repo' : matches[2]
        }

    return None

def parse_github(repositoryUrl):

    """
    # Testing Github parser for ssh urls
    >>> parse_github('ssh://git@github.com:githubusername/repopath.git')
    {'repo': 'repopath', 'github_account_name': 'githubusername'}

    # Testing Github parser for caps
    >>> parse_github('ssh://git@giTHub.com:gIThubusername/repopath.git')
    {'repo': 'repopath', 'github_account_name': 'gIThubusername'}

    # Testing Github parser for ssh urls without protocol
    >>> parse_github('git@github.com:githubusername/repopath.git')
    {'repo': 'repopath', 'github_account_name': 'githubusername'}

    # Testing Github parser for https urls
    >>> parse_github('https://github.com/githubusername/repopath.git')
    {'repo': 'repopath', 'github_account_name': 'githubusername'}

    # Testing Github parser for http urls
    >>> parse_github('http://github.com/githubusername/repopath.git')
    {'repo': 'repopath', 'github_account_name': 'githubusername'}

    # Testing Github parser for empty string
    >>> parse_github('') is None
    True

    # Testing Github parser for completely wrong urls
    >>> parse_github('http://github.com/githubusernamakpsod') is None
    True

    # Testing Github parser for missing git
    >>> parse_github('http://github.com/githubusername/repopath')
    {'repo': 'repopath', 'github_account_name': 'githubusername'}

    # Testing Github parser for missing it
    >>> parse_github('ssh://git@github.com:githubusername/repopath')
    {'repo': 'repopath', 'github_account_name': 'githubusername'}

    # Testing Github parser for http/https with username@github.com
    >>> parse_github('https://githubusername@github.com/user/sample-app.git')
    {'repo': 'user/sample-app', 'github_account_name': 'githubusername'}

    # Testing Github parser for http/https with username@github.com without git
    >>> parse_github('https://githubusername@github.com/user/sample-app')
    {'repo': 'user/sample-app', 'github_account_name': 'githubusername'}
    """

    # Parse a github repo url
    # 1. ssh://git@github.com:{githubusername}/{repopath}.git
    matches = reg_find_if_one(repositoryUrl, '^(?:ssh\:\/\/){0,1}[gG][iI][tT]\@[gG][iI][tT][hH][uU][bB]\.[cC][oO][mM]\:([^\/]+)\/([^\s]+)\.git$')
    if matches:
        assert_friendly(len(matches) == 2, 'Invalid github repository URL')
        return {
            'github_account_name' : matches[0],
            'repo' : matches[1]
        }

    # 2. https://github.com/{githubusername}/{repopath}.git
    matches = reg_find_if_one(repositoryUrl, '^http[s]{0,1}\:\/\/[gG][iI][tT][hH][uU][bB]\.[cC][oO][mM]\/([^\/]+)\/([^\s]+)\.git$')
    if matches:
        # one set of matches with two captures
        assert_friendly( len(matches) == 2, 'Invalid github repository URL')
        return {
            'github_account_name' : matches[0],
            'repo' : matches[1]
        }

    # 3. https://{githubusername}@github.com/{githubusername}/{repopath}.git
    matches = reg_find_if_one(repositoryUrl, '^http[s]{0,1}\:\/\/([^@]+)\@[gG][iI][tT][hH][uU][bB]\.[cC][oO][mM]\/([^\s]+)\.git$')
    if matches:
        # one set of matches with two captures
        assert_friendly( len(matches) == 2, 'Invalid github repository URL')
        return {
            'github_account_name' : matches[0],
            'repo' : matches[1]
        }

    # 4. ssh://git@github.com:{githubusername}/{repopath}
    matches = reg_find_if_one(repositoryUrl, '^(?:ssh\:\/\/){0,1}[gG][iI][tT]\@[gG][iI][tT][hH][uU][bB]\.[cC][oO][mM]\:([^\/]+)\/([^\s]+)$')
    if matches:
        assert_friendly(len(matches) == 2, 'Invalid github repository URL')
        return {
            'github_account_name' : matches[0],
            'repo' : matches[1]
        }

    # 5. https://github.com/{githubusername}/{repopath}
    matches = reg_find_if_one(repositoryUrl, '^http[s]{0,1}\:\/\/[gG][iI][tT][hH][uU][bB]\.[cC][oO][mM]\/([^\/]+)\/([^\s]+)$')
    if matches:
        # one set of matches with two captures
        assert_friendly( len(matches) == 2, 'Invalid github repository URL')
        return {
            'github_account_name' : matches[0],
            'repo' : matches[1]
        }

    # 6. https://{githubusername}@github.com/{githubusername}/{repopath}
    matches = reg_find_if_one(repositoryUrl, '^http[s]{0,1}\:\/\/([^@]+)\@[gG][iI][tT][hH][uU][bB]\.[cC][oO][mM]\/([^\s]+)$')
    if matches:
        # one set of matches with two captures
        assert_friendly( len(matches) == 2, 'Invalid github repository URL')
        return {
            'github_account_name' : matches[0],
            'repo' : matches[1]
        }
    return None

def reg_find_if_one(string, expression):
    # returns match if and only if one match exists or None
    r=re.compile(expression) # find all matches for regex expression in a string
    m=re.findall(r,string)
    # only one match should be found
    if len(m) != 1:
        return None
    m=m[0]
    return m

def assert_friendly(condition, msg):
    # User friendly assertion
    if not condition:
        raise CLIError(msg)