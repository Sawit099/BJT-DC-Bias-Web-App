# Lab 04 BJT CE Amplifier Simulator v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the Lab 03 Flask BJT DC bias app with a real ngspice-backed CE voltage-divider amplifier simulator (`.op/.ac/.tran`) while preserving all three existing analytical bias modes.

**Architecture:** Keep `dc_bias.py` as the untouched analytical reference. Add `spice_engine.py` as a subprocess adapter that builds a CE netlist, runs `ngspice_con -b`, and parses deterministic output files. Flask exposes a SPICE simulation endpoint; the template/JS render status, provenance, tables, and Chart.js plots from real run data.

**Tech Stack:** Python 3 / Flask / unittest, ngspice 47 batch (`ngspice_con.exe -b`), Chart.js 4.4.1 UMD (vendored static), vanilla JS.

**Spec:** `docs/superpowers/specs/2026-11-24-lab04-bjt-amplifier-simulator-design.md` (implementing Lab 04 handout at `C:\Users\b6829643\Downloads\Lab04_BJT_Amplifier_Simulator_2-2569.html`)

## Global Constraints

- Preserve Lab 03 behavior: divider/fixed/emitter analytical modes, existing 38 tests, `dc_bias.py` physics unchanged.
- ngspice is an external process: `subprocess.run([...], shell=False, timeout=..., cwd=run_dir, capture_output=True, text=True)`.
- No fabricated/hard-coded simulation results. Errors/timeouts/missing engine must not return stale graphs with success status.
- Distinguish analytical reference vs SPICE output in UI and docs; show engine/model/provenance.
- BJT model is explicitly named `Q2N3904_LAB04` with parameters declared in netlist/code and documented in README.
- No `.venv/`, `.env`, keys/tokens, or large temp run files in git. Chart.js vendored as one static file (no pip dep).

## Review Focus

- **Stale result after failed run:** changing input then causing ngspice failure must clear old SPICE charts/table and show error status, not old success.
- **Missing ngspice:** when engine not found, UI/API reports actionable error (include checked path/env hint) and no fake data.
- **Unit/provenance confusion:** SPICE `.op` values and analytical Lab 3 values are labeled separately; AC gain is dB magnitude `vdb(out)` and phase degrees `vp(out)` with frequency axis.
- **Input validation bypass:** RE=0, negative/NaN/huge freq or amplitude rejected before netlist/run; no user text interpolated unsafely into command args.
- **Lab 3 regression:** fixed/emitter/divider POST still returns expected values and error-mode labels after UI refactor.

## File Structure

| File | Responsibility |
|---|---|
| `spice_engine.py` | CE netlist builder, ngspice discovery, batch run, parse `.op/.ac/.tran`, typed dataclasses/errors. |
| `app.py` | Existing bias routes + new `POST /api/simulate` JSON endpoint for SPICE. |
| `templates/index.html` | Lab 03 bias UI + CE Amplifier Simulator section, canvases, status/provenance. |
| `static/app.js` | Fetch simulation API, render Chart.js plots, clear stale state, display errors. |
| `static/style.css` | Layout/responsive/status/chart styling. |
| `static/chart.umd.min.js` | Vendored Chart.js 4.4.1 (already downloaded). |
| `tests/test_spice_engine.py` | Engine unit/integration tests (skip if ngspice unavailable for real-run tests). |
| `tests/test_web.py` | Keep existing; add SPICE endpoint/error/regression assertions. |
| `docs/validation.md` | Append Lab 04 B1–B8 with real observed evidence. |
| `README.md` | Lab 04 setup/run/provenance/checklist. |

---

### Task 1: Spice engine scaffold and ngspice discovery

**Files:**
- Create: `spice_engine.py`
- Create: `tests/test_spice_engine.py`

**Interfaces:**
- Produces: `NgspiceError(RuntimeError)`, `NgspiceNotFoundError(NgspiceError)`, `find_ngspice() -> str`, `DEFAULT_MODEL_NAME = "Q2N3904_LAB04"`, `DEFAULT_MODEL_CARD` (string `.model ...`).

- [ ] **Step 1: Write the failing tests**

```python
import os, unittest
from unittest import mock
import spice_engine as se

class TestNgspiceDiscovery(unittest.TestCase):
    def test_default_model_name_constant(self):
        self.assertEqual(se.DEFAULT_MODEL_NAME, "Q2N3904_LAB04")
        self.assertIn(".model Q2N3904_LAB04 NPN", se.DEFAULT_MODEL_CARD)

    def test_find_ngspice_uses_env_override(self):
        with mock.patch.dict(os.environ, {"NGSPICE_EXE": __file__}):
            self.assertEqual(se.find_ngspice(), os.path.abspath(__file__))

    def test_find_ngspice_raises_when_missing(self):
        with mock.patch.dict(os.environ, {"NGSPICE_EXE": ""}, clear=False):
            with mock.patch("spice_engine.shutil.which", return_value=None):
                with mock.patch("spice_engine.os.path.isfile", return_value=False):
                    with self.assertRaises(se.NgspiceNotFoundError):
                        se.find_ngspice()
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m unittest tests.test_spice_engine -v`  
Expected: FAIL with import/module attribute errors.

- [ ] **Step 3: Implement minimal discovery in `spice_engine.py`**

Implement `NgspiceError`, `NgspiceNotFoundError`, constants, and `find_ngspice()` checking `NGSPICE_EXE` (if file), `shutil.which("ngspice_con")/("ngspice")`, then common Windows paths including `C:\Users\b6829643\AppData\Local\Tools\ngspice\Spice64\bin\ngspice_con.exe`. Return absolute path or raise `NgspiceNotFoundError` with checked locations.

- [ ] **Step 4: Run test to verify pass**

Run: `python -m unittest tests.test_spice_engine -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add spice_engine.py tests/test_spice_engine.py
git commit -m "feat: add ngspice discovery scaffold"
```

### Task 2: CE netlist builder and .op run/parse

**Files:**
- Modify: `spice_engine.py`
- Modify: `tests/test_spice_engine.py`

**Interfaces:**
- Consumes: Task 1 discovery/constants.
- Produces: `CEInput` dataclass, `OpResult` dataclass, `build_ce_netlist(inp: CEInput, analysis: str) -> str`, `run_op(inp: CEInput) -> OpResult`.

- [ ] **Step 1: Write failing tests**

```python
@unittest.skipUnless(se.ngspice_available(), "ngspice not installed")
class TestOpRun(unittest.TestCase):
    def test_run_op_reference_values(self):
        inp = se.CEInput(vcc=12, r1k=100, r2k=22, rck=2.2, rek=1.0, rlk=10, cin_u=10, cout_u=10, vin_mvp=10, freq_hz=1000)
        r = se.run_op(inp)
        self.assertEqual(r.engine, "ngspice")
        self.assertEqual(r.model, "Q2N3904_LAB04")
        self.assertAlmostEqual(r.vb, 2.05, delta=0.15)
        self.assertAlmostEqual(r.ve, 1.38, delta=0.15)
        self.assertAlmostEqual(r.vc, 8.98, delta=0.25)
        self.assertAlmostEqual(r.vce, 7.60, delta=0.25)
        self.assertTrue(r.ic_ma > 0)

    def test_invalid_rejected_before_run(self):
        with self.assertRaises(se.NgspiceError):
            se.CEInput(vcc=12, r1k=100, r2k=22, rck=2.2, rek=0, rlk=10, cin_u=10, cout_u=10, vin_mvp=10, freq_hz=1000).validate()
```

Add `ngspice_available()` helper returning True/False via `find_ngspice`.

- [ ] **Step 2: Run to verify failure**

Run: `python -m unittest tests.test_spice_engine -v`  
Expected: FAIL (missing CEInput/run_op).

- [ ] **Step 3: Implement netlist + .op**

`CEInput` fields: `vcc,r1k,r2k,rck,rek,rlk,cin_u,cout_u,vin_mvp,freq_hz` (floats). `validate()` rejects non-finite/non-positive where required, freq<=0, amplitude<0, caps<=0. `build_ce_netlist` emits nodes `vcc b c e in out 0`, components with k/u units, `Vin ... DC 0 AC 1 SIN(0 {vin_mvp}m {freq_hz})`, Q1 using `DEFAULT_MODEL_NAME`, `.control ... op; print v(b) v(e) v(c) v(c,e) i(vcc); quit; .endc .end`. `run_op` creates temp dir, writes `ce.cir`, runs ngspice, parses log for `v(b)=...` etc; `ic_ma = abs(i(vcc))*1000`. Raise `NgspiceError` on nonzero exit/timeout/missing parse.

- [ ] **Step 4: Run test to verify pass**

Run: `python -m unittest tests.test_spice_engine -v`  
Expected: PASS (or skip only if ngspice absent).

- [ ] **Step 5: Commit**

```bash
git add spice_engine.py tests/test_spice_engine.py
git commit -m "feat: add CE netlist builder and ngspice op run"
```

### Task 3: AC analysis parse

**Files:**
- Modify: `spice_engine.py`
- Modify: `tests/test_spice_engine.py`

**Interfaces:**
- Produces: `AcResult(freq_hz:list[float], gain_db:list[float], phase_deg:list[float], engine, model, run_id)`, `run_ac(inp: CEInput, fstart=10, fstop=1_000_000, points=20) -> AcResult`.

- [ ] **Step 1: Write failing test**

```python
@unittest.skipUnless(se.ngspice_available(), "ngspice not installed")
class TestAcRun(unittest.TestCase):
    def test_ac_returns_bode_data(self):
        inp = se.CEInput(12,100,22,2.2,1,10,10,10,10,1000)
        r = se.run_ac(inp)
        self.assertGreater(len(r.freq_hz), 50)
        self.assertEqual(len(r.freq_hz), len(r.gain_db))
        self.assertEqual(len(r.phase_deg), len(r.gain_db))
        self.assertTrue(any(f >= 900 and f <= 1100 for f in r.freq_hz))
        self.assertTrue(any(g > 0 for g in r.gain_db))
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m unittest tests.test_spice_engine.TestAcRun -v`  
Expected: FAIL.

- [ ] **Step 3: Implement `.ac dec` + `wrdata ac.txt vdb(out) vp(out)`**

Use control block `ac dec {points} {fstart} {fstop}`. Parse wrdata pairs: columns `(freq,gain,freq2,phase)`; validate lengths equal and numeric. Return `AcResult`.

- [ ] **Step 4: Run test to verify pass**

Run: `python -m unittest tests.test_spice_engine -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add spice_engine.py tests/test_spice_engine.py
git commit -m "feat: add ngspice ac bode parsing"
```

### Task 4: Transient analysis parse

**Files:**
- Modify: `spice_engine.py`
- Modify: `tests/test_spice_engine.py`

**Interfaces:**
- Produces: `TranResult(time_ms:list[float], vin_v:list[float], vout_v:list[float], engine, model, run_id)`, `run_tran(inp: CEInput) -> TranResult`.

- [ ] **Step 1: Write failing test**

```python
@unittest.skipUnless(se.ngspice_available(), "ngspice not installed")
class TestTranRun(unittest.TestCase):
    def test_tran_returns_waveforms(self):
        inp = se.CEInput(12,100,22,2.2,1,10,10,10,10,1000)
        r = se.run_tran(inp)
        self.assertEqual(len(r.time_ms), len(r.vin_v))
        self.assertEqual(len(r.vout_v), len(r.vin_v))
        self.assertGreater(max(r.time_ms), 2.0)
        self.assertGreater(max(abs(v) for v in r.vin_v), 0.005)
        self.assertGreater(max(abs(v) for v in r.vout_v), 0.01)
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m unittest tests.test_spice_engine.TestTranRun -v`  
Expected: FAIL.

- [ ] **Step 3: Implement `.tran` + `wrdata tran.txt v(in) v(out)`**

Use step `max(1u, 1/(freq_hz*200))`, stop `max(5/freq_hz, 5m)`. Parse wrdata pairs into `time_ms = time_s*1000`, `vin_v`, `vout_v`. Return `TranResult`.

- [ ] **Step 4: Run test to verify pass**

Run: `python -m unittest tests.test_spice_engine -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add spice_engine.py tests/test_spice_engine.py
git commit -m "feat: add ngspice transient parsing"
```

### Task 5: Flask SPICE API endpoint

**Files:**
- Modify: `app.py`
- Modify: `tests/test_web.py`

**Interfaces:**
- Consumes: `spice_engine.CEInput/run_op/run_ac/run_tran/NgspiceError`.
- Produces: `POST /api/simulate` JSON: `{ok, analysis, engine, model, run_id, op|ac|tran, error}`.

- [ ] **Step 1: Write failing tests**

Add to `tests/test_web.py`:

```python
class TestSpiceApi(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.payload = {"analysis":"op","vcc":"12","r1":"100","r2":"22","rc":"2.2","re":"1","rl":"10","cin":"10","cout":"10","amp":"10","freq":"1000"}

    def test_invalid_re_returns_ok_false(self):
        res = self.client.post("/api/simulate", json={**self.payload, "re":"0"})
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertFalse(data["ok"])
        self.assertIn("RE", data["error"])

    def test_missing_ngspice_reports_error(self):
        with mock.patch("app.spice_engine.find_ngspice", side_effect=app.spice_engine.NgspiceNotFoundError("not found")):
            res = self.client.post("/api/simulate", json=self.payload)
        self.assertFalse(res.get_json()["ok"])
```

Add `from unittest import mock` and `import spice_engine` as needed.

- [ ] **Step 2: Run to verify failure**

Run: `python -m unittest tests.test_web.TestSpiceApi -v`  
Expected: FAIL (404/no endpoint).

- [ ] **Step 3: Implement endpoint in `app.py`**

Parse JSON/form, validate required numeric fields, map to `CEInput` (`r*` in kΩ, cin/cout µF, amp mV peak). `analysis` in `{op,ac,tran}` else error. Call engine; catch `NgspiceError` -> `{ok:false,error:str(e)}`. Success returns typed dict with `engine:"ngspice"`, `model`.

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_web -v`  
Expected: PASS including existing Lab 03 tests.

- [ ] **Step 5: Commit**

```bash
git add app.py tests/test_web.py
git commit -m "feat: add spice simulation API endpoint"
```

### Task 6: UI layout for CE amplifier and charts

**Files:**
- Modify: `templates/index.html`
- Modify: `static/style.css`

**Interfaces:**
- Consumes: existing Lab 3 form context and `/api/simulate` contract.
- Produces: CE simulator section with inputs (`r1,r2,rc,re,rl,cin,cout,amp,freq`), analysis selector op/ac/tran, Run button, status box, SPICE DC table, two canvases (`acChart`, `tranChart`), provenance labels.

- [ ] **Step 1: Write failing web assertions**

Add to `tests/test_web.py`:

```python
class TestSimulatorUi(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_has_simulator_section(self):
        body = self.client.get("/").get_data(as_text=True)
        for token in ["CE Amplifier", "ngspice", "amp", "freq", "acChart", "tranChart", "Run Simulation"]:
            self.assertIn(token, body)

    def test_chartjs_script_included(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn("chart.umd.min.js", body)
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m unittest tests.test_web.TestSimulatorUi -v`  
Expected: FAIL.

- [ ] **Step 3: Implement template/CSS**

Add a section below Lab 3 results with clearly labeled "CE Voltage Divider (ngspice)" controls and analysis mode; keep Lab 3 form unchanged. Add status/provenance area (`data-source="ngspice"` text). Add canvases and result table placeholders. Style responsive two-column on desktop, stacked on mobile; no hidden overflow for charts.

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_web -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add templates/index.html static/style.css tests/test_web.py
git commit -m "feat: add CE amplifier simulator UI shell"
```

### Task 7: Frontend simulation JS and Chart rendering

**Files:**
- Create: `static/app.js`
- Modify: `templates/index.html` (script include)

**Interfaces:**
- Consumes: `/api/simulate` JSON.
- Produces: `runSimulation()` fetch, renders op table, Bode (log freq axis, dB/deg datasets), transient (time ms, Vin/Vout), clears stale charts on new run/error.

- [ ] **Step 1: Write failing source/behavior assertions**

Add tests in `tests/test_web.py`:

```python
def test_app_js_has_no_fake_data(self):
    src = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    self.assertIn("fetch('/api/simulate'", src)
    self.assertIn("clearResults", src)
    self.assertNotIn("hardcoded", src.lower())
```

(Behavior verified by browser acceptance; keep unit tests light.)

- [ ] **Step 2: Run to verify failure**

Run: `python -m unittest tests.test_web.TestSimulatorUi -v` (or new test class)  
Expected: FAIL if assertion added.

- [ ] **Step 3: Implement `static/app.js`**

On submit/click: set status Running, clear previous SPICE table/charts/errors; `fetch('/api/simulate', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)})`. On `ok:false` show error, keep charts cleared. On success render by analysis: op table; ac Chart.js with logarithmic x-axis label "Frequency (Hz)", y axes Gain (dB)/Phase (deg); tran Chart.js with Time (ms), Vin/Vout (V). Destroy previous Chart instances before re-render.

- [ ] **Step 4: Run tests**

Run: `python -m unittest discover -s tests -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add static/app.js templates/index.html tests/test_web.py
git commit -m "feat: render ngspice results with Chart.js"
```

### Task 8: Validation docs, README, and browser acceptance evidence

**Files:**
- Modify: `docs/validation.md`
- Modify: `README.md`
- Modify: `.gitignore` (only if needed; do not ignore evidence images)

**Interfaces:**
- Consumes: working app + Playwright MCP/browser tools.
- Produces: B1–B8 table with real observed values, method, evidence; README ngspice setup/run/provenance.

- [ ] **Step 1: Write failing doc checks (lightweight)**

```python
class TestLab04Docs(unittest.TestCase):
    def test_readme_mentions_ngspice_and_b1_b8(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for token in ["ngspice", "B1", "B8", "Q2N3904_LAB04"]:
            self.assertIn(token, text)
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m unittest tests.test_web.TestLab04Docs -v`  
Expected: FAIL.

- [ ] **Step 3: Run real browser acceptance and record evidence**

Start Flask app, use Playwright MCP to execute B1–B8. Capture screenshots in `docs/evidence/`. Record observed values/units/status honestly in `docs/validation.md`. If a case cannot run, mark NOT RUN with reason.

- [ ] **Step 4: Update README and docs**

Document ngspice install/path/env var, `python app.py`/flask run, B1–B8, model provenance, AI/student responsibility. Run: `python -m unittest discover -s tests -v`.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/validation.md docs/evidence tests/test_web.py .gitignore
git commit -m "docs: add Lab 04 validation evidence and setup"
```

## Final Verification

- [ ] `python -m unittest discover -s tests -v` — all pass.
- [ ] `git status --short` clean except intended files; no `.venv/.env/large temp`.
- [ ] Manual smoke: `python app.py` serves page; Lab 3 modes still work; SPICE op/ac/tran produce real charts.
- [ ] Push branch/commits as requested.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-11-24-lab04-bjt-amplifier-simulator.md`. Please review the plan. Which execution approach would you prefer?

- **Subagent-driven** - A fresh subagent implements each task and a fresh reviewer checks it before the next one starts, then a whole-branch review at the end. Most thorough; costs a fresh context per task and per review.
- **Native** - I implement every task myself in this session, the way this harness runs work, then one fresh reviewer on the most capable model checks the whole branch. Cheapest and fastest; no independent review until the end. Runs well with a mid-tier session model, since the plan carries the design.

**For this plan I recommend Native, because the tasks are tightly coupled around one UI/app and share the same ngspice engine contracts, so doing them in one session with frequent test runs will be faster and less coordination-heavy than per-task subagent handoffs.** Does the plan capture what you want, and which approach should we use?