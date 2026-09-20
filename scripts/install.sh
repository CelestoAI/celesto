#!/bin/bash

# Copyright 2026 Celesto AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# install.sh - One-command installer for Celesto.
#
# Usage:
#   curl -fsSL https://celesto.ai/install.sh | bash
#   curl -fsSL https://celesto.ai/install.sh | bash -s -- --with-docker
#   curl -fsSL https://celesto.ai/install.sh | bash -s -- --skip-deps
#
# What it does:
#   1. Installs uv (Python package manager) if not present
#   2. Installs celesto into an isolated tool environment via uv
#   3. Runs `celesto setup` to configure the host
#
# Options (forwarded to `celesto setup`):
#   --skip-deps              Skip operating-system package installation
#   --with-docker            Also install Docker for SSH image support
#   --firecracker-dir <dir>  Install Firecracker in a specific folder
#
# After installation, the `celesto` command is available globally.

set -euo pipefail

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
RESET="\033[0m"

info()  { printf "${BOLD}${GREEN}==>${RESET} ${BOLD}%s${RESET}\n" "$*"; }
warn()  { printf "${BOLD}${YELLOW}warning:${RESET} %s\n" "$*"; }
error() { printf "${BOLD}${RED}error:${RESET} %s\n" "$*" >&2; }
die()   { error "$@"; exit 1; }

# Collect extra flags to forward to `celesto setup`. Remember the Firecracker
# folder so the final doctor check uses the same location.
SETUP_ARGS=()
FIRECRACKER_DIR_ARG=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --firecracker-dir)
            if [[ $# -lt 2 ]]; then
                die "--firecracker-dir needs a folder."
            fi
            SETUP_ARGS+=("$1" "$2")
            FIRECRACKER_DIR_ARG="$2"
            shift 2
            ;;
        --firecracker-dir=*)
            SETUP_ARGS+=("$1")
            FIRECRACKER_DIR_ARG="${1#*=}"
            shift
            ;;
        *)
            SETUP_ARGS+=("$1")
            shift
            ;;
    esac
done

if [[ -n "${FIRECRACKER_DIR_ARG}" ]]; then
    export SMOLVM_FIRECRACKER_DIR="${FIRECRACKER_DIR_ARG}"
fi

# ---------------------------------------------------------------------------
# Step 1 — Ensure uv is available
# ---------------------------------------------------------------------------

find_uv() {
    # 1. Already on PATH
    if command -v uv >/dev/null 2>&1; then
        return 0
    fi
    # 2. Common install locations (not yet on PATH in this session)
    for candidate in "$HOME/.local/bin/uv" "$HOME/.cargo/bin/uv"; do
        if [ -x "$candidate" ]; then
            local candidate_dir
            candidate_dir="$(dirname "$candidate")"
            export PATH="${candidate_dir}:$PATH"
            return 0
        fi
    done
    return 1
}

ensure_uv() {
    if find_uv; then
        info "uv is already installed ($(uv --version))"
        return
    fi

    info "Installing uv …"
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # The installer puts uv in ~/.local/bin (or ~/.cargo/bin on older versions)
    if ! find_uv; then
        die "uv installation failed. Please install it manually: https://docs.astral.sh/uv/getting-started/installation/"
    fi

    info "uv installed ($(uv --version))"
}

# ---------------------------------------------------------------------------
# Step 2 — Install celesto
# ---------------------------------------------------------------------------

install_celesto() {
    if uv tool list 2>/dev/null | grep -q '^celesto '; then
        # Installed as a uv tool — upgrade in place
        info "celesto is already installed (uv tool), upgrading …"
        uv tool install --upgrade 'celesto[server]>=0.0.15a0'
    else
        # Fresh install (or installed via pip/editable — uv tool install won't conflict)
        info "Installing celesto …"
        uv tool install 'celesto[server]>=0.0.15a0'
    fi

    # uv tool bin dir may not be on PATH yet in this session
    local tool_bin
    tool_bin="$(uv tool dir --bin)"
    if [ -d "$tool_bin" ]; then
        export PATH="$tool_bin:$PATH"
    fi

    if ! command -v celesto >/dev/null 2>&1; then
        die "celesto installation failed — 'celesto' command not found on PATH."
    fi

    info "$(celesto --version)"
}

# ---------------------------------------------------------------------------
# Step 3 — Run celesto setup
# ---------------------------------------------------------------------------

run_setup() {
    info "Running celesto setup …"
    if ((${#SETUP_ARGS[@]})); then
        celesto setup "${SETUP_ARGS[@]}"
    else
        celesto setup
    fi
}

# ---------------------------------------------------------------------------
# Step 4 — Shell PATH reminder
# ---------------------------------------------------------------------------

shell_hint() {
    warn "If 'celesto' is not found, run 'uv tool update-shell' and restart your terminal."
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

main() {
    printf "\n"
    printf "%b" "${GREEN}"
    cat <<'BANNER'
      ___      _        _          _   ___
     / __|___ | |___ __| |_ ___   /_\ |_ _|
    | (__/ -_)| / -_|_-<  _/ _ \ / _ \ | |
     \___\___||_\___/__/\__\___//_/ \_\___|
BANNER
    printf "%b" "${RESET}"
    printf "    %bCelesto Installer%b\n" "${BOLD}" "${RESET}"
    printf "    One command to give AI agents their own computer.\n\n"

    ensure_uv
    install_celesto
    run_setup
    shell_hint

    printf "\n"
    info "Verifying installation …"
    celesto doctor
    printf "\n"
    info "Done! Celesto is ready to use."
    printf "\n"
}

main
