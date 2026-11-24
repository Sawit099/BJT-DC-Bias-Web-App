# BJT DC Bias Web App

Flask Web Application สำหรับคำนวณ **DC Operating Point** ของวงจร BJT NPN Common Emitter
**3 แบบ**: **Fixed Bias**, **Emitter Bias** และ **Voltage-Divider Bias** — เลือกโหมดในฟอร์ม
กรอกค่าอุปกรณ์ แล้ว Python Backend คำนวณ VB, VE, VC, VCE, IC, IB, IE ส่งกลับมาแสดงพร้อมหน่วย

สร้างเป็นผลงาน Lab 02–03 รายวิชา ENG29 2121 Computer Programming for Electrical Engineers

## ลิงก์งานส่ง (Lab 03–04)

- **Repository:** <https://github.com/Sawit099/BJT-DC-Bias-Web-App>
- **Commit SHA ของงาน Lab 03:** `aae798d5a382846aada9299ef4f4ede7b3f7b8a0`
- **Commit SHA ของงาน Lab 04:** `PENDING_LAB04_SHA`
- **วิธีตรวจ A1–A5 (Lab 03):** Playwright MCP (Chrome จริง) — ตารางและภาพหลักฐานอยู่ที่ [`docs/validation.md`](docs/validation.md) §5
- **วิธีตรวจ B1–B8 (Lab 04):** Playwright MCP (Chrome จริง) + ngspice 47 + Impeccable — ตารางและภาพหลักฐานอยู่ที่ [`docs/validation.md`](docs/validation.md) §8
- Commit ถัดจาก SHA ของ Lab 03 แก้เฉพาะส่วน "ลิงก์งานส่ง" ใน README ไม่มีการเปลี่ยนโค้ดหรือผลคำนวณ
- Commit ถัดจาก SHA ของ Lab 04 แก้เฉพาะเลข SHA ใน README เช่นกัน; โค้ดและผลตรวจทั้งหมดอยู่ใน commit ที่ระบุ

วิธีรันและเปิดเว็บอยู่ในหัวข้อ [การติดตั้ง](#การติดตั้ง) และ [การรันเว็บ](#การรันเว็บ) ด้านล่าง

## ความต้องการของระบบ

- Python 3.15 (ทดสอบด้วย 3.15.2)
- Flask 3.1 ขึ้นไป (ติดตั้งจาก `requirements.txt`)
- ใช้ `unittest` ในการทดสอบ ไม่ใช้ pytest

## การติดตั้ง

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate

python -m pip install -r requirements.txt
```

## การรันเว็บ

บน Windows วิธีเร็วที่สุด: **ดับเบิลคลิก `start.bat`** — สคริปต์จะเปิดเซิร์ฟเวอร์แล้วเปิดเบราว์เซอร์ให้เอง

หรือรันจาก terminal ในโฟลเดอร์โปรเจกต์ (เลือกทางใดทางหนึ่ง):

```bash
python app.py
python -m flask --app app run --debug
```

แล้วเปิดเบราว์เซอร์ที่ <http://127.0.0.1:5000/>

> ต้องเปิดผ่าน Flask server เท่านั้น — การ double-click เปิด `templates/index.html`
> ด้วย `file://` จะไม่ได้ผล เพราะฟอร์มต้องส่ง HTTP request ไปให้ Python คำนวณ
> Flask development server ใช้สำหรับเครื่องผู้พัฒนาเท่านั้น ห้ามเปิดสู่เครือข่ายสาธารณะ

### ถ้าเปิดเว็บไม่ขึ้น

| อาการที่เห็น | สาเหตุ | วิธีแก้ |
|---|---|---|
| ดับเบิลคลิก `templates/index.html` แล้วหน้าว่างหรือเห็น `{{ ... }}` | เปิดด้วย `file://` ไม่ผ่าน Flask | เปิด <http://127.0.0.1:5000/> หลังรัน `python app.py` |
| `This site can't be reached` / `ERR_CONNECTION_REFUSED` | ยังไม่ได้รันเซิร์ฟเวอร์ หรือปิดหน้าต่าง terminal ไปแล้ว | รัน `python app.py` หรือ `start.bat` แล้วโหลดหน้าใหม่ |
| `Address already in use` / พอร์ต 5000 ไม่ว่าง | มีเซิร์ฟเวอร์รันค้างอยู่แล้ว | เปิด <http://127.0.0.1:5000/> ได้เลย ไม่ต้องรันซ้ำ — ถ้าต้องการคนละพอร์ต ใช้ `set PORT=5001` (PowerShell: `$env:PORT=5001`) แล้วค่อย `python app.py` |
| เปิดจากมือถือหรือเครื่องอื่นในวงแลน | เซิร์ฟเวอร์ผูกที่ `127.0.0.1` เท่านั้น | ใช้เครื่องเดียวกัน หรือแก้ `host` ใน `app.py` (เฉพาะเครือข่ายที่ไว้ใจได้) |

## การรันเทสต์

```bash
python -m unittest discover -s tests -v
```

ผลที่คาดหวัง: `Ran 57 tests ... OK` (รวมเทสต์ Lab 03 เดิม + เทสต์ ngspice/API/UI/เอกสาร/Impeccable fixes ของ Lab 04)

## โครงสร้างโปรเจกต์

```
app.py                  Flask routes (Lab 03) + POST /api/simulate (Lab 04 ngspice)
start.bat               เปิดเซิร์ฟเวอร์และเปิดเบราว์เซอร์ให้ (Windows)
dc_bias.py              สมการ 3 โหมด analytical (ไม่เปลี่ยนตาม Lab 03) + validation + region + as_dict()
spice_engine.py         ngspice adapter: สร้าง netlist, รัน batch, parse .op/.ac/.tran
templates/index.html    ฟอร์ม Lab 03 + ส่วน CE Amplifier Simulator (Jinja, ไม่มีสมการฟิสิกส์)
static/style.css        รูปแบบหน้าจอ
static/app.js           เรียก /api/simulate และวาดกราฟ Chart.js จากผลจริง
static/chart.umd.min.js Chart.js 4.4.1 UMD (vendored)
tests/test_dc_bias.py   เทสต์สมการและ validation (22 tests)
tests/test_spice_engine.py  เทสต์ ngspice discovery/netlist/run/parse (7 tests, skip ถ้าไม่มี ngspice)
tests/test_web.py       เทสต์ HTTP/UI/API/เอกสาร + UI polish regression (28 tests)
```

## โหมดวงจร

เลือกโหมดจาก dropdown แล้วกด **เปลี่ยนโหมด** — ฟอร์มจะแสดงเฉพาะช่องที่โหมดนั้นใช้

| โหมด | ช่องที่ใช้ | I_B |
|---|---|---|
| Voltage Divider Bias | VCC, R1, R2, RC, RE, β, VBE | (VTH − VBE) / [RTH + (β+1)RE] |
| Fixed Bias | VCC, RB, RC, β, VBE | (VCC − VBE) / RB |
| Emitter Bias | VCC, RB, RC, RE, β, VBE | (VCC − VBE) / [RB + (β+1)RE] |

Fixed Bias ต่อ emitter ลงกราวด์โดยตรง จึงได้ `VE = 0 V` และไม่มีแถว VTH/RTH ในตารางผล

## แบบจำลองที่ใช้

ใช้ **Forward-Active Approximation** โดยถือว่า

- β คงที่ตามค่าที่ผู้ใช้กรอก
- VBE คงที่ตามค่าที่ผู้ใช้กรอก
- ไม่คิด Early effect, leakage current หรือผลของอุณหภูมิ

สมการ:

```
Divider  IB = (VTH − VBE) / (RTH + (β + 1)·RE)
Fixed    IB = (VCC − VBE) / RB
Emitter  IB = (VCC − VBE) / [RB + (β + 1)·RE]

ร่วมทุกโหมด
IC  = β · IB        IE = (β + 1)·IB
VB  = VE + VBE      VC = VCC − IC · RC
VCE = VC − VE       VE = IE · RE (Fixed: VE = 0)

เฉพาะ Divider
VTH = VCC · R2 / (R1 + R2)    RTH = R1 · R2 / (R1 + R2)
```

ความต้านทานกรอกเป็น **kΩ** และถูกแปลงเป็น Ω ที่ฟังก์ชัน `_kohm_to_ohm()` ใน `dc_bias.py`
จุดเดียว ก่อนเข้าสมการทุกโหมด — template ไม่แปลงหน่วยกระแสเอง แต่ใช้คีย์ `ic_ma` / `ib_ua` / `ie_ma` จาก `as_dict()`

## เกณฑ์การตัดสิน Region

| เงื่อนไข | Region | สิ่งที่เว็บแสดง |
|---|---|---|
| `IB ≤ 0` | Cutoff | badge Cutoff + warning ว่า IB ติดลบและแบบจำลองใช้ไม่ได้ |
| `VCE ≤ 0.2 V` | Saturation | badge Saturation + warning ว่า VCE ไม่เกิน VCE(sat) |
| นอกนั้น | Active | badge Active |

> **0.2 V** เป็นค่าที่ใบงาน Lab 03 กำหนด (Lab 02 ใช้ 0.3 V)
> เป็นค่ามาตรฐานของ BJT ขนาดเล็ก ไม่ได้มาจาก datasheet ของอุปกรณ์จริง

เมื่อผลอยู่นอก forward-active เว็บจะ **แสดงค่าดิบจากสมการทั้งหมด** (ไม่ clamp ไม่แทนด้วย 0)
พร้อมขีดฆ่าและแบนเนอร์เตือน เนื่องจากสมการ forward-active ไม่ใช่แบบจำลองที่ใช้ได้ในช่วงนั้น

## ค่าอ้างอิงสำหรับตรวจรับ

VCC = 12 V, R1 = 100 kΩ, R2 = 22 kΩ, RC = 2.2 kΩ, RE = 1 kΩ, β = 100, VBE = 0.70 V

| ปริมาณ | ค่า |
|---|---|
| VTH | 2.1639 V |
| RTH | 18.033 kΩ |
| IB | 12.299 µA |
| IC | 1.2299 mA |
| IE | 1.2422 mA |
| VE | 1.2422 V |
| VB | 1.9422 V |
| VC | 9.2943 V |
| VCE | 8.0522 V |
| Region | Active |

## เอกสารเพิ่มเติม

- [`docs/design-note.md`](docs/design-note.md) — สรุปการออกแบบ
- [`docs/validation.md`](docs/validation.md) — ตารางตรวจสอบผล, ตาราง A1–A5 และข้อจำกัด
- [`docs/reflection.md`](docs/reflection.md) — สิ่งที่ได้เรียนรู้

## Lab 03 — ส่วนที่ AI ช่วยและส่วนที่ตรวจเอง

| ส่วน | AI ช่วย | นักศึกษาตรวจ |
|---|---|---|
| `dc_bias.py` | เขียน `calculate_fixed`, `calculate_emitter`, `_solve`, `as_dict()`, `parse_fixed`, `parse_emitter` | เทียบสมการกับใบงานทีละบรรทัด, ตรวจหน่วย kΩ→Ω, ตรวจว่า Condition `IB ≤ 0` และ `VCE ≤ 0.2 V` ตรงใบงาน |
| `app.py` | เขียน `if/elif` เลือกโฟลเดอร์ตาม `mode` และส่ง `mode` ให้ template | ตรวจว่าโหมดไม่รู้จักไม่ถูกเดาเป็น Divider และ error ไม่แสดงผลรอบก่อน |
| `tests/` | เขียนเทสต์ตามค่าอ้างอิง A1–A5 | รันเองทั้งหมด 57 เทสต์ (38 ของ Lab 03 + 19 ของ Lab 04) และตรวจว่า Divider ยังได้ค่าเดิม |
| เอกสาร | ร่างตาราง A1–A5 และ README | ตรวจตัวเลขกับเครื่องคิดเลขก่อนส่ง |

**จุดที่เลือกฟังก์ชัน:** `app.py` ฟังก์ชัน `calculate_view()` — `if mode == "fixed" … elif mode == "emitter" … else`  
**จุดที่แปลงหน่วย:** `dc_bias.py` ฟังก์ชัน `_kohm_to_ohm()` จุดเดียว — kΩ → Ω ก่อนเข้าสมการ แล้วคืนค่าเป็น SI (V, A, Ω)  
**จุดที่ส่งผลให้ template:** `app.py` เรียก `result.as_dict()` แล้ว template อ่านเฉพาะคีย์ `vb_v, ve_v, vc_v, vce_v, ic_ma, ib_ua, ie_ma` (ไม่มีการคำนวณหรือแปลงหน่วยใน HTML)

## คำถามปิด Lab 03 — ถ้าเปลี่ยน RE แล้วผลไม่เปลี่ยน จะตรวจอะไร

ไล่จากปลายทางกลับต้นทาง ทีละชั้น — ชั้นไหนหลุดจะเห็นทันที

| ชั้น | ตรวจอะไร | วิธีตรวจ | ค่าที่ถูกต้อง |
|---|---|---|---|
| 1 | ค่าที่ **ฟอร์มส่งออกไป** | DevTools → Network → คลิก request `POST /` → แท็บ Payload | ต้องเห็น `re=2` และ `mode=emitter` (ถ้าไม่มี = input ไม่มี `name`, ถูก `disabled`, หรืออยู่นอก `<form>`) |
| 2 | ค่าที่ **Flask รับเข้า** | ชั่วคราว log `request.form.get("re")` ใน `calculate_view()` | `"2"` ไม่ใช่ `"1"` หรือ `None` |
| 3 | ค่าที่ **parse + แปลงหน่วย** | เรียก `parse_emitter(form).re_kohm` และ `_kohm_to_ohm(2.0)` | `2.0` และ `2000.0` |
| 4 | ค่าที่ **เข้าสมการ** | ตรวจตัวส่วน `rb + (β+1)·re` ใน `calculate_emitter` | 1,101,000 → 1,202,000 Ω ทำให้ IB ลด |
| 5 | ค่าที่ **ส่งให้ template** | ตรวจ `result.as_dict()["ic_ma"]` ก่อน `render_template` | 1.0263 → 0.9401 |

ถ้าชั้น 1–5 ถูกทั้งหมดแต่หน้าจอไม่เปลี่ยน ปัญหาอยู่ที่ **การแสดงผล/cache** ไม่ใช่สมการ
วิธีที่เร็วที่สุดในการแยกให้ขาดคือเทสต์ HTTP สองเคส (RE=1 กับ RE=2 แล้ว assert ว่า IC ต่างกัน)
ซึ่งมีอยู่แล้วในโปรเจกต์นี้: `test_emitter_post_uses_re` และ `test_more_re_lowers_ic`

## Lab 04 — CE Amplifier Simulator (ngspice)

ส่วนนี้ต่อยอดจาก Lab 03 โดย **คงโหมด DC bias 3 แบบเดิม** และเพิ่ม CE Voltage Divider reference circuit ที่รันด้วย **ngspice จริง** (`.op`, `.ac`, `.tran`) ผ่าน `spice_engine.py` + `POST /api/simulate`

### การติดตั้ง ngspice

- ต้องมี ngspice ที่รัน batch mode ได้ (`ngspice_con.exe` หรือ `ngspice`)
- โปรแกรมจะค้นหาอัตโนมัติจาก `NGSPICE_EXE`, PATH (`ngspice_con`/`ngspice`) และ path มาตรฐาน Windows
- แนะนำตั้งค่า env var ถ้าติดตั้งนอก path มาตรฐาน:

```powershell
$env:NGSPICE_EXE="C:\path\to\Spice64\bin\ngspice_con.exe"
python app.py
```

เครื่องที่ใช้ทดสอบงานนี้ติดตั้ง ngspice 47 (portable) ที่ `C:\Users\b6829643\AppData\Local\Tools\ngspice\Spice64\bin\ngspice_con.exe` และตรวจแล้วว่ารัน batch `.op/.ac/.tran` ได้จริง

### Model / Provenance

- โมเดล BJT ที่ใช้: `Q2N3904_LAB04` (NPN) ประกาศใน netlist ที่สร้างโดย `spice_engine.py`
- พารามิเตอร์: `BF=200 IS=6.734f VAF=74.03 CJE=4.493p CJC=3.638p TF=301.2p TR=239.5n`
- เป็นโมเดล 2N3904-like แบบระบุพารามิเตอร์ชัดเจนเพื่อ reproducibility ใน Lab นี้ **ไม่ใช่ manufacturer-certified SPICE card** และไม่ได้ hard-code ผลลัพธ์ simulation
- ผล `.op/.ac/.tran` ที่แสดงใน UI มาจากการรัน ngspice จริงทุกครั้ง; ถ้า engine หาย/ผิดพลาด/timeout จะคืน `ok:false` พร้อมข้อความ error และไม่แสดงกราฟเก่าพร้อมสถานะสำเร็จ

### B1–B8 Browser Acceptance (สรุป)

รายละเอียดเต็ม (Method/Input/Expected/Observed/Evidence) อยู่ใน [`docs/validation.md`](docs/validation.md) §8.2

| Case | เป้าหมายตามใบงาน | ผลจริง |
|---|---|---|
| B1 | Regression: Fixed / Emitter / Divider ด้วยค่า Lab 3 | PASS — Divider IC 1.230 mA/VCE 8.052 V; Fixed 1.130/9.514; Emitter 1.026/8.705; ทั้งสาม Active |
| B2 | DC SPICE: รัน `.op` แสดง VB/VE/VC/VCE/IC + Model + Run Status | PASS — VB 2.0507, VE 1.3795, VC 8.9790, VCE 7.5995 V, IC 1.4727 mA; Engine ngspice; Model Q2N3904_LAB04 |
| B3 | เปลี่ยนเฉพาะ RE แล้วรันใหม่; operating point ต้องเปลี่ยน | PASS — RE 1→2 kΩ: IC 1.4727→0.8213 mA; VCE 7.5995→8.9596 V; run id เปลี่ยน |
| B4 | AC: Bode plot frequency/gain/phase จาก run จริง | PASS — 101 points; gain 4.7979–4.9108 dB; phase −181.87°…−167.10°; x ticks 10 Hz–1 MHz |
| B5 | Transient: `.tran` 10 mVpk, 1 kHz; Vin/Vout ตามเวลาและกลับเฟส | PASS — 1008 points; Vin max 0.0099996 V; Vout max 0.017627 V; correlation −0.999997 |
| B6 | เปลี่ยน amplitude/frequency แล้ว waveform ต้องเปลี่ยนจริง | PASS — 20 mVpk/5 kHz: 5008 points; Vin max 0.02 V; Vout max 0.03520 V; run id เปลี่ยน |
| B7 | Invalid/Fail: RE=0 หรือ engine หาย; ต้องมี error และไม่มี stale success | PASS — `การจำลองล้มเหลว` + `RE ต้องมีค่ามากกว่า 0`; ตาราง/กราฟซ่อน; engine missing คืน `ok:false` (automated test) |
| B8 | UI desktop/mobile: สลับโหมด อ่านได้ ไม่ถูกตัด | PASS — desktop 1280 px และ mobile 390 px ไม่มี horizontal overflow; ปุ่ม/กราฟอ่านได้ |

### ทำไมผล analytical กับ SPICE ไม่เท่ากัน

| ปริมาณ | Lab 03 analytical (β = 100, VBE = 0.70 V) | Lab 04 SPICE (`Q2N3904_LAB04`) | เหตุผล |
|---|---|---|---|
| IC | 1.230 mA | 1.4727 mA | SPICE ใช้ `BF=200`, `IS=6.734f`, `VAF=74.03` และคำนวณ VBE จากโมเดล ไม่ใช่ β/VBE ที่ผู้ใช้กรอก |
| VCE | 8.052 V | 7.5995 V | กระแส collector สูงขึ้นทำให้แรงดันตกคร่อม RC มากขึ้น |

ความต่างนี้เป็นธรรมชาติของแบบจำลอง two different models ไม่ใช่ bug; UI แยกส่วน
"ผลคำนวณเชิงวิเคราะห์" (Lab 03) กับ "CE Amplifier Simulator" (Lab 04) ไว้ชัดเจน
และแสดง Engine/Model/Run id ทุกครั้ง

### Impeccable — UI critique / polish

- ติดตั้ง skill แบบ project-scoped: `npx impeccable install --project --providers=opencode`
  (ไฟล์เครื่องมืออยู่ใน `.opencode/` ซึ่งไม่ commit; ผู้ตรวจสามารถติดตั้งใหม่ได้)
- ใช้ **dual-agent critique**: Assessment A (design review) + Assessment B (detector/browser)
  แยกกัน แล้วสังเคราะห์; รายละเอียดและ before/after อยู่ใน
  [`docs/evidence/lab04-impeccable-critique.md`](docs/evidence/lab04-impeccable-critique.md)
- **ก่อนแก้:** URL scan 0 anti-patterns + 1 advisory; critique พบ transient tick เป็น float ดิบ,
  AC label ชนกัน, ปุ่ม `เปลี่ยนโหมด` ขึ้น 3 บรรทัดบน mobile, error ไม่ถูก announce/focus
- **หลังแก้:** URL scan ที่ 1280 px และ 390 px คืน `[]`; แก้ tick format, mobile mode bar,
  `aria-live`, `aria-invalid` + focus, `thead`/`scope`, `aria-label` ของ canvas และ `text-wrap: balance`
- Source scan ยังรายงาน `flat-type-hierarchy` 1 รายการ แต่เป็น false positive เพราะ detector
  อ่าน Jinja `url_for()` เป็น path ไม่ได้; ค่าจริงจาก browser คือ 24/18.4/16 px
- **ยังไม่แก้ (ตั้งใจ/นอกขอบเขต v1):** ไม่มี schematic; ฟอร์ม analytical กับ simulator แยกกัน;
  การเปลี่ยนโหมด Lab 03 ยัง reset input; chart เป็น canvas (มี `aria-label` แต่ไม่มี data table เต็ม);
  label `Engine/Model/Run` คงเป็นอังกฤษตามข้อกำหนด Model/Run Status; การ์ดกว้างสูงสุด 720 px

### Lab 04 — ส่วนที่ AI ช่วยและส่วนที่นักศึกษาตรวจ

| ส่วน | AI ช่วย | นักศึกษาตรวจ |
|---|---|---|
| `spice_engine.py` | เขียน netlist, subprocess adapter, parser `.op/.ac/.tran`, phase conversion | ตรวจว่า ngspice 47 รัน batch ได้จริง, ตรวจ path/timeout/error handling และเทียบค่ากับ log |
| `app.py` + `static/app.js` | เขียน `POST /api/simulate`, fetch, Chart.js rendering | ตรวจว่าไม่มีผลลัพธ์ hard-code, กราฟมาจาก run จริง, invalid/fail ไม่ค้างกราฟเก่า |
| UI / Impeccable | ร่าง UI, ใช้ detector/critique, แก้ tick/mobile/aria | เลือก scope ที่แก้เฉพาะ UI, ตรวจว่าสมการฟิสิกส์และผล Lab 03 ไม่เปลี่ยน, ตรวจ before/after |
| เอกสาร / Git | ร่าง README, validation, evidence | ตรวจตัวเลขกับ ngspice log/เครื่องคิดเลข, ตรวจ diff ก่อน commit, ตัดสินใจเรื่อง model provenance และข้อจำกัด |

### หมายเหตุ Lab 04

- Chart.js เป็นไฟล์ vendored ใน `static/chart.umd.min.js` (ไม่พึ่ง CDN ตอนรัน)
- ผล analytical Lab 03 และผล SPICE Lab 04 แสดงแยกส่วนกันชัดเจน
- ไฟล์ temp ของ ngspice สร้างใน temporary directory ต่อรัน และไม่ commit
- หลักฐาน ngspice log/sample อยู่ใน `docs/evidence/lab04-ngspice-*.txt` และ `lab04-ngspice-op.log`

## การเชื่อม Playwright MCP

### MCP ทำงานอะไรในโปรเจกต์นี้

MCP (Model Context Protocol) เป็นมาตรฐานที่ให้แอป AI รู้ว่ามีเครื่องมืออะไรให้เรียก และรับผลกลับมา
ใน Lab นี้ **OpenCode = MCP Client**, **Playwright MCP = MCP Server** ที่สั่ง Chrome
ส่วน Chrome คุยกับ Flask ผ่าน HTTP ตามปกติ จึงไม่ต้องใส่ Playwright ลง `requirements.txt`
และ Flask ไม่รู้จัก MCP เลย

```
OpenCode ──MCP──> Playwright MCP ──สั่ง──> Chrome ──HTTP──> Flask/Python
    ^                                          |
    └──────MCP (Snapshot)──── Playwright ◄─────┘  อ่านหน้าเว็บ
```

รอบตรวจ A1–A5 ทำแบบนี้: เปิดหน้า → อ่าน Snapshot → เลือกโหมด → กรอกค่า → กดคำนวณ →
อ่าน Snapshot ใหม่ → เทียบกับค่าอ้างอิงที่คำนวณมือไว้ก่อนรัน

### ไฟล์ตั้งค่า

โปรเจกต์มี `opencode.json` ที่ราก ซึ่งบอก OpenCode ให้เริ่ม Playwright MCP:

```json
{
  "mcp": {
    "servers": {
      "playwright": {
        "type": "local",
        "command": ["npx", "-y", "@playwright/mcp@latest", "--browser", "chrome", "--isolated"]
      }
    }
  }
}
```

ต้องมี **Node.js 18+** (ติดตั้งแล้ว: v24.20.0) และ **Chrome** — ถ้าไม่ครบให้ใช้ **OpenCode Browser Tool**
แทนได้ โดยระบุวิธีจริงในตาราง A1–A5

### ตรวจว่าเชื่อมต่อแล้ว

```sh
opencode mcp list
# ✓ playwright  connected
```

รอบตรวจ A1–A5 ของงานนี้ใช้ Playwright MCP 1.66.0 ควบคุม Chrome จริง
ภาพหลักฐานอยู่ใน [`docs/evidence/`](docs/evidence/) (A1, A4, A5)

### แก้ปัญหา `'npx' is not recognized`

Background service ของ OpenCode จำ PATH ไว้ตั้งแต่ตอนเริ่ม process ถ้าติดตั้ง Node.js
หลังจากนั้นจะเห็นข้อความนี้ใน `opencode mcp list` — แก้ด้วย `opencode service restart`
(หรือปิด–เปิดแอปใหม่ทั้งหมด) หรือชี้ `environment.PATH` ไปที่โฟลเดอร์ Node ชั่วคราว
เช่น

```json
"environment": { "PATH": "C:\\Program Files\\nodejs;{env:PATH}" }
```
