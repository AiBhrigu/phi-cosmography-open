from tools.market_cosmographer_btc_daily_pilot.daily_test_support import *

class DailyPilotCoreTests(DailyPilotBase):
    def test_policy_and_day_index(self):
        self.assertEqual(pilot.pilot_day_index(self.policy, self.observation), 1)
        self.assertEqual(pilot.pilot_day_index(self.policy, date(2026, 8, 24)), 30)
        with self.assertRaises(pilot.PilotError):
            pilot.pilot_day_index(self.policy, date(2026, 8, 25))

    def test_realistic_build_contains_only_accepted_product_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, output, packet, report, _ = self.build(root)
            self.assertEqual(report['status'], 'PASS')
            self.assertEqual(report['source_archive_count'], 32)
            self.assertEqual([item['metric_id'] for item in packet['metrics']], list(pilot.TIER2_METRICS))
            self.assertEqual(packet['labels'][0]['label_id'], 'range_state')
            self.assertEqual(packet['observation']['freshness_status'], 'FRESH')
            self.assertTrue((output / 'btc_daily_descriptive_read.ru.md').stat().st_size > 500)

    def test_build_is_byte_deterministic_for_same_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive_dir, output_a, _, _, _ = self.build(root / 'a')
            root_b = root / 'b'
            archive_b = root_b / 'archives'
            archive_b.mkdir(parents=True)
            for path in archive_dir.iterdir():
                (archive_b / path.name).write_bytes(path.read_bytes())
            rows, manifest = pilot.read_source_window(archive_b, self.start, self.observation, self.generated)
            correction = pilot.build_correction_ledger(manifest, None, self.observation)
            proof = pilot.build_no_lookahead_proof(rows, self.observation - timedelta(days=1), self.observation)
            packet, state, diagnostics = pilot.build_packet(self.policy, rows, manifest, correction, proof, self.observation, self.generated, FakeValidator)
            output_b = root_b / 'output'
            pilot.write_build_outputs(output_b, packet, state, manifest, correction, proof, diagnostics, self.policy, FakeValidator, root_b)
            self.assertEqual({path.name: path.read_bytes() for path in output_a.iterdir()}, {path.name: path.read_bytes() for path in output_b.iterdir()})

    def test_checksum_tampering_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive_dir = root / 'archives'
            make_window(archive_dir, self.start, self.observation)
            target = archive_dir / pilot.archive_name(self.observation)
            target.write_bytes(target.read_bytes() + b'tamper')
            with self.assertRaises(pilot.PilotError):
                pilot.read_source_window(archive_dir, self.start, self.observation, self.generated)

    def test_missing_day_fails_contiguity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive_dir = root / 'archives'
            make_window(archive_dir, self.start, self.observation)
            missing = self.start + timedelta(days=5)
            (archive_dir / pilot.archive_name(missing)).unlink()
            with self.assertRaises(pilot.PilotError):
                pilot.read_source_window(archive_dir, self.start, self.observation, self.generated)

    def test_stale_observation_fails_pilot_acceptance(self):
        with tempfile.TemporaryDirectory() as temp:
            archive_dir = Path(temp) / 'archives'
            make_window(archive_dir, self.start, self.observation)
            generated = '2026-07-30T12:00:00Z'
            rows, manifest = pilot.read_source_window(archive_dir, self.start, self.observation, generated)
            correction = pilot.build_correction_ledger(manifest, None, self.observation)
            proof = pilot.build_no_lookahead_proof(rows, self.observation - timedelta(days=1), self.observation)
            with self.assertRaises(pilot.PilotError):
                pilot.build_packet(self.policy, rows, manifest, correction, proof, self.observation, generated, FakeValidator)

    def test_correction_drift_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive_dir = root / 'archives'
            make_window(archive_dir, self.start, self.observation)
            _, manifest = pilot.read_source_window(archive_dir, self.start, self.observation, self.generated)
            previous = json.loads(json.dumps(manifest))
            previous['window_end_date'] = '2026-07-25'
            previous['archives'] = previous['archives'][:-1]
            previous['archives'][0]['actual_sha256'] = '0' * 64
            previous_path = root / 'previous.json'
            previous_path.write_text(json.dumps(previous), encoding='utf-8')
            with self.assertRaises(pilot.PilotError):
                pilot.build_correction_ledger(manifest, previous_path, self.observation)

    def test_no_lookahead_prefix_invariance(self):
        with tempfile.TemporaryDirectory() as temp:
            archive_dir = Path(temp) / 'archives'
            make_window(archive_dir, self.start, self.observation)
            rows, _ = pilot.read_source_window(archive_dir, self.start, self.observation, self.generated)
            proof = pilot.build_no_lookahead_proof(rows, self.observation - timedelta(days=1), self.observation)
            self.assertEqual(proof['status'], 'PASS')
            self.assertTrue(all((item['status'] == 'PASS' for item in proof['prefix_invariance'])))
