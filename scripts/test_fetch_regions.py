import importlib.util
from pathlib import Path
import unittest
import io

spec = importlib.util.spec_from_file_location("fetch_regions", Path(__file__).with_name("fetch_regions.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def xml(rows, total):
    entries = "".join("<row>" + "".join("<%s>%s</%s>" % (k, v, k) for k, v in r.items()) + "</row>" for r in rows)
    return ("<StanReginCd><head><totalCount>%s</totalCount><RESULT><resultCode>INFO-0</resultCode></RESULT></head>%s</StanReginCd>" % (total, entries)).encode()


class RegionTests(unittest.TestCase):
    def setUp(self):
        # Synthetic hierarchy; not official codes or region names.
        self.parent = {"region_cd": "9900000000", "locathigh_cd": "0000000000", "locatadd_nm": "시험광역"}
        self.child = {"region_cd": "9910000000", "locathigh_cd": "9900000000", "locatadd_nm": "시험광역 시험시"}

    def test_parse_and_pages(self):
        responses = iter([xml([self.parent], 2), xml([self.child], 2)])
        result = module.collect("fake-key", lambda *a, **kw: io.BytesIO(next(responses)))
        self.assertEqual(len(result), 2)

    def test_incomplete(self):
        responses = iter([xml([self.parent], 2), xml([], 2)])
        with self.assertRaises(ValueError):
            module.collect("fake-key", lambda *a, **kw: io.BytesIO(next(responses)))

    def test_duplicate(self):
        with self.assertRaises(ValueError):
            module.validate([self.parent, self.parent])

    def test_missing_parent(self):
        with self.assertRaises(ValueError):
            module.validate([self.child])

    def test_api_error(self):
        with self.assertRaises(ValueError):
            module.parse(b"<response><resultCode>30</resultCode></response>")

    def test_cycle(self):
        self.parent["locathigh_cd"] = self.child["region_cd"]
        with self.assertRaises(ValueError):
            module.validate([self.parent, self.child])


if __name__ == "__main__":
    unittest.main()
