from __future__ import annotations

import hashlib
import importlib.util
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


verify_mod = load('verify_design', Path(__file__).with_name('verify_experiment_design.py'))
gen_mod = load('generate_delta', Path(__file__).with_name('generate_protocol_delta_snapshot.py'))


def fixture():
    header = bytes(range(80))
    block_hash = hashlib.sha256(hashlib.sha256(header).digest()).digest()[::-1].hex()
    tip = 960000
    tip_timestamp = int(datetime(2026, 7, 29, tzinfo=timezone.utc).timestamp())
    block = {'id': block_hash, 'height': tip, 'timestamp': tip_timestamp}
    digests = {
        'tip_height_response_sha256': '1' * 64,
        'tip_hash_response_sha256': '2' * 64,
        'tip_block_response_sha256': '3' * 64,
        'tip_header_response_sha256': '4' * 64,
    }
    return tip, block, header.hex(), digests


class ExperimentTests(unittest.TestCase):
    def test_design(self):
        verify_mod.verify(ROOT)

    def test_snapshot_math_header_and_boundary(self):
        tip, block, header, digests = fixture()
        snapshot = gen_mod.build_snapshot(ROOT, tip, block, header, '2026-07-29T01:00:00Z', digests)
        self.assertEqual(snapshot['delta']['blocks_since_current_epoch_start'], 120000)
        self.assertEqual(snapshot['delta']['blocks_to_next_halving'], 90000)
        self.assertAlmostEqual(snapshot['delta']['current_epoch_progress_ratio'], 120000 / 210000)
        self.assertEqual(snapshot['source']['header_proof']['proof_status'], 'PASS')
        self.assertEqual(snapshot['source']['tip_chain_state'], 'UNFINALIZED_TIP_SUBJECT_TO_REORG')
        self.assertFalse(snapshot['astromodule']['planetary_values_in_this_snapshot'])
        self.assertFalse(snapshot['boundary']['prediction'])
        self.assertFalse(snapshot['boundary']['calendar_eta_is_exact'])
        self.assertFalse(snapshot['boundary']['tip_is_finalized'])

    def test_tip_outside_epoch_fails(self):
        _, block, header, digests = fixture()
        block['height'] = 1050000
        with self.assertRaises(ValueError):
            gen_mod.build_snapshot(ROOT, 1050000, block, header, '2026-07-29T01:00:00Z', digests)

    def test_height_mismatch_fails(self):
        tip, block, header, digests = fixture()
        block['height'] = tip - 1
        with self.assertRaises(ValueError):
            gen_mod.build_snapshot(ROOT, tip, block, header, '2026-07-29T01:00:00Z', digests)

    def test_header_mismatch_fails(self):
        tip, block, _, digests = fixture()
        with self.assertRaises(ValueError):
            gen_mod.build_snapshot(ROOT, tip, block, '00' * 80, '2026-07-29T01:00:00Z', digests)


if __name__ == '__main__':
    unittest.main()
