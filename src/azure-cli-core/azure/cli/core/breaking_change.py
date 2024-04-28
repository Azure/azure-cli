# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import abc

NEXT_BREAKING_CHANGE_RELEASE = '2.61.0'


def _next_breaking_change_version():
    return NEXT_BREAKING_CHANGE_RELEASE


# pylint: disable=too-few-public-methods
class TargetVersion(abc.ABC):
    @abc.abstractmethod
    def __str__(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def version(self):
        raise NotImplementedError()


# pylint: disable=too-few-public-methods
class NextBreakingChangeWindow(TargetVersion):
    def __str__(self):
        return f'in next breaking change release({_next_breaking_change_version()})'

    def version(self):
        return _next_breaking_change_version()


# pylint: disable=too-few-public-methods
class ExactVersion(TargetVersion):
    def __init__(self, version):
        self.version = version

    def __str__(self):
        return f'in {self.version}'

    def version(self):
        return self.version()


# pylint: disable=too-few-public-methods
class UnspecificVersion(TargetVersion):
    def __str__(self):
        return 'in future'

    def version(self):
        return None


class BreakingChange(abc.ABC):
    @property
    @abc.abstractmethod
    def message(self):
        pass

    @property
    @abc.abstractmethod
    def target_version(self):
        pass


class Remove(BreakingChange):
    """
    Remove the command groups, commands or arguments in a future release.

    **It is recommended to utilize `deprecate_info` instead of this class to pre-announce Breaking Change of Removal.**
    :param target: name of the removed command group, command or argument
    :param target_version: version where the breaking change is expected to happen.
    :type target_version: TargetVersion
    :param redirect: alternative way to replace the old behavior
    :param doc_link: link of the related document
    """
    def __init__(self, target, target_version=NextBreakingChangeWindow(), redirect=None, doc_link=None):
        self.target = target
        self._target_version = target_version
        self.alter = redirect
        self.doc_link = doc_link

    @property
    def message(self):
        alter = f' Please use {self.alter} instead.' if self.alter else ''
        doc = f' To know more about the Breaking Change, please visit {self.doc_link}.' if self.doc_link else ''
        return f'`{self.target}` will be removed {str(self._target_version)}.{alter}{doc}'

    @property
    def target_version(self):
        return self._target_version


class Rename(BreakingChange):
    """
    Rename the command groups, commands or arguments to a new name in a future release.

    **It is recommended to utilize `deprecate_info` instead of this class to pre-announce Breaking Change of Renaming.**
    It is recommended that the old name and the new name should be reserved in few releases.
    :param target: name of the renamed command group, command or argument
    :param new_name: new name
    :param target_version: version where the breaking change is expected to happen.
    :type target_version: TargetVersion
    :param doc_link: link of the related document
    """
    def __init__(self, target, new_name, target_version=NextBreakingChangeWindow(), doc_link=None):
        self.target = target
        self.new_name = new_name
        self._target_version = target_version
        self.doc_link = doc_link

    @property
    def message(self):
        doc = f' To know more about the Breaking Change, please visit {self.doc_link}.' if self.doc_link else ''
        return f'`{self.target}` will be renamed to `{self.new_name}` {str(self._target_version)}.{doc}'

    @property
    def target_version(self):
        return self._target_version


class OutputChange(BreakingChange):
    """
    The output of the command will be changed in a future release.
    :param description: describe the changes in output
    :param target_version: version where the breaking change is expected to happen.
    :type target_version: TargetVersion
    :param guide: how to adapt to the change
    :param doc_link: link of the related document
    """
    def __init__(self, description: str, target_version=NextBreakingChangeWindow(), guide=None, doc_link=None):
        self.desc = description
        self._target_version = target_version
        self.guide = guide
        self.doc_link = doc_link

    @property
    def message(self):
        desc = self.desc.rstrip()
        if desc and desc[-1] not in ',.;?!':
            desc = desc + '.'
        if self.guide:
            guide = self.guide.rstrip()
            if guide and guide[-1] not in ',.;?!':
                guide = guide + '.'
        else:
            guide = ''
        doc = f' To know more about the Breaking Change, please visit {self.doc_link}.' if self.doc_link else ''
        return f'The output will be changed {str(self._target_version)}. {desc} {guide}{doc}'

    @property
    def target_version(self):
        return self._target_version


class LogicChange(BreakingChange):
    """
    There would be a breaking change in the logic of the command in future release.
    :param summary: a short summary about the breaking change
    :param target_version: version where the breaking change is expected to happen.
    :type target_version: TargetVersion
    :param detail: detailed information
    :param doc_link: link of the related document
    """
    def __init__(self, summary, target_version=NextBreakingChangeWindow(), detail=None, doc_link=None):
        self.summary = summary
        self._target_version = target_version
        self.detail = detail
        self.doc_link = doc_link

    @property
    def message(self):
        detail = f' {self.detail}' if self.detail else ''
        doc = f' To know more about the Breaking Change, please visit {self.doc_link}.' if self.doc_link else ''
        return f'{self.summary} {str(self._target_version)}.{detail}{doc}'

    @property
    def target_version(self):
        return self._target_version


class DefaultChange(BreakingChange):
    """
    The default value of an argument would be changed in a future release.
    :param target: name of the related argument
    :param current_default: current default value of the argument
    :param new_default: new default value of the argument
    :param target_version: version where the breaking change is expected to happen.
    :type target_version: TargetVersion
    :param doc_link: link of the related document
    """
    def __init__(self, target, current_default, new_default, target_version=NextBreakingChangeWindow(), doc_link=None):
        self.target = target
        self.current_default = current_default
        self.new_default = new_default
        self._target_version = target_version
        self.doc_link = doc_link

    @property
    def message(self):
        doc = f' To know more about the Breaking Change, please visit {self.doc_link}.' if self.doc_link else ''
        return (f'The default value of `{self.target}` will be changed to `{self.new_default}` from '
                f'`{self.current_default}` {str(self._target_version)}.{doc}')

    @property
    def target_version(self):
        return self._target_version


class BeRequired(BreakingChange):
    """
    The argument would become required in a future release.
    :param target: name of the related argument
    :param target_version: version where the breaking change is expected to happen.
    :type target_version: TargetVersion
    :param doc_link: link of the related document
    """
    def __init__(self, target, target_version=NextBreakingChangeWindow(), doc_link=None):
        self.target = target
        self._target_version = target_version
        self.doc_link = doc_link

    @property
    def message(self):
        doc = f' To know more about the Breaking Change, please visit {self.doc_link}.' if self.doc_link else ''
        return f'The argument `{self.target}` will become required {str(self._target_version)}.{doc}'

    @property
    def target_version(self):
        return self._target_version


class OtherChange(BreakingChange):
    """
    Other custom breaking changes.
    :param message: A description of the breaking change, including the version number where it is expected to occur.
    :param target_version: version where the breaking change is expected to happen.
    :type target_version: TargetVersion
    """
    def __init__(self, message, target_version=NextBreakingChangeWindow()):
        self._message = message
        self._target_version = target_version

    @property
    def message(self):
        return self._message

    @property
    def target_version(self):
        return self._target_version


upcoming_breaking_changes = {}
