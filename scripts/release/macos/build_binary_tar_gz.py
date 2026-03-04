#!/usr/bin/env python3
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
"""Build Azure CLI tar.gz using Homebrew Python (no bundled Python).

This build produces a lightweight tar.gz with:
1. Azure CLI packages and dependencies (site-packages)
2. Pre-built native extensions (.so files) - Will be signed & notarized separately.
3. No bundled Python runtime embedded - relies on Homebrew Python or AZ_PYTHON environment variable.
4. An entry script that supports Homebrew Python or AZ_PYTHON


Output Structure:
```
dist/binary_tar_gz/
    azure-cli-{VERSION}-macos-arm64-nopython.tar.gz
    azure-cli-{VERSION}-macos-arm64-nopython.tar.gz.sha256
```

Archive Contents:
```
├── bin/
│   └── az → ../libexec/bin/az
└── libexec/
    ├── bin/
    │   └── az (entry script - Homebrew or AZ_PYTHON)
    ├── lib/
    │   └── python3.13
    │       └── site-packages/
    │           ├── azure/
    │           ├── msal/
    │           └── ... (all CLI packages)
    └── README.txt
```

Usage:
    python build_binary_tar_gz.py --help
    python build_binary_tar_gz.py --platform-tag macos-arm64
    python build_binary_tar_gz.py --platform-tag macos-arm64 --output-dir ./dist/custom
    python build_binary_tar_gz.py --platform-tag macos-arm64 --keep-temp    

Requirements:
    - Homebrew python@x.yz installed: brew install python@x.yz
    - Packages are installed into a temporary venv during the build
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

# Azure CLI project structure
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "src"
AZURE_CLI_CORE_DIR = SRC_DIR / "azure-cli-core"
REQUIREMENTS_FILE = SRC_DIR / "azure-cli" / "requirements.py3.Darwin.txt"

# Package configuration
APP_NAME = "azure-cli"
CLI_EXECUTABLE_NAME = "az"
TARBALL_NAME_TEMPLATE_DEFAULT = "{APP_NAME}-{VERSION}-{PLATFORM_TAG}-nopython.tar.gz"

# Python version we're building for (must match Homebrew python@X.Y)
# Can be overridden via --python-version CLI arg or PYTHON_MAJOR_MINOR env var
PYTHON_MAJOR_MINOR = os.environ.get("PYTHON_MAJOR_MINOR", "3.13")
PYTHON_BIN = "python3"
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
LAUNCHER_TEMPLATE_PATH = TEMPLATE_DIR / "az_launcher.sh.in"
README_TEMPLATE_PATH = TEMPLATE_DIR / "README.txt.in"


class BuildError(RuntimeError):
    """Raised when the packaging pipeline fails."""


def get_cli_version() -> str:
    """Get Azure CLI version from source."""
    version_file = AZURE_CLI_CORE_DIR / "azure" / "cli" / "core" / "__init__.py"
    if not version_file.exists():
        raise BuildError(f"Version file not found: {version_file}")

    content = version_file.read_text(encoding="utf-8")
    for line in content.splitlines():
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip("'\"")
            return version

    raise BuildError(f"Could not find __version__ in {version_file}")


def _is_python_version(python_path: Path, major_minor: str) -> bool:
    """Return True when python_path matches the requested major.minor."""
    try:
        result = subprocess.run(
            [str(python_path), "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() == major_minor
    except subprocess.CalledProcessError:
        return False


def _render_template(template: str, values: dict[str, str]) -> str:
    """Replace template placeholders using the provided values."""
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"{{{key}}}", value)
    return rendered


def _load_template(path: Path) -> str:
    """Load a template file from disk."""
    if not path.exists():
        raise BuildError(f"Template not found: {path}")
    return path.read_text(encoding="utf-8")


def find_homebrew_python() -> Path:
    """Find necessary Homebrew Python x.yz installation."""
    candidates = [
        Path(f"/opt/homebrew/opt/python@{PYTHON_MAJOR_MINOR}/libexec/bin/python3"),
        Path(f"/usr/local/opt/python@{PYTHON_MAJOR_MINOR}/libexec/bin/python3"),
        Path(f"/opt/homebrew/bin/python{PYTHON_MAJOR_MINOR}"),
        Path(f"/usr/local/bin/python{PYTHON_MAJOR_MINOR}"),
    ]

    for python_path in candidates:
        if python_path.exists() and _is_python_version(python_path, PYTHON_MAJOR_MINOR):
            print(f"Found Homebrew Python: {python_path}")
            return python_path

    try:
        result = subprocess.run(
            ["brew", "--prefix", f"python@{PYTHON_MAJOR_MINOR}"],
            capture_output=True,
            text=True,
            check=True,
        )
        prefix = Path(result.stdout.strip())
        python_path = prefix / "libexec" / "bin" / "python3"
        if python_path.exists() and _is_python_version(python_path, PYTHON_MAJOR_MINOR):
            print(f"Found Homebrew Python via brew --prefix: {python_path}")
            return python_path
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    raise BuildError(f"Homebrew Python {PYTHON_MAJOR_MINOR} not found. Install it with: brew install python@{PYTHON_MAJOR_MINOR}")


def create_venv(python_path: Path, venv_dir: Path) -> Path:
    """Create a virtual environment using Homebrew Python."""
    print("\n=== Creating virtual environment ===")
    print(f"Python: {python_path}")
    print(f"Venv: {venv_dir}")

    subprocess.run([str(python_path), "-m", "venv", str(venv_dir)], check=True)

    venv_python = venv_dir / "bin" / "python3"

    subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], check=True)

    return venv_python


def install_azure_cli(venv_python: Path) -> None:
    """Install Azure CLI components from source, then install pinned dependencies.

    Mirrors the run.sh approach:
      1. Install all src packages with --no-deps (local source code takes precedence)
      2. Install pinned dependencies from requirements.py3.Darwin.txt
    """
    # Step 1: install every package found under SRC_DIR from source, without pulling
    # transitive deps from PyPI (--no-deps). This ensures the locally-built wheels
    # are used for the CLI components themselves.
    print("\n=== Step 1: Installing Azure CLI components from source (--no-deps) ===")

    # Install from local source first so in-tree patches are picked up
    components = [
        SRC_DIR / "azure-cli-telemetry",
        SRC_DIR / "azure-cli-core",
        SRC_DIR / "azure-cli",
    ]

    for component in components:
        print(f"  Installing {component.name} (--no-deps)...")
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "--no-deps", str(component)],
            check=True,
        )

    # Step 2: install all pinned transitive dependencies so every package
    # resolves to the exact version recorded in the requirements file.
    print("\n=== Step 2: Installing pinned dependencies from requirements file ===")

    if not REQUIREMENTS_FILE.exists():
        raise BuildError(f"Requirements file not found: {REQUIREMENTS_FILE}")

    print(f"  Using: {REQUIREMENTS_FILE}")
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)],
        check=True,
    )

    print("\nVerifying Azure CLI installation...")
    subprocess.run([str(venv_python), "-m", "azure.cli", "--version"], check=True)


def create_install_structure(venv_dir: Path, install_dir: Path, version: str, platform_tag: str) -> None:
    """Create the final installation directory structure."""
    print("\n=== Creating installation structure ===")

    libexec_dir = install_dir / "libexec"
    bin_dir = install_dir / "bin"
    libexec_bin = libexec_dir / "bin"
    libexec_lib = libexec_dir / "lib" / f"python{PYTHON_MAJOR_MINOR}"
    site_packages = libexec_lib / "site-packages"

    for d in [bin_dir, libexec_bin, site_packages]:
        d.mkdir(parents=True, exist_ok=True)

    venv_site_packages = venv_dir / "lib" / f"python{PYTHON_MAJOR_MINOR}" / "site-packages"
    print(f"Copying site-packages from: {venv_site_packages}")
    print(f"                       to: {site_packages}")

    shutil.copytree(venv_site_packages, site_packages, dirs_exist_ok=True)

    _create_launcher_script(bin_dir=libexec_bin, python_version=PYTHON_MAJOR_MINOR)

    az_symlink = bin_dir / CLI_EXECUTABLE_NAME
    az_target = Path("..") / "libexec" / "bin" / CLI_EXECUTABLE_NAME
    az_symlink.symlink_to(az_target)
    print(f"Created symlink: {az_symlink} -> {az_target}")

    _create_readme(install_dir=libexec_dir, version=version, platform_tag=platform_tag)

    _cleanup_bytecode(root=site_packages)

    _report_sizes(install_dir=install_dir)


def _create_launcher_script(bin_dir: Path, python_version: str) -> None:
    """Create az launcher script that supports Homebrew and offline installs."""
    template = _load_template(path=LAUNCHER_TEMPLATE_PATH)
    launcher_script = _render_template(
        template=template,
        values={
            "PYTHON_MAJOR_MINOR": python_version,
            "PYTHON_BIN": PYTHON_BIN,
        },
    )

    az_path = bin_dir / CLI_EXECUTABLE_NAME
    az_path.write_text(launcher_script, encoding="utf-8")
    az_path.chmod(0o755)
    print(f"Created launcher script: {az_path}")


def _create_readme(install_dir: Path, version: str, platform_tag: str) -> None:
    """Create README.txt."""
    template = _load_template(path=README_TEMPLATE_PATH)
    readme_content = _render_template(
        template=template,
        values={
            "AZURE_CLI_VERSION": version,
            "PLATFORM_TAG": platform_tag,
            "PYTHON_MAJOR_MINOR": PYTHON_MAJOR_MINOR,
        },
    )

    readme_path = install_dir / "README.txt"
    readme_path.write_text(readme_content, encoding="utf-8")
    print(f"Created README: {readme_path}")


def _cleanup_bytecode(root: Path) -> None:
    """Remove __pycache__ directories and .pyc files."""
    print("\n=== Cleaning bytecode cache ===")

    removed_count = 0
    for path in sorted(root.rglob("*.pyc"), reverse=True):
        path.unlink()
        removed_count += 1

    for path in sorted(root.rglob("__pycache__"), reverse=True):
        if path.is_dir():
            try:
                shutil.rmtree(path)
                removed_count += 1
            except OSError:
                pass

    print(f"Removed {removed_count} bytecode files/directories")


def _report_sizes(install_dir: Path) -> None:
    """Report sizes of components."""
    print("\n=== Size Report ===")

    def get_size(path: Path) -> int:
        if path.is_file():
            return path.stat().st_size
        total = 0
        for p in path.rglob("*"):
            if p.is_file():
                total += p.stat().st_size
        return total

    def fmt_size(size: int) -> str:
        if size >= 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        if size >= 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size} B"

    print(f"  Total: {fmt_size(get_size(install_dir))}")

    for subdir in ["bin", "libexec/bin", "libexec/lib"]:
        path = install_dir / subdir
        if path.exists():
            print(f"  {subdir}: {fmt_size(get_size(path))}")

    so_files = list((install_dir / "libexec" / "lib").rglob("*.so"))
    print(f"\n  Native extensions (.so): {len(so_files)} files")
    for so_file in sorted(so_files)[:10]:
        rel_path = so_file.relative_to(install_dir)
        print(f"    - {rel_path.name}: {fmt_size(get_size(so_file))}")
    if len(so_files) > 10:
        print(f"    ... and {len(so_files) - 10} more")


def create_tarball(
    install_dir: Path,
    output_dir: Path,
    version: str,
    platform_tag: str,
    tarball_name_template: str,
) -> Path:
    """Create the final tar.gz archive."""
    print("\n=== Creating tarball ===")

    output_dir.mkdir(parents=True, exist_ok=True)

    tarball_name = tarball_name_template.format(
        APP_NAME=APP_NAME,
        VERSION=version,
        PLATFORM_TAG=platform_tag,
    )
    tarball_path = output_dir / tarball_name

    with tarfile.open(tarball_path, "w:gz") as tar:
        for item in install_dir.iterdir():
            arcname = item.name
            tar.add(item, arcname=arcname)

    print(f"Created: {tarball_path}")
    print(f"Size: {tarball_path.stat().st_size / (1024 * 1024):.1f} MB")

    sha256_path = Path(str(tarball_path) + ".sha256")
    sha256_hash = hashlib.sha256()
    with open(tarball_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)

    checksum = sha256_hash.hexdigest()
    sha256_path.write_text(f"{checksum}  {tarball_name}\n")
    print(f"SHA256: {checksum}")

    return tarball_path


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build Azure CLI tar.gz using Homebrew Python (no bundled Python)"
    )
    parser.add_argument(
        "--platform-tag", required=True, choices=["macos-arm64", "macos-x86_64"], help="Platform tag for the build"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "dist" / "binary_tar_gz",
        help="Output directory for the tarball",
    )
    parser.add_argument(
        "--tarball-name-template",
        default=TARBALL_NAME_TEMPLATE_DEFAULT,
        help="Tarball filename template with {APP_NAME}, {VERSION} (from azure-cli-core), {PLATFORM_TAG}",
    )
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary build directory for debugging")

    args = parser.parse_args()

    print("=" * 70)
    print("Azure CLI Tarball Builder (Homebrew Python)")
    print("=" * 70)
    print(f"Platform: {args.platform_tag}")
    print(f"Output: {args.output_dir}")
    print()

    try:
        version = get_cli_version()
        print(f"Azure CLI version: {version}")

        python_path = find_homebrew_python()

        with tempfile.TemporaryDirectory(prefix="azure-cli-build-") as temp_dir:
            temp_path = Path(temp_dir)
            venv_dir = temp_path / "venv"
            install_dir = temp_path / "install"

            venv_python = create_venv(python_path=python_path, venv_dir=venv_dir)
            install_azure_cli(venv_python=venv_python)

            create_install_structure(
                venv_dir=venv_dir,
                install_dir=install_dir,
                version=version,
                platform_tag=args.platform_tag,
            )

            tarball_path = create_tarball(
                install_dir=install_dir,
                output_dir=args.output_dir,
                version=version,
                platform_tag=args.platform_tag,
                tarball_name_template=args.tarball_name_template,
            )

            if args.keep_temp:
                print(f"\nTemp directory preserved: {temp_path}")
                preserved_dir = args.output_dir / "build-temp"
                if preserved_dir.exists():
                    shutil.rmtree(preserved_dir)
                shutil.copytree(temp_path, preserved_dir)
                print(f"Copied to: {preserved_dir}")

        print("\n" + "=" * 70)
        print("BUILD SUCCESSFUL")
        print("=" * 70)
        print(f"Tarball: {tarball_path}")
        print("\nTo test locally:")
        print(f"  tar xzf {tarball_path}")
        print("  ./libexec/bin/az --version")
        print()

        return 0

    except BuildError as e:
        print(f"\nBUILD FAILED: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
