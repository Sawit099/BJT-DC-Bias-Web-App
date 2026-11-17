"""Flask web layer for the multi-mode BJT DC bias calculator.

Routes only: parsing and physics live in :mod:`dc_bias`.
"""

import os

from flask import Flask, render_template, request

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


if __name__ == "__main__":
    # `python app.py` must also work: students often launch the file directly
    # instead of `python -m flask --app app run`. Set PORT to avoid a busy 5000.
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "5000")),
        debug=True,
    )
