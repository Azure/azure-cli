# RPM Packaging

## Building RPM packages

On a machine with Docker, execute the following command from the root directory of this repository:

_Enterprise Linux:_
```bash
docker build --target build-env -f ./scripts/release/rpm/centos7.dockerfile -t azure/azure-cli:centos7-builder .
```
_Fedora 44 (local build, not production publication):_

```bash
CLI_VERSION=$(sed -n 's/^__version__ = "\(.*\)"/\1/p' src/azure-cli/azure/cli/__main__.py)
docker build --target build-env \
    --build-arg image=registry.fedoraproject.org/fedora:44 \
    --build-arg cli_version="$CLI_VERSION" --build-arg python_package=python3 \
    -f ./scripts/release/rpm/fedora.dockerfile -t azure/azure-cli:fedora44-builder .
```

Fedora 44's native `python3` package provides Python 3.14 and `/usr/bin/python3`.
Use `python3-devel` for building and `python3-pip` (`pip3`) for the package tests,
not the UBI matrix's `python3.12`/`pip3.12` selectors. The Python libraries require
`python-pip-wheel`, which supplies the virtual environment's pip bootstrap.
These package names and executable paths are present in the
[Fedora 44 RPM metadata](https://dl.fedoraproject.org/pub/fedora/linux/releases/44/Everything/x86_64/os/Packages/p/).
The [Fedora image manifest](https://registry.fedoraproject.org/v2/fedora/manifests/44)
includes both `amd64` and `arm64`; a successful build and package run on each
architecture is still required.

_Azure Linux:_

```bash
# Build against Azure Linux 4.0 (Beta) - the default in the dockerfile
docker build --target build-env -f ./scripts/release/rpm/azurelinux.dockerfile -t azure/azure-cli:azurelinux-builder .

# Or build against Azure Linux 3.0 explicitly
docker build --target build-env --build-arg image=mcr.microsoft.com/azurelinux/base/core:3.0 \
    -f ./scripts/release/rpm/azurelinux.dockerfile -t azure/azure-cli:azurelinux3-builder .
```

After several minutes, this will have created the selected Docker image containing an
unsigned `.rpm` built from the current contents of your azure-cli directory. To extract the build product from the image
you can run the following command:

_Enterprise Linux:_
```bash
docker run azure/azure-cli:centos7-builder cat /root/rpmbuild/RPMS/x86_64/azure-cli-dev-1.el7.x86_64.rpm > ./bin/azure-cli-dev-1.el7.x86_64.rpm
```

_Fedora 44:_
```bash
id=$(docker create azure/azure-cli:fedora44-builder)
docker cp "$id:/out/." ./bin/
docker rm "$id"
# Native amd64 output: azure-cli-${CLI_VERSION}-1.fc44.x86_64.rpm
# Native arm64 output: azure-cli-${CLI_VERSION}-1.fc44.aarch64.rpm
```

_Azure Linux:_
```bash
# AZL4 output path (rpmbuild default topdir is /root/rpmbuild)
docker run azure/azure-cli:azurelinux-builder cat /root/rpmbuild/RPMS/x86_64/azure-cli-dev-1.azl4.x86_64.rpm > ./bin/azure-cli-dev-1.azl4.x86_64.rpm

# AZL3 output path (rpmbuild default topdir is /usr/src/azl)
docker run azure/azure-cli:azurelinux3-builder cat /usr/src/azl/RPMS/x86_64/azure-cli-dev-1.azl3.x86_64.rpm > ./bin/azure-cli-dev-1.azl3.x86_64.rpm
```

The `docker run ... cat` commands copy a specific package through standard output.
The Fedora example copies `/out/` without assuming the native RPM architecture.

### Additional Build Flags

`--build-arg cli_version={your version string}`

This will allow you to name your build. If not specified, the value "dev" is assumed.
Use the CLI source version as above for release builds. The package tests require
the reported CLI version to match the RPM version, except for the default `dev`
label, which does not change the CLI's embedded source version. Development builds
still run the version command and all other package checks.

`--build-arg image={container image}`

The Fedora Dockerfile defaults to `registry.fedoraproject.org/fedora:44`. Its
`python_package` argument defaults to `python3`, and `python_cmd` defaults to the
selected package name. Both can be overridden when building directly with Docker.
The existing `pipeline.sh` selects the image and Python package through `IMAGE`
and `PYTHON_PACKAGE`; its Fedora defaults therefore use the same Python executable.

### Verification

Run the RPM package
-------------------

On a machine with Docker, execute the following command from the root directory of this repository:

```bash
docker build -f ./scripts/release/rpm/centos7.dockerfile -t azure/azure-cli:centos7 .
``` 

For Fedora 44, run both installation smoke checks (`az --version` and `az self-test`):

```bash
docker build --build-arg cli_version="$CLI_VERSION" \
    -f ./scripts/release/rpm/fedora.dockerfile -t azure/azure-cli:fedora44 .
```

If you had previously followed this instructions above for building an RPM package, this should finish very quickly.
Otherwise, it'll take a few minutes to create an image with a copy of the azure-cli installed.
> Note: The image that is created by this command does not contain the source code of the azure-cli.

Verification
------------

Install the RPM:
```bash
sudo rpm -i RPMS/*/azure-cli-2.0.16-1.noarch.rpm
az --version
```

Check the file permissions of the package:  
```bash
rpmlint RPMS/*/azure-cli-2.0.16-1.x86_64.rpm
```

Check the file permissions of the package:  
```bash
rpm -qlvp RPMS/*/azure-cli-2.0.16-1.x86_64.rpm
```

To remove:  
```bash
sudo rpm -e azure-cli
```

### Fedora 44 local package tests

Use a disposable, normal Git checkout on each native Linux architecture. The
existing test script builds test wheels with `scripts/ci/build.sh`, which requires
Git metadata and modifies the mounted checkout. It cannot run from a source-only
snapshot. After extracting the unsigned RPM to `bin/` as above:

```bash
RPM_TEST_RESULTS=$(mktemp -d)
docker run --rm \
    -v "$(pwd):/azure-cli" -v "$(pwd)/bin:/mnt/rpm:ro" \
    -v "$RPM_TEST_RESULTS:/azure_cli_test_result" \
    -e RPM_NAME="azure-cli-${CLI_VERSION}-1.fc44.*.rpm" \
    -e PYTHON_PACKAGE=python3 -e PYTHON_CMD=python3 -e PIP_CMD=pip3 \
    registry.fedoraproject.org/fedora:44 \
    bash /azure-cli/scripts/release/rpm/test_rpm_in_docker.sh
```

This runs the existing self-test, version smoke check and package suites. The
package checks also require the installed RPM to match the requested version and
distro suffix, have the native architecture, report the same CLI version (except
for the `dev` label), and declare an installed dependency on the selected Python
package. The local installer's `--nogpgcheck` is only for unsigned build artifacts;
it is not suitable for production-feed acceptance.

Credential-free regression checks for the packaging scripts use the existing
Python unittest tooling:

```bash
python -m unittest discover -s scripts/release/rpm/tests
```

These checks do not build an RPM or replace Fedora/UBI/Azure Linux container CI.

### Fedora 44 CI and release-owner gates

The main `azure-pipelines.yml` currently has no Fedora 44 entry in either
`BuildRpmPackages` or `TestRpmPackage`. The Dockerfile change alone does not add
those jobs. After release-owner approval, the paired entries under the existing
architecture loops must use the same image, artifact and Python selection:

```yaml
# BuildRpmPackages matrix
Fedora 44 ${{ arch.name }}:
  dockerfile: fedora
  image: registry.fedoraproject.org/fedora:44
  artifact: rpm-fedora44-${{ arch.value }}
  python_package: python3
  pool: ${{ arch.pool }}

# TestRpmPackage matrix
Fedora 44 ${{ arch.name }}:
  artifact: rpm-fedora44-${{ arch.value }}
  distro: fc44
  image: registry.fedoraproject.org/fedora:44
  python_package: python3
  python_cmd: python3
  pip_cmd: pip3
  pool: ${{ arch.pool }}
```

Keep the existing build/test dependencies, trigger conditions, UBI entries and
separate Azure Linux jobs unchanged. `rpm-fedora44-amd64` must contain the
`1.fc44.x86_64.rpm` artifact, and `rpm-fedora44-arm64` the `1.fc44.aarch64.rpm`
artifact; the install jobs must download the corresponding artifact.

`PublishPipelineArtifact` only uploads an Azure Pipelines artifact. No approved
Fedora 44 signing/production publication mapping is defined in this repository.
The `/scripts/` CODEOWNERS teams can route a release-owner review, but code
ownership is not approval to publish to a feed. The release owner must confirm
the supported destination and signing key, onboard the artifact through the
existing approved signing/publication process, and complete post-publication
acceptance. Do not infer a destination from an issue URL or substitute a
RHEL/CentOS feed.

Local builds, CI artifacts and even successful local installations do not
establish Fedora 44 production availability or Microsoft support.

### Fedora 44 repository acceptance (after approved publication)

The release owner must first configure the approved repository and trusted signing
keys in a clean Fedora 44 container on each native architecture. Do not use a
container that already has the Azure CLI RPM installed or an `az` executable on
`PATH`. From the mounted repository root, run as root:

```bash
# Use the approved repository ID and the exact version the owner published.
RPM_REPOSITORY_ID="${APPROVED_REPO_ID:?Set the approved Fedora repository ID}" \
CLI_VERSION="${EXPECTED_VERSION:?Set the published X.Y.Z CLI version}" \
RPM_RELEASE=1.fc44 \
bash scripts/release/rpm/verify_rpm_in_docker.sh
```

`RPM_REPOSITORY_ID` selects an existing repository, not a URL. `CLI_VERSION` must be
an exact `X.Y.Z` version, not `dev` or `latest`; set `RPM_RELEASE` to the published
numeric release with the `.fc44` suffix. The verifier refreshes available metadata
restricted to the selected repository, then installs that exact version, release
and native architecture from it. Other configured repositories may satisfy
dependencies, but cannot substitute their Azure CLI package.

Package signature checking is required, and any configured repository-metadata
signature policy is preserved. This mode does not configure a repository or choose
signing keys. Never copy the local installer's `--nogpgcheck` option into this
acceptance procedure.

| Scenario | Required result |
| --- | --- |
| Requested version, release and native architecture are available from the approved repository | Install succeeds; installed RPM metadata, DNF origin, `/usr/bin/az` ownership and reported CLI version match; `az --version` and `az self-test` succeed. |
| Selected repository has no package, only an older version, or the wrong release/architecture | Fail, even if another enabled repository has a matching package. |
| Package is available only from Fedora's downstream repository or another unrelated feed | Fail without falling back to that feed. |
| Azure CLI RPM or an `az` executable is already present | Fail; retry in a fresh container. |
| Package signature checking or an enabled metadata-signature check fails | Fail; do not bypass the signature check. |
| Installed package origin/version/ownership differs, or either smoke check fails | Fail. |

The script neither starts a release nor waits for a package to appear. Run it only
after the release owner confirms approved publication. A successful local build
or unsigned artifact installation cannot satisfy this acceptance gate.

Leaving `RPM_REPOSITORY_ID` unset preserves the existing generic-yum verification
path; that path is not Fedora 44 repository acceptance. An explicitly empty
selector is rejected rather than silently selecting the legacy path.

Links
-----

- [Fedora Project: How to Create an RPM Package](https://fedoraproject.org/wiki/How_to_create_an_RPM_package)
- [Fedora Project: Packaging RPM Macros](https://fedoraproject.org/wiki/Packaging:RPMMacros?rd=Packaging/RPMMacros)
