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

"""Sandbox IDs.

A sandbox's ID is also its name: it keys the disk, logs, sockets and inventory
row. When the caller gives none, :func:`generate_sandbox_id` returns a readable,
random one such as ``sbx-volta-k3x9p2``.
"""

from __future__ import annotations

import secrets
import string

SANDBOX_PREFIX = "sbx"

SCIENTISTS: tuple[str, ...] = (
    "einstein",
    "tesla",
    "newton",
    "darwin",
    "curie",
    "hawking",
    "feynman",
    "turing",
    "lovelace",
    "edison",
    "galileo",
    "kepler",
    "maxwell",
    "planck",
    "bohr",
    "schrodinger",
    "heisenberg",
    "fermi",
    "oppenheimer",
    "mendel",
    "pasteur",
    "watson",
    "crick",
    "sagan",
    "hubble",
    "dirac",
    "faraday",
    "archimedes",
    "copernicus",
    "descartes",
    "euler",
    "gauss",
    "ramanujan",
    "noether",
    "hopper",
    "babbage",
    "pauling",
    "fleming",
    "jenner",
    "mendeleev",
    "rutherford",
    "ohm",
    "volta",
    "ampere",
    "joule",
    "kelvin",
    "leibniz",
    "pythagoras",
    "riemann",
    "fibonacci",
)

_ID_SUFFIX_ALPHABET = string.ascii_lowercase + string.digits
ID_SUFFIX_LENGTH = 6
# Sandbox IDs may be up to 64 characters. Leave room for "-", the longest
# scientist, "-" and the suffix so every random pick fits.
MAX_PREFIX_LENGTH = 64 - (1 + max(map(len, SCIENTISTS)) + 1 + ID_SUFFIX_LENGTH)


def generate_sandbox_id(prefix: str = SANDBOX_PREFIX) -> str:
    """Return a new sandbox ID like ``sbx-volta-k3x9p2``.

    The scientist keeps the ID easy to read and say; the six random letters
    and digits from :mod:`secrets` keep it unique. Together they give about
    37 bits, so IDs created at the same moment from many threads or processes
    that share no inventory do not collide in practice.
    """
    if len(prefix) > MAX_PREFIX_LENGTH:
        raise ValueError(
            f"Name prefix {prefix!r} is too long. Use at most {MAX_PREFIX_LENGTH} characters."
        )
    scientist = secrets.choice(SCIENTISTS)
    suffix = "".join(secrets.choice(_ID_SUFFIX_ALPHABET) for _ in range(ID_SUFFIX_LENGTH))
    return f"{prefix}-{scientist}-{suffix}"
