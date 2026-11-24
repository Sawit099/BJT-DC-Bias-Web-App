# Lab 04 — BJT CE Amplifier Simulator v1 Design

**Date:** 2026-11-24  
**Status:** Approved by user ("ไปเลย")  
**Spec source:** `C:\Users\b6829643\Downloads\Lab04_BJT_Amplifier_Simulator_2-2569.html`

## Intent

Extend the existing Lab 03 Flask BJT DC Bias web app into a minimal working Common-Emitter Amplifier Simulator v1. Preserve all three Lab 03 analytical DC bias modes and their tests. Add real ngspice simulation for one reference CE voltage-divider circuit: `.op`, `.ac`, `.tran`, with real charts, clear provenance, and browser acceptance evidence.

## Goals

- Keep Lab 03 DC bias modes (divider/fixed/emitter) working unchanged.
- Add a CE Voltage Divider SPICE analysis flow using real ngspice batch runs.
- Show DC operating point from ngspice (`.op`), Bode magnitude/phase (`.ac`), and Vin/Vout waveform (`.tran`).
- Expose amplitude/frequency source inputs; show units, run status, engine/model provenance.
- Distinguish analytical reference (`dc_bias.py`) from SPICE outputs.
- Handle ngspice missing/errors/timeout/invalid input without fake success or stale plots.
- Record B1–B8 validation evidence and update README for reproducibility.

## Non-goals

- Drag-drop circuit editor, arbitrary circuit topology, AC for every bias mode.
- FETs, custom SPICE solver, animated circuit overlay, deployment.
- Writing unittest/Playwright scripts by hand as a required deliverable (tests may be added by agent where useful).

## Key Decisions (approved defaults)

| Decision | Call | Rationale |
|---|---|---|
| ngspice availability | Use installed ngspice 47 at `C:\Users\b6829643\AppData\Local\Tools\ngspice\Spice64\bin\ngspice_con.exe`; adapter also discovers `NGSPICE_EXE`, PATH, common Windows locations | Machine had no ngspice; installed portable 47 and verified batch mode. |
| Starter kit | None found; build transparent `spice_engine.py` adapter | Handout allows instructor starter kit if present; none present. |
| BJT model | Explicit NPN model named `Q2N3904_LAB04` with documented parameters in code/README | No starter kit model specified; must not guess silently. |
| Charting | Vendor `Chart.js` UMD in `static/chart.umd.min.js` (single file, no pip dep) | Bode log axis + waveform readable; no CDN/runtime dep. |
| UI structure | Extend existing single-page app: keep Lab 03 bias form; add CE Amplifier (ngspice) section for divider reference with analysis tabs/mode and results/plots | Preserves Lab 3 UX, keeps one Flask app. |
| Netlist/output | Per-run temp working dir; write `circuit.cir`, capture stdout/log, parse deterministic output files/printed values; no `shell=True` | Reproducible and safe. |

## Architecture / Files

- `dc_bias.py` — unchanged analytical calculations.
- `spice_engine.py` — new: input validation, netlist generation, ngspice discovery/run, parsing `.op/.ac/.tran`, typed result/errors.
- `app.py` — add routes/handlers for SPICE run (POST), keep existing bias routes; return structured JSON or render with SPICE result.
- `templates/index.html` — keep Lab 03 form/results; add CE amplifier controls (VCC,R1,R2,RC,RE,RL,Cin,Cout,Vamp,freq, analysis mode) and result panels/charts.
- `static/style.css` — extend for simulator layout, status, charts, responsive.
- `static/app.js` — chart rendering, form submit UX, stale-result clearing; no physics calculations.
- `static/chart.umd.min.js` — vendored Chart.js.
- `tests/test_dc_bias.py`, `tests/test_web.py` — keep passing; add/adjust tests only where compatible and useful.
- `docs/validation.md` — add Lab 04 B1–B8 table and evidence.
- `README.md` — ngspice install/path, run steps, model/provenance, Lab 04 notes.

## Verification

- `python -m unittest discover -s tests -v` green (existing + any added).
- Manual/Playwright B1–B8 recorded honestly.
- ngspice log/output evidence retained or reproducible; no fabricated plots.
- Git diff checked before commit; no `.venv/.env/secrets/large temp run files`.
