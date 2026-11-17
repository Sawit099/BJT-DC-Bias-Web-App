# Lab 03 Multi-mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** เพิ่มโหมด Fixed Bias และ Emitter Bias ให้เว็บ Flask เดิม โดยผล Voltage Divider ต้องไม่เปลี่ยน

**Architecture:** สมการทั้งหมดอยู่ใน `dc_bias.py` (ฟังก์ชันแยกต่อโหมด + `as_dict()`), `app.py` เลือกฟังก์ชันด้วย `if/elif` ตามค่าจากฟอร์ม, `templates/index.html` แสดงเฉพาะช่องของโหมดและปรับตารางผล

**Tech Stack:** Python 3.15, Flask 3.1, Jinja2, unittest

**Spec:** `docs/superpowers/specs/2026-11-17-lab03-multi-mode-design.md`

## Global Constraints

- ค่าเริ่มต้น A1–A5: `VCC=12 V`, `RC=2.2 kΩ`, `β=100`, `VBE=0.70 V`
- ความต้านทานในฟอร์มเป็น kΩ, แปลงเป็น Ω ใน `dc_bias.py` เท่านั้น
- เกณฑ์ warning: `IB ≤ 0` → Cutoff, `VCE ≤ 0.2 V` → Saturation
- ข้อความ UI/error เป็นภาษาไทย, ชื่อปริมาณเป็นอังกฤษ
- ห้ามมีสมการใน template หรือ `app.py`
- รันเทสต์ด้วย `python -m unittest discover -s tests -v`

## Review Focus

1. เลือก Fixed แล้วยังต้องกรอก RE → ต้องไม่บังคับ (A2 ผ่านโดยไม่กรอก RE)
2. Emitter เปลี่ยน RE จาก 1k → 2k แล้วผลไม่เปลี่ยน → ค่า RE ต้องถึงสมการ
3. `mode` ที่ไม่รู้จัก (เช่น `?mode=foo`) → error ไม่ใช่ Divider เงียบ ๆ
4. หลัง error ต้องไม่เห็นผลรอบก่อนค้างบนหน้า
5. Divider เดิมต้องได้ IC 1.2299 mA / VCE 8.0522 V เท่าเดิม

---

### Task 1: ฟังก์ชันคำนวณ Fixed และ Emitter + `as_dict()`

**Files:**
- Modify: `dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Produces: `FixedInput(vcc_v, rb_kohm, rc_kohm, beta, vbe_v)`, `EmitterInput(vcc_v, rb_kohm, rc_kohm, re_kohm, beta, vbe_v)`, `calculate_fixed(FixedInput) -> BiasResult`, `calculate_emitter(EmitterInput) -> BiasResult`, `BiasResult.as_dict() -> dict`, `VCE_SAT_V = 0.2`

- [ ] **Step 1: เขียนเทสต์ที่ยังไม่ผ่าน** — `test_fixed_bias_reference`, `test_emitter_bias_reference`, `test_emitter_more_re_still_has_lower_ic`, `test_as_dict_uses_lab_key_names`, `test_saturation_threshold_is_0_2_v`
- [ ] **Step 2: รันให้เห็น fail** — `python -m unittest tests.test_dc_bias -v`
- [ ] **Step 3: เพิ่ม `FixedInput`, `EmitterInput`, `calculate_fixed`, `calculate_emitter`, `as_dict()`; เปลี่ยน `VCE_SAT_V = 0.2` และข้อความ warning; เปลี่ยนเงื่อนไข cutoff เป็น `ib <= 0`**
- [ ] **Step 4: รันให้ผ่านทั้งชุด** — `python -m unittest discover -s tests -v` (ต้องได้ 21 tests OK)

### Task 2: แยกการ parse ตามโหมด

**Files:**
- Modify: `dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Produces: `parse_fixed(form) -> FixedInput`, `parse_emitter(form) -> EmitterInput`, `parse_divider(form)` = `parse_inputs` เดิม, `MODE_LABELS`

- [ ] **Step 1: เขียนเทสต์** — `test_parse_fixed_ignores_re`, `test_parse_emitter_requires_re`, `test_parse_fixed_rejects_zero_rb`
- [ ] **Step 2: รันให้ fail**
- [ ] **Step 3: เพิ่ม `FIELD_LABELS` ของ `rb`, ตัวช่วย `_require_positive`, และฟังก์ชัน parse ทั้งสาม**
- [ ] **Step 4: รันทั้งชุดให้ผ่าน**

### Task 3: Flask routing + ฟอร์มเลือกโหมด

**Files:**
- Modify: `app.py`, `templates/index.html`, `static/style.css`
- Test: `tests/test_web.py`

**Interfaces:**
- Consumes: `calculate_fixed`, `calculate_emitter`, `calculate`, `parse_*`
- Produces: `GET /?mode=fixed` คืนฟอร์มโหมด Fixed, `POST /` รับ `mode` ในฟอร์ม

- [ ] **Step 1: เขียนเทสต์ HTTP** — `test_fixed_mode_shows_only_its_fields`, `test_emitter_mode_uses_re`, `test_unknown_mode_is_error`, `test_error_does_not_show_previous_result`
- [ ] **Step 2: รันให้ fail**
- [ ] **Step 3: เพิ่ม `MODES`, dispatch `if/elif`, ส่ง `mode` และ `modes` ให้ template; ปรับฟอร์มเป็น select + ปุ่มเปลี่ยนโหมด (GET) และช่องตามโหมด**
- [ ] **Step 4: รันทั้งชุดให้ผ่าน** (ต้องได้ 25 tests OK)

### Task 4: เอกสาร A1–A5 และ README

**Files:**
- Modify: `docs/validation.md`, `README.md`

- [ ] **Step 1: เพิ่มตาราง A1–A5 พร้อมค่าคาดหมาย/เห็นจริง/วิธีตรวจ/สถานะ**
- [ ] **Step 2: เพิ่มหัวข้อโหมดทั้งสาม + เกณฑ์ 0.2 V + วิธีตรวจ (OpenCode Browser) ใน README**
- [ ] **Step 3: รันเทสต์ทั้งชุดและ `git status` ก่อน commit**
