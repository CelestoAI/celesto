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
    export CELESTO_FIRECRACKER_DIR="${FIRECRACKER_DIR_ARG}"
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
        uv tool install --upgrade --refresh-package celesto 'celesto[server]>=0.0.15a0'
    else
        # Fresh install (or installed via pip/editable — uv tool install won't conflict)
        info "Installing celesto …"
        uv tool install --refresh-package celesto 'celesto[server]>=0.0.15a0'
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

    install_latest_pypi_release
    info "$(celesto --version)"
}

install_latest_pypi_release() {
    # PyPI can accept a release while its installer index still lists only the
    # previous version. Compare the two public APIs and use the verified wheel
    # when that happens. Keep the wheel so uv's tool receipt remains usable.
    local tool_python wheel_uri
    tool_python="$(uv tool dir)/celesto/bin/python"
    if [[ ! -x "$tool_python" ]]; then
        die "Celesto's Python environment is missing. Run 'curl -fsSL https://celesto.ai/install.sh | bash' again."
    fi

    if ! wheel_uri="$("$tool_python" - "$(celesto --version)" <<'PY'
import hashlib
import json
import os
import sys
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


def get_json(url, *, simple=False):
    headers = {"Accept": "application/vnd.pypi.simple.v1+json"} if simple else {}
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
        return json.load(response)


try:
    installed = sys.argv[1].removeprefix("celesto ")
    project = get_json("https://pypi.org/pypi/celesto/json")
    # The PyPI project page can lag the exact release page as well as the
    # installer index. Keep this minimum release until both indexes recover.
    baseline = get_json("https://pypi.org/pypi/celesto/0.1.3.post1/json")
    release = max((project, baseline), key=lambda item: item["last_serial"])
    latest = release["info"]["version"]
    if installed != latest:
        index = get_json("https://pypi.org/simple/celesto/", simple=True)
        if release["last_serial"] > index["meta"]["_last-serial"]:
            filename = f"celesto-{latest}-py3-none-any.whl"
            wheel = next(item for item in release["urls"] if item["filename"] == filename)
            url = wheel["url"]
            digest = wheel["digests"]["sha256"]
            if urlparse(url).scheme != "https" or urlparse(url).hostname != "files.pythonhosted.org":
                raise ValueError("the published wheel URL is invalid")
            cache = Path.home() / ".celesto" / "packages"
            cache.mkdir(parents=True, exist_ok=True)
            target = cache / filename
            if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                with urllib.request.urlopen(url, timeout=60) as response:
                    data = response.read()
                if hashlib.sha256(data).hexdigest() != digest:
                    raise ValueError("the published wheel SHA-256 does not match PyPI")
                with tempfile.NamedTemporaryFile(dir=cache, delete=False) as temporary:
                    temporary.write(data)
                    temporary_path = Path(temporary.name)
                os.replace(temporary_path, target)
            print(target.as_uri())
except Exception as exc:
    print(f"Could not verify the latest Celesto release: {exc}", file=sys.stderr)
    sys.exit(1)
PY
    )"; then
        warn "The latest Celesto release could not be checked. Run 'curl -fsSL https://celesto.ai/install.sh | bash' again later."
        return
    fi

    if [[ -n "$wheel_uri" ]]; then
        info "The package catalog is delayed; installing the verified Celesto release …"
        uv tool install --upgrade "celesto[server] @ $wheel_uri"
    fi
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
# Step 5 — Verify the installation
# ---------------------------------------------------------------------------

run_doctor() {
    # On Linux, setup may have just added this user to the kvm group. The
    # current shell cannot see that new membership yet, so run the check under
    # `sg` instead of reporting a false failure and asking for a new login.
    if [[ "$(uname -s)" == "Linux" ]] && command -v sg >/dev/null 2>&1; then
        local current_user current_groups account_groups
        if current_user="$(id -un 2>/dev/null)" \
            && current_groups="$(id -Gn 2>/dev/null)" \
            && account_groups="$(id -Gn "$current_user" 2>/dev/null)" \
            && [[ " $account_groups " == *" kvm "* ]] \
            && [[ " $current_groups " != *" kvm "* ]]; then
            local celesto_path doctor_command
            celesto_path="$(command -v celesto)"
            printf -v doctor_command '%q doctor' "$celesto_path"
            info "Activating pending kvm group membership for verification …"
            sg kvm -c "$doctor_command"
            return
        fi
    fi

    celesto doctor
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
    run_doctor
    printf "\n"
    info "Done! Celesto is ready to use."
    printf "\n"
}

main
