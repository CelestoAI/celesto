"""Provider-specific lifecycle only; repository commands never run on the host."""

import os
import shutil
import sys
import time
from pathlib import Path


def prepare_local_tools():
    """Homebrew keeps ext4 utilities outside PATH; expose them only to this app."""
    if sys.platform == "darwin":
        for prefix in ("/opt/homebrew/opt/e2fsprogs", "/usr/local/opt/e2fsprogs"):
            sbin = Path(prefix) / "sbin"
            if all((sbin / tool).is_file() for tool in ("e2fsck", "resize2fs")):
                entries = os.environ.get("PATH", "").split(os.pathsep)
                if str(sbin) not in entries:
                    os.environ["PATH"] = os.pathsep.join([str(sbin), *entries])
                break
    if any(shutil.which(tool) is None for tool in ("e2fsck", "resize2fs")):
        recovery = "brew install e2fsprogs" if sys.platform == "darwin" else "sudo apt-get install e2fsprogs"
        raise RuntimeError(f"Disk preparation tools are missing; run '{recovery}' and retry the review.")


class Sandbox:
    def __init__(self, provider):
        self.provider = provider
        if provider == "local":
            prepare_local_tools()
            from celesto import Celesto

            self.vm = Celesto(os="ubuntu", memory=4096, disk_size=16384)
            try:
                self.vm.start()
            except BaseException:
                self.vm.delete()
                self.vm.close()
                raise
        elif provider == "cloud":
            from celesto import CloudComputer as Computer

            self.vm = Computer(template_id=os.getenv("CELESTO_TEMPLATE", "coding-agent"))
            try:
                deadline = time.monotonic() + 180
                while self.vm.get("status") != "running":
                    if self.vm.get("status") in {"error", "failed", "deleted"}:
                        raise RuntimeError("Cloud computer failed to start.")
                    if time.monotonic() > deadline:
                        raise TimeoutError("Cloud computer did not become ready within 180 seconds.")
                    time.sleep(1)
                    self.vm.refresh()
            except BaseException:
                self.vm.delete()
                raise
        else:
            raise ValueError("Choose local or cloud.")

    def run(self, command, timeout=180):
        result = self.vm.run(command, timeout=timeout)
        if self.provider == "cloud":
            return {key: result.get(key) for key in ("stdout", "stderr", "exit_code")}
        return {"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.exit_code}

    def close(self):
        try:
            self.vm.delete()
        finally:
            if self.provider == "local":
                self.vm.close()
