import json
import unittest
from io import BytesIO
from orion.airtable_sync import record_payloads, sync, expected_us_session


REPORT = {
    "kind": "price_observation_only",
    "observed_at": "2026-09-28T23:25:34Z",
    "results": [
        {"symbol": "AAPL", "status": "observed", "date": "2026-09-28", "close": 338.4,
         "source": "https://example.com/aapl"},
        {"symbol": "BAD", "status": "unavailable"},
    ],
}


class Response(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class AirtableSyncTest(unittest.TestCase):
    def test_payload_is_explicitly_observation_only(self):
        rows = record_payloads(REPORT, "123", "amirmogh-ORION/ORION")
        self.assertEqual([row[0] for row in rows], ["Runs", "Activity Log"])
        self.assertIn("1 observed prices", rows[0][3]["Output Summary"])
        self.assertIn("no research conclusions", rows[1][3]["Details"])
        self.assertIn("/actions/runs/123", rows[0][3]["Output Summary"])

    def test_existing_records_are_not_duplicated(self):
        requests = []

        def opener(req, timeout):
            requests.append(req)
            return Response(json.dumps({"records": [{"id": "recExisting"}]}).encode())

        sync(REPORT, "123", "amirmogh-ORION/ORION", "appExample", "secret", opener)
        self.assertEqual(len(requests), 2)
        self.assertTrue(all(req.get_method() == "GET" for req in requests))

    def test_stale_friday_price_on_monday_evening_is_failed(self):
        stale = dict(REPORT, observed_at='2026-09-29T00:44:00Z',
                     results=[dict(REPORT['results'][0], date='2026-09-25')])
        rows = record_payloads(stale, '456', 'amirmogh-ORION/ORION')
        self.assertEqual(rows[0][3]['Status'], 'FAILED')
        self.assertEqual(rows[1][3]['Event Type'], 'ERROR')
        self.assertIn('stale', rows[0][3]['Output Summary'])

    def test_preopen_monday_allows_friday_close(self):
        self.assertEqual(expected_us_session('2026-09-28T13:00:00Z'), '2026-09-25')

    def test_missing_credentials_fail_visibly(self):
        with self.assertRaisesRegex(ValueError, "required"):
            sync(REPORT, "123", "amirmogh-ORION/ORION", "", "")


if __name__ == "__main__":
    unittest.main()
