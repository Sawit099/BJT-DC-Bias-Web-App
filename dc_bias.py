"""DC bias calculations for a BJT common-emitter voltage-divider bias circuit.

This module is pure engineering logic: it does not know about HTTP, HTML or
Flask. All resistances arrive in kOhm and are converted to Ohm internally;
every value in :class:`BiasResult` is an SI unit (V, A, Ohm).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

import math

VCE_SAT_V = 0.2

WARNING_CUTOFF = (
    "IB ที่คำนวณได้มีค่า ≤ 0 — transistor ไม่ได้อยู่ในช่วง forward active (cutoff) "
    "แบบจำลอง forward-active ใช้ไม่ได้กับผลชุดนี้"
)
WARNING_SATURATION = (
    "VCE ≤ 0.2 V (VCE,sat) — transistor อยู่ในช่วงอิ่มตัว (saturation) "
    "ผลจากแบบจำลอง forward-active ใช้ไม่ได้ ห้ามใช้ค่านี้เป็นคำตอบ"
)


class Region(Enum):
    ACTIVE = "active"
    CUTOFF = "cutoff"
    SATURATION = "saturation"


class ValidationError(ValueError):
    """A user-fixable input problem, tied to the form field that caused it."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field
        self.message = message


@dataclass(frozen=True)
class BiasInput:
    vcc_v: float
    r1_kohm: float
    r2_kohm: float
    rc_kohm: float
    re_kohm: float
    beta: float
    vbe_v: float


@dataclass(frozen=True)
class FixedInput:
    """Fixed bias: RB from VCC to base, emitter grounded."""

    vcc_v: float
    rb_kohm: float
    rc_kohm: float
    beta: float
    vbe_v: float


@dataclass(frozen=True)
class EmitterInput:
    """Emitter bias: RB from VCC to base, RE from emitter to ground."""

    vcc_v: float
    rb_kohm: float
    rc_kohm: float
    re_kohm: float
    beta: float
    vbe_v: float


@dataclass(frozen=True)
class BiasResult:
    vth_v: float | None
    rth_ohm: float | None
    ib_a: float
    ic_a: float
    ie_a: float
    ve_v: float
    vb_v: float
    vc_v: float
    vce_v: float
    region: Region
    warning: str | None

    def as_dict(self) -> dict:
        """Shared result contract: the key names the Flask layer and docs use."""
        return {
            "vth_v": self.vth_v,
            "rth_ohm": self.rth_ohm,
            "vb_v": self.vb_v,
            "ve_v": self.ve_v,
            "vc_v": self.vc_v,
            "vce_v": self.vce_v,
            "ib_ua": self.ib_a * 1e6,
            "ic_ma": self.ic_a * 1e3,
            "ie_ma": self.ie_a * 1e3,
            "region": self.region.value,
            "warning": self.warning,
        }


def _solve(
    *,
    ib: float,
    beta: float,
    vcc_v: float,
    rc_ohm: float,
    re_ohm: float,
    vbe_v: float,
    vth_v: float | None = None,
    rth_ohm: float | None = None,
) -> BiasResult:
    """Turn IB into the full operating point and decide the region."""
    ic = beta * ib
    ie = (beta + 1.0) * ib
    ve = ie * re_ohm
    vb = ve + vbe_v
    vc = vcc_v - ic * rc_ohm
    vce = vc - ve

    if ib <= 0:
        region, warning = Region.CUTOFF, WARNING_CUTOFF
    elif vce <= VCE_SAT_V:
        region, warning = Region.SATURATION, WARNING_SATURATION
    else:
        region, warning = Region.ACTIVE, None

    return BiasResult(
        vth_v=vth_v,
        rth_ohm=rth_ohm,
        ib_a=ib,
        ic_a=ic,
        ie_a=ie,
        ve_v=ve,
        vb_v=vb,
        vc_v=vc,
        vce_v=vce,
        region=region,
        warning=warning,
    )


def calculate(bias: BiasInput) -> BiasResult:
    """Voltage-divider bias (Lab 02 reference circuit)."""
    r1 = bias.r1_kohm * 1000.0
    r2 = bias.r2_kohm * 1000.0
    rc = bias.rc_kohm * 1000.0
    re = bias.re_kohm * 1000.0

    vth = bias.vcc_v * r2 / (r1 + r2)
    rth = r1 * r2 / (r1 + r2)
    ib = (vth - bias.vbe_v) / (rth + (bias.beta + 1.0) * re)

    return _solve(
        ib=ib,
        beta=bias.beta,
        vcc_v=bias.vcc_v,
        rc_ohm=rc,
        re_ohm=re,
        vbe_v=bias.vbe_v,
        vth_v=vth,
        rth_ohm=rth,
    )


def calculate_fixed(bias: FixedInput) -> BiasResult:
    """Fixed bias: IB = (VCC - VBE) / RB, emitter tied to ground (VE = 0)."""
    rc = bias.rc_kohm * 1000.0
    ib = (bias.vcc_v - bias.vbe_v) / (bias.rb_kohm * 1000.0)

    return _solve(
        ib=ib,
        beta=bias.beta,
        vcc_v=bias.vcc_v,
        rc_ohm=rc,
        re_ohm=0.0,
        vbe_v=bias.vbe_v,
    )


def calculate_emitter(bias: EmitterInput) -> BiasResult:
    """Emitter bias: IB = (VCC - VBE) / [RB + (beta + 1)RE]."""
    rc = bias.rc_kohm * 1000.0
    re = bias.re_kohm * 1000.0
    rb = bias.rb_kohm * 1000.0
    ib = (bias.vcc_v - bias.vbe_v) / (rb + (bias.beta + 1.0) * re)

    return _solve(
        ib=ib,
        beta=bias.beta,
        vcc_v=bias.vcc_v,
        rc_ohm=rc,
        re_ohm=re,
        vbe_v=bias.vbe_v,
    )


FIELD_LABELS = {
    "vcc": "VCC [V]",
    "r1": "R1 [kΩ]",
    "r2": "R2 [kΩ]",
    "rb": "RB [kΩ]",
    "rc": "RC [kΩ]",
    "re": "RE [kΩ]",
    "beta": "β",
    "vbe": "VBE [V]",
}

RESISTOR_UNIT = "kΩ"


def _parse_float(form: Mapping[str, str], field: str) -> float:
    raw = (form.get(field) or "").strip()
    try:
        value = float(raw)
    except ValueError:
        raise ValidationError(
            field, f"กรุณากรอก {FIELD_LABELS[field]} เป็นตัวเลข"
        ) from None
    if not math.isfinite(value):
        raise ValidationError(
            field, f"กรุณากรอก {FIELD_LABELS[field]} เป็นตัวเลขที่จำกัด"
        )
    return value


def parse_inputs(form: Mapping[str, str]) -> BiasInput:
    values = _read(form, ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"))

    if values["vcc"] <= 0:
        raise ValidationError("vcc", "VCC ต้องมากกว่า 0 V")
    for field in ("r1", "r2", "rc", "re"):
        if values[field] <= 0:
            raise ValidationError(field, f"{FIELD_LABELS[field]} ต้องมากกว่า 0 kΩ")
    if values["beta"] <= 0:
        raise ValidationError("beta", "β ต้องมากกว่า 0")
    if not 0 <= values["vbe"] < values["vcc"]:
        raise ValidationError("vbe", "VBE ต้องอยู่ระหว่าง 0 ถึง VCC")

    return BiasInput(
        vcc_v=values["vcc"],
        r1_kohm=values["r1"],
        r2_kohm=values["r2"],
        rc_kohm=values["rc"],
        re_kohm=values["re"],
        beta=values["beta"],
        vbe_v=values["vbe"],
    )


def _require_positive(values: Mapping[str, float], field: str) -> None:
    if values[field] <= 0:
        raise ValidationError(
            field, f"{FIELD_LABELS[field]} ต้องมากกว่า 0 {RESISTOR_UNIT}"
            if field != "vcc" else "VCC ต้องมากกว่า 0 V"
        )


def _validate_common(values: Mapping[str, float]) -> None:
    """Rules shared by every bias mode: VCC, beta and VBE."""
    if values["vcc"] <= 0:
        raise ValidationError("vcc", "VCC ต้องมากกว่า 0 V")
    if values["beta"] <= 0:
        raise ValidationError("beta", "β ต้องมากกว่า 0")
    if not 0 <= values["vbe"] < values["vcc"]:
        raise ValidationError("vbe", "VBE ต้องอยู่ระหว่าง 0 ถึง VCC")


def _read(form: Mapping[str, str], fields: tuple[str, ...]) -> dict[str, float]:
    return {field: _parse_float(form, field) for field in fields}


def parse_fixed(form: Mapping[str, str]) -> FixedInput:
    """Fixed bias only needs VCC, RB, RC, beta and VBE."""
    values = _read(form, ("vcc", "rb", "rc", "beta", "vbe"))
    _validate_common(values)
    for field in ("rb", "rc"):
        _require_positive(values, field)

    return FixedInput(
        vcc_v=values["vcc"],
        rb_kohm=values["rb"],
        rc_kohm=values["rc"],
        beta=values["beta"],
        vbe_v=values["vbe"],
    )


def parse_emitter(form: Mapping[str, str]) -> EmitterInput:
    """Emitter bias adds RE to the fixed-bias field set."""
    values = _read(form, ("vcc", "rb", "rc", "re", "beta", "vbe"))
    _validate_common(values)
    for field in ("rb", "rc", "re"):
        _require_positive(values, field)

    return EmitterInput(
        vcc_v=values["vcc"],
        rb_kohm=values["rb"],
        rc_kohm=values["rc"],
        re_kohm=values["re"],
        beta=values["beta"],
        vbe_v=values["vbe"],
    )
