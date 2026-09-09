import unittest
from unittest.mock import patch

from aeris_runtime.engineering import catalog


class EngineeringNumericalTests(unittest.TestCase):
    def test_loaded_code_cannot_relabel_itself_after_disk_change(self):
        with patch.object(catalog,"_disk_implementation_digest",return_value="changed"):
            with self.assertRaises(RuntimeError): catalog.implementation_digest()
    def test_each_distinct_method_against_analytical_and_negative_cases(self):
        for skill in catalog.definitions():
            with self.subTest(skill=skill):
                result=catalog.evaluate(skill)
                self.assertTrue(result["passed"],result)

    def test_nonfinite_and_unknown_parameters_fail_closed(self):
        p=catalog.definitions()["spectral-analysis"]["fixture"]["input"]
        for extra in ({"sample_rate_hz":float("nan")},{"command":"run arbitrary shell"},{"sample_rate_hz":True}):
            with self.assertRaises((ValueError,KeyError)):
                catalog.execute("spectral-analysis",{**p,**extra})

    def test_nyquist_and_dc_are_not_doubled(self):
        for samples,index in (([1.0]*32,0),([(-1.0)**i for i in range(32)],16)):
            result=catalog.execute("spectral-analysis",{"samples":samples,"sample_rate_hz":32,"window":"rectangular"})
            self.assertAlmostEqual(result["values"]["amplitude"][index],1)
            self.assertEqual(result["values"]["ifft_reconstructed_windowed_samples"],samples)

    def test_harmonic_fit_handles_noncoherent_record(self):
        import math
        samples=[math.sin(2*math.pi*517*i/8192)+.1*math.sin(2*math.pi*1034*i/8192) for i in range(1001)]
        result=catalog.execute("harmonic-noise-analysis",{"samples":samples,"sample_rate_hz":8192,"fundamental_hz":517,"harmonics":5})
        self.assertAlmostEqual(result["values"]["thd_ratio"],.1,places=10)

    def test_uncertainty_rejects_non_psd_correlation(self):
        p=catalog.definitions()["uncertainty-propagation"]["fixture"]["input"]
        with self.assertRaises(ValueError): catalog.execute("uncertainty-propagation",{**p,"correlation_matrix":[[1,2],[2,1]]})

    def test_synthetic_cannot_be_promoted_to_physical(self):
        p=catalog.definitions()["evidence-counterreview"]["fixture"]["input"]
        p["claims"]=[{"classification":"EVIDENCE","source_kind":"SYNTHETIC","real_measurement_verified":True,"evidence_refs":[]}]
        result=catalog.execute("evidence-counterreview",p)
        self.assertIn("SYNTHETIC_AS_PHYSICAL",{r["code"] for r in result["values"]["findings"]})
