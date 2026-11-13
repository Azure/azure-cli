# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
from dataclasses import dataclass

import semver

from azure.cli.core.azclierror import ValidationError


_comparator_pattern = re.compile(
    r"(>=|<=|>|<|=)?\s*(0|[1-9][0-9]*)(?:\.(0|[1-9][0-9]*)(?:\.(0|[1-9][0-9]*))?)?"
)
_max_version_component = 2147483647


@dataclass(frozen=True)
class BicepVersionConstraint:
    lower_bound: semver.VersionInfo | None = None
    upper_bound: semver.VersionInfo | None = None
    lower_inclusive: bool = True
    upper_inclusive: bool = True

    @property
    def is_exact_version(self) -> bool:
        return (
            self.lower_bound is not None and self.lower_bound == self.upper_bound and
            self.lower_inclusive and self.upper_inclusive
        )

    @property
    def is_satisfiable(self) -> bool:
        if self.lower_bound is None or self.upper_bound is None:
            return True
        if self.lower_bound == self.upper_bound:
            return self.lower_inclusive and self.upper_inclusive
        if self.lower_bound > self.upper_bound:
            return False
        # Stable numeric versions have no value between adjacent patch numbers.
        return not (
            not self.lower_inclusive and not self.upper_inclusive and
            self.lower_bound.major == self.upper_bound.major and
            self.lower_bound.minor == self.upper_bound.minor and
            self.lower_bound.patch + 1 == self.upper_bound.patch
        )

    def is_satisfied_by(self, version: semver.VersionInfo) -> bool:
        """Check a stable numeric compiler version against both bounds."""
        if version.prerelease is not None or version.build is not None:
            return False
        if self.lower_bound is not None:
            if version < self.lower_bound or (version == self.lower_bound and not self.lower_inclusive):
                return False
        if self.upper_bound is not None:
            if version > self.upper_bound or (version == self.upper_bound and not self.upper_inclusive):
                return False
        return True

    def __str__(self) -> str:
        if self.is_exact_version:
            return str(self.lower_bound)
        parts = []
        if self.lower_bound is not None:
            parts.append(f"{'>=' if self.lower_inclusive else '>'}{self.lower_bound}")
        if self.upper_bound is not None:
            parts.append(f"{'<=' if self.upper_inclusive else '<'}{self.upper_bound}")
        return ", ".join(parts)


def parse_bicep_version_constraint(value: str) -> BicepVersionConstraint:
    """Parse Bicep.Core's exact-version or lower/upper-bound constraint syntax."""
    error_message = f'The bicep.version property "{value}" is not a valid Bicep version or version range.'
    if not isinstance(value, str):
        raise ValidationError(error_message)
    parts = value.split(",")
    if len(parts) > 2:
        raise ValidationError(error_message)

    lower_bound = None
    upper_bound = None
    lower_inclusive = True
    upper_inclusive = True
    for part in parts:
        match = _comparator_pattern.fullmatch(part.strip())
        if match is None:
            raise ValidationError(error_message)
        components = [component or "0" for component in match.groups()[1:]]
        # Match the compiler's int32 limit before converting arbitrarily long inputs.
        if any(len(component) > 10 or int(component) > _max_version_component for component in components):
            raise ValidationError(error_message)
        version = semver.VersionInfo(*(int(component) for component in components))
        comparator = match.group(1) or "="
        if comparator == "=":
            if lower_bound is not None or upper_bound is not None:
                raise ValidationError(error_message)
            lower_bound = upper_bound = version
        elif comparator in (">", ">="):
            if lower_bound is not None:
                raise ValidationError(error_message)
            lower_bound = version
            lower_inclusive = comparator == ">="
        else:
            if upper_bound is not None:
                raise ValidationError(error_message)
            upper_bound = version
            upper_inclusive = comparator == "<="

    return BicepVersionConstraint(
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        lower_inclusive=lower_inclusive,
        upper_inclusive=upper_inclusive,
    )
