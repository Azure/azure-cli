#!/bin/bash
# Azure CLI Snap Build Script
# Build snap package from wheel files
#
# Usage: ./build-snap.sh [VERSION] [--multi-arch]
#
# Environment variables:
#   WHEEL_DIR     Directory containing wheel files (default: /mnt/pypi)
#   OUTPUT_DIR    Output directory for snap file (default: /mnt/output)

set -e

VERSION=""
MULTI_ARCH=false
WHEEL_DIR="${WHEEL_DIR:-/mnt/pypi}"
OUTPUT_DIR="${OUTPUT_DIR:-/mnt/output}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/snap-build"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --multi-arch)
            MULTI_ARCH=true
            shift
            ;;
        help|--help|-h)
            echo "Azure CLI Snap Build Script"
            echo ""
            echo "Usage: $0 [VERSION] [--multi-arch]"
            echo ""
            echo "Arguments:"
            echo "  VERSION       CLI version (auto-detected from wheel if not specified)"
            echo "  --multi-arch  Build for amd64 and arm64 using Launchpad remote-build"
            echo ""
            echo "Environment Variables:"
            echo "  WHEEL_DIR   Directory containing wheel files (default: /mnt/pypi)"
            echo "  OUTPUT_DIR  Output directory for snap file (default: /mnt/output)"
            echo ""
            echo "Examples:"
            echo "  $0                           # Build amd64 only"
            echo "  $0 --multi-arch              # Build amd64 + arm64"
            echo "  $0 2.81.0 --multi-arch       # Build specific version, multi-arch"
            exit 0
            ;;
        *)
            if [[ "$1" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
                VERSION="$1"
            fi
            shift
            ;;
    esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Get version from wheel filename
get_version() {
    if [ -n "$VERSION" ]; then
        echo "$VERSION"
        return
    fi

    local wheel_file
    wheel_file=$(ls -1 "${WHEEL_DIR}"/azure_cli-*.whl 2>/dev/null | head -1)
    if [ -n "$wheel_file" ]; then
        basename "$wheel_file" | sed -E 's/azure_cli-([0-9]+\.[0-9]+\.[0-9]+).*/\1/'
        return
    fi

    log_error "Cannot detect version. Please specify: $0 2.81.0"
    exit 1
}

# Validate wheel files exist
validate_wheels() {
    log_info "Validating wheel files in ${WHEEL_DIR}..."

    if [ ! -d "$WHEEL_DIR" ]; then
        log_error "Wheel directory not found: $WHEEL_DIR"
        exit 1
    fi

    local wheel_count
    wheel_count=$(ls -1 "${WHEEL_DIR}"/*.whl 2>/dev/null | wc -l)
    if [ "$wheel_count" -eq 0 ]; then
        log_error "No wheel files found in $WHEEL_DIR"
        exit 1
    fi

    log_info "Found $wheel_count wheel files"
}

# Create snapcraft.yaml from template
create_snapcraft_yaml() {
    local version=$1

    log_info "Creating snapcraft.yaml for version $version..."

    mkdir -p "$BUILD_DIR/scripts"
    mkdir -p "$BUILD_DIR/wheels"

    # Copy wheel files
    cp "${WHEEL_DIR}"/*.whl "$BUILD_DIR/wheels/"

    # Wrapper script
    cat > "$BUILD_DIR/scripts/az-wrapper" << 'WRAPPER'
#!/bin/bash
PYTHON_VERSION="$("${SNAP}/opt/az/bin/python3" - << 'EOF'
import sys
print(f"python{sys.version_info.major}.{sys.version_info.minor}")
EOF
)"
export PYTHONPATH="${SNAP}/opt/az/lib/${PYTHON_VERSION}/site-packages"
export PATH="${SNAP}/opt/az/bin:${PATH}"
export AZ_INSTALLER="SNAP"
exec "${SNAP}/opt/az/bin/python3" -m azure.cli "$@"
WRAPPER
    chmod +x "$BUILD_DIR/scripts/az-wrapper"

    # Determine architecture section
    local arch_section
    if [ "$MULTI_ARCH" = true ]; then
        arch_section="architectures:\\
  - build-on: [amd64]\\
    build-for: [amd64]\\
  - build-on: [arm64]\\
    build-for: [arm64]"
    else
        arch_section="architectures:\\
  - build-on: amd64"
    fi

    # Generate snapcraft.yaml from template
    # Template variables:
    #   ${CLI_VERSION}   - Azure CLI version (e.g., 2.81.0)
    #   ${ARCHITECTURES} - Architecture configuration block
    sed -e "s/\${CLI_VERSION}/${version}/g" \
        -e "s/\${ARCHITECTURES}/${arch_section}/" \
        "${SCRIPT_DIR}/snapcraft.yaml.template" > "$BUILD_DIR/snapcraft.yaml"

    log_success "snapcraft.yaml created from template"
}

# Build snap
build_snap() {
    local version=$1
    cd "$BUILD_DIR"

    if [ "$MULTI_ARCH" = true ]; then
        log_info "Building for amd64 + arm64 using Launchpad remote-build..."
        log_warn "This requires SNAPCRAFT_STORE_CREDENTIALS and may take 10-20 minutes"

        if [ -z "$SNAPCRAFT_STORE_CREDENTIALS" ]; then
            log_error "SNAPCRAFT_STORE_CREDENTIALS not set. Required for remote-build."
            exit 1
        fi

        snapcraft remote-build --launchpad-accept-public-upload

        log_success "Multi-arch build completed!"
        ls -la *.snap 2>/dev/null || true
    else
        log_info "Building for local architecture (amd64)..."

        # Clean old build
        if [ -d "parts" ] || [ -d "stage" ] || [ -d "prime" ]; then
            snapcraft clean 2>/dev/null || true
        fi

        # Use --destructive-mode in CI (no LXD container, better network access)
        # Use --use-lxd for local builds (isolated environment)
        if [ -n "$CI" ] || [ -n "$BUILD_BUILDID" ]; then
            log_info "CI environment detected, using destructive mode..."
            snapcraft --destructive-mode --verbosity=verbose
        else
            snapcraft --use-lxd --verbosity=verbose
        fi

        local snap_file
        snap_file=$(ls -1 *.snap 2>/dev/null | head -1)

        if [ -n "$snap_file" ]; then
            log_success "Build successful: $snap_file"
            log_info "Size: $(du -h "$snap_file" | cut -f1)"
        else
            log_error "Build failed - no snap file generated"
            exit 1
        fi
    fi

    # Copy to output directory
    mkdir -p "$OUTPUT_DIR"
    cp *.snap "$OUTPUT_DIR/" 2>/dev/null || true
    log_success "Copied snap files to: $OUTPUT_DIR"

    # Copy build logs to output directory
    local log_dir="$HOME/.local/state/snapcraft/log"
    if [ -d "$log_dir" ]; then
        cp "$log_dir"/snapcraft-*.log "$OUTPUT_DIR/" 2>/dev/null || true
        log_info "Copied build logs to: $OUTPUT_DIR"
    fi
}

# Main
main() {
    log_info "Azure CLI Snap Build Script"
    log_info "============================"

    validate_wheels

    VERSION=$(get_version)
    log_info "CLI Version: $VERSION"
    log_info "Multi-arch: $MULTI_ARCH"
    log_info "Wheel Dir: $WHEEL_DIR"
    log_info "Output Dir: $OUTPUT_DIR"

    create_snapcraft_yaml "$VERSION"
    build_snap "$VERSION"

    log_success "Build completed successfully!"
}

main