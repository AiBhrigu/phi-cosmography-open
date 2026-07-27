"""Immutable daily utility entry finalization."""
from __future__ import annotations
from datetime import timedelta
from pathlib import Path
from tools.market_cosmographer_btc_daily_pilot.common import *

def validate_previous_entry(previous: dict, policy: dict, expected_index: int) -> None:
    if previous.get('schema_version') != 'market_cosmographer_btc_daily_utility_entry_v0_1':
        raise PilotError('previous utility entry schema')
    if previous.get('pilot_id') != policy['pilot_id'] or previous.get('pilot_day_index') != expected_index:
        raise PilotError('previous utility entry index')
    if set(previous.get('automated_gates', {})) != GATE_NAMES or any(value != 'PASS' for value in previous['automated_gates'].values()):
        raise PilotError('previous utility entry gates')
    if previous.get('predictive_boundary_incidents') != 0:
        raise PilotError('previous predictive boundary incident')
    if previous.get('distribution') != 'INTERNAL_RESEARCH_ONLY' or previous.get('commercial_ai_feed') is not False:
        raise PilotError('previous utility entry distribution')
    if not isinstance(previous.get('packet_id'), str) or not previous['packet_id']:
        raise PilotError('previous packet ID')
    if not valid_sha256(previous.get('source_manifest_sha256')):
        raise PilotError('previous manifest hash')

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
        validate_previous_entry(previous, policy, day_index - 1)
        previous_date = parse_date(previous['observation_date'])
        current_date = parse_date(report['observation_date'])
        if current_date - previous_date != timedelta(days=1):
            raise PilotError('previous utility entry date')
        previous_entry_sha = sha256_bytes(previous_entry_path.read_bytes())
        previous_packet_id = previous['packet_id']
    entry = {
        'schema_version': 'market_cosmographer_btc_daily_utility_entry_v0_1',
        'pilot_id': policy['pilot_id'],
        'pilot_day_index': day_index,
        'planned_days': policy['planned_consecutive_days'],
        'observation_date': report['observation_date'],
        'generated_at_utc': report['generated_at_utc'],
        'packet_id': packet['packet_id'],
        'packet_sha256': sha256_bytes((output_dir / 'btc_daily_descriptive_packet.json').read_bytes()),
        'previous_packet_id': previous_packet_id,
        'previous_utility_entry_sha256': previous_entry_sha,
        'source_manifest_sha256': sha256_bytes((output_dir / 'btc_daily_source_manifest.json').read_bytes()),
        'build_report_sha256': sha256_bytes((output_dir / 'btc_daily_build_report.json').read_bytes()),
        'read_en_sha256': sha256_bytes((output_dir / 'btc_daily_descriptive_read.en.md').read_bytes()),
        'read_ru_sha256': sha256_bytes((output_dir / 'btc_daily_descriptive_read.ru.md').read_bytes()),
        'automated_gates': {name: 'PASS' for name in GATE_NAMES},
        'predictive_boundary_incidents': 0,
        'manual_utility_review': {'status': 'PENDING', 'clarity': 'PENDING', 'evidence_comprehension': 'PENDING', 'useful_without_prediction': 'PENDING'},
        'distribution': 'INTERNAL_RESEARCH_ONLY',
        'commercial_ai_feed': False,
    }
    (output_dir / 'btc_daily_utility_entry.json').write_bytes(pretty_bytes(entry))
    return entry
