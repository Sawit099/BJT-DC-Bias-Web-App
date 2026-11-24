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


if __name__ == "__main__":
    unittest.main()
