"""DC bias calculations for a BJT common-emitter voltage-divider bias circuit.

This module is pure engineering logic: it does not know about HTTP, HTML or
Flask. All resistances arrive in kOhm and are converted to Ohm internally;
every value in :class:`BiasResult` is an SI unit (V, A, Ohm).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

import math

VCE_SAT_V = 0.3

WARNING_CUTOFF = (
    "VTH ต่ำกว่าหรือเท่ากับ VBE ทำให้ IB ที่คำนวณได้ติดลบ — transistor อยู่ในช่วง "
    "cutoff และแบบจำลอง forward-active ใช้ไม่ได้กับผลชุดนี้"
)
WARNING_SATURATION = (
    "VCE ต่ำกว่า 0.3 V (VCE,sat) — transistor อยู่ในช่วงอิ่มตัว (saturation) "
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
class BiasResult:
    vth_v: float
    rth_ohm: float
    ib_a: float
    ic_a: float
    ie_a: float
    ve_v: float
    vb_v: float
    vc_v: float
    vce_v: float
    region: Region
    warning: str | None


def calculate(bias: BiasInput) -> BiasResult:
    r1 = bias.r1_kohm * 1000.0
    r2 = bias.r2_kohm * 1000.0
    rc = bias.rc_kohm * 1000.0
    re = bias.re_kohm * 1000.0

    vth = bias.vcc_v * r2 / (r1 + r2)
    rth = r1 * r2 / (r1 + r2)

    ib = (vth - bias.vbe_v) / (rth + (bias.beta + 1.0) * re)
    ic = bias.beta * ib
    ie = (bias.beta + 1.0) * ib

    ve = ie * re
    vb = ve + bias.vbe_v
    vc = bias.vcc_v - ic * rc
    vce = vc - ve

    if vth <= bias.vbe_v:
        region = Region.CUTOFF
        warning = WARNING_CUTOFF
    elif vce < VCE_SAT_V:
        region = Region.SATURATION
        warning = WARNING_SATURATION
    else:
        region = Region.ACTIVE
        warning = None

    return BiasResult(
        vth_v=vth,
        rth_ohm=rth,
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


FIELD_LABELS = {
    "vcc": "VCC [V]",
    "r1": "R1 [kΩ]",
    "r2": "R2 [kΩ]",
    "rc": "RC [kΩ]",
    "re": "RE [kΩ]",
    "beta": "β",
    "vbe": "VBE [V]",
}


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
    values = {field: _parse_float(form, field) for field in FIELD_LABELS}

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
