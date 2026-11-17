# Lab 03 — เว็บเลือกวงจรได้ 3 โหมด (Design)

วันที่: 2026-11-17
ต่อยอดจาก: Lab 02 (`docs/superpowers/specs/2026-11-10-bjt-dc-bias-web-app-design.md`)

## เป้าหมาย

เว็บ Flask เดิมรองรับ **3 วงจรไบอัส** เลือกได้จากฟอร์ม: Voltage Divider (ของเดิม),
Fixed Bias และ Emitter Bias โดย **ผลของ Divider ต้องไม่เปลี่ยน** และตรวจผลผ่าน
เบราว์เซอร์จริงตามตาราง A1–A5 ของใบงาน Lab 03

## ขอบเขต

**ทำ**: เพิ่มตัวเลือกโหมด, ฟังก์ชันคำนวณสองตัวใหม่, routing ใน Flask,
ฟอร์มที่แสดงเฉพาะช่องของโหมด, ตารางผลที่ปรับตามโหมด, เอกสาร A1–A5

**ไม่ทำ**: SPICE, DC load line, AC/transient, capacitor bypass, JavaScript,
สคริปต์ Playwright, unittest ของ lab (แต่ยังเขียนเทสต์ตาม AGENTS.md)

## สมการ (จากใบงาน Lab 03)

| โหมด | I_B | V_E |
|---|---|---|
| Divider | (V_TH − V_BE) / [R_TH + (β+1)R_E] | I_E·R_E |
| Fixed | (V_CC − V_BE) / R_B | 0 |
| Emitter | (V_CC − V_BE) / [R_B + (β+1)R_E] | I_E·R_E |

ร่วมทุกโหมด: `IC = β·IB`, `IE = (β+1)·IB`, `VB = VE + VBE`, `VC = VCC − IC·RC`, `VCE = VC − VE`
`VTH = VCC·R2/(R1+R2)`, `RTH = R1R2/(R1+R2)` (เฉพาะ Divider)

## สัญญาผลลัพธ์

ทุกฟังก์ชันคืน `BiasResult` (frozen dataclass, หน่วย SI) และมี `as_dict()`
คืน dict ที่ใช้ชื่อคีย์ตามใบงาน: `vb_v, ve_v, vc_v, vce_v, ic_ma,
ib_ua, ie_ma, vth_v, rth_ohm, region, warning`
(`vth_v`/`rth_ohm` เป็น `None` ในโหมด Fixed/Emitter)

## การตรวจอินพุต

- ค่าไม่ครบ / ไม่ใช่ตัวเลข / ไม่ finite / ≤ 0 → `ValidationError(field, ข้อความไทย)`
- ตรวจเฉพาะช่องที่โหมดนั้นใช้: Divider = vcc,r1,r2,rc,re,beta,vbe ·
  Fixed = vcc,rb,rc,beta,vbe · Emitter = vcc,rb,rc,re,beta,vbe
- `mode` ไม่รู้จัก → error ไม่เดาเป็น Divider
- อินพุตถูกแต่ `IB ≤ 0` → Region CUTOFF + warning
- อินพุตถูกแต่ `VCE ≤ 0.2 V` → Region SATURATION + warning
- ค่าที่ผิดไม่แสดงผลรอบก่อน (result = None ทุกครั้งที่ error)

## UI

```
[ โหมดวงจร ▼ ]  [ เปลี่ยนโหมด ]      ← GET /?mode=...  (ไม่ใช้ JS)
------------------------------------
VCC, β, VBE  +  ช่องเฉพาะโหมด
[ Calculate DC Bias ]                 ← POST /
------------------------------------
ผลลัพธ์ (ระบุชื่อโหมด) + badge + warning
```

## การตัดสินใจ

| เรื่อง | เลือก | เหตุผล | ถ้าผิด |
|---|---|---|---|
| รูปแบบผลลัพธ์ | dataclass + `as_dict()` | รักษาเทสต์ 16 ตัวเดิมที่ยืนยัน Divider | อาจเสียคะแนน "ส่งผลด้วย dict" บางส่วน |
| เกณฑ์ saturation | 0.2 V | ใบงาน Lab 03 ระบุชัด (Lab 02 ใช้ 0.3) | ผลตัดสิน region ต่างจากใบงาน |
| unittest | เขียนเพิ่ม | AGENTS.md ข้อ 3 บังคับ; ใบงานบอกแค่ "ไม่ต้อง" ไม่ใช่ "ห้าม" | เสียเวลาเล็กน้อย |
| Playwright MCP | ไม่ติดตั้ง Node | เครื่องไม่มี Node และใบงานอนุญาตให้ใช้ OpenCode Browser แทน | ต้องระบุวิธีตรวจว่าเป็น OpenCode Browser |
| ฟังก์ชันเดิม | เก็บ `calculate()` เป็น alias ของ Divider | เทสต์เดิมและ README ยังใช้ได้ | — |

## ความเสี่ยง

- Divider เสียจาก refactor → คุมด้วยเทสต์เดิม 16 ตัวที่ต้องเขียวก่อน/หลัง
- ฟอร์มเปลี่ยนช่องตามโหมดแล้วค่าเก่าหลุด → เก็บค่าเดิมไว้ใน `form` ที่ส่งกลับ
- เทมเพลตอาจมีผลรอบก่อนค้าง → error ต้อง `result=None`
