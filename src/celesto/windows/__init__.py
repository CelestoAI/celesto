# Copyright 2026 Celesto AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Windows-guest support: image building and (future) image catalog.

Phase 3c ships :class:`WindowsImageBuilder` and the
``celesto windows build-image`` CLI command, which drive an unattended
Windows install from a user-supplied Windows ISO + virtio-win driver
ISO to a ready-to-use qcow2 baseline that ``Celesto(os="windows",
image=...)`` can boot directly.
"""

from celesto.windows.build_image import WindowsImageBuilder, render_autounattend

__all__ = ["WindowsImageBuilder", "render_autounattend"]
