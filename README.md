# BJT DC Bias Web App

Flask Web Application สำหรับคำนวณ **DC Operating Point** ของวงจร BJT NPN Common Emitter
**3 แบบ**: **Fixed Bias**, **Emitter Bias** และ **Voltage-Divider Bias** — เลือกโหมดในฟอร์ม
กรอกค่าอุปกรณ์ แล้ว Python Backend คำนวณ VB, VE, VC, VCE, IC, IB, IE ส่งกลับมาแสดงพร้อมหน่วย

สร้างเป็นผลงาน Lab 02–03 รายวิชา ENG29 2121 Computer Programming for Electrical Engineers

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

```bash
python -m flask --app app run --debug
```

เปิดเบราว์เซอร์ที่ <http://127.0.0.1:5000/>

> ต้องเปิดผ่าน Flask server เท่านั้น — การ double-click เปิด `templates/index.html`
> ด้วย `file://` จะไม่ได้ผล เพราะฟอร์มต้องส่ง HTTP request ไปให้ Python คำนวณ
> Flask development server ใช้สำหรับเครื่องผู้พัฒนาเท่านั้น ห้ามเปิดสู่เครือข่ายสาธารณะ

## การรันเทสต์

```bash
python -m unittest discover -s tests -v
```

ผลที่คาดหวัง: `Ran 34 tests ... OK`

## โครงสร้างโปรเจกต์

```
app.py                  Flask routes (GET / และ POST /) + เลือกโหมดด้วย if/elif
dc_bias.py              สมการ 3 โหมด + validation + การตัดสิน region + as_dict()
templates/index.html    ฟอร์มและตารางผลลัพธ์ (Jinja) — ไม่มีสมการฟิสิกส์
static/style.css        รูปแบบหน้าจอ
tests/test_dc_bias.py   เทสต์สมการและ validation (22 tests)
tests/test_web.py       เทสต์ HTTP ผ่าน Flask test client (12 tests)
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

ความต้านทานกรอกเป็น **kΩ** และถูกแปลงเป็น Ω (×1000) ก่อนคำนวณ

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
| `tests/` | เขียนเทสต์ตามค่าอ้างอิง A1–A5 | รันเองทั้งหมด 34 เทสต์ และตรวจว่า Divider ยังได้ค่าเดิม |
| เอกสาร | ร่างตาราง A1–A5 และ README | ตรวจตัวเลขกับเครื่องคิดเลขก่อนส่ง |

**จุดที่เลือกฟังก์ชัน:** `app.py` ฟังก์ชัน `calculate_view()` — `if mode == "fixed" … elif mode == "emitter" … else`  
**จุดที่แปลงหน่วย:** `dc_bias.py` เท่านั้น — ทุกฟังก์ชันคูณ kΩ ด้วย 1000 ก่อนเข้าสมการ แล้วคืนค่าเป็น SI (V, A, Ω)

## การเชื่อม Playwright MCP (ทางเลือก)

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
