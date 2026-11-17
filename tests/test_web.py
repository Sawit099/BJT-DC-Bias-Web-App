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


FIXED_FORM = {"mode": "fixed", "vcc": "12", "rb": "1000", "rc": "2.2",
              "beta": "100", "vbe": "0.70"}
EMITTER_FORM = {"mode": "emitter", "vcc": "12", "rb": "1000", "rc": "2.2",
                "re": "1", "beta": "100", "vbe": "0.70"}


class TestModeSelection(unittest.TestCase):
    """Lab 03: choose the bias mode, show only the fields that mode needs."""

    def setUp(self):
        self.client = app.test_client()

    def test_fixed_form_shows_rb_and_not_divider_fields(self):
        body = self.client.get("/?mode=fixed").get_data(as_text=True)
        self.assertIn('name="rb"', body)
        self.assertNotIn('name="r1"', body)

    def test_emitter_form_shows_rb_and_re(self):
        body = self.client.get("/?mode=emitter").get_data(as_text=True)
        self.assertIn('name="rb"', body)
        self.assertIn('name="re"', body)

    def test_fixed_post_calculates_without_re(self):
        body = self.client.post("/", data=FIXED_FORM).get_data(as_text=True)
        self.assertIn("1.130", body)     # IC [mA]
        self.assertIn("9.514", body)     # VCE [V]
        self.assertNotIn("2.164", body)  # no VTH row for fixed bias

    def test_emitter_post_uses_re(self):
        body = self.client.post("/", data=EMITTER_FORM).get_data(as_text=True)
        self.assertIn("1.026", body)     # IC [mA]
        self.assertIn("8.705", body)     # VCE [V]

    def test_result_names_the_mode(self):
        body = self.client.post("/", data=FIXED_FORM).get_data(as_text=True)
        self.assertIn("Fixed Bias", body)

    def test_unknown_mode_is_an_error(self):
        res = self.client.post("/", data={**FIXED_FORM, "mode": "spice"})
        body = res.get_data(as_text=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("โหมด", body)
        self.assertNotIn("badge-active", body)

    def test_failed_input_does_not_show_previous_result(self):
        body = self.client.post("/", data={**FIXED_FORM, "rb": "0"}).get_data(as_text=True)
        self.assertIn("RB [kΩ] ต้องมากกว่า 0", body)
        self.assertNotIn("9.514", body)
