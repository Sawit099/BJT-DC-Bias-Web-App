"""ngspice-backed CE amplifier simulation for Lab 04.

This module is a subprocess adapter around ngspice batch mode. It builds a
deterministic CE voltage-divider netlist, runs ngspice, and parses real
output files. It does not know about Flask or HTML.
"""

from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass, asdict


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


def _as_finite(name: str, value: object) -> float:
    try:
        num = float(value)
    except (TypeError, ValueError) as exc:
        raise NgspiceError(f"{name} ต้องเป็นตัวเลข") from exc
    if not math.isfinite(num):
        raise NgspiceError(f"{name} ต้องเป็นตัวเลขที่จำกัด (finite)")
    return num


@dataclass
class CEInput:
    vcc: float
    r1k: float
    r2k: float
    rck: float
    rek: float
    rlk: float
    cin_u: float
    cout_u: float
    vin_mvp: float
    freq_hz: float

    def validate(self) -> "CEInput":
        fields = {
            "VCC": (self.vcc, 0.0, 1000.0, False),
            "R1": (self.r1k, 0.0, 1_000_000.0, False),
            "R2": (self.r2k, 0.0, 1_000_000.0, False),
            "RC": (self.rck, 0.0, 1_000_000.0, False),
            "RE": (self.rek, 0.0, 1_000_000.0, False),
            "RL": (self.rlk, 0.0, 1_000_000.0, False),
            "Cin": (self.cin_u, 0.0, 1_000_000.0, False),
            "Cout": (self.cout_u, 0.0, 1_000_000.0, False),
            "Amplitude": (self.vin_mvp, -1e-12, 1_000_000.0, True),
            "Frequency": (self.freq_hz, 0.0, 1_000_000_000.0, False),
        }
        cleaned: dict[str, float] = {}
        for name, (value, lower, upper, allow_zero) in fields.items():
            num = _as_finite(name, value)
            if allow_zero:
                if num < 0:
                    raise NgspiceError(f"{name} ต้องมีค่ามากกว่าหรือเท่ากับ 0")
            else:
                if num <= lower:
                    raise NgspiceError(f"{name} ต้องมีค่ามากกว่า 0")
            if num > upper:
                raise NgspiceError(f"{name} มีค่าเกินช่วงที่รองรับ")
            cleaned[name] = num
        self.vcc = cleaned["VCC"]
        self.r1k = cleaned["R1"]
        self.r2k = cleaned["R2"]
        self.rck = cleaned["RC"]
        self.rek = cleaned["RE"]
        self.rlk = cleaned["RL"]
        self.cin_u = cleaned["Cin"]
        self.cout_u = cleaned["Cout"]
        self.vin_mvp = cleaned["Amplitude"]
        self.freq_hz = cleaned["Frequency"]
        return self


@dataclass
class OpResult:
    vb: float
    ve: float
    vc: float
    vce: float
    ic_ma: float
    engine: str
    model: str
    run_id: str

    def as_dict(self) -> dict:
        return asdict(self)


def build_ce_netlist(
    inp: CEInput,
    analysis: str = "op",
    *,
    ac_fstart: float = 10.0,
    ac_fstop: float = 1_000_000.0,
    ac_points: int = 20,
) -> str:
    inp.validate()
    if analysis not in {"op", "ac", "tran"}:
        raise NgspiceError(f"analysis ไม่รองรับ: {analysis}")
    # Values are numeric floats; formatting as .12g avoids injection.
    lines = [
        "* Lab 04 CE Voltage Divider Amplifier",
        f"VCC vcc 0 DC {inp.vcc:.12g}",
        f"R1 vcc b {inp.r1k:.12g}k",
        f"R2 b 0 {inp.r2k:.12g}k",
        f"RC vcc c {inp.rck:.12g}k",
        f"RE e 0 {inp.rek:.12g}k",
        f"Cin in b {inp.cin_u:.12g}u",
        f"Cout c out {inp.cout_u:.12g}u",
        f"RL out 0 {inp.rlk:.12g}k",
        f"Vin in 0 DC 0 AC 1 SIN(0 {inp.vin_mvp / 1000.0:.12g} {inp.freq_hz:.12g})",
        f"Q1 c b e {DEFAULT_MODEL_NAME}",
        DEFAULT_MODEL_CARD,
        ".control",
        "set noaskquit",
        "set filetype=ascii",
    ]
    if analysis == "op":
        lines += [
            "op",
            "print v(b) v(e) v(c) v(c,e) i(vcc)",
        ]
    elif analysis == "ac":
        fstart = _as_finite("AC fstart", ac_fstart)
        fstop = _as_finite("AC fstop", ac_fstop)
        points = int(ac_points)
        if fstart <= 0 or fstop <= fstart or points <= 0:
            raise NgspiceError("ช่วงความถี่ AC ไม่ถูกต้อง")
        lines += [
            f"ac dec {points} {fstart:.12g} {fstop:.12g}",
            "wrdata ac.txt vdb(out) vp(out)",
        ]
    elif analysis == "tran":
        step = max(1e-6, 1.0 / (inp.freq_hz * 200.0))
        stop = max(5.0 / inp.freq_hz, 0.005)
        lines += [
            f"tran {step:.12g} {stop:.12g}",
            "wrdata tran.txt v(in) v(out)",
        ]
    lines += ["quit", ".endc", ".end", ""]
    return "\n".join(lines)


def _run_ngspice(netlist: str, run_dir: str, timeout_s: float = 30.0) -> str:
    exe = find_ngspice()
    cir_path = os.path.join(run_dir, "circuit.cir")
    log_path = os.path.join(run_dir, "run.log")
    with open(cir_path, "w", encoding="ascii", newline="\n") as f:
        f.write(netlist)
    cmd = [exe, "-b", "-o", log_path, cir_path]
    try:
        proc = subprocess.run(
            cmd,
            cwd=run_dir,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise NgspiceError(f"ngspice ทำงานเกินเวลา ({timeout_s:.0f}s)") from exc
    except OSError as exc:
        raise NgspiceError(f"ไม่สามารถเรียก ngspice ได้: {exc}") from exc

    log_text = ""
    if os.path.isfile(log_path):
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            log_text = f.read()
    merged = (log_text + "\n" + (proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    if proc.returncode != 0:
        tail = "\n".join(merged.splitlines()[-20:])
        raise NgspiceError(f"ngspice ล้มเหลว (exit {proc.returncode})\n{tail}")
    return log_text


def _parse_op_value(log_text: str, name: str) -> float:
    # Matches: v(b) = 2.050717e+00
    pattern = re.compile(rf"^{re.escape(name)}\s*=\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*$", re.MULTILINE)
    m = pattern.search(log_text)
    if not m:
        raise NgspiceError(f"ไม่พบค่า {name} ในผลลัพธ์ ngspice")
    return float(m.group(1))


@dataclass
class AcResult:
    freq_hz: list[float]
    gain_db: list[float]
    phase_deg: list[float]
    engine: str
    model: str
    run_id: str

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class TranResult:
    time_ms: list[float]
    vin_v: list[float]
    vout_v: list[float]
    engine: str
    model: str
    run_id: str

    def as_dict(self) -> dict:
        return asdict(self)


def _parse_wrdata(path: str, expected_pairs: int) -> list[list[float]]:
    if not os.path.isfile(path):
        raise NgspiceError(f"ไม่พบไฟล์ผลลัพธ์ ngspice: {os.path.basename(path)}")
    cols: list[list[float]] = [[] for _ in range(expected_pairs * 2)]
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("*") or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < expected_pairs * 2:
                continue
            # skip non-numeric rows
            try:
                nums = [float(p) for p in parts[: expected_pairs * 2]]
            except ValueError:
                continue
            for i, n in enumerate(nums):
                cols[i].append(n)
    if not cols or not cols[0]:
        raise NgspiceError(f"ไฟล์ผลลัพธ์ {os.path.basename(path)} ว่างหรืออ่านไม่ได้")
    lengths = {len(c) for c in cols}
    if len(lengths) != 1:
        raise NgspiceError(f"ไฟล์ผลลัพธ์ {os.path.basename(path)} มีความยาวคอลัมน์ไม่ตรงกัน")
    return cols


def run_op(inp: CEInput) -> OpResult:
    inp.validate()
    netlist = build_ce_netlist(inp, analysis="op")
    run_id = uuid.uuid4().hex[:12]
    with tempfile.TemporaryDirectory(prefix="ngce_op_") as run_dir:
        log_text = _run_ngspice(netlist, run_dir)
        vb = _parse_op_value(log_text, "v(b)")
        ve = _parse_op_value(log_text, "v(e)")
        vc = _parse_op_value(log_text, "v(c)")
        vce = _parse_op_value(log_text, "v(c,e)")
        i_vcc = _parse_op_value(log_text, "i(vcc)")
        ic_ma = abs(i_vcc) * 1000.0
        return OpResult(
            vb=vb,
            ve=ve,
            vc=vc,
            vce=vce,
            ic_ma=ic_ma,
            engine="ngspice",
            model=DEFAULT_MODEL_NAME,
            run_id=run_id,
        )


def run_ac(
    inp: CEInput,
    fstart: float = 10.0,
    fstop: float = 1_000_000.0,
    points: int = 20,
) -> AcResult:
    inp.validate()
    netlist = build_ce_netlist(
        inp, analysis="ac", ac_fstart=fstart, ac_fstop=fstop, ac_points=points
    )
    run_id = uuid.uuid4().hex[:12]
    with tempfile.TemporaryDirectory(prefix="ngce_ac_") as run_dir:
        _run_ngspice(netlist, run_dir)
        cols = _parse_wrdata(os.path.join(run_dir, "ac.txt"), expected_pairs=2)
        freq_hz = cols[0]
        gain_db = cols[1]
        phase_deg = cols[3]
        return AcResult(
            freq_hz=freq_hz,
            gain_db=gain_db,
            phase_deg=phase_deg,
            engine="ngspice",
            model=DEFAULT_MODEL_NAME,
            run_id=run_id,
        )

