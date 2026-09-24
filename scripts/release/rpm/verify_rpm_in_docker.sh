#!/usr/bin/env bash

# This script should be run in a docker to verify installing rpm package from the yum repository.

# Opt in on a clean Fedora 44 container with RPM_REPOSITORY_ID, CLI_VERSION
# (major.minor.patch), and RPM_RELEASE (e.g. 1.fc44). The repository and its
# signing keys must already be configured and approved by the maintainer.
# This verifies that configured repository, not public availability.
# Leave RPM_REPOSITORY_ID unset to retain legacy verification; empty is invalid.
if [[ ${RPM_REPOSITORY_ID+x} == x ]]; then
    set -euo pipefail

    if [[ ! "$RPM_REPOSITORY_ID" =~ ^[a-zA-Z0-9][a-zA-Z0-9_.:-]*$ ]]; then
        echo "RPM_REPOSITORY_ID must be a single preconfigured repository ID." >&2
        exit 1
    fi
    if [[ ! ${CLI_VERSION:-} =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "CLI_VERSION must be an explicit major.minor.patch version." >&2
        exit 1
    fi
    if [[ ! ${RPM_RELEASE:-} =~ ^[0-9]+(\.[0-9]+)*\.fc44$ ]]; then
        echo "RPM_RELEASE must be an explicit Fedora 44 release, e.g. 1.fc44." >&2
        exit 1
    fi

    # Unlike a failed rpm -q, an empty successful query is unambiguously absent.
    preinstalled=$(rpm -qa azure-cli --queryformat '%{NAME}\n')
    if [[ -n "$preinstalled" ]] || command -v az >/dev/null 2>&1; then
        echo "Strict verification requires a clean container: no azure-cli RPM or az on PATH." >&2
        exit 1
    fi

    arch=$(rpm --eval '%{_arch}')
    if [[ ! "$arch" =~ ^[a-zA-Z0-9_]+$ ]]; then
        echo "Could not determine the native RPM architecture." >&2
        exit 1
    fi
    package="azure-cli-${CLI_VERSION}-${RPM_RELEASE}.${arch}"
    expected_rpm="azure-cli|${CLI_VERSION}|${RPM_RELEASE}|${arch}"
    expected_repo="${expected_rpm}|${RPM_REPOSITORY_ID}"
    rpm_format='%{NAME}|%{VERSION}|%{RELEASE}|%{ARCH}\n'
    available_format='%{name}|%{version}|%{release}|%{arch}|%{repoid}\n'
    installed_format='%{name}|%{version}|%{release}|%{arch}|%{from_repo}\n'

    # Override package signature checks even for repos that disable them.
    # Leave each repository's metadata signature policy (repo_gpgcheck) intact.
    dnf_options=(
        --setopt=gpgcheck=1
        '--setopt=*.gpgcheck=1'
        "--setopt=${RPM_REPOSITORY_ID}.gpgcheck=1"
    )
    available=$(dnf5 "${dnf_options[@]}" --quiet --refresh "--repo=${RPM_REPOSITORY_ID}" \
        repoquery --available --queryformat "$available_format" "$package")
    if [[ "$available" != "$expected_repo" ]]; then
        echo "The exact Fedora 44 package is not available from RPM_REPOSITORY_ID." >&2
        exit 1
    fi

    # --from-repo restricts the requested package, not its distro dependencies.
    dnf5 "${dnf_options[@]}" install --assumeyes "--from-repo=${RPM_REPOSITORY_ID}" "$package"

    installed=$(rpm -q --queryformat "$rpm_format" azure-cli)
    if [[ "$installed" != "$expected_rpm" ]]; then
        echo "Installed azure-cli RPM does not match the expected name/version/release/architecture." >&2
        exit 1
    fi
    installed_repo=$(dnf5 "${dnf_options[@]}" --quiet repoquery --installed \
        --queryformat "$installed_format" azure-cli)
    if [[ "$installed_repo" != "$expected_repo" ]]; then
        echo "Installed azure-cli does not match the expected package and repository origin." >&2
        exit 1
    fi
    owner=$(rpm -qf --queryformat "$rpm_format" /usr/bin/az)
    if [[ "$owner" != "$expected_rpm" ]]; then
        echo "/usr/bin/az is not owned by the expected azure-cli RPM." >&2
        exit 1
    fi

    actual_version=$(/usr/bin/az version --query '"azure-cli"' -o tsv)
    if [[ "$actual_version" != "$CLI_VERSION" ]]; then
        echo "/usr/bin/az reports a different CLI version." >&2
        exit 1
    fi
    /usr/bin/az --version
    /usr/bin/az self-test
    echo "Verified ${package} from configured repository ${RPM_REPOSITORY_ID}."
    exit 0
fi

rpm --import https://packages.microsoft.com/keys/microsoft.asc
sh -c 'echo -e "[azure-cli]
name=Azure CLI
baseurl=https://packages.microsoft.com/yumrepos/azure-cli
enabled=1
gpgcheck=1
gpgkey=https://packages.microsoft.com/keys/microsoft.asc" > /etc/yum.repos.d/azure-cli.repo'

counter=4

while [ $counter -gt 0 ]
do
    yum install azure-cli -y
    ACTUAL_VERSION=$(az version | sed -n 's|"azure-cli": "\(.*\)",|\1|p' | sed 's|[[:space:]]||g')
    echo "actual version:${ACTUAL_VERSION}"
    echo "expected version:${CLI_VERSION}"

    if [ "$ACTUAL_VERSION" != "$CLI_VERSION" ]; then
        if [ ! -z "$ACTUAL_VERSION" ]; then
            echo "Latest package is not in the repo."
            exit 1
        fi
        echo "wait 5m"
        sleep 300
        counter=$(( $counter - 1 ))
    else
        echo "Latest package is verified."
        exit 0
    fi
done
echo "Timeout!"
exit 1
