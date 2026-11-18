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

"""Tests for Celesto kernel config fragments."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMON_FRAGMENT = REPO_ROOT / "kernel" / "microvm" / "config.fragment"


def test_android_kernel_has_builtin_kvm_without_changing_ordinary_profiles() -> None:
    """The Android image cannot load modules; ordinary images must not acquire KVM."""
    profiles = REPO_ROOT / "kernel" / "microvm" / "profiles"
    required = {"CONFIG_VIRTUALIZATION", "CONFIG_KVM", "CONFIG_KVM_INTEL", "CONFIG_KVM_AMD"}
    assert required <= _enabled_symbols(profiles / "github-ci-android.fragment")
    for profile in ("sandbox", "github-ci"):
        assert "CONFIG_KVM" not in _enabled_symbols(profiles / f"{profile}.fragment")


def _enabled_symbols(fragment: Path) -> set[str]:
    """Return symbols explicitly enabled in a kernel config fragment."""
    symbols: set[str] = set()
    for raw_line in fragment.read_text().splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if line.startswith("CONFIG_") and line.endswith("=y"):
            symbols.add(line.removesuffix("=y"))
    return symbols


def test_microvm_kernel_enables_podman_netavark_networking() -> None:
    """Podman/Netavark needs nftables support for default bridge networking."""
    symbols = _enabled_symbols(COMMON_FRAGMENT)

    required = {
        "CONFIG_NETFILTER_ADVANCED",
        "CONFIG_NETFILTER_XTABLES",
        "CONFIG_NF_TABLES",
        "CONFIG_NF_TABLES_INET",
        "CONFIG_NFT_CT",
        "CONFIG_NFT_NAT",
        "CONFIG_NFT_MASQ",
        "CONFIG_NFT_COMPAT",
        "CONFIG_NETFILTER_XT_MATCH_COMMENT",
    }
    missing = required - symbols
    assert required <= symbols, f"missing symbols: {missing}"


def test_microvm_kernel_supports_user_installed_docker() -> None:
    """Docker can be installed later without relying on unavailable modules."""
    symbols = _enabled_symbols(COMMON_FRAGMENT)

    required = {
        "CONFIG_MEMCG",
        "CONFIG_CGROUP_SCHED",
        "CONFIG_FAIR_GROUP_SCHED",
        "CONFIG_CFS_BANDWIDTH",
        "CONFIG_CGROUP_BPF",
        "CONFIG_USER_NS",
        "CONFIG_VETH",
        "CONFIG_BRIDGE",
        "CONFIG_BRIDGE_NETFILTER",
        "CONFIG_DUMMY",
        "CONFIG_MACVLAN",
        "CONFIG_IPVLAN",
        "CONFIG_NETFILTER_XT_MATCH_IPVS",
        "CONFIG_IP_VS",
        "CONFIG_IP_NF_RAW",
        "CONFIG_IP6_NF_RAW",
        "CONFIG_IP6_NF_NAT",
        "CONFIG_IP6_NF_TARGET_MASQUERADE",
    }
    missing = required - symbols
    assert required <= symbols, f"missing symbols: {missing}"


PROFILES_DIR = REPO_ROOT / "kernel" / "microvm" / "profiles"
ARCH_FRAGMENTS = sorted((REPO_ROOT / "kernel" / "microvm").glob("config.*.fragment"))
THP_SYMBOLS = {"CONFIG_TRANSPARENT_HUGEPAGE", "CONFIG_TRANSPARENT_HUGEPAGE_ALWAYS"}


def test_github_ci_kernel_enables_transparent_huge_pages_always() -> None:
    """CI builds run faster with THP on by default (fewer page faults)."""
    symbols = _enabled_symbols(PROFILES_DIR / "github-ci.fragment")

    missing = THP_SYMBOLS - symbols
    assert not missing, f"missing symbols: {missing}"


def test_sandbox_kernel_keeps_transparent_huge_pages_off() -> None:
    """Sandboxes keep 4 KiB pages: THP stays out of every shared fragment."""
    sandbox_inputs = [COMMON_FRAGMENT, *ARCH_FRAGMENTS, PROFILES_DIR / "sandbox.fragment"]
    symbols = set().union(*(_enabled_symbols(fragment) for fragment in sandbox_inputs))

    unexpected = THP_SYMBOLS & symbols
    assert not unexpected, f"unexpected symbols: {unexpected}"
