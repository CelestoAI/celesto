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

# configure-runtime-sudoers.sh - Remove unsafe legacy runtime sudo grants.
set -euo pipefail

SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_USER="${SUDO_USER:-}"
CHECK_ONLY=false
REMOVE=false
SKIP_RUNTIME_CHECK=false
LOOPFS_HELPER_SRC="${SCRIPT_DIR}/image-build-loopfs.sh"
LOOPFS_HELPER_DIR="/var/lib/celesto/libexec"
LOOPFS_HELPER_DST="${LOOPFS_HELPER_DIR}/celesto-loopfs-helper"

usage() {
    cat <<EOF
Usage: ${SCRIPT_NAME} [--runtime-user <user>] [--check-only] [--remove] [--skip-runtime-check]

Replaces legacy runtime sudo grants with a policy that grants no root commands.
Linux TAP networking requires an explicitly trusted root administrator; ordinary
users can use QEMU user networking and Docker image builds.

Options:
  --runtime-user <user>   Target non-root user (default: \$SUDO_USER).
  --check-only            Validate existing runtime sudoers and command access.
  --remove                Remove generated runtime sudoers file.
  --skip-runtime-check    Install sudoers without running the post-install live
                          access self-test (use during AMI bake; verify on the
                          runtime host with --check-only or 'celesto doctor').
  -h, --help              Show this help.
EOF
}

if [[ ${EUID} -ne 0 ]]; then
    if command -v sudo >/dev/null 2>&1; then
        exec sudo -E "$0" "$@"
    fi
    echo "❌ This script must run as root (sudo not found)."
    exit 1
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        --runtime-user)
            if [[ $# -lt 2 ]]; then
                echo "❌ --runtime-user requires a value"
                usage
                exit 1
            fi
            RUNTIME_USER="$2"
            shift
            ;;
        --check-only)
            CHECK_ONLY=true
            ;;
        --remove)
            REMOVE=true
            ;;
        --skip-runtime-check)
            SKIP_RUNTIME_CHECK=true
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "❌ Unknown argument: $1"
            usage
            exit 1
            ;;
    esac
    shift
done

if [[ -z "${RUNTIME_USER}" ]]; then
    echo "❌ Runtime user is required. Pass --runtime-user <user> or run via sudo as that user."
    exit 1
fi

if ! id "${RUNTIME_USER}" >/dev/null 2>&1; then
    echo "❌ User does not exist: ${RUNTIME_USER}"
    exit 1
fi

VISUDO_BIN="$(command -v visudo || true)"
INSTALL_BIN="$(command -v install || true)"

for item in \
    "visudo:${VISUDO_BIN}" \
    "install:${INSTALL_BIN}"
do
    name="${item%%:*}"
    path="${item#*:}"
    if [[ -z "${path}" ]]; then
        echo "❌ Required command not found: ${name}"
        exit 1
    fi
done

SUDOERS_FILE="/etc/sudoers.d/celesto-runtime-${RUNTIME_USER}"

validate_helper_directory() {
    local path
    local owner
    local mode
    for path in /var /var/lib /var/lib/celesto "${LOOPFS_HELPER_DIR}"; do
        if [[ -L "${path}" ]]; then
            echo "❌ Runtime helper folder cannot be a link: '${path}'; remove the link, then run 'celesto setup' again."
            return 1
        fi
        if [[ ! -e "${path}" ]]; then
            continue
        fi
        owner="$(stat -c %u "${path}")"
        mode="$(stat -c %a "${path}")"
        if [[ "${owner}" != "0" ]] || (( (8#${mode} & 8#022) != 0 )); then
            echo "❌ Runtime helper folder must be controlled by root: '${path}'; run 'sudo chown root:root ${path} && sudo chmod 755 ${path}', then run 'celesto setup' again."
            return 1
        fi
    done
}

validate_helper_file() {
    if [[ -L "${LOOPFS_HELPER_DST}" || ! -f "${LOOPFS_HELPER_DST}" || ! -x "${LOOPFS_HELPER_DST}" ]]; then
        echo "❌ Runtime helper is missing or not executable: '${LOOPFS_HELPER_DST}'; run 'celesto setup' to restore it."
        return 1
    fi
    local owner
    local mode
    owner="$(stat -c %u "${LOOPFS_HELPER_DST}")"
    mode="$(stat -c %a "${LOOPFS_HELPER_DST}")"
    if [[ "${owner}" != "0" ]] || (( (8#${mode} & 8#022) != 0 )); then
        echo "❌ Runtime helper must be controlled by root: '${LOOPFS_HELPER_DST}'; run 'celesto setup' to restore it."
        return 1
    fi
}

install_loopfs_helper() {
    if [[ ! -f "${LOOPFS_HELPER_SRC}" ]]; then
        echo "❌ Runtime helper source is missing: '${LOOPFS_HELPER_SRC}'; reinstall Celesto, then run 'celesto setup' again."
        exit 1
    fi
    validate_helper_directory
    "${INSTALL_BIN}" -d -o root -g root -m 0755 /var/lib/celesto "${LOOPFS_HELPER_DIR}"
    validate_helper_directory
    "${INSTALL_BIN}" -o root -g root -m 0755 "${LOOPFS_HELPER_SRC}" "${LOOPFS_HELPER_DST}"
    validate_helper_file
}

render_sudoers() {
    local target_file="$1"
    cat > "${target_file}" <<EOF
# Managed by Celesto (${SCRIPT_NAME}) for user ${RUNTIME_USER}
# No root commands are delegated to runtime accounts.
# Linux TAP networking requires an explicitly trusted root administrator.
# Ordinary accounts use QEMU user networking and Docker image builds.
EOF
}

validate_sudoers_file() {
    local file_path="$1"
    "${VISUDO_BIN}" -cf "${file_path}" >/dev/null
}

check_runtime_access() {
    # A syntactically valid legacy file may still grant arbitrary root access.
    # Check its policy bytes as well, so --check-only never blesses old grants.
    if ! cmp -s "${SUDOERS_FILE}" <(render_sudoers /dev/stdout); then
        echo "❌ Runtime permissions are outdated; run 'celesto setup --runtime-user ${RUNTIME_USER}' to replace them."
        return 1
    fi
    echo "✅ Runtime policy grants no root commands to '${RUNTIME_USER}'."
}

if [[ "${REMOVE}" == "true" ]]; then
    if [[ -f "${SUDOERS_FILE}" ]]; then
        rm -f "${SUDOERS_FILE}"
        echo "✅ Removed runtime sudoers: ${SUDOERS_FILE}"
    else
        echo "ℹ️ Runtime sudoers not present: ${SUDOERS_FILE}"
    fi
    exit 0
fi

if [[ "${CHECK_ONLY}" == "true" ]]; then
    if [[ ! -f "${SUDOERS_FILE}" ]]; then
        echo "❌ Runtime sudoers file missing: ${SUDOERS_FILE}"
        exit 1
    fi
    validate_sudoers_file "${SUDOERS_FILE}"
    validate_helper_directory
    validate_helper_file
    check_runtime_access
    exit 0
fi

tmp_file="$(mktemp)"
trap 'rm -f "${tmp_file}"' EXIT
install_loopfs_helper
render_sudoers "${tmp_file}"
validate_sudoers_file "${tmp_file}"
"${INSTALL_BIN}" -m 0440 "${tmp_file}" "${SUDOERS_FILE}"

echo "✅ Installed runtime sudoers: ${SUDOERS_FILE}"
echo "✅ Installed administrator-only image helper: ${LOOPFS_HELPER_DST}"
echo "ℹ️ Linux TAP networking requires a trusted root administrator; ordinary users can use QEMU user networking and Docker image builds."
if [[ "${SKIP_RUNTIME_CHECK}" == "true" ]]; then
    echo "ℹ️ Skipping post-install runtime access check (--skip-runtime-check)."
    echo "   Verify on the runtime host with --check-only or 'celesto doctor'."
else
    check_runtime_access
fi
