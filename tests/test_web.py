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
        self.assertIn("2.164", body)     # VTH [V]
        self.assertIn("18.033", body)    # RTH [kΩ]
        self.assertIn("12.299", body)    # IB [µA]


class TestInvalidInput(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_missing_field_shows_error_not_500(self):
        res = self.client.post("/", data={"vcc": "12"})
        self.assertEqual(res.status_code, 200)
        body = res.get_data(as_text=True)
        self.assertNotIn("Traceback", body)
        self.assertIn("กรุณากรอก R1 [kΩ] เป็นตัวเลข", body)

    def test_invalid_value_shows_thai_error(self):
        res = self.client.post("/", data={**FORM, "beta": "0"})
        self.assertEqual(res.status_code, 200)
        body = res.get_data(as_text=True)
        self.assertIn("β ต้องมากกว่า 0", body)
        self.assertNotIn("β ต้องมากกว่า 0", self.client.post("/", data=FORM).get_data(as_text=True))

    def test_post_without_any_form_data_does_not_crash(self):
        res = self.client.post("/")
        self.assertEqual(res.status_code, 200)
