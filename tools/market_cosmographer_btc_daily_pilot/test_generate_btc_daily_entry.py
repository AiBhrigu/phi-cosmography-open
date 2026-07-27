from tools.market_cosmographer_btc_daily_pilot.daily_test_support import *

class DailyPilotEntryTests(DailyPilotBase):
    def test_finalize_day_one_entry(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, output, packet, _, _ = self.build(root)
            entry = pilot.finalize_utility_entry(self.policy, output, None)
            self.assertEqual(entry['pilot_day_index'], 1)
            self.assertEqual(entry['packet_id'], packet['packet_id'])
            self.assertEqual(entry['automated_gates']['deterministic_dual_build'], 'PASS')
            self.assertTrue((output / 'btc_daily_utility_entry.json').is_file())

    def test_finalize_later_day_requires_previous_entry(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            report = {'status': 'PASS', 'contract_validation': 'PASS', 'pilot_day_index': 2, 'observation_date': '2026-07-27', 'generated_at_utc': '2026-07-28T06:00:00Z', 'output_sha256': {}}
            (output / 'btc_daily_build_report.json').write_text(json.dumps(report), encoding='utf-8')
            (output / 'btc_daily_descriptive_packet.json').write_text(json.dumps({'packet_id': 'x'}), encoding='utf-8')
            with self.assertRaises(pilot.PilotError):
                pilot.finalize_utility_entry(self.policy, output, None)
