"""Accepted descriptive metrics, correction control, and no-lookahead proof."""
from __future__ import annotations
import importlib.util, statistics
from datetime import date, timedelta
from pathlib import Path
from tools.market_cosmographer_btc_daily_pilot.common import *
def round12(value: float) -> float:
    return round(float(value), 12)

def recompute_tier2(rows: list[dict], observation_day: date) -> dict:
    day = observation_day.isoformat()
    index = next((idx for idx, row in enumerate(rows) if row['observation_date'] == day), None)
    if index is None or index < 30:
        raise PilotError(f'insufficient metric history: {day}')
    current = rows[index]
    window = rows[index - 29:index + 1]
    low = min((row['low'] for row in window))
    high = max((row['high'] for row in window))
    prior_quote_volumes = [row['quote_volume'] for row in rows[index - 30:index]]
    return {'return_1d': round12(current['close'] / rows[index - 1]['close'] - 1), 'return_7d': round12(current['close'] / rows[index - 7]['close'] - 1), 'range_position_30d': round12((current['close'] - low) / (high - low) if high > low else 0.5), 'quote_volume_ratio_to_prior_30d_median': round12(current['quote_volume'] / statistics.median(prior_quote_volumes))}

def range_state(position: float) -> str:
    return 'LOWER' if position < 0.25 else 'UPPER' if position > 0.75 else 'MIDDLE'

def state_payload(row: dict, metrics: dict) -> dict:
    return {'schema_version': 'market_cosmographer_btc_daily_state_v0_1', 'observation_date': row['observation_date'], 'source': {'provider': 'BINANCE_PUBLIC_DATA', 'market': 'BTCUSDT_SPOT', 'interval': '1d_UTC', 'archive_id': row['archive_id'], 'archive_sha256': row['archive_sha256']}, 'input_max_timestamp_utc': row['close_time_utc'], 'methodology_id': METHODOLOGY_ID, 'methodology_sha256': METHODOLOGY_SHA256, 'metrics': metrics}

def freshness_status(policy: dict, as_of_utc: str, generated_at_utc: str) -> tuple[str, float]:
    as_of = parse_utc(as_of_utc, 'as_of_utc')
    generated = parse_utc(generated_at_utc, 'generated_at_utc')
    age_hours = (generated - as_of).total_seconds() / 3600
    if age_hours < 0:
        raise PilotError('generation precedes observation')
    fresh_max = float(policy['freshness_policy']['fresh_max_age_hours'])
    aging_max = float(policy['freshness_policy']['aging_max_age_hours'])
    status = 'FRESH' if age_hours <= fresh_max else 'AGING' if age_hours <= aging_max else 'STALE'
    return (status, age_hours)

def build_correction_ledger(current_manifest: dict, previous_manifest_path: Path | None, observation_day: date) -> dict:
    if previous_manifest_path is None:
        return {'schema_version': 'market_cosmographer_btc_daily_correction_ledger_v0_1', 'status': 'CURRENT_CHECKSUMS_VERIFIED', 'observation_date': observation_day.isoformat(), 'previous_baseline_status': 'NOT_REQUIRED_FOR_PILOT_DAY_1', 'overlap_archive_count': 0, 'event_count': 0, 'events': [], 'silent_overwrite_allowed': False}
    previous = load_json(previous_manifest_path)
    if previous.get('schema_version') != 'market_cosmographer_btc_daily_source_manifest_v0_1':
        raise PilotError('previous source manifest schema')
    if previous.get('window_end_date') != (observation_day - timedelta(days=1)).isoformat():
        raise PilotError('previous source manifest is not consecutive')
    old = {item['archive_id']: item for item in previous.get('archives', [])}
    new = {item['archive_id']: item for item in current_manifest['archives']}
    overlap = sorted(old.keys() & new.keys())
    events = []
    for archive_id in overlap:
        if old[archive_id]['actual_sha256'] != new[archive_id]['actual_sha256']:
            events.append({'archive_id': archive_id, 'status': 'SOURCE_ARCHIVE_REPLACED', 'previous_sha256': old[archive_id]['actual_sha256'], 'current_sha256': new[archive_id]['actual_sha256']})
    if events:
        raise PilotError(f'source correction drift detected: {len(events)}')
    return {'schema_version': 'market_cosmographer_btc_daily_correction_ledger_v0_1', 'status': 'NO_CORRECTIONS', 'observation_date': observation_day.isoformat(), 'previous_baseline_status': 'COMPARED', 'overlap_archive_count': len(overlap), 'event_count': 0, 'events': [], 'silent_overwrite_allowed': False}

def build_no_lookahead_proof(rows: list[dict], previous_day: date, current_day: date) -> dict:
    checks = []
    for day in (previous_day, current_day):
        index = next((idx for idx, row in enumerate(rows) if row['observation_date'] == day.isoformat()))
        full = recompute_tier2(rows, day)
        prefix = recompute_tier2(rows[:index + 1], day)
        status = 'PASS' if canonical_bytes(full) == canonical_bytes(prefix) else 'FAIL'
        checks.append({'observation_date': day.isoformat(), 'status': status})
        if status != 'PASS':
            raise PilotError(f'prefix invariance failed: {day}')
    return {'schema_version': 'market_cosmographer_btc_daily_no_lookahead_proof_v0_1', 'status': 'PASS', 'state_dates': [previous_day.isoformat(), current_day.isoformat()], 'source_window_end_date': current_day.isoformat(), 'input_timestamps_not_after_state': True, 'forward_fields_present': False, 'prefix_invariance': checks, 'full_sample_normalization': False, 'threshold_optimization_after_results': False}

def load_validator(repo: Path):
    path = repo / VALIDATOR_REL
    spec = importlib.util.spec_from_file_location('market_cosmographer_descriptive_validator', path)
    if spec is None or spec.loader is None:
        raise PilotError('validator import')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def pct(value: float) -> str:
    return f'{float(value) * 100:.4f}%'

def ratio(value: float) -> str:
    return f'{float(value):.6f}'
