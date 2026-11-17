import math
import unittest

from dc_bias import (
    BiasInput,
    EmitterInput,
    FixedInput,
    Region,
    ValidationError,
    calculate,
    calculate_emitter,
    calculate_fixed,
    parse_emitter,
    parse_fixed,
    parse_inputs,
)

REF = BiasInput(vcc_v=12.0, r1_kohm=100.0, r2_kohm=22.0, rc_kohm=2.2,
                re_kohm=1.0, beta=100.0, vbe_v=0.70)
FORM = {"vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
        "re": "1", "beta": "100", "vbe": "0.70"}


class TestReferenceCase(unittest.TestCase):
    def test_reference_case_matches_hand_calculation(self):
        r = calculate(REF)
        self.assertAlmostEqual(r.vth_v, 2.1639, delta=0.0108)
        self.assertAlmostEqual(r.rth_ohm, 18032.8, delta=90.2)
        self.assertAlmostEqual(r.ib_a * 1e6, 12.299, delta=0.0615)
        self.assertAlmostEqual(r.ic_a * 1e3, 1.2299, delta=0.00615)
        self.assertAlmostEqual(r.ie_a * 1e3, 1.2422, delta=0.00621)
        self.assertAlmostEqual(r.ve_v, 1.2422, delta=0.00621)
        self.assertAlmostEqual(r.vb_v, 1.9422, delta=0.00971)
        self.assertAlmostEqual(r.vc_v, 9.2942, delta=0.0465)
        self.assertAlmostEqual(r.vce_v, 8.0520, delta=0.0403)
        self.assertIsNone(r.warning)

    def test_region_is_active_for_reference_case(self):
        self.assertEqual(calculate(REF).region, Region.ACTIVE)


class TestRegionDetection(unittest.TestCase):
    def test_cutoff_when_vth_not_above_vbe(self):
        r = calculate(BiasInput(12.0, 100.0, 22.0, 2.2, 1.0, 100.0, 3.0))
        self.assertEqual(r.region, Region.CUTOFF)
        self.assertLess(r.ib_a, 0.0)
        self.assertIsNotNone(r.warning)

    def test_saturation_when_vce_below_saturation(self):
        r = calculate(BiasInput(12.0, 100.0, 22.0, 10.0, 1.0, 100.0, 0.70))
        self.assertEqual(r.region, Region.SATURATION)
        self.assertLess(r.vce_v, 0.3)
        self.assertIsNotNone(r.warning)


class TestUnitsAndParsing(unittest.TestCase):
    def test_inputs_interpreted_as_kohm(self):
        self.assertAlmostEqual(calculate(REF).rth_ohm, 18032.8, delta=90.2)

    def test_strips_surrounding_whitespace(self):
        parsed = parse_inputs({**FORM, "vcc": " 12 ", "re": " 1 "})
        self.assertAlmostEqual(parsed.vcc_v, 12.0)
        self.assertAlmostEqual(parsed.re_kohm, 1.0)

    def test_rejects_comma_decimal(self):
        with self.assertRaises(ValidationError) as ctx:
            parse_inputs({**FORM, "rc": "2,2"})
        self.assertEqual(ctx.exception.field, "rc")

    def test_rejects_vbe_not_below_vcc(self):
        with self.assertRaises(ValidationError) as ctx:
            parse_inputs({**FORM, "vbe": "12"})
        self.assertEqual(ctx.exception.field, "vbe")


class TestValidation(unittest.TestCase):
    def test_rejects_non_positive_and_non_numeric(self):
        cases = [("vcc", "0"), ("vcc", "-1"), ("r1", "-1"), ("r1", "0"),
                 ("beta", "0"), ("beta", "-5"), ("vcc", "abc"), ("r2", "")]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValidationError) as ctx:
                    parse_inputs({**FORM, field: value})
                self.assertEqual(ctx.exception.field, field)

    def test_huge_beta_stays_finite(self):
        r = calculate(BiasInput(12.0, 100.0, 22.0, 2.2, 1.0, 1e6, 0.70))
        for value in (r.ib_a, r.ic_a, r.ie_a, r.vce_v):
            self.assertTrue(math.isfinite(value))

    def test_rejects_non_finite_numbers(self):
        for value in ("nan", "inf", "-inf", "1e400"):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError) as ctx:
                    parse_inputs({**FORM, "vcc": value})
                self.assertEqual(ctx.exception.field, "vcc")


class TestFixedBias(unittest.TestCase):
    """Lab 03 A2: Fixed Bias, RB = 1 MOhm, RC = 2.2 kOhm."""

    def test_fixed_bias_reference(self):
        r = calculate_fixed(FixedInput(12.0, 1000.0, 2.2, 100.0, 0.70))
        self.assertAlmostEqual(r.ib_a * 1e6, 11.300, delta=0.06)
        self.assertAlmostEqual(r.ic_a * 1e3, 1.1300, delta=0.006)
        self.assertAlmostEqual(r.ve_v, 0.0, delta=1e-12)
        self.assertAlmostEqual(r.vb_v, 0.70, delta=0.005)
        self.assertAlmostEqual(r.vc_v, 9.5140, delta=0.05)
        self.assertAlmostEqual(r.vce_v, 9.5140, delta=0.05)
        self.assertEqual(r.region, Region.ACTIVE)

    def test_fixed_result_has_no_divider_terms(self):
        r = calculate_fixed(FixedInput(12.0, 1000.0, 2.2, 100.0, 0.70))
        self.assertIsNone(r.vth_v)
        self.assertIsNone(r.rth_ohm)


class TestEmitterBias(unittest.TestCase):
    """Lab 03 A3/A4: Emitter Bias, RB = 1 MOhm, RE = 1 kOhm then 2 kOhm."""

    def test_emitter_bias_reference(self):
        r = calculate_emitter(EmitterInput(12.0, 1000.0, 2.2, 1.0, 100.0, 0.70))
        self.assertAlmostEqual(r.ib_a * 1e6, 10.263, delta=0.06)
        self.assertAlmostEqual(r.ic_a * 1e3, 1.0263, delta=0.006)
        self.assertAlmostEqual(r.ve_v, 1.0366, delta=0.006)
        self.assertAlmostEqual(r.vce_v, 8.7054, delta=0.02)

    def test_more_re_lowers_ic(self):
        one_k = calculate_emitter(EmitterInput(12.0, 1000.0, 2.2, 1.0, 100.0, 0.70))
        two_k = calculate_emitter(EmitterInput(12.0, 1000.0, 2.2, 2.0, 100.0, 0.70))
        self.assertLess(two_k.ic_a, one_k.ic_a)
        self.assertAlmostEqual(two_k.ic_a * 1e3, 0.9401, delta=0.006)
        self.assertAlmostEqual(two_k.vce_v, 8.0328, delta=0.02)


class TestResultDictionary(unittest.TestCase):
    def test_as_dict_uses_lab_key_names(self):
        data = calculate(REF).as_dict()
        for key in ("vb_v", "ve_v", "vc_v", "vce_v", "ic_ma", "ib_ua",
                    "ie_ma", "vth_v", "rth_ohm", "region", "warning"):
            self.assertIn(key, data)
        self.assertAlmostEqual(data["ic_ma"], 1.2299, delta=0.006)
        self.assertEqual(data["region"], "active")
        self.assertIsNone(data["warning"])


class TestSaturationThreshold(unittest.TestCase):
    """Lab 03 uses VCE(sat) = 0.2 V, not the 0.3 V of Lab 02."""

    def test_vce_of_0_243_v_is_active(self):
        r = calculate(BiasInput(12.0, 100.0, 22.0, 8.55, 1.0, 100.0, 0.70))
        self.assertAlmostEqual(r.vce_v, 0.2426, delta=0.005)
        self.assertEqual(r.region, Region.ACTIVE)
        self.assertIsNone(r.warning)


FIXED_FORM = {"mode": "fixed", "vcc": "12", "rb": "1000", "rc": "2.2",
              "beta": "100", "vbe": "0.70"}
EMITTER_FORM = {"mode": "emitter", "vcc": "12", "rb": "1000", "rc": "2.2",
                "re": "1", "beta": "100", "vbe": "0.70"}


class TestModeParsing(unittest.TestCase):
    def test_parse_fixed_does_not_need_re(self):
        parsed = parse_fixed(FIXED_FORM)
        self.assertAlmostEqual(parsed.rb_kohm, 1000.0)
        self.assertFalse(hasattr(parsed, "re_kohm"))

    def test_parse_emitter_requires_re(self):
        with self.assertRaises(ValidationError) as ctx:
            parse_emitter(EMITTER_FORM | {"re": ""})
        self.assertEqual(ctx.exception.field, "re")

    def test_parse_fixed_rejects_zero_rb(self):
        with self.assertRaises(ValidationError) as ctx:
            parse_fixed(FIXED_FORM | {"rb": "0"})
        self.assertEqual(ctx.exception.field, "rb")

    def test_parse_emitter_rejects_negative_re(self):
        with self.assertRaises(ValidationError) as ctx:
            parse_emitter(EMITTER_FORM | {"re": "-1"})
        self.assertEqual(ctx.exception.field, "re")

    def test_parse_divider_still_requires_r1(self):
        with self.assertRaises(ValidationError) as ctx:
            parse_inputs(FORM | {"r1": ""})
        self.assertEqual(ctx.exception.field, "r1")
