"""Exercise profile composition through the actual kernel build entry point.

The tiny source fixture checks the build orchestration, not Linux or KVM itself.
It catches a missing parent, mutually exclusive THP policies and a verifier that
uses a different fragment order from the build. Real kernel builds remain CI's
responsibility.
"""

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("profile", ["sandbox", "github-ci", "github-ci-android"])
def test_kernel_build_inherits_ci_before_android_overrides(tmp_path: Path, profile: str) -> None:
    root = Path(__file__).resolve().parents[2]
    kernel = tmp_path / "kernel"
    shutil.copytree(root / "kernel/microvm", kernel)
    parent = kernel / "profiles/github-ci.fragment"
    with parent.open("a") as output:
        output.write("\nCONFIG_CELESTO_TEST_PARENT=y\n")
    work = tmp_path / "work" / f"{profile}-amd64"
    source = work / "linux-7.3"
    (source / "scripts/kconfig").mkdir(parents=True)
    (source / "arch/x86").mkdir(parents=True)
    # Exact context for the Android-only source patch; no real kernel is built.
    (source / "arch/x86/Kconfig").write_text(
        "\tselect ARCH_HAS_EARLY_DEBUG\t\tif KGDB\n"
        "\tselect ARCH_HAS_ELF_RANDOMIZE\n"
        "\tselect ARCH_HAS_EXECMEM_ROX\t\tif X86_64 && STRICT_MODULE_RWX\n"
        "\tselect ARCH_HAS_FAST_MULTIPLIER\n"
        "\tselect ARCH_HAS_FORTIFY_SOURCE\n"
    )
    archive = work / "linux-7.3.tar.xz"
    archive.write_bytes(b"already-extracted-test-source")
    (kernel / "linux.sha256").write_text(
        hashlib.sha256(archive.read_bytes()).hexdigest() + "  " + archive.name + "\n"
    )
    merger = source / "scripts/kconfig/merge_config.sh"
    merger.write_text(
        f"#!{sys.executable}\n"
        "import pathlib, re, sys\n"
        "values = {}\n"
        "for name in sys.argv[4:]:\n"
        "    for raw in pathlib.Path(name).read_text().splitlines():\n"
        "        unset = re.fullmatch(r'# (CONFIG_\\w+) is not set', raw.strip())\n"
        "        line = raw.split('#', 1)[0].strip()\n"
        "        if unset:\n"
        "            values[unset[1]] = '# ' + unset[1] + ' is not set'\n"
        "        elif line.startswith('CONFIG_') and '=' in line:\n"
        "            values[line.split('=', 1)[0]] = line\n"
        "pathlib.Path('.config').write_text('\\n'.join(values.values()) + '\\n')\n"
    )
    merger.chmod(0o755)
    make = tmp_path / "make"
    make.write_text(
        f"#!{sys.executable}\n"
        "import pathlib, sys\n"
        "if '--version' in sys.argv:\n"
        "    print('GNU Make 4.3')\n"
        "elif sys.argv[-1] == 'x86_64_defconfig':\n"
        "    pathlib.Path('.config').write_text('')\n"
        "elif sys.argv[-1] == 'olddefconfig':\n"
        "    path = pathlib.Path('.config')\n"
        "    text = path.read_text()\n"
        "    if 'CONFIG_TRANSPARENT_HUGEPAGE_MADVISE=y' in text:\n"
        "        text = text.replace('CONFIG_TRANSPARENT_HUGEPAGE_ALWAYS=y',\n"
        "                            '# CONFIG_TRANSPARENT_HUGEPAGE_ALWAYS is not set')\n"
        "    path.write_text(text)\n"
        "else:\n"
        "    sys.exit('unexpected build target: ' + repr(sys.argv))\n"
    )
    make.chmod(0o755)
    result = subprocess.run(
        ["bash", str(kernel / "build.sh")],
        cwd=tmp_path,
        env={
            **os.environ,
            "MAKE": str(make),
            "CELESTO_ARCH_OVERRIDE": "amd64",
            "CELESTO_KERNEL_PROFILE": profile,
            "CELESTO_VERIFY_ONLY": "1",
            "WORK_DIR": str(tmp_path / "work"),
            "OUT_DIR": str(tmp_path / "out"),
        },
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    resolved = (source / ".config").read_text().splitlines()
    assert ("CONFIG_CELESTO_TEST_PARENT=y" in resolved) == (profile != "sandbox")
    if profile == "github-ci-android":
        assert "CONFIG_KVM=y" in resolved
        assert "CONFIG_KVM_INTEL=y" in resolved
        assert "CONFIG_XFS_FS=y" in resolved
        assert "CONFIG_TRANSPARENT_HUGEPAGE=y" in resolved
        assert "CONFIG_TRANSPARENT_HUGEPAGE_MADVISE=y" in resolved
        assert "CONFIG_TRANSPARENT_HUGEPAGE_ALWAYS=y" not in resolved
    elif profile == "github-ci":
        assert "CONFIG_TRANSPARENT_HUGEPAGE_ALWAYS=y" in resolved
        assert "CONFIG_KVM=y" not in resolved
    else:
        assert "CONFIG_TRANSPARENT_HUGEPAGE=y" not in resolved
        assert "CONFIG_KVM=y" not in resolved
