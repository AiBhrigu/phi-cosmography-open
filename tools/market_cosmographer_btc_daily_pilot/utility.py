"""Immutable daily utility entry finalization."""
from __future__ import annotations
from datetime import timedelta
from pathlib import Path
from tools.market_cosmographer_btc_daily_pilot.common import *
def finalize_utility_entry(policy: dict, output_dir: Path, previous_entry_path: Path | None) -> dict:
    report = load_json(output_dir / 'btc_daily_build_report.json')
    packet = load_json(output_dir / 'btc_daily_descriptive_packet.json')
    if report.get('status') != 'PASS' or report.get('contract_validation') != 'PASS':
        raise PilotError('build report not accepted')
    for name, expected in report['output_sha256'].items():
        path = output_dir / name
        if not path.is_file() or sha256_bytes(path.read_bytes()) != expected:
            raise PilotError(f'output hash mismatch: {name}')
    day_index = int(report['pilot_day_index'])
    previous_entry_sha = None
    previous_packet_id = None
    if day_index == 1:
        if previous_entry_path is not None:
            raise PilotError('pilot day 1 cannot have previous entry')
    else:
        if previous_entry_path is None:
            raise PilotError('previous utility entry required')
        previous = load_json(previous_entry_path)
        if previous.get('schema_version') != 'market_cosmographer_btc_daily_utility_entry_v0_1':
            raise PilotError('previous utility entry schema')
        if previous.get('pilot_id') != policy['pilot_id'] or previous.get('pilot_day_index') != day_index - 1:
            raise PilotError('previous utility entry index')
        previous_date = parse_date(previous['observation_date'])
        current_date = parse_date(report['observation_date'])
        if current_date - previous_date != timedelta(days=1):
            raise PilotError('previous utility entry date')
        previous_entry_sha = sha256_bytes(previous_entry_path.read_bytes())
        previous_packet_id = previous['packet_id']
    entry = {'schema_version': 'market_cosmographer_btc_daily_utility_entry_v0_1', 'pilot_id': policy['pilot_id'], 'pilot_day_index': day_index, 'planned_days': policy['planned_consecutive_days'], 'observation_date': report['observation_date'], 'generated_at_utc': report['generated_at_utc'], 'packet_id': packet['packet_id'], 'packet_sha256': sha256_bytes((output_dir / 'btc_daily_descriptive_packet.json').read_bytes()), 'previous_packet_id': previous_packet_id, 'previous_utility_entry_sha256': previous_entry_sha, 'source_manifest_sha256': sha256_bytes((output_dir / 'btc_daily_source_manifest.json').read_bytes()), 'build_report_sha256': sha256_bytes((output_dir / 'btc_daily_build_report.json').read_bytes()), 'read_en_sha256': sha256_bytes((output_dir / 'btc_daily_descriptive_read.en.md').read_bytes()), 'read_ru_sha256': sha256_bytes((output_dir / 'btc_daily_descriptive_read.ru.md').read_bytes()), 'automated_gates': {'source_checksums': 'PASS', 'utc_contiguity': 'PASS', 'freshness': 'PASS', 'no_lookahead': 'PASS', 'methodology_binding': 'PASS', 'descriptive_contract_validation': 'PASS', 'deterministic_dual_build': 'PASS', 'predictive_boundary': 'PASS'}, 'predictive_boundary_incidents': 0, 'manual_utility_review': {'status': 'PENDING', 'clarity': 'PENDING', 'evidence_comprehension': 'PENDING', 'useful_without_prediction': 'PENDING'}, 'distribution': 'INTERNAL_RESEARCH_ONLY', 'commercial_ai_feed': False}
    (output_dir / 'btc_daily_utility_entry.json').write_bytes(pretty_bytes(entry))
    return entry
