import os
import unittest
from unittest import mock

import spice_engine as se


class TestNgspiceDiscovery(unittest.TestCase):
    def test_default_model_name_constant(self):
        self.assertEqual(se.DEFAULT_MODEL_NAME, "Q2N3904_LAB04")
        self.assertIn(".model Q2N3904_LAB04 NPN", se.DEFAULT_MODEL_CARD)

    def test_find_ngspice_uses_env_override(self):
        with mock.patch.dict(os.environ, {"NGSPICE_EXE": __file__}):
            self.assertEqual(se.find_ngspice(), os.path.abspath(__file__))

    def test_find_ngspice_raises_when_missing(self):
        with mock.patch.dict(os.environ, {"NGSPICE_EXE": ""}, clear=False):
            with mock.patch("spice_engine.shutil.which", return_value=None):
                with mock.patch("spice_engine.os.path.isfile", return_value=False):
                    with self.assertRaises(se.NgspiceNotFoundError):
                        se.find_ngspice()


@unittest.skipUnless(se.ngspice_available(), "ngspice not installed")
class TestOpRun(unittest.TestCase):
    def test_run_op_reference_values(self):
        inp = se.CEInput(vcc=12, r1k=100, r2k=22, rck=2.2, rek=1.0, rlk=10, cin_u=10, cout_u=10, vin_mvp=10, freq_hz=1000)
        r = se.run_op(inp)
        self.assertEqual(r.engine, "ngspice")
        self.assertEqual(r.model, "Q2N3904_LAB04")
        self.assertAlmostEqual(r.vb, 2.05, delta=0.15)
        self.assertAlmostEqual(r.ve, 1.38, delta=0.15)
        self.assertAlmostEqual(r.vc, 8.98, delta=0.25)
        self.assertAlmostEqual(r.vce, 7.60, delta=0.25)
        self.assertTrue(r.ic_ma > 0)

    def test_invalid_rejected_before_run(self):
        with self.assertRaises(se.NgspiceError):
            se.CEInput(vcc=12, r1k=100, r2k=22, rck=2.2, rek=0, rlk=10, cin_u=10, cout_u=10, vin_mvp=10, freq_hz=1000).validate()


if __name__ == "__main__":
    unittest.main()

