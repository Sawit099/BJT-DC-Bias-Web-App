# Design — BJT Common-Emitter DC Bias Web App (Lab 02)

วันที่: 2026-11-10
รายวิชา: ENG29 2121 Computer Programming for Electrical Engineers (2/2569)
สถานะ: **อนุมัติแล้ว** 2026-11-10 (แผน: `docs/superpowers/plans/2026-11-10-bjt-dc-bias-web-app.md`)

---

## 1. Intent และเหตุผล

Lab 02 ต้องการให้นักศึกษาเห็นภาพการทำงานจริงของ Web Application ที่มี Backend
ไม่ใช่ไฟล์ HTML ที่เปิดด้วย `file://` แล้วคำนวณเองในเบราว์เซอร์ ผลงานจึงต้องเป็น
Flask application หลายไฟล์ ที่รับค่าอุปกรณ์จากฟอร์ม แล้วให้ Python คำนวณ
DC Operating Point ของวงจร BJT NPN Common Emitter แบบ Voltage-Divider Bias
ส่งกลับมาแสดงในหน้าเว็บเดียวกัน

เหตุผลเชิงรายวิชา: ให้นักศึกษาแยกแยะได้ว่า HTTP Request, Route, Template,
Static Resource, Engineering Logic และ Test อยู่คนละส่วนกันอย่างไร และต้อง
ตรวจสอบผลคำนวณเอง ไม่เชื่อ AI โดยไม่ตรวจ

## 2. Goals

- G1 เปิดผ่าน `http://127.0.0.1:5000/` แล้วเห็นฟอร์ม (GET, HTTP 200)
- G2 กรอกค่าแล้วกด Calculate → Python คำนวณจริงและแสดง VB, VE, VC, VCE, IC
  พร้อมหน่วย (ไม่ใช่ค่าคงที่ใน HTML)
- G3 ผลตรงกับการคำนวณมือภายใต้แบบจำลอง forward-active (±0.5%)
- G4 ค่าอินพุตผิด (R ≤ 0, β ≤ 0, VCC ≤ 0, ไม่ใช่ตัวเลข, ว่าง) → ข้อความ error
  ที่อ่านรู้เรื่อง หน้าเว็บไม่ล้ม (HTTP 200 หรือ 400 ที่มีหน้าแสดงผล)
- G5 ผลอยู่นอก forward-active → แสดง warning ชัดเจนว่าแบบจำลองใช้ไม่ได้
- G6 Automated tests: ≥ 3 ตัวตรวจสมการวิศวกรรม + ≥ 1 ตัวผ่าน Flask test client
- G7 README ที่ clone repo แล้วติดตั้ง/รัน/รันเทสต์ได้จริง

## 3. Non-goals

- AC small-signal, gain, Bode plot
- Transient analysis, signal generator, amplitude/frequency control
- SPICE/ngspice integration, DC load line
- Bias type อื่น (Fixed, Emitter bias), FET, op-amp
- ระบบ login, ฐานข้อมูล, deploy ขึ้น cloud, multi-page routing
- JavaScript คำนวณผลฝั่ง client

## 4. Anti-goals (ทำแล้วถือว่าล้มเหลว)

- A-1 ตัวเลขผลลัพธ์ hardcode ไว้ใน template หรือ JavaScript
- A-2 `dc_bias.py` import Flask หรือรู้จัก HTTP/HTML
- A-3 แสดงผลนอก active region โดยไม่มี warning
- A-4 Test ที่ assert ค่าที่คำนวณซ้ำจากสูตรเดียวกันโดยไม่มีการคำนวณมืออ้างอิง
- A-5 Commit `.venv/`, `__pycache__/`, `.env` หรือ credential ใด ๆ

## 5. Constraints

- เวลาพัฒนา ~75 นาที ภายในคาบเดียว
- Windows 11, Python 3.15.2, Flask (เวอร์ชันล่าสุดที่ pip ให้), `unittest` เท่านั้น
  (ไม่เพิ่ม pytest เพื่อให้ตรงคำสั่ง `python -m unittest discover -s tests -v` ในเอกสาร Lab)
- รันเฉพาะ localhost ไม่ deploy (Flask debug server ห้ามเปิดสู่เครือข่ายสาธารณะ)
- Commit ผ่าน GitHub Desktop เท่านั้น (ไม่ใช้ `git commit` จาก command line)
- Repo เดิม: `Sawit099/BJT-DC-Bias-Web-App` branch `main` (เริ่มจาก commit `ad98fb2`)
- สภาพเริ่มต้นจริง: commit `ad98fb2` มีเพียง `.gitattributes` — **ไม่มีโค้ดเดิมให้รักษา**
  ทุกไฟล์ในข้อ 9 สร้างใหม่ทั้งหมด และ working directory คือ clone ของ repo นี้แล้ว
- ป้ายกำกับ UI และข้อความ error: ภาษาไทย + ชื่อปริมาณภาษาอังกฤษ (VCC, VCE, IC)

## 6. Approaches ที่พิจารณา

### ทางที่ 1 — หน้าเดียว `GET /` + `POST /` (server-rendered) — **เลือก**

ฟอร์มและผลลัพธ์อยู่ใน `templates/index.html` ไฟล์เดียว กด Calculate แล้ว POST
กลับไปที่ `/` Flask คำนวณแล้ว render หน้าเดิมพร้อมผล โดยคงค่าที่ผู้ใช้กรอกไว้

- ข้อดี: ตรง A1/A2 ตรงที่สุด, ทดสอบด้วย Flask test client ได้ตรงไปตรงมา,
  แสดง error ข้างช่องกรอกได้, ไม่ต้องมี session/secret key
- ข้อเสีย: refresh หน้าผลลัพธ์หลัง POST จะถูกเบราว์เซอร์เตือนให้ re-submit

### ทางที่ 2 — `POST /calculate` + redirect กลับ `/` (PRG)

- ข้อดี: กัน double-submit, สะอาดเชิง HTTP semantics
- ข้อเสีย: ต้องใช้ `secret_key`, session, flash message และเพิ่ม test case
  โดยไม่ได้คะแนนเพิ่ม — ตัดออกเพราะเวลาไม่พอ

### ทางที่ 3 — JSON API + `fetch()`

- ข้อดี: แยก frontend/backend ชัดเจน ทันสมัย
- ข้อเสีย: เกินขอบเขต Lab, เสี่ยงไม่ตรงเกณฑ์ A2 ที่ต้องการ HTML ที่ server render
  และเพิ่ม dependency ฝั่ง client — ตัดออก

## 7. การตัดสินใจที่ตกลงกันแล้ว

| เรื่อง | ข้อสรุป | เหตุผล |
|---|---|---|
| Route | `GET /` แสดงฟอร์ม, `POST /` คำนวณและ render หน้าเดิม | ทางที่ 1 |
| หน่วยความต้านทานในฟอร์ม | รับเป็น **kΩ** (ทศนิยมได้) แปลง ×1000 เป็น Ω ภายใน `dc_bias.py` | ตรงค่าตัวอย่างใน Lab (100k, 22k, 2.2k, 1k) และตรงข้อกำหนด "แปลง kΩ เป็น Ω" |
| เกณฑ์ Region | `VTH ≤ VBE` → CUTOFF; `VCE < 0.3 V` → SATURATION; อื่น ๆ → ACTIVE | Lab ไม่ระบุตัวเลข ใช้ 0.3 V เป็น VCE(sat) มาตรฐาน และเขียนบอกใน README |
| Test framework | `unittest` | ตรงคำสั่งในเอกสาร Lab |
| โครงผลลัพธ์ | `dataclass` immutable + `Region` enum | template อ่านง่าย, test ตรวจชนิด/ค่าได้ชัด |
| ระดับความสมบูรณ์ | ระดับ ค. (ขั้นต่ำ + IB/IE/region badge/CSS + docs 3 ไฟล์) | ตรง rubric ข้อ 5 |
| ภาษาของเอกสาร | ไทย (ศัพท์เทคนิคเป็นอังกฤษ), โค้ด/comment/ชื่อ test เป็นอังกฤษ | ผู้อ่านคืออาจารย์ไทย, แต่ reviewer โค้ดอ่านอังกฤษได้ |
| หน่วย Ω ใน `BiasResult` | เก็บเฉพาะ `rth_ohm` (ไม่เพิ่ม `rc_ohm`/`re_ohm`) | แปลง kΩ→Ω ตรวจได้จาก `rth_ohm` และจากค่า VCE/IC ที่เปลี่ยนตาม |
| Commit sequence | แบ่ง 4 commit ตามข้อ 14 แล้วให้ผู้ใช้กดใน GitHub Desktop | Review ทีละก้อนง่าย และตรงเกณฑ์ rubric |
| การแสดงผลนอก active region | **โชว์ค่าดิบจากสมการทั้งหมด** แล้วตีตราว่าใช้ไม่ได้ (สีเทา/ขีดฆ่า + ⚠) พร้อมแบนเนอร์อธิบาย | โปร่งใสว่าสมการให้อะไร และตอบ A5 ได้ชัดว่าไม่รายงานว่า approximation ใช้ได้ |
| การ clamp ค่า | **ไม่ clamp** ค่าใด ๆ ทั้งสิ้น | การ clamp คือการแต่งตัวเลขขึ้นมาเอง ซึ่งขัด anti-goal A-1 spirit |

## 8. แบบจำลองทางไฟฟ้า

วงจร: NPN Common Emitter, Voltage-Divider Bias
(R1 จาก VCC ไป Base, R2 จาก Base ไป Ground, RC จาก VCC ไป Collector,
RE จาก Emitter ไป Ground)

สมมติฐาน: forward-active, β คงที่, VBE คงที่ตามที่ผู้ใช้กรอก, อุณหภูมิคงที่
(ไม่คิด early effect, ไม่คิด leakage)

```
VTH = VCC · R2 / (R1 + R2)
RTH = R1 · R2 / (R1 + R2)
IB  = (VTH − VBE) / (RTH + (β + 1)·RE)
IC  = β · IB
IE  = (β + 1) · IB
VE  = IE · RE
VB  = VE + VBE
VC  = VCC − IC · RC
VCE = VC − VE
```

กรณีอ้างอิง (ใช้ตรวจรับ A3): VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ,
RE=1 kΩ, β=100, VBE=0.70 V

| ปริมาณ | ค่าคำนวณมือ |
|---|---|
| VTH | 2.1639 V |
| RTH | 18.033 kΩ |
| IB | 12.299 µA |
| IC | 1.2299 mA |
| IE | 1.2422 mA |
| VE | 1.2422 V |
| VB | 1.9422 V |
| VC | 9.2942 V |
| VCE | 8.0520 V |
| Region | ACTIVE |

## 9. โครงสร้างไฟล์

```
BJT DC Bias Web App/
├── app.py                  # Flask routes เท่านั้น
├── dc_bias.py              # สมการ + validation + region (ไม่ import Flask)
├── templates/index.html    # ฟอร์ม + ผลลัพธ์ (Jinja) ไม่มีสมการฟิสิกส์
├── static/style.css        # layout
├── tests/
│   ├── test_dc_bias.py
│   └── test_web.py
├── requirements.txt
├── README.md
├── AGENTS.md
├── .gitignore
└── docs/
    ├── design-note.md
    ├── validation.md
    └── reflection.md
```

## 10. สัญญาระหว่างโมดูล (interfaces)

### `dc_bias.py`

```python
class Region(Enum):
    ACTIVE = "active"
    CUTOFF = "cutoff"
    SATURATION = "saturation"

class ValidationError(ValueError):
    """มี field และ message ภาษาไทยที่แสดงให้ผู้ใช้ได้"""

@dataclass(frozen=True)
class BiasInput:
    vcc_v: float          # V
    r1_kohm: float
    r2_kohm: float
    rc_kohm: float
    re_kohm: float
    beta: float
    vbe_v: float

@dataclass(frozen=True)
class BiasResult:
    vth_v, rth_ohm, ib_a, ic_a, ie_a, ve_v, vb_v, vc_v, vce_v: float
    region: Region
    warning: str | None

def parse_inputs(form: Mapping[str, str]) -> BiasInput   # raises ValidationError
def calculate(bias: BiasInput) -> BiasResult
```

- หน่วยภายใน `BiasResult`: SI (V, A, Ω) — การแปลงเป็น mA/µA/kΩ ทำที่ template หรือ property
- `warning` เป็น `None` เฉพาะกรณี ACTIVE

### `app.py`

```python
@app.get("/")   -> render index.html (form ว่าง/ค่าเริ่มต้น, ไม่มีผลลัพธ์)
@app.post("/")  -> parse_inputs -> calculate -> render index.html พร้อมผล
                   ถ้า ValidationError -> render index.html พร้อม errors + ค่าที่กรอก
```
ค่าเริ่มต้นในฟอร์ม: 12 / 100 / 22 / 2.2 / 1 / 100 / 0.70 (ตามเอกสาร Lab)

### `templates/index.html`

- ฟอร์ม 7 ช่อง + ปุ่ม Calculate
- แสดง `errors` เป็นรายการใต้ช่องที่ผิด (อย่างน้อยเหนือฟอร์ม)
- แสดงตารางผล: VB, VE, VC, VCE [V], IC, IB, IE [mA/µA]
- แสดง badge Region + `warning` เมื่อมี
- ถ้า Region ≠ ACTIVE: ทุกค่าในตารางผลได้ class `unreliable` + ⚠ และมีแบนเนอร์อธิบายเหนือตาราง
- ไม่มีสูตรคำนวณหรือตัวเลขผลลัพธ์ฝังในไฟล์

## 11. Validation rules

| เงื่อนไข | ผล |
|---|---|
| ช่องว่าง หรือแปลงเป็น float ไม่ได้ | ValidationError: "กรุณากรอก … เป็นตัวเลข" |
| VCC ≤ 0 | "VCC ต้องมากกว่า 0 V" |
| R1, R2, RC, RE ≤ 0 | "R… ต้องมากกว่า 0 kΩ" |
| β ≤ 0 | "β ต้องมากกว่า 0" |
| VBE < 0 หรือ VBE ≥ VCC | "VBE ต้องอยู่ระหว่าง 0 ถึง VCC" |
| R1 + R2 = 0 (เป็นไปไม่ได้เมื่อ R > 0 แต่กันไว้) | ValidationError |
| VTH ≤ VBE | คำนวณต่อด้วยสูตรเดิม (IB ติดลบได้) → Region.CUTOFF + warning |
| VCE < 0.3 V | Region.SATURATION + warning |
| VCE < 0 | SATURATION + warning ระบุว่าผลไม่มีความหมายทางกายภาพ |
| Region ≠ ACTIVE | แสดงค่าดิบทุกตัวพร้อมเครื่องหมาย ⚠ และสไตล์ `.unreliable` (สีเทา/ขีดฆ่า) + แบนเนอร์อธิบายว่า forward-active model ใช้ไม่ได้ในช่วงนี้ — **ห้าม clamp หรือแทนค่าด้วย 0/—** |

## 12. แผนการทดสอบ

`tests/test_dc_bias.py`
1. `test_reference_case_matches_hand_calculation` — ค่าอ้างอิงข้อ 8, tolerance 0.5%
2. `test_region_is_active_for_reference_case`
3. `test_cutoff_when_vth_not_above_vbe` — เช่น VBE=3 V → CUTOFF + warning
4. `test_saturation_when_vce_below_saturation` — RC ใหญ่มาก → SATURATION + warning
5. `test_inputs_interpreted_as_kohm` — เคสอ้างอิงต้องได้ `rth_ohm ≈ 18032.8 Ω` (พิสูจน์ว่า kΩ ถูกแปลง ×1000) และ R ที่เป็น kΩ ต้องไม่ถูกตีความเป็น Ω
6. `test_rejects_non_positive_and_non_numeric` — VCC=0, R1=-1, β=0, "abc"

`tests/test_web.py`
7. `test_get_root_returns_form` — 200 + มี `name="vcc"` ครบ 7 ช่อง
8. `test_post_valid_inputs_shows_results` — 200 + มี "1.229" หรือ "1.23" และ "Active"
9. `test_post_invalid_input_shows_error_and_keeps_page` — 200 + ข้อความ error, ไม่มี traceback

## 13. เอกสารที่ต้องส่ง

- `README.md` — วิธีติดตั้ง (venv), รัน, รันเทสต์, สมมติฐานแบบจำลอง, เกณฑ์ region,
  ตารางค่าอ้างอิง
- `docs/design-note.md` — สรุป design นี้ (เวอร์ชันสั้นสำหรับอาจารย์)
- `docs/validation.md` — ตารางเทียบค่ามือกับค่าแอป + ผลรันเทสต์ + เคสที่ล้มเหลว/ข้อจำกัด
- `docs/reflection.md` — สิ่งที่เรียนรู้, จุดที่ AI ช่วย/ที่ต้องแก้เอง, ปัญหาที่เจอ
- `AGENTS.md` — กติกาโค้ด (แยก layer, ห้าม hardcode ผล, unittest, ภาษาไทยใน UI)

หลักฐานส่ง Moodle (ทำนอก repo): ภาพหน้าจอเว็บที่คำนวณสำเร็จ, ภาพ/ไฟล์ Test Log,
Repository URL และ Commit SHA — ทั้ง 3 อย่างนี้เป็นสิ่งที่ผู้ใช้ต้องเก็บเองตอนท้ายคาบ

## 14. ลำดับ Commit (กดใน GitHub Desktop)

1. `chore: add project scaffold, gitignore and agent conventions`
   → `.gitignore`, `requirements.txt`, `AGENTS.md`, `docs/superpowers/specs/…-design.md`
2. `feat: add DC bias engineering module with unit tests`
   → `dc_bias.py`, `tests/test_dc_bias.py`
3. `feat: add Flask web UI for DC bias calculation`
   → `app.py`, `templates/index.html`, `static/style.css`, `tests/test_web.py`
4. `docs: add README, validation table and reflection`
   → `README.md`, `docs/design-note.md`, `docs/validation.md`, `docs/reflection.md`

## 15. สิ่งที่เหลือให้ผู้สร้างตัดสินใจ

- รายละเอียดหน้าตา CSS, สี, ฟอนต์, การจัดวาง (ดูสวยและอ่านง่ายบนมือถือ)
- ถ้อยคำภาษาไทยของ label/error/warning (ให้ตรงกับที่ระบุด้านบน)
- จะแยก helper แปลงหน่วยใน `dc_bias.py` หรือทำ property ใน `BiasResult`
- จะเพิ่ม test ที่ตรวจ `IE = IC + IB` หรือไม่ (ไม่บังคับ แต่ราคาถูก)
