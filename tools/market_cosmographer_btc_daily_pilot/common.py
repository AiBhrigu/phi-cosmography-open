"""Shared constants and validation for the BTC daily utility pilot."""
from __future__ import annotations
import hashlib
import json
import math
from datetime import date, datetime
from pathlib import Path

POLICY_REL = Path('docs/crypto-astro-service/market_cosmographer_btc_daily_utility_pilot_policy_v0_1.json')
VALIDATOR_REL = Path('tools/market_cosmographer_descriptive_contract/verify_descriptive_contract.py')
CONTRACT_REL = Path('docs/crypto-astro-service/market_cosmographer_descriptive_product_contract_v0_1.json')
METHODOLOGY_ID = 'btc_730d_price_state_methodology_v0_1'
METHODOLOGY_SHA256 = 'e88e62c114d81178d52391cc63f0957d3114475f9d952ccc8bf7e72489e7111b'
STABILITY_REVIEW_ID = 'BTC_2190D_RETROSPECTIVE_REPLICATION_ASSOCIATION_STABILITY_AND_LABEL_SUPPORT_REVIEW_SCOPE_v0_1'
STABILITY_REVIEW_SHA256 = 'cd54909a6ef429a231e5fa3a51cd4092435e83df36f64a43dc77f136d009261c'
SOURCE_ROOT = 'https://data.binance.vision/data/spot/daily/klines/BTCUSDT/1d'
T0 = 'TIER_0_RAW_SOURCE_FACT'
T2 = 'TIER_2_STABLE_DESCRIPTIVE_METRIC'
TIER2_METRICS = ('return_1d', 'return_7d', 'range_position_30d', 'quote_volume_ratio_to_prior_30d_median')
WINDOWS = {'return_1d': '1 completed UTC day', 'return_7d': '7 completed UTC days', 'range_position_30d': '30 completed UTC days', 'quote_volume_ratio_to_prior_30d_median': 'current completed UTC day versus prior 30 completed UTC days'}
FACT_BINDING = {'return_1d': ['btc_close'], 'return_7d': ['btc_close'], 'range_position_30d': ['btc_high', 'btc_low', 'btc_close'], 'quote_volume_ratio_to_prior_30d_median': ['btc_quote_volume']}
GATE_NAMES = {'source_checksums', 'utc_contiguity', 'freshness', 'no_lookahead', 'methodology_binding', 'descriptive_contract_validation', 'deterministic_dual_build', 'predictive_boundary'}

class PilotError(RuntimeError):
    """Fail-closed daily-pilot error."""

def canonical_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')

def pretty_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')

def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))

def parse_date(value: str, where: str='date') -> date:
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise PilotError(f'{where}: invalid ISO date') from exc
    if parsed.isoformat() != value:
        raise PilotError(f'{where}: noncanonical ISO date')
    return parsed

def parse_utc(value: str, where: str='datetime') -> datetime:
    if not isinstance(value, str) or not value.endswith('Z'):
        raise PilotError(f'{where}: UTC Z datetime required')
    try:
        return datetime.fromisoformat(value[:-1] + '+00:00')
    except ValueError as exc:
        raise PilotError(f'{where}: invalid UTC datetime') from exc

def finite(value, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise PilotError(f'{where}: finite number required')
    return float(value)

def valid_sha256(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in '0123456789abcdef' for char in value)

def validate_policy(policy: dict) -> dict:
    if policy.get('schema_version') != 'market_cosmographer_btc_daily_utility_pilot_policy_v0_1' or policy.get('status') != 'AUTHORIZED_INTERNAL_PILOT':
        raise PilotError('pilot policy identity')
    start = parse_date(policy['start_observation_date'], 'pilot start')
    end = parse_date(policy['end_observation_date'], 'pilot end')
    if policy.get('planned_consecutive_days') != 30 or (end - start).days + 1 != 30:
        raise PilotError('pilot window')
    if policy.get('source_policy') != {'provider': 'BINANCE_PUBLIC_DATA', 'archive_frequency': 'daily', 'source_window_days': 32, 'checksum_required': True, 'raw_archive_distribution': False, 'repository_storage': False}:
        raise PilotError('source policy')
    freshness = policy.get('freshness_policy', {})
    if freshness != {'freshness_policy_id': 'completed_utc_daily_snapshot_36h_v0_1', 'fresh_max_age_hours': 36, 'aging_max_age_hours': 72, 'pilot_accepts_only': 'FRESH'}:
        raise PilotError('freshness policy')
    accepted = policy.get('accepted_product_fields', {})
    if tuple(accepted.get('tier2_metrics', [])) != TIER2_METRICS or accepted.get('tier3_labels') != ['range_state']:
        raise PilotError('accepted product fields')
    thresholds = policy.get('completion_thresholds')
    if thresholds != {'accepted_daily_entries': 30, 'automated_gate_pass_rate': 1.0, 'clarity_pass_min': 24, 'evidence_comprehension_pass_min': 24, 'predictive_boundary_incidents_max': 0, 'useful_without_prediction_pass_min': 21}:
        raise PilotError('completion thresholds')
    distribution = policy.get('distribution')
    if distribution != {'backend_api': False, 'commercial_ai_feed': False, 'mode': 'INTERNAL_RESEARCH_ONLY', 'payment_or_subscription': False, 'public_page': False, 'public_snapshot': False}:
        raise PilotError('pilot distribution')
    return policy

def pilot_day_index(policy: dict, observation_day: date) -> int:
    start = parse_date(policy['start_observation_date'])
    end = parse_date(policy['end_observation_date'])
    if not start <= observation_day <= end:
        raise PilotError('observation outside pilot window')
    return (observation_day - start).days + 1
