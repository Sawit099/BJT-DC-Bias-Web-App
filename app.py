"""Flask web layer for the BJT DC bias calculator.

Routes only: parsing and physics live in :mod:`dc_bias`.
"""

from flask import Flask, render_template, request

from dc_bias import ValidationError, calculate, parse_inputs

DEFAULTS = {
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1",
    "beta": "100",
    "vbe": "0.70",
}

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html", form=DEFAULTS, result=None, errors={})


@app.post("/")
def calculate_view():
    try:
        bias = parse_inputs(request.form)
    except ValidationError as exc:
        return render_template(
            "index.html",
            form=request.form,
            result=None,
            errors={exc.field: exc.message},
        )

    return render_template(
        "index.html",
        form=request.form,
        result=calculate(bias),
        errors={},
    )
