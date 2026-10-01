#!/bin/sh
# Celesto PID 1 init for layered presets (codex, claude-code, hermes, pi).
#
# These presets boot off a generic Ubuntu rootfs that doesn't have a
# preset-specific /init like openclaw does. Rather than running systemd
# (which adds 5–15s of boot overhead and isn't needed for a sandbox VM
# whose only job is to host an agent CLI behind SSH), we replace it with
# this minimal script that:
#
#   1. mounts the essential virtual filesystems
#   2. creates new SSH host keys and a new machine ID when the kernel cmdline
#      param celesto.instance_id=<id> differs from the saved one
#   3. starts the vsock guest-agent control plane
#   4. brings up loopback + eth0 (DHCP-style static IP from kernel cmdline)
#   5. generates a lightweight SSH host key on first boot
#   6. injects the launching user's pubkey from the kernel cmdline param
#      celesto.authorized_key_b64=<base64> (matches openclaw's mechanism)
#   7. starts sshd
#   8. parks PID 1 in a sleep loop, signal-handling Firecracker shutdown
#
# Mirrors `_base_init_script()` in src/celesto/images/builder.py — keep
# them in sync if either changes.

set -u

# ── Signal handling ──────────────────────────────────────────
# Firecracker's SendCtrlAltDel sends Ctrl+Alt+Del to the guest kernel.
# Default kernel response is hardware reboot (not supported in
# Firecracker → VM hangs). We disable CAD so the kernel sends SIGINT to
# PID 1 instead, where we trap it.
shutdown() {
    echo "Celesto init: shutting down..."
    kill -TERM -1 2>/dev/null
    sleep 0.2
    sync
    poweroff -f
}
trap shutdown INT TERM

# ── Timestamp helpers (for host-side startup profiling) ──────
ts_uptime() {
    cut -d' ' -f1 /proc/uptime 2>/dev/null || echo "0.00"
}

ts_epoch() {
    date +%s 2>/dev/null || echo "0"
}

log_ts() {
    STAGE="$1"
    EPOCH="$(ts_epoch)"
    UPTIME="$(ts_uptime)"
    LINE="CELESTO_TS stage=${STAGE} epoch_s=${EPOCH} uptime_s=${UPTIME}"
    echo "$LINE"
    if [ -d /run ]; then
        mkdir -p /run/celesto 2>/dev/null || true
        printf '{"stage":"%s","epoch_s":%s,"uptime_s":%s}\n' "$STAGE" "$EPOCH" "$UPTIME" >> /run/celesto/milestones.jsonl 2>/dev/null || true
        printf '{"stage":"%s","epoch_s":%s,"uptime_s":%s}\n' "$STAGE" "$EPOCH" "$UPTIME" >> /run/celesto/boot-milestones.jsonl 2>/dev/null || true
    fi
    if [ -d /var/log ]; then
        echo "$LINE" >> /var/log/celesto-boot.log 2>/dev/null || true
    fi
}

log_ts "init-start"

# ── Mount essential filesystems ──────────────────────────────
mount -t proc proc /proc
mount -t sysfs sys /sys
mount -t devtmpfs dev /dev 2>/dev/null   # may already be mounted
mkdir -p /dev/pts
mount -t devpts devpts /dev/pts
mount -t tmpfs tmpfs /run
mkdir -p /sys/fs/cgroup
if ! grep -q ' /sys/fs/cgroup cgroup2 ' /proc/mounts; then
    mount -t cgroup2 cgroup2 /sys/fs/cgroup
fi
# Keep /tmp on the root disk, not tmpfs. Package managers use /tmp for
# temporary writes, and a memory-sized tmpfs can fill up even when the disk
# still has plenty of space.

log_ts "mounts-ready"

echo 0 > /proc/sys/kernel/ctrl-alt-del
mount -o remount,rw /
mkdir -p /run/sshd /var/log /tmp
chmod 1777 /tmp

log_ts "root-ready"

# ── Sandbox identity ─────────────────────────────────────────
# Runs before the guest agent and sshd so neither ever serves another
# machine's SSH host keys or machine ID.
# >>> Celesto identity reset
# Keep this block identical in src/celesto/images/builder.py
# (_IDENTITY_RESET_SCRIPT) and scripts/ci/preset-init.sh; a test checks it.
#
# Celesto passes each sandbox's instance ID on the kernel command line as
# celesto.instance_id=<32 hex>. A restart or restore of the same sandbox
# passes the same ID. A different ID means this disk is booting as a new
# machine, so it gets new SSH host keys and a new machine ID before the guest
# agent or sshd can read the old ones. The ID is saved last, so a reset cut
# short is redone on the next boot. Without an ID, keys and machine ID are
# left alone.
#
# Arguments: the kernel command line file, and the root to change ("" for /).
celesto_new_machine_id() {
    NEW_ID=$(tr -d '-' < /proc/sys/kernel/random/uuid 2>/dev/null)
    case "$NEW_ID" in
        *[!0-9a-f]*) NEW_ID="" ;;
    esac
    if [ "${#NEW_ID}" -ne 32 ]; then
        NEW_ID=$(od -An -N16 -tx1 /dev/urandom 2>/dev/null | tr -d ' \n')
    fi
    echo "$NEW_ID"
}

celesto_reset_identity() {
    ID_CMDLINE="$1"
    ID_ROOT="$2"
    # Tells Celesto that this startup script understands instance IDs.
    mkdir -p "$ID_ROOT/etc/celesto/features"
    [ -e "$ID_ROOT/etc/celesto/features/instance-id" ] \
        || : > "$ID_ROOT/etc/celesto/features/instance-id"

    INSTANCE_ID=$(tr ' ' '\n' < "$ID_CMDLINE" | grep '^celesto\.instance_id=' | head -1 \
        | cut -d= -f2-)
    [ -n "$INSTANCE_ID" ] || return 0
    case "$INSTANCE_ID" in
        *[!0-9a-f]*) INSTANCE_ID="" ;;
    esac
    if [ "${#INSTANCE_ID}" -ne 32 ]; then
        echo "Celesto init: ignoring malformed celesto.instance_id" >&2
        return 0
    fi
    if [ "$(cat "$ID_ROOT/etc/celesto/instance-id" 2>/dev/null)" = "$INSTANCE_ID" ]; then
        return 0
    fi

    echo "Celesto init: new instance ID; creating new SSH host keys and machine ID"
    rm -f "$ID_ROOT"/etc/ssh/ssh_host_*_key "$ID_ROOT"/etc/ssh/ssh_host_*_key.pub
    MACHINE_ID=$(celesto_new_machine_id)
    if [ "${#MACHINE_ID}" -ne 32 ]; then
        echo "Celesto init: could not create a machine ID" >&2
        return 1
    fi
    rm -f "$ID_ROOT/etc/machine-id"
    printf '%s\n' "$MACHINE_ID" > "$ID_ROOT/etc/machine-id"
    chmod 0444 "$ID_ROOT/etc/machine-id"
    # dbus keeps its own copy, often as a symlink to /etc/machine-id. A
    # symlink already follows the new file; a plain copy is rewritten.
    DBUS_MACHINE_ID="$ID_ROOT/var/lib/dbus/machine-id"
    if [ ! -L "$DBUS_MACHINE_ID" ] && [ -d "$ID_ROOT/var/lib/dbus" ]; then
        rm -f "$DBUS_MACHINE_ID"
        printf '%s\n' "$MACHINE_ID" > "$DBUS_MACHINE_ID"
    fi
    mkdir -p "$ID_ROOT/etc/ssh"
    if ! ssh-keygen -t ed25519 -f "$ID_ROOT/etc/ssh/ssh_host_ed25519_key" -N "" -q \
        2>/dev/null; then
        echo "Celesto init: could not create SSH host keys" >&2
        return 1
    fi
    mkdir -p "$ID_ROOT/etc/celesto"
    printf '%s\n' "$INSTANCE_ID" > "$ID_ROOT/etc/celesto/instance-id.tmp"
    mv -f "$ID_ROOT/etc/celesto/instance-id.tmp" "$ID_ROOT/etc/celesto/instance-id"
}
# <<< Celesto identity reset

log_ts "identity-check-start"
celesto_reset_identity /proc/cmdline ""
log_ts "identity-check-done"

# ── Guest agent (vsock control plane) ────────────────────────
# Started before networking and sshd, so explicit-vsock sandboxes can become
# ready without waiting for SSH host-key generation or network setup. SSH-only
# sandboxes can still boot if the agent is missing, but vsock sandboxes require
# the Rust agent to answer.
# Mirrors _base_init_script() in src/celesto/images/builder.py.
log_ts "guest-agent-start"
if [ -x /usr/local/bin/celesto-guest-agent ]; then
    /usr/local/bin/celesto-guest-agent --listen vsock://1024 >/var/log/celesto-agent.log 2>&1 &
    echo "Celesto init: guest agent started (PID=$!)"
else
    echo "Celesto init: guest agent not found; vsock control will be unavailable" >&2
fi
log_ts "guest-agent-started"

# ── Networking ───────────────────────────────────────────────
log_ts "net-config-start"
# Format: ip=<guest_ip>::<gateway>:<netmask>::eth0:off (kernel ip= param)
netmask_to_prefix() {
    IFS=.
    set -- $1
    IFS=' '

    [ $# -eq 4 ] || return 1

    PREFIX=0
    ZERO_SEEN=0
    for OCTET in "$@"; do
        case "$OCTET" in
            255) [ "$ZERO_SEEN" -eq 0 ] || return 1; PREFIX=$((PREFIX + 8)) ;;
            254) [ "$ZERO_SEEN" -eq 0 ] || return 1; PREFIX=$((PREFIX + 7)); ZERO_SEEN=1 ;;
            252) [ "$ZERO_SEEN" -eq 0 ] || return 1; PREFIX=$((PREFIX + 6)); ZERO_SEEN=1 ;;
            248) [ "$ZERO_SEEN" -eq 0 ] || return 1; PREFIX=$((PREFIX + 5)); ZERO_SEEN=1 ;;
            240) [ "$ZERO_SEEN" -eq 0 ] || return 1; PREFIX=$((PREFIX + 4)); ZERO_SEEN=1 ;;
            224) [ "$ZERO_SEEN" -eq 0 ] || return 1; PREFIX=$((PREFIX + 3)); ZERO_SEEN=1 ;;
            192) [ "$ZERO_SEEN" -eq 0 ] || return 1; PREFIX=$((PREFIX + 2)); ZERO_SEEN=1 ;;
            128) [ "$ZERO_SEEN" -eq 0 ] || return 1; PREFIX=$((PREFIX + 1)); ZERO_SEEN=1 ;;
            0) ZERO_SEEN=1 ;;
            *) return 1 ;;
        esac
    done

    echo "$PREFIX"
}

IP_CONFIG=$(cat /proc/cmdline | tr ' ' '\n' | grep '^ip=' | head -1)
GUEST_MANAGED=$(cat /proc/cmdline | tr ' ' '\n' | grep -E '^(celesto|smolvm)\.network=guest' | head -1)

configure_guest_managed_network() {
    ip link set lo up

    # A custom hook is the authoritative static/DHCP configuration supplied
    # inside the image. The interface name is passed as its first argument.
    if [ -x /etc/celesto/network.sh ]; then
        /etc/celesto/network.sh eth0
        return $?
    fi

    # Respect a conventional interfaces file when this image ships ifup.
    if command -v ifup >/dev/null 2>&1 \
        && grep -Eq '^[[:space:]]*iface[[:space:]]+eth0' /etc/network/interfaces 2>/dev/null \
        && ifup eth0; then
        return
    fi

    # Celesto-provided images use guest-side DHCP when no static hook exists.
    ip link set eth0 up 2>/dev/null || true
    if command -v udhcpc >/dev/null 2>&1 && udhcpc -q -n -t 5 -i eth0; then
        return
    fi
    if command -v dhclient >/dev/null 2>&1 && dhclient -1 eth0; then
        return
    fi

    echo "Celesto init: eth0 has no guest network configuration; add /etc/celesto/network.sh" >&2
    return 1
}

if [ -n "$GUEST_MANAGED" ]; then
    if configure_guest_managed_network; then
        log_ts "net-ready"
    else
        log_ts "net-config-failed"
    fi
    log_ts "net-config-done"
else
    if [ -n "$IP_CONFIG" ]; then
        IP_FIELDS=$(echo "$IP_CONFIG" | cut -d= -f2-)
        GUEST_IP=$(echo "$IP_FIELDS" | cut -d: -f1)
        GATEWAY=$(echo "$IP_FIELDS" | cut -d: -f3)
        NETMASK=$(echo "$IP_FIELDS" | cut -d: -f4)
    else
        GUEST_IP="172.16.0.2"
        GATEWAY="172.16.0.1"
        NETMASK="255.255.255.0"
    fi

    PREFIX=$(netmask_to_prefix "$NETMASK") || PREFIX=24
    ip link set lo up
    ip link set eth0 up 2>/dev/null || true
    ip addr add "${GUEST_IP}/${PREFIX}" dev eth0 2>/dev/null || true
    ip route add default via "${GATEWAY}" dev eth0 2>/dev/null || true

    if [ -n "$GATEWAY" ]; then
        echo "nameserver ${GATEWAY}" > /etc/resolv.conf
        echo "nameserver 8.8.8.8" >> /etc/resolv.conf
        echo "nameserver 8.8.4.4" >> /etc/resolv.conf
    else
        echo "nameserver 8.8.8.8" > /etc/resolv.conf
        echo "nameserver 8.8.4.4" >> /etc/resolv.conf
    fi

    log_ts "net-config-done"
    log_ts "net-ready"
fi

hostname celesto
if ! grep -Fqx '127.0.1.1 celesto # Celesto guest hostname' /etc/hosts 2>/dev/null; then
    echo '127.0.1.1 celesto # Celesto guest hostname' >> /etc/hosts
fi

# ── SSH host keys ────────────────────────────────────────────
log_ts "ssh-hostkey-check-start"
if ! ls /etc/ssh/ssh_host_*_key >/dev/null 2>&1; then
    ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -N "" -q 2>/dev/null
fi
log_ts "ssh-hostkey-check-done"

# ── Pubkey injection from kernel cmdline ─────────────────────
# Format: celesto.authorized_key_b64=<base64-of-the-pubkey-line>. The legacy
# parameter is accepted while published images transition to Celesto.
# Published images don't bake keys at build time, so each VM gets the launching
# user's key.
log_ts "ssh-authkey-inject-start"
AUTHKEY_B64=$(cat /proc/cmdline | tr ' ' '\n' \
    | grep -E '^(celesto|smolvm)\.authorized_key_b64=' | head -1 | cut -d= -f2-)
if [ -n "$AUTHKEY_B64" ]; then
    DECODED=$(echo "$AUTHKEY_B64" | base64 -d 2>/dev/null)
    if [ -n "$DECODED" ]; then
        mkdir -p /root/.ssh
        chmod 700 /root/.ssh
        echo "$DECODED" > /root/.ssh/authorized_keys
        chmod 600 /root/.ssh/authorized_keys
    fi
fi
log_ts "ssh-authkey-inject-done"

# ── Clock sync (host-sleep drift) ────────────────────────────
# The guest's clocksource (the TSC under HVF/QEMU) stops advancing
# while the host is asleep, so on wake the system clock lags by the
# sleep duration (issue #330). With no NTP daemon in the sandbox, we
# periodically re-read the emulated hardware RTC — which QEMU keeps
# pinned to host wall-clock time (-rtc clock=host) — and step the
# system clock to match. No-ops on backends with no RTC (Firecracker).
# Mirrors _base_init_script() in src/celesto/images/builder.py.
log_ts "clock-sync-start"
HWCLOCK=""
for cand in hwclock /usr/sbin/hwclock /sbin/hwclock; do
    if HWCLOCK_PATH=$(command -v "$cand" 2>/dev/null); then
        HWCLOCK="$HWCLOCK_PATH"
        break
    fi
done
if [ -n "$HWCLOCK" ]; then
    (
        while true; do
            "$HWCLOCK" -s -u 2>/dev/null || true
            sleep 30
        done
    ) &
    echo "Celesto init: clock-sync loop started (PID=$!)"
    log_ts "clock-sync-started"
else
    log_ts "clock-sync-disabled"
fi

log_ts "sshd-start"
/usr/sbin/sshd -e &
log_ts "sshd-invoked"

echo "Celesto init complete: IP=${GUEST_IP}, SSH listening on port 22"
log_ts "init-complete"

# ── Keep PID 1 alive ────────────────────────────────────────
# Use `wait` so signals are delivered promptly (plain `sleep` in a
# while-loop blocks signal delivery until sleep finishes).
while true; do
    sleep 3600 &
    wait $!
done
