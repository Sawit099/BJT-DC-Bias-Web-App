"""ngspice-backed CE amplifier simulation for Lab 04.

This module is a subprocess adapter around ngspice batch mode. It builds a
deterministic CE voltage-divider netlist, runs ngspice, and parses real
output files. It does not know about Flask or HTML.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass


class NgspiceError(RuntimeError):
    """Base error for ngspice discovery, validation, or run failures."""


class NgspiceNotFoundError(NgspiceError):
    """Raised when no ngspice executable can be located."""


DEFAULT_MODEL_NAME = "Q2N3904_LAB04"
# Explicit BJT model used for Lab 04 reproducibility/provenance.
# Parameters are a compact 2N3904-like NPN model; not a manufacturer-certified
# SPICE card. Source/provenance must be documented in README/validation.
DEFAULT_MODEL_CARD = (
    ".model Q2N3904_LAB04 NPN("
    "BF=200 IS=6.734f VAF=74.03 "
    "CJE=4.493p CJC=3.638p TF=301.2p TR=239.5n)"
)

_COMMON_WINDOWS_PATHS = [
    os.path.join(
        os.environ.get("LOCALAPPDATA", ""),
        "Tools",
        "ngspice",
        "Spice64",
        "bin",
        "ngspice_con.exe",
    ),
    r"C:\Spice64\bin\ngspice_con.exe",
    r"C:\Program Files\Spice64\bin\ngspice_con.exe",
    r"C:\Program Files (x86)\Spice64\bin\ngspice_con.exe",
]


def find_ngspice() -> str:
    """Return absolute path to an ngspice batch executable or raise."""
    checked: list[str] = []

    env = os.environ.get("NGSPICE_EXE", "").strip()
    if env:
        env_path = os.path.abspath(env)
        checked.append(f"NGSPICE_EXE={env_path}")
        if os.path.isfile(env_path):
            return env_path

    for name in ("ngspice_con", "ngspice"):
        found = shutil.which(name)
        checked.append(f"PATH:{name}")
        if found and os.path.isfile(found):
            return os.path.abspath(found)

    for path in _COMMON_WINDOWS_PATHS:
        if not path:
            continue
        abs_path = os.path.abspath(path)
        checked.append(abs_path)
        if os.path.isfile(abs_path):
            return abs_path

    checked_msg = "; ".join(checked) if checked else "(none)"
    raise NgspiceNotFoundError(
        "ไม่พบ ngspice executable สำหรับรัน simulation จริง "
        "กรุณาติดตั้ง ngspice หรือกำหนดตัวแปรสภาพแวดล้อม NGSPICE_EXE ให้ชี้ไปยัง ngspice_con.exe. "
        f"Checked: {checked_msg}"
    )


def ngspice_available() -> bool:
    try:
        find_ngspice()
        return True
    except NgspiceNotFoundError:
        return False
