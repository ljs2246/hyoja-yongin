import importlib.util
import unittest
from unittest.mock import patch
from urllib.error import URLError

spec = importlib.util.spec_from_file_location("fetch_data", __file__.replace("test_fetch_data.py", "fetch_data.py"))
data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data)


class FetchTests(unittest.TestCase):
    def test_collects_all_pages(self):
        first = [{"id": str(i)} for i in range(200)]
        last = [{"id": "200"}]
        with patch.object(data, "call_page", side_effect=[(first, 201), (last, 201)]) as api:
            self.assertEqual(len(data.call("path", {})), 201)
            self.assertEqual(api.call_args_list[1].args[2], 2)

    def test_incomplete_and_changing_results_fail(self):
        for pages in [
            [([{"id": "1"}], 2), ([], 2)],
            [([{"id": "1"}], 2), ([{"id": "2"}], 3)],
            [([{"id": "1"}], 2), ([{"id": "1"}], 2)],
        ]:
            with self.subTest(pages=pages), patch.object(data, "call_page", side_effect=pages):
                with self.assertRaises(RuntimeError):
                    data.call("path", {})

    def test_no_total_count_uses_short_page(self):
        first = [{"id": str(i)} for i in range(200)]
        with patch.object(data, "call_page", side_effect=[(first, None), ([], None)]):
            self.assertEqual(len(data.call("path", {})), 200)

    def test_errors_never_include_request_or_key(self):
        secret = "test+secret/key="
        encoded = "test%2Bsecret%2Fkey%3D"
        with patch.object(data, "KEY", secret), patch.object(data.urllib.request, "urlopen", side_effect=URLError("https://example/?serviceKey=" + encoded)), patch.object(data.time, "sleep"):
            with self.assertRaises(RuntimeError) as caught:
                data.call_page("path", {}, 1)
        self.assertNotIn(secret, str(caught.exception))
        self.assertNotIn(encoded, str(caught.exception))
        self.assertNotIn("https", str(caught.exception))



class ScrubTests(unittest.TestCase):
    def test_masks_phone_numbers_in_free_text(self):
        rows = [{"dutyName": "가나약국", "dutyEtc": "전화번호 010-8232-7579 휴무 없음", "dutyInf": "070-7608-4016, 031-897-3007, 01082327579, +82 10-1234-5678, 1577-1000", "dutyMapimg": "역 앞 2층"}]
        out = data.scrub_rows(rows)[0]
        for k in ("dutyEtc", "dutyInf"):
            self.assertIsNone(data.PHONE_RE.search(out[k]), out[k])
        self.assertIn("휴무 없음", out["dutyEtc"])
        self.assertEqual(out["dutyMapimg"], "역 앞 2층")
        self.assertEqual(out["dutyName"], "가나약국")

    def test_keeps_non_phone_numbers(self):
        rows = [{"dutyEtc": "오전9시부터 오후7시까지 2026-11-08 3층 305호 우편 16890", "dutyInf": ""}]
        out = data.scrub_rows(rows)[0]
        self.assertEqual(out["dutyEtc"], "오전9시부터 오후7시까지 2026-11-08 3층 305호 우편 16890")

if __name__ == "__main__":
    unittest.main()
