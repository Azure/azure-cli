Releasing Components
====================

To create a release for a component, create a PR with title `Release <component-name> <version>`

    e.g. 'Release azure-cli-vm 0.1.1'

The 'Release' label should be added to the PR.

PR checklist:

- [ ] The PR title (commit) has format `Release <component-name> <version>`.
- [ ] `setup.py` has been modified with the same version as in the PR title.
- [ ] If required, `__version__` defined in any `__init__.py` should also be modified to match.
- [ ] `HISTORY.rst` has been modified with appropriate release notes.

When the PR is approved and merged, the component will be released and available on PyPI.
