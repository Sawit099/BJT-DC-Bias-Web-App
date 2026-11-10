# AGENTS.md — กติกาการพัฒนาโปรเจกต์ BJT DC Bias Web App

เอกสารนี้ใช้กับทั้งมนุษย์และ AI agent ที่เข้ามาแก้โค้ดใน repository นี้

## 1. แยกชั้นความรับผิดชอบ

| ไฟล์ | รับผิดชอบ | ห้าม |
|---|---|---|
| `dc_bias.py` | สมการ DC bias, validation, การตัดสิน region | ห้าม import `flask`, `jinja2`, `werkzeug` หรืออะไรที่เกี่ยวกับ HTTP/HTML |
| `app.py` | Flask app และ route เท่านั้น | ห้ามมีสมการฟิสิกส์ |
| `templates/index.html` | แสดงฟอร์มและผลลัพธ์ด้วย Jinja | ห้ามมีสูตรคำนวณหรือตัวเลขผลลัพธ์ฝังอยู่ |
| `static/style.css` | รูปแบบหน้าจอ | — |
| `tests/` | ตรวจพฤติกรรมของทั้ง engine และ HTTP | — |

## 2. ห้าม hardcode ผลลัพธ์

ตัวเลข VB, VE, VC, VCE, IC, IB, IE ต้องมาจาก `calculate()` ใน `dc_bias.py` เท่านั้น
ถ้าพบตัวเลขผลลัพธ์ใน template หรือ JavaScript ถือว่าเป็น bug

## 3. การทดสอบ

- ใช้ `unittest` เท่านั้น (ไม่ใช้ pytest)
- รันด้วย `python -m unittest discover -s tests -v`
- ทุกฟีเจอร์ใหม่ต้องมีเทสต์ที่เขียนก่อนโค้ด และต้องเห็นเทสต์ fail ก่อน implement

## 4. ภาษา

- UI labels, ข้อความ error และ warning: ภาษาไทย
- ชื่อปริมาณ: อังกฤษ (VCC, R1, VB, VCE, IC, β)
- ชื่อตัวแปร ฟังก์ชัน และชื่อ test: อังกฤษ
- เอกสาร (README, docs/) : ภาษาไทย

## 5. Git

- Commit ผ่าน **GitHub Desktop** เป็นวิธีหลัก; กรณีจำเป็น (หรือทำผ่าน agent) ใช้ `git` CLI ได้
  แต่ต้องตรวจ diff ก่อน commit ทุกครั้ง
- ห้าม commit `.venv/`, `__pycache__/`, `.env` หรือ credential ใด ๆ
- ข้อความ commit ใช้รูปแบบ `type: subject` เช่น `feat:`, `fix:`, `docs:`, `chore:`
