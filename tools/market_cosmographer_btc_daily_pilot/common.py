"""Shared constants and validation for the BTC daily utility pilot."""
from __future__ import annotations
import hashlib, json, math
from datetime import date, datetime
from pathlib import Path
from datetime import date, datetime, timedelta, timezone
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
        parsed = datetime.fromisoformat(value[:-1] + '+00:00')
    except ValueError as exc:
        raise PilotError(f'{where}: invalid UTC datetime') from exc
    return parsed

def finite(value, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or (not math.isfinite(float(value))):
        raise PilotError(f'{where}: finite number required')
    return float(value)

def validate_policy(policy: dict) -> dict:
    if policy.get('schema_version') != 'market_cosmographer_btc_daily_utility_pilot_policy_v0_1':
        raise PilotError('pilot policy schema')
    if policy.get('status') != 'AUTHORIZED_INTERNAL_PILOT':
        raise PilotError('pilot policy status')
    start = parse_date(policy['start_observation_date'], 'pilot start')
    end = parse_date(policy['end_observation_date'], 'pilot end')
    planned = int(policy['planned_consecutive_days'])
    if planned != 30 or (end - start).days + 1 != planned:
        raise PilotError('pilot window')
    source = policy['source_policy']
    if source != {'provider': 'BINANCE_PUBLIC_DATA', 'archive_frequency': 'daily', 'source_window_days': 32, 'checksum_required': True, 'raw_archive_distribution': False, 'repository_storage': False}:
        raise PilotError('source policy')
    freshness = policy['freshness_policy']
    if freshness['freshness_policy_id'] != 'completed_utc_daily_snapshot_36h_v0_1':
        raise PilotError('freshness policy id')
    if freshness['fresh_max_age_hours'] != 36 or freshness['aging_max_age_hours'] != 72:
        raise PilotError('freshness thresholds')
    if freshness['pilot_accepts_only'] != 'FRESH':
        raise PilotError('pilot freshness gate')
    accepted = policy['accepted_product_fields']
    if tuple(accepted['tier2_metrics']) != TIER2_METRICS or accepted['tier3_labels'] != ['range_state']:
        raise PilotError('accepted product fields')
    return policy

def pilot_day_index(policy: dict, observation_day: date) -> int:
    start = parse_date(policy['start_observation_date'])
    end = parse_date(policy['end_observation_date'])
    if not start <= observation_day <= end:
        raise PilotError('observation outside pilot window')
    return (observation_day - start).days + 1
