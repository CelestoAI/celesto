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

# image-build-loopfs.sh - Privileged helper for Celesto image-build loop mounts.
set -euo pipefail

SCRIPT_NAME="$(basename "$0")"

usage() {
    cat <<EOF
Usage:
  ${SCRIPT_NAME} mount <rootfs.ext4> <mount_dir>
  ${SCRIPT_NAME} extract <rootfs.tar> <mount_dir>
  ${SCRIPT_NAME} umount <mount_dir>
  ${SCRIPT_NAME} --help
EOF
}

die() {
    echo "❌ ${SCRIPT_NAME}: $1" >&2
    exit 1
}

resolve_abs_existing_path() {
    local input="$1"
    [[ "${input}" = /* ]] || die "path must be absolute: ${input}"
    readlink -f -- "${input}"
}

require_administrator() {
    # This is a trusted-root tool, not a privilege broker. Path ownership checks
    # cannot authorize mounting caller-controlled filesystem bytes or restoring
    # privileged archive metadata. Refuse the old sudo-delegated entry point,
    # including installations whose sudoers policy has not yet been upgraded.
    if [[ ${EUID} -ne 0 || "${SUDO_UID:-0}" != "0" || ( -n "${SUDO_USER:-}" && "${SUDO_USER}" != "root" ) ]]; then
        die "Image operations require a trusted root administrator; run 'celesto setup' to update permissions and use Docker for ordinary image builds."
    fi
}

require_restricted_image_mount() {
    local directory="$1"
    local filesystem options source
    filesystem="$(findmnt --noheadings --raw --output FSTYPE --mountpoint "${directory}")" || \
        die "Image folder is not ready; run the mount action before extracting or unmounting."
    options="$(findmnt --noheadings --raw --output OPTIONS --mountpoint "${directory}")"
    source="$(findmnt --noheadings --raw --output SOURCE --mountpoint "${directory}")"
    if [[ "${filesystem}" != "ext4" || ! "${source}" =~ ^/dev/loop[0-9]+$ || \
          ",${options}," != *,nosuid,* || ",${options}," != *,nodev,* || ",${options}," != *,noexec,* ]]; then
        die "Image folder lacks required protections; unmount it as an administrator, then rerun the mount action."
    fi
}

mount_rootfs() {
    [[ $# -eq 2 ]] || die "mount requires: <rootfs.ext4> <mount_dir>"
    local rootfs_real
    local mount_real
    rootfs_real="$(resolve_abs_existing_path "$1")"
    mount_real="$(resolve_abs_existing_path "$2")"

    [[ -f "${rootfs_real}" ]] || die "rootfs is not a regular file: ${rootfs_real}"
    [[ "${rootfs_real}" == *.ext4 ]] || die "rootfs must end with .ext4: ${rootfs_real}"
    [[ -d "${mount_real}" ]] || die "mount dir does not exist: ${mount_real}"

    mount -t ext4 -o loop,nosuid,nodev,noexec "${rootfs_real}" "${mount_real}"
}

extract_rootfs_tar() {
    [[ $# -eq 2 ]] || die "extract requires: <rootfs.tar> <mount_dir>"
    local tar_real
    local mount_real
    tar_real="$(resolve_abs_existing_path "$1")"
    mount_real="$(resolve_abs_existing_path "$2")"

    [[ -f "${tar_real}" ]] || die "tar path is not a regular file: ${tar_real}"
    [[ "${tar_real}" == *.tar ]] || die "tar path must end with .tar: ${tar_real}"
    [[ -d "${mount_real}" ]] || die "mount dir does not exist: ${mount_real}"

    require_restricted_image_mount "${mount_real}"

    tar -xf "${tar_real}" -C "${mount_real}"
}

unmount_rootfs() {
    [[ $# -eq 1 ]] || die "umount requires: <mount_dir>"
    local mount_real
    mount_real="$(resolve_abs_existing_path "$1")"

    [[ -d "${mount_real}" ]] || die "mount dir does not exist: ${mount_real}"
    require_restricted_image_mount "${mount_real}"

    umount "${mount_real}"
}

main() {
    if [[ $# -eq 0 ]]; then
        usage
        return 2
    fi

    case "$1" in
        --help|-h)
            usage
            ;;
        mount)
            shift
            require_administrator
            mount_rootfs "$@"
            ;;
        extract)
            shift
            require_administrator
            extract_rootfs_tar "$@"
            ;;
        umount)
            shift
            require_administrator
            unmount_rootfs "$@"
            ;;
        *)
            usage
            return 2
            ;;
    esac
}

main "$@"
