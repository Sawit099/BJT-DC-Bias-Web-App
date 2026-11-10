# BJT DC Bias Web App

Flask Web Application สำหรับคำนวณ **DC Operating Point** ของวงจร BJT NPN Common Emitter
แบบ **Voltage-Divider Bias** — กรอกค่าอุปกรณ์ในเบราว์เซอร์ แล้ว Python Backend
คำนวณ VB, VE, VC, VCE, IC, IB, IE ส่งกลับมาแสดงพร้อมหน่วย

สร้างเป็นผลงาน Lab 02 รายวิชา ENG29 2121 Computer Programming for Electrical Engineers

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

ผลที่คาดหวัง: `Ran 16 tests ... OK`

## โครงสร้างโปรเจกต์

```
app.py                  Flask routes (GET / และ POST /)
dc_bias.py              สมการ DC bias + validation + การตัดสิน region
templates/index.html    ฟอร์มและตารางผลลัพธ์ (Jinja) — ไม่มีสมการฟิสิกส์
static/style.css        รูปแบบหน้าจอ
tests/test_dc_bias.py   เทสต์สมการและ validation (11 tests)
tests/test_web.py       เทสต์ HTTP ผ่าน Flask test client (5 tests)
```

## แบบจำลองที่ใช้

ใช้ **Forward-Active Approximation** โดยถือว่า

- β คงที่ตามค่าที่ผู้ใช้กรอก
- VBE คงที่ตามค่าที่ผู้ใช้กรอก
- ไม่คิด Early effect, leakage current หรือผลของอุณหภูมิ

สมการ:

```
VTH = VCC · R2 / (R1 + R2)          RTH = R1 · R2 / (R1 + R2)
IB  = (VTH − VBE) / (RTH + (β + 1)·RE)
IC  = β · IB        IE = (β + 1)·IB
VE  = IE · RE       VB = VE + VBE
VC  = VCC − IC · RC VCE = VC − VE
```

ความต้านทานกรอกเป็น **kΩ** และถูกแปลงเป็น Ω (×1000) ก่อนคำนวณ

## เกณฑ์การตัดสิน Region

| เงื่อนไข | Region | สิ่งที่เว็บแสดง |
|---|---|---|
| `VTH ≤ VBE` | Cutoff | badge Cutoff + warning ว่าค่า IB ติดลบและแบบจำลองใช้ไม่ได้ |
| `VCE < 0.3 V` | Saturation | badge Saturation + warning ว่า VCE ต่ำกว่า VCE(sat) |
| นอกนั้น | Active | badge Active |

> **0.3 V เป็นสมมติฐานของผู้พัฒนา** (ค่า VCE(sat) ที่ใช้กันทั่วไปสำหรับ BJT ขนาดเล็ก)
> ไม่ได้มาจาก datasheet ของอุปกรณ์จริง

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
- [`docs/validation.md`](docs/validation.md) — ตารางตรวจสอบผลและข้อจำกัด
- [`docs/reflection.md`](docs/reflection.md) — สิ่งที่ได้เรียนรู้
