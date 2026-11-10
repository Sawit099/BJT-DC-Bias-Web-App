# BJT DC Bias Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** สร้าง Flask Web App หลายไฟล์ที่รับค่า VCC, R1, R2, RC, RE, β, VBE แล้วคำนวณ DC operating point ของ BJT Common-Emitter Voltage-Divider Bias ด้วย Python พร้อม validation, region warning และ automated tests

**Architecture:** แยก 3 ชั้นชัดเจน — `dc_bias.py` (สมการ + validation, ไม่รู้จัก Flask/HTML) → `app.py` (route `GET /` และ `POST /`, แปลงผลเป็น response) → `templates/index.html` + `static/style.css` (แสดงผลเท่านั้น ไม่มีสมการ). ผลลัพธ์ส่งต่อเป็น `BiasResult` dataclass ที่เป็น SI units

**Tech Stack:** Python 3.15.2, Flask (>=3.1), Jinja2, `unittest` (ไม่ใช้ pytest)

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-dc-bias-web-app-design.md`

## Global Constraints

- Python 3.15.2; ติดตั้ง dependency ผ่าน `python -m pip install -r requirements.txt`
- ใช้ `unittest` เท่านั้น — รันด้วย `python -m unittest discover -s tests -v`
- Route: `GET /` แสดงฟอร์ม, `POST /` คำนวณแล้ว render template เดิม (ไม่มี `/calculate`, ไม่มี redirect, ไม่มี session)
- อินพุตความต้านทานเป็น **kΩ** แปลง ×1000 เป็น Ω ภายใน `dc_bias.py`; `BiasResult` เก็บ SI units (V, A, Ω)
- เกณฑ์ region: `VTH ≤ VBE` → `CUTOFF`; `VCE < 0.3` → `SATURATION`; นอกนั้น `ACTIVE`
- **ห้าม clamp หรือแทนค่าด้วย 0/—** เมื่อ region ≠ ACTIVE — แสดงค่าดิบทั้งหมดพร้อม marking
- `dc_bias.py` ห้าม import Flask, `jinja2`, หรือ `werkzeug`
- `templates/index.html` ห้ามมีสูตรคำนวณหรือตัวเลขผลลัพธ์ฝังอยู่
- UI labels และข้อความ error/warning เป็นภาษาไทย; ชื่อปริมาณเป็นอังกฤษ (VCC, VCE, IC, β)
- Commit ทำผ่าน **GitHub Desktop เท่านั้น** — ทุก step "Commit" ในแผนนี้คือการหยุดให้ผู้ใช้กดเอง ไม่ใช่ `git commit` จาก shell
- ห้าม commit `.venv/`, `__pycache__/`, `.env`

## Review Focus

สิ่งที่สเปกไม่ได้เขียนไว้แต่ผู้ใช้จริงจะเจอแน่ และต้องมี test รองรับ (ผูกไว้ใน task ที่ดูแลโค้ดส่วนนั้นแล้ว):

1. **POST ที่ขาดฟิลด์ไปเลย** (เช่น client ส่งแค่ `vcc`) → ต้องเห็นข้อความ error ภาษาไทย ไม่ใช่ 500 `BadRequestKeyError` (Task 3)
2. **ช่องว่างหัวท้ายตัวเลข** (`" 12 "`) → ต้อง parse ได้ ไม่ใช่ error (Task 2)
3. **ทศนิยมแบบ comma** (`"2,2"` จากคีย์บอร์ดไทย) → ต้องได้ error ที่อ่านรู้เรื่อง ไม่ใช่ crash (Task 2)
4. **VBE ≥ VCC** → ต้องเป็น error การกรอก ไม่ใช่รายงานเป็น Cutoff (Task 2)
5. **β มหาศาล (1e6)** → ต้องคืนค่าจำกัด (finite) และ region ที่ถูกต้อง ไม่ใช่ overflow/ZeroDivision (Task 2)

---

## File Structure

| ไฟล์ | ความรับผิดชอบ |
|---|---|
| `.gitignore` | กัน `.venv/`, `__pycache__/`, `.env` หลุดเข้า repo |
| `requirements.txt` | Flask เวอร์ชันที่ใช้ |
| `AGENTS.md` | กติกาโค้ดสำหรับ AI/ผู้ร่วมงาน |
| `dc_bias.py` | `Region`, `ValidationError`, `BiasInput`, `BiasResult`, `parse_inputs()`, `calculate()` |
| `tests/test_dc_bias.py` | เทสต์สมการ, region, validation |
| `app.py` | Flask app + 2 route |
| `templates/index.html` | ฟอร์ม + ตารางผล + badge/warning |
| `static/style.css` | layout และ marking `.unreliable` |
| `tests/test_web.py` | เทสต์ HTTP ผ่าน test client |
| `README.md` | วิธีติดตั้ง/รัน/ทดสอบ + สมมติฐาน |
| `docs/design-note.md`, `docs/validation.md`, `docs/reflection.md` | เอกสารส่งงาน |

---

### Task 1: Project scaffold

**Files:**
- Create: `.gitignore`
- Create: `requirements.txt`
- Create: `AGENTS.md`

**Interfaces:**
- Consumes: nothing
- Produces: ชุด dependency ที่ Task 2 และ 3 ใช้ (`Flask`), และกฎใน `AGENTS.md` ที่ทุก task ต้องทำตาม

- [ ] **Step 1: สร้าง `.gitignore`**

```
.venv/
__pycache__/
*.py[cod]
.env
.pytest_cache/
```

- [ ] **Step 2: สร้าง `requirements.txt`**

```
Flask>=3.1
```

- [ ] **Step 3: ตรวจว่า dependency ติดตั้งได้**

Run: `python -m pip install -r requirements.txt` แล้ว `python -c "import flask; print(flask.__version__)"`
Expected: พิมพ์เลขเวอร์ชัน 3.x และไม่มี error

- [ ] **Step 4: สร้าง `AGENTS.md`**

เนื้อหาต้องมี 5 ข้อ: แยกชั้น `dc_bias.py` (pure Python) / `app.py` (Flask) / template (แสดงผลเท่านั้น) · ห้าม hardcode ผลคำนวณใน HTML หรือ JS · เทสต์ใช้ `unittest` และต้องมีทั้ง engine test กับ Flask client test · UI และข้อความ error เป็นภาษาไทย · commit ผ่าน GitHub Desktop เท่านั้น

- [ ] **Step 5: Commit (ผู้ใช้กดใน GitHub Desktop)**

Stage: `.gitignore`, `requirements.txt`, `AGENTS.md`, `docs/superpowers/specs/2026-11-10-bjt-dc-bias-web-app-design.md`
Message: `chore: add project scaffold, gitignore and agent conventions`

---

### Task 2: DC bias engineering engine

**Files:**
- Create: `dc_bias.py`
- Create: `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: nothing (pure Python stdlib)
- Produces:
  - `class Region(Enum)` — ค่า `ACTIVE = "active"`, `CUTOFF = "cutoff"`, `SATURATION = "saturation"`
  - `class ValidationError(ValueError)` — constructor `ValidationError(field: str, message: str)`, attributes `.field`, `.message`
  - `@dataclass(frozen=True) class BiasInput` — `vcc_v, r1_kohm, r2_kohm, rc_kohm, re_kohm, beta, vbe_v` (float ทุกตัว)
  - `@dataclass(frozen=True) class BiasResult` — `vth_v, rth_ohm, ib_a, ic_a, ie_a, ve_v, vb_v, vc_v, vce_v` (float), `region: Region`, `warning: str | None`
  - `parse_inputs(form: Mapping[str, str]) -> BiasInput`
  - `calculate(bias: BiasInput) -> BiasResult`

- [ ] **Step 1: เขียนเทสต์ที่ยังไม่ผ่าน — เคสอ้างอิง**

สร้าง `tests/test_dc_bias.py`:

```python
import math
import unittest

from dc_bias import BiasInput, Region, ValidationError, calculate, parse_inputs

REF = BiasInput(vcc_v=12.0, r1_kohm=100.0, r2_kohm=22.0, rc_kohm=2.2,
                re_kohm=1.0, beta=100.0, vbe_v=0.70)
FORM = {"vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
        "re": "1", "beta": "100", "vbe": "0.70"}


class TestReferenceCase(unittest.TestCase):
    def test_reference_case_matches_hand_calculation(self):
        r = calculate(REF)
        self.assertAlmostEqual(r.vth_v, 2.1639, delta=0.0108)
        self.assertAlmostEqual(r.rth_ohm, 18032.8, delta=90.2)
        self.assertAlmostEqual(r.ib_a * 1e6, 12.299, delta=0.0615)
        self.assertAlmostEqual(r.ic_a * 1e3, 1.2299, delta=0.00615)
        self.assertAlmostEqual(r.ie_a * 1e3, 1.2422, delta=0.00621)
        self.assertAlmostEqual(r.ve_v, 1.2422, delta=0.00621)
        self.assertAlmostEqual(r.vb_v, 1.9422, delta=0.00971)
        self.assertAlmostEqual(r.vc_v, 9.2942, delta=0.0465)
        self.assertAlmostEqual(r.vce_v, 8.0520, delta=0.0403)
        self.assertIsNone(r.warning)

    def test_region_is_active_for_reference_case(self):
        self.assertEqual(calculate(REF).region, Region.ACTIVE)
```

- [ ] **Step 2: รันให้เห็นว่า fail**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dc_bias'`

- [ ] **Step 3: สร้าง `dc_bias.py` ให้ผ่าน 2 เทสต์แรก**

สร้าง `Region`, `ValidationError(field, message)`, `BiasInput`, `BiasResult` ตาม Interfaces และฟังก์ชัน `calculate()` ที่ใช้สมการในสเปกข้อ 8 (แปลง kΩ → Ω ด้วย `* 1000`) โดย `warning` เป็น `None` และ `region` ตัดสินด้วย `VTH <= VBE` → CUTOFF, `VCE < 0.3` → SATURATION, นอกนั้น ACTIVE ยังไม่ต้องมีข้อความ warning และยังไม่ต้องมี `parse_inputs()` (ใส่ `raise NotImplementedError` ไว้)

- [ ] **Step 4: รันให้ผ่าน**

Run: `python -m unittest discover -s tests -v`
Expected: PASS 2 tests

- [ ] **Step 5: เขียนเทสต์ที่ยังไม่ผ่าน — cutoff และ saturation**

เพิ่มในไฟล์เดิม:

```python
class TestRegionDetection(unittest.TestCase):
    def test_cutoff_when_vth_not_above_vbe(self):
        r = calculate(BiasInput(12.0, 100.0, 22.0, 2.2, 1.0, 100.0, 3.0))
        self.assertEqual(r.region, Region.CUTOFF)
        self.assertLess(r.ib_a, 0.0)
        self.assertIsNotNone(r.warning)

    def test_saturation_when_vce_below_saturation(self):
        r = calculate(BiasInput(12.0, 100.0, 22.0, 10.0, 1.0, 100.0, 0.70))
        self.assertEqual(r.region, Region.SATURATION)
        self.assertLess(r.vce_v, 0.3)
        self.assertIsNotNone(r.warning)
```

- [ ] **Step 6: รันให้เห็นว่า fail**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL — `warning` เป็น `None` ทั้งสองเคส

- [ ] **Step 7: เติมข้อความ warning**

กำหนดข้อความภาษาไทยคงที่ 2 แบบ — CUTOFF: อธิบายว่า `VTH ≤ VBE` ทำให้ IB ติดลบและ transistor ไม่นำกระแส; SATURATION: อธิบายว่า `VCE` ต่ำกว่า 0.3 V ผลจาก forward-active model ใช้ไม่ได้ ห้ามใช้ค่านี้เป็นคำตอบ

- [ ] **Step 8: รันให้ผ่าน**

Run: `python -m unittest discover -s tests -v`
Expected: PASS 4 tests

- [ ] **Step 9: เขียนเทสต์ที่ยังไม่ผ่าน — kΩ และ validation**

เพิ่มในไฟล์เดิม:

```python
class TestUnitsAndParsing(unittest.TestCase):
    def test_inputs_interpreted_as_kohm(self):
        self.assertAlmostEqual(calculate(REF).rth_ohm, 18032.8, delta=90.2)

    def test_strips_surrounding_whitespace(self):
        parsed = parse_inputs({**FORM, "vcc": " 12 ", "re": " 1 "})
        self.assertAlmostEqual(parsed.vcc_v, 12.0)
        self.assertAlmostEqual(parsed.re_kohm, 1.0)

    def test_rejects_comma_decimal(self):
        with self.assertRaises(ValidationError) as ctx:
            parse_inputs({**FORM, "rc": "2,2"})
        self.assertEqual(ctx.exception.field, "rc")

    def test_rejects_vbe_not_below_vcc(self):
        with self.assertRaises(ValidationError) as ctx:
            parse_inputs({**FORM, "vbe": "12"})
        self.assertEqual(ctx.exception.field, "vbe")


class TestValidation(unittest.TestCase):
    def test_rejects_non_positive_and_non_numeric(self):
        cases = [("vcc", "0"), ("vcc", "-1"), ("r1", "-1"), ("r1", "0"),
                 ("beta", "0"), ("beta", "-5"), ("vcc", "abc"), ("r2", "")]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValidationError) as ctx:
                    parse_inputs({**FORM, field: value})
                self.assertEqual(ctx.exception.field, field)

    def test_huge_beta_stays_finite(self):
        r = calculate(BiasInput(12.0, 100.0, 22.0, 2.2, 1.0, 1e6, 0.70))
        for value in (r.ib_a, r.ic_a, r.ie_a, r.vce_v):
            self.assertTrue(math.isfinite(value))
```

- [ ] **Step 10: รันให้เห็นว่า fail**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL — `NotImplementedError` จาก `parse_inputs`

- [ ] **Step 11: เติม `parse_inputs()`**

อ่านค่าจาก mapping 7 คีย์ (`vcc`, `r1`, `r2`, `rc`, `re`, `beta`, `vbe`), `strip()` ก่อนแปลง `float` (ทศนิยม comma จะได้ `ValueError` → แปลงเป็น `ValidationError(field, "กรุณากรอก … เป็นตัวเลข")`; คีย์ที่หายไปใช้ `form.get(key, "")` ให้ลงเอยที่ error เดียวกัน ไม่ใช่ `KeyError`) แล้วตรวจ: `vcc > 0`, `r1/r2/rc/re > 0`, `beta > 0`, `0 <= vbe < vcc` — ข้อความภาษาไทยตามสเปกข้อ 11

- [ ] **Step 12: รันให้ผ่านทั้งหมด**

Run: `python -m unittest discover -s tests -v`
Expected: PASS 10 tests (0 failures, 0 errors)

- [ ] **Step 13: Commit (ผู้ใช้กดใน GitHub Desktop)**

Stage: `dc_bias.py`, `tests/test_dc_bias.py`
Message: `feat: add DC bias engineering module with unit tests`

---

### Task 3: Flask web layer

**Files:**
- Create: `app.py`
- Create: `templates/index.html`
- Create: `static/style.css`
- Create: `tests/test_web.py`

**Interfaces:**
- Consumes: `parse_inputs()`, `calculate()`, `ValidationError`, `BiasResult`, `Region` จาก Task 2
- Produces: Flask `app` object ที่ `tests/test_web.py` import; template context keys `form`, `result`, `errors`

- [ ] **Step 1: เขียนเทสต์ที่ยังไม่ผ่าน — GET และ POST ที่ถูกต้อง**

สร้าง `tests/test_web.py`:

```python
import unittest

from app import app

FORM = {"vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
        "re": "1", "beta": "100", "vbe": "0.70"}


class TestIndex(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_root_returns_form(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        body = res.get_data(as_text=True)
        for name in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
            self.assertIn(f'name="{name}"', body)

    def test_post_valid_inputs_shows_results(self):
        res = self.client.post("/", data=FORM)
        self.assertEqual(res.status_code, 200)
        body = res.get_data(as_text=True)
        self.assertIn("Active", body)
        self.assertIn("8.05", body)      # VCE [V]
        self.assertIn("1.230", body)     # IC [mA]
```

- [ ] **Step 2: รันให้เห็นว่า fail**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: สร้าง `app.py` + `templates/index.html` + `static/style.css` ให้ผ่าน**

`app.py`: `app = Flask(__name__)`, `@app.get("/")` render `index.html` ด้วย `form=DEFAULTS`, `result=None`, `errors={}` (ค่าเริ่มต้น 12/100/22/2.2/1/100/0.70) · `@app.post("/")` เรียก `parse_inputs(request.form)`; ถ้า `ValidationError` ให้ render พร้อม `errors={exc.field: exc.message}` และ `form=request.form`; ถ้าผ่านให้ `calculate()` แล้ว render พร้อม `result`

`index.html`: ฟอร์ม 7 ช่อง (มี `name` ตรงกับคีย์), ปุ่ม submit, ตารางผล VB/VE/VC/VCE เป็น V และ IC/IB/IE เป็น mA/µA (ทศนิยม 3 ตำแหน่ง), badge ชื่อ region (`Active`/`Cutoff`/`Saturation`), แบนเนอร์ + class `unreliable` เมื่อ region ≠ ACTIVE, แสดง `errors` เหนือฟอร์ม

`style.css`: layout อย่างง่าย ใช้งานได้บนมือถือ, `.unreliable { color: #888; text-decoration: line-through; }`, badge สีต่างกันตาม region

- [ ] **Step 4: รันให้ผ่าน**

Run: `python -m unittest discover -s tests -v`
Expected: PASS 12 tests

- [ ] **Step 5: เขียนเทสต์ที่ยังไม่ผ่าน — ฟิลด์หาย และค่าผิด**

เพิ่มใน `tests/test_web.py`:

```python
class TestInvalidInput(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_missing_field_shows_error_not_500(self):
        res = self.client.post("/", data={"vcc": "12"})
        self.assertEqual(res.status_code, 200)
        self.assertNotIn("Traceback", res.get_data(as_text=True))

    def test_invalid_value_shows_thai_error(self):
        res = self.client.post("/", data={**FORM, "beta": "0"})
        self.assertEqual(res.status_code, 200)
        self.assertIn("β", res.get_data(as_text=True))

    def test_post_without_any_form_data_does_not_crash(self):
        res = self.client.post("/")
        self.assertEqual(res.status_code, 200)
```

- [ ] **Step 6: รันให้เห็นว่า fail**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL — `test_missing_field_shows_error_not_500` ได้ 400/500 จาก `request.form`

- [ ] **Step 7: ทำให้ผ่าน**

ส่ง `request.form` เข้า `parse_inputs` โดยตรงตามสัญญา Task 2 (คีย์ที่หายไปต้องไม่ทำให้เกิด `KeyError`/`BadRequestKeyError`) และให้ template แสดง `errors` เสมอเมื่อไม่มีผลลัพธ์

- [ ] **Step 8: รันให้ผ่านทั้งหมด**

Run: `python -m unittest discover -s tests -v`
Expected: PASS 15 tests (0 failures, 0 errors)

- [ ] **Step 9: ทดลองด้วยมือในเบราว์เซอร์**

Run: `python -m flask --app app run --debug` แล้วเปิด `http://127.0.0.1:5000/`
Expected: เห็นฟอร์ม, กด Calculate ด้วยค่าเริ่มต้น → VCE 8.052 V, IC 1.230 mA, badge Active; ลองใส่ `beta=0` → เห็น error ภาษาไทย ไม่มี traceback

- [ ] **Step 10: Commit (ผู้ใช้กดใน GitHub Desktop)**

Stage: `app.py`, `templates/index.html`, `static/style.css`, `tests/test_web.py`
Message: `feat: add Flask web UI for DC bias calculation`

---

### Task 4: Documentation set

**Files:**
- Create: `README.md`
- Create: `docs/design-note.md`
- Create: `docs/validation.md`
- Create: `docs/reflection.md`

**Interfaces:**
- Consumes: ค่าจริงจาก Task 2–3 (ผลรันเทสต์, ผลในเบราว์เซอร์)
- Produces: nothing (เอกสาร)

- [ ] **Step 1: รันเทสต์เก็บผลจริงสำหรับ `validation.md`**

Run: `python -m unittest discover -s tests -v`
Expected: PASS 15 tests — คัดลอกบรรทัดสรุป (`Ran 15 tests ... OK`) ลงเอกสาร

- [ ] **Step 2: เขียน `README.md`**

ต้องมี: ความต้องการของระบบ (Python 3.15) · วิธีติดตั้ง (`python -m venv .venv`, activate ตาม OS, `python -m pip install -r requirements.txt`) · วิธีรัน (`python -m flask --app app run --debug`) · วิธีรันเทสต์ · คำอธิบายแบบจำลองและสมมติฐาน (β คงที่, VBE คงที่, ไม่มี early effect) · เกณฑ์ region พร้อมระบุว่า `VCE < 0.3 V` เป็นสมมติฐานของผู้พัฒนา ไม่ได้มาจาก datasheet · ตารางค่าอ้างอิงจากสเปกข้อ 8

- [ ] **Step 3: เขียน `docs/design-note.md`**

สรุป 1 หน้า: โจทย์, สถาปัตยกรรม 3 ชั้น, เหตุผลที่เลือก `GET/POST /` แทน PRG และ JSON API, สมการที่ใช้, ข้อจำกัดของแบบจำลอง

- [ ] **Step 4: เขียน `docs/validation.md`**

ตาราง 3 คอลัมน์: ปริมาณ / คำนวณมือ / ค่าแอป สำหรับเคสอ้างอิง 9 ค่า · ผลรันเทสต์ · เคส Cutoff และ Saturation พร้อมข้อความ warning ที่แสดง · ระบุชัดว่าเคสพวกนี้ **ไม่ใช่** ผลจำลองที่แม่นยำ

- [ ] **Step 5: เขียน `docs/reflection.md`**

ตอบ 4 ข้อ: อะไรที่ AI ช่วยได้เร็ว · อะไรที่ต้องตรวจเองและตรวจอย่างไร · จุดที่แบบจำลองใช้ไม่ได้และจะรู้ได้อย่างไร · ถ้ามีเวลาอีก 1 ชั่วโมงจะทำอะไรต่อ (อ้างอิง roadmap W3–W5)

- [ ] **Step 6: ตรวจว่าไม่มีไฟล์ต้องห้ามหลุดเข้า git**

Run: `git status --short`
Expected: ไม่มี `.venv/`, `__pycache__/`, `.env` ในรายการ

- [ ] **Step 7: Commit (ผู้ใช้กดใน GitHub Desktop)**

Stage: `README.md`, `docs/design-note.md`, `docs/validation.md`, `docs/reflection.md`
Message: `docs: add README, validation table and reflection`

---

## Acceptance mapping

| เกณฑ์ Lab | Task ที่ทำให้สำเร็จ |
|---|---|
| A1 GET / (200, เห็นฟอร์ม) | Task 3 Step 1 |
| A2 POST คำนวณจริง | Task 3 Step 3 |
| A3 ค่าตรงการคำนวณมือ | Task 2 Step 1, Task 4 Step 4 |
| A4 Validation | Task 2 Step 9, Task 3 Step 5 |
| A5 Warning นอก active region | Task 2 Step 5 |
| A6 ≥3 math tests + ≥1 Flask test | Task 2 Step 9, Task 3 Step 5 |
| A7 GitHub reproducibility | Task 1 Step 2, Task 4 Step 2 |
