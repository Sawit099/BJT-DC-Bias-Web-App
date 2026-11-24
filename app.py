"""Flask web layer for the multi-mode BJT DC bias calculator.

Routes only: parsing and physics live in :mod:`dc_bias`.
"""

import math
import os

from flask import Flask, jsonify, render_template, request

import spice_engine
from dc_bias import (
    ValidationError,
    calculate,
    calculate_emitter,
    calculate_fixed,
    parse_emitter,
    parse_fixed,
    parse_inputs,
)

MODE_LABELS = {
    "divider": "Voltage Divider Bias",
    "fixed": "Fixed Bias",
    "emitter": "Emitter Bias",
}

DEFAULTS = {
    "vcc": "12",
    "beta": "100",
    "vbe": "0.70",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1",
    "rb": "1000",
}

app = Flask(__name__)


def _unknown_mode_error(mode: str) -> dict[str, str]:
    return {
        "mode": (
            f'ไม่รู้จักโหมดวงจร "{mode}" — เลือกได้เฉพาะ Voltage Divider Bias, '
            "Fixed Bias หรือ Emitter Bias"
        )
    }


def _render(mode: str, form, result=None, errors=None, error_mode=None):
    return render_template(
        "index.html",
        mode=mode,
        modes=MODE_LABELS,
        error_mode=error_mode or MODE_LABELS[mode],
        form=form,
        result=result,
        errors=errors or {},
    )


@app.get("/")
def index():
    mode = (request.args.get("mode") or "divider").strip()
    if mode not in MODE_LABELS:
        return _render(
            "divider", DEFAULTS,
            errors=_unknown_mode_error(mode),
            error_mode=f'"{mode}"',
        )
    return _render(mode, DEFAULTS)


@app.post("/")
def calculate_view():
    # A missing mode keeps the Lab 2 behaviour; an unknown mode is an error.
    mode = (request.form.get("mode") or "divider").strip()
    if mode not in MODE_LABELS:
        return _render(
            "divider", request.form,
            errors=_unknown_mode_error(mode),
            error_mode=f'"{mode}"',
        )

    try:
        if mode == "fixed":
            result = calculate_fixed(parse_fixed(request.form))
        elif mode == "emitter":
            result = calculate_emitter(parse_emitter(request.form))
        else:
            result = calculate(parse_inputs(request.form))
    except ValidationError as exc:
        return _render(mode, request.form, errors={exc.field: exc.message})

    return _render(mode, request.form, result=result.as_dict())


def _sim_payload() -> dict:
    data = request.get_json(silent=True)
    if isinstance(data, dict):
        return data
    return request.form.to_dict()


def _sim_float(payload: dict, key: str, label: str) -> float:
    raw = payload.get(key)
    if raw is None or str(raw).strip() == "":
        raise spice_engine.NgspiceError(f"{label} ต้องไม่เว้นว่าง")
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise spice_engine.NgspiceError(f"{label} ต้องเป็นตัวเลข") from exc
    if not math.isfinite(value):
        raise spice_engine.NgspiceError(f"{label} ต้องเป็นตัวเลขที่จำกัด (finite)")
    return value


@app.post("/api/simulate")
def simulate_view():
    payload = _sim_payload()
    analysis = str(payload.get("analysis", "op")).strip().lower()
    if analysis not in {"op", "ac", "tran"}:
        return jsonify(
            {
                "ok": False,
                "analysis": analysis,
                "engine": "ngspice",
                "model": spice_engine.DEFAULT_MODEL_NAME,
                "error": "analysis ต้องเป็น op, ac หรือ tran",
            }
        )

    try:
        inp = spice_engine.CEInput(
            vcc=_sim_float(payload, "vcc", "VCC"),
            r1k=_sim_float(payload, "r1", "R1"),
            r2k=_sim_float(payload, "r2", "R2"),
            rck=_sim_float(payload, "rc", "RC"),
            rek=_sim_float(payload, "re", "RE"),
            rlk=_sim_float(payload, "rl", "RL"),
            cin_u=_sim_float(payload, "cin", "Cin"),
            cout_u=_sim_float(payload, "cout", "Cout"),
            vin_mvp=_sim_float(payload, "amp", "Amplitude"),
            freq_hz=_sim_float(payload, "freq", "Frequency"),
        )
        inp.validate()
        if analysis == "op":
            result = spice_engine.run_op(inp)
        elif analysis == "ac":
            result = spice_engine.run_ac(inp)
        else:
            result = spice_engine.run_tran(inp)
        return jsonify(
            {
                "ok": True,
                "analysis": analysis,
                "engine": result.engine,
                "model": result.model,
                "run_id": result.run_id,
                analysis: result.as_dict(),
            }
        )
    except spice_engine.NgspiceError as exc:
        return jsonify(
            {
                "ok": False,
                "analysis": analysis,
                "engine": "ngspice",
                "model": spice_engine.DEFAULT_MODEL_NAME,
                "error": str(exc),
            }
        )


if __name__ == "__main__":
    # `python app.py` must also work: students often launch the file directly
    # instead of `python -m flask --app app run`. Set PORT to avoid a busy 5000.
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "5000")),
        debug=True,
    )
