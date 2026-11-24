import unittest
from pathlib import Path
from unittest import mock

import spice_engine
from app import app

ROOT = Path(__file__).resolve().parent.parent

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

    def test_error_names_the_selected_mode(self):
        """Lab 03: errors must say which mode failed, not just 'cannot calculate'."""
        body = self.client.post("/", data={**FIXED_FORM, "rb": "0"}).get_data(as_text=True)
        self.assertIn("ไม่สามารถคำนวณได้ · Fixed Bias", body)

    def test_unknown_mode_error_names_the_bad_value(self):
        body = self.client.post("/", data={**FIXED_FORM, "mode": "spice"}).get_data(as_text=True)
        self.assertIn("ไม่สามารถคำนวณได้", body)
        self.assertIn("spice", body)


class TestSharedResultContract(unittest.TestCase):
    """Lab 03 grades the shared dict keys, so the page must read them directly."""

    def test_template_reads_the_shared_result_keys(self):
        source = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
        for key in ("vb_v", "ve_v", "vc_v", "vce_v", "ic_ma", "ib_ua", "ie_ma"):
            self.assertIn(f"result['{key}']", source)

    def test_template_does_no_unit_conversion_of_current(self):
        source = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("result['ic_a']", source)
        self.assertNotIn("result['ib_a']", source)
        self.assertNotIn("result['ie_a']", source)


class TestSpiceApi(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.payload = {
            "analysis": "op",
            "vcc": "12",
            "r1": "100",
            "r2": "22",
            "rc": "2.2",
            "re": "1",
            "rl": "10",
            "cin": "10",
            "cout": "10",
            "amp": "10",
            "freq": "1000",
        }

    def test_invalid_re_returns_ok_false(self):
        res = self.client.post("/api/simulate", json={**self.payload, "re": "0"})
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertFalse(data["ok"])
        self.assertIn("RE", data["error"])

    def test_missing_ngspice_reports_error(self):
        with mock.patch("app.spice_engine.find_ngspice", side_effect=spice_engine.NgspiceNotFoundError("not found")):
            res = self.client.post("/api/simulate", json=self.payload)
        data = res.get_json()
        self.assertFalse(data["ok"])


class TestSimulatorUi(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_has_simulator_section(self):
        body = self.client.get("/").get_data(as_text=True)
        for token in ["CE Amplifier", "ngspice", "amp", "freq", "acChart", "tranChart", "Run Simulation"]:
            self.assertIn(token, body)

    def test_chartjs_script_included(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn("chart.umd.min.js", body)
