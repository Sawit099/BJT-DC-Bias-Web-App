# Design Note — BJT DC Bias Web App (Lab 02)

## โจทย์

พัฒนา Web Application สำหรับคำนวณ DC Operating Point ของวงจร BJT NPN Common Emitter
แบบ Voltage-Divider Bias โดยรับ VCC, R1, R2, RC, RE, β, VBE จากหน้าเว็บ
และให้ Python เป็นผู้คำนวณ ไม่ใช่ JavaScript หรือค่าที่เขียนค้างไว้ใน HTML

## สถาปัตยกรรม 3 ชั้น

```
Browser (ฟอร์ม HTML)
   │  POST /  (application/x-www-form-urlencoded)
   ▼
app.py — Flask route
   │  เรียก parse_inputs(request.form)
   ▼
dc_bias.py — parse_inputs() → BiasInput → calculate() → BiasResult
   │  (pure Python: ไม่รู้จัก HTTP/HTML)
   ▼
templates/index.html — แสดงผลด้วย Jinja
```

| ชั้น | ไฟล์ | หน้าที่ |
|---|---|---|
| Presentation | `templates/index.html`, `static/style.css` | ฟอร์ม, ตารางผล, badge, warning |
| Web / HTTP | `app.py` | รับ request, เรียก logic, เลือก template |
| Engineering | `dc_bias.py` | สมการ, validation, ตัดสิน region |
| Verification | `tests/` | ตรวจทั้งสมการและ HTTP |

การแยกชั้นนี้ทำให้แก้สมการในไฟล์เดียวโดยไม่ต้องแตะ HTML และเขียนเทสต์สมการได้
โดยไม่ต้องเปิด Flask

## ทางเลือกที่พิจารณา

| ทาง | ข้อดี | ข้อเสีย | สรุป |
|---|---|---|---|
| **หน้าเดียว `GET /` + `POST /`** | ตรงเกณฑ์ A1/A2, test ง่าย, ไม่ต้องมี session | refresh แล้วเบราว์เซอร์เตือน re-submit | **เลือก** |
| `POST /calculate` + redirect (PRG) | กัน double-submit | ต้องมี secret key, session, flash และเทสต์เพิ่ม | ตัดออก |
| JSON API + `fetch()` | แยก frontend/backend ชัด | เกินขอบเขต Lab และไม่ตรง A2 | ตัดออก |

## การตัดสินใจสำคัญ

1. **รับความต้านทานเป็น kΩ** แล้วแปลง ×1000 ภายใน `dc_bias.py` — ตรงกับค่าตัวอย่าง
   ในเอกสาร Lab และลดโอกาสกรอกผิด (100 แทน 100000)
2. **`BiasResult` เป็น immutable dataclass หน่วย SI** — template แปลงเป็น mA/µA เอง
   ทำให้ชั้นวิศวกรรมไม่ผูกกับรูปแบบการแสดงผล
3. **เกณฑ์ Saturation ที่ VCE < 0.3 V** — เอกสาร Lab ไม่ได้ระบุตัวเลข
   จึงเลือกค่า VCE(sat) มาตรฐานและประกาศไว้ใน README ว่าเป็นสมมติฐาน
4. **ไม่ clamp ค่าเมื่อออกนอก active region** — แสดงค่าดิบพร้อมขีดฆ่าและ warning
   เพื่อไม่ให้เข้าใจผิดว่าเป็นผลที่ใช้ได้

## ข้อจำกัดของแบบจำลอง

- ใช้ forward-active approximation เท่านั้น: β และ VBE คงที่
- ไม่มี Early effect (output resistance), leakage, self-heating
- ไม่ใช่ SPICE simulator — ผลในย่าน cutoff/saturation เป็นเพียงค่าที่สมการให้
  ไม่ใช่คำตอบทางกายภาพ
- ขอบเขตคาบนี้ไม่มี AC analysis, load line, transient หรือ Bode plot
