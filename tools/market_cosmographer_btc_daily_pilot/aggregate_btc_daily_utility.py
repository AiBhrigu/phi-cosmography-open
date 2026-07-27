#!/usr/bin/env python3
"""Aggregate immutable Market Cosmographer BTC daily utility entries and optional reviews."""
from __future__ import annotations
import argparse
import json
from datetime import date, timedelta
from pathlib import Path
POLICY_REL = Path('docs/crypto-astro-service/market_cosmographer_btc_daily_utility_pilot_policy_v0_1.json')
GATE_NAMES = {'source_checksums', 'utc_contiguity', 'freshness', 'no_lookahead', 'methodology_binding', 'descriptive_contract_validation', 'deterministic_dual_build', 'predictive_boundary'}
REVIEW_FIELDS = ('clarity', 'evidence_comprehension', 'useful_without_prediction')

class AggregateError(RuntimeError):
    """Fail-closed pilot aggregation error."""

def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))

def parse_date(value: str) -> date:
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise AggregateError('invalid observation date') from exc
    if parsed.isoformat() != value:
        raise AggregateError('noncanonical observation date')
    return parsed

def load_policy(repo: Path) -> dict:
    policy = load_json(repo / POLICY_REL)
    if policy.get('schema_version') != 'market_cosmographer_btc_daily_utility_pilot_policy_v0_1':
        raise AggregateError('policy schema')
    if policy.get('planned_consecutive_days') != 30:
        raise AggregateError('policy planned days')
    start = parse_date(policy['start_observation_date'])
    end = parse_date(policy['end_observation_date'])
    if (end - start).days + 1 != 30:
        raise AggregateError('policy window')
    return policy

def discover_json(root: Path, filename: str) -> list[Path]:
    if not root.exists():
        return []
    return sorted((path for path in root.rglob(filename) if path.is_file()))

def validate_entry(entry: dict, policy: dict) -> None:
    required = {'schema_version', 'pilot_id', 'pilot_day_index', 'planned_days', 'observation_date', 'generated_at_utc', 'packet_id', 'packet_sha256', 'previous_packet_id', 'previous_utility_entry_sha256', 'source_manifest_sha256', 'build_report_sha256', 'read_en_sha256', 'read_ru_sha256', 'automated_gates', 'predictive_boundary_incidents', 'manual_utility_review', 'distribution', 'commercial_ai_feed'}
    if set(entry) != required:
        raise AggregateError('entry fields')
    if entry['schema_version'] != 'market_cosmographer_btc_daily_utility_entry_v0_1':
        raise AggregateError('entry schema')
    if entry['pilot_id'] != policy['pilot_id'] or entry['planned_days'] != 30:
        raise AggregateError('entry pilot binding')
    day_index = entry['pilot_day_index']
    if not isinstance(day_index, int) or not 1 <= day_index <= 30:
        raise AggregateError('entry day index')
    start = parse_date(policy['start_observation_date'])
    expected_date = start + timedelta(days=day_index - 1)
    if parse_date(entry['observation_date']) != expected_date:
        raise AggregateError('entry date/index binding')
    for field in ('packet_sha256', 'source_manifest_sha256', 'build_report_sha256', 'read_en_sha256', 'read_ru_sha256'):
        value = entry[field]
        if not isinstance(value, str) or len(value) != 64 or any((char not in '0123456789abcdef' for char in value)):
            raise AggregateError(f'entry hash: {field}')
    if set(entry['automated_gates']) != GATE_NAMES:
        raise AggregateError('automated gate set')
    if any((value != 'PASS' for value in entry['automated_gates'].values())):
        raise AggregateError('automated gate failure')
    if entry['predictive_boundary_incidents'] != 0:
        raise AggregateError('predictive boundary incident')
    if entry['distribution'] != 'INTERNAL_RESEARCH_ONLY' or entry['commercial_ai_feed'] is not False:
        raise AggregateError('entry distribution')
    review = entry['manual_utility_review']
    if set(review) != {'status', *REVIEW_FIELDS}:
        raise AggregateError('embedded review fields')
    if review['status'] != 'PENDING' or any((review[field] != 'PENDING' for field in REVIEW_FIELDS)):
        raise AggregateError('immutable entry manual review must remain pending')

def validate_review(review: dict, policy: dict) -> None:
    required = {'schema_version', 'pilot_id', 'observation_date', 'packet_id', 'reviewed_at_utc', 'clarity', 'evidence_comprehension', 'useful_without_prediction', 'notes'}
    if set(review) != required:
        raise AggregateError('review fields')
    if review['schema_version'] != 'market_cosmographer_btc_daily_utility_review_v0_1':
        raise AggregateError('review schema')
    if review['pilot_id'] != policy['pilot_id']:
        raise AggregateError('review pilot binding')
    parse_date(review['observation_date'])
    if any((review[field] not in {'PASS', 'FAIL'} for field in REVIEW_FIELDS)):
        raise AggregateError('review value')
    if not isinstance(review['notes'], str):
        raise AggregateError('review notes')

def aggregate(policy: dict, entries: list[dict], reviews: list[dict]) -> dict:
    for entry in entries:
        validate_entry(entry, policy)
    entries = sorted(entries, key=lambda item: item['pilot_day_index'])
    indices = [item['pilot_day_index'] for item in entries]
    if len(indices) != len(set(indices)):
        raise AggregateError('duplicate day index')
    if indices and indices != list(range(1, len(indices) + 1)):
        raise AggregateError('entries are not a consecutive prefix')
    packet_ids = [item['packet_id'] for item in entries]
    if len(packet_ids) != len(set(packet_ids)):
        raise AggregateError('duplicate packet ID')
    for position, entry in enumerate(entries):
        if position == 0:
            if entry['previous_packet_id'] is not None or entry['previous_utility_entry_sha256'] is not None:
                raise AggregateError('day 1 previous chain')
        else:
            previous = entries[position - 1]
            if entry['previous_packet_id'] != previous['packet_id']:
                raise AggregateError('packet chain')
            if not isinstance(entry['previous_utility_entry_sha256'], str) or len(entry['previous_utility_entry_sha256']) != 64:
                raise AggregateError('utility chain hash')
    review_map = {}
    for review in reviews:
        validate_review(review, policy)
        key = review['observation_date']
        if key in review_map:
            raise AggregateError('duplicate review')
        review_map[key] = review
    entry_dates = {entry['observation_date'] for entry in entries}
    if not set(review_map) <= entry_dates:
        raise AggregateError('review without entry')
    for entry in entries:
        review = review_map.get(entry['observation_date'])
        if review and review['packet_id'] != entry['packet_id']:
            raise AggregateError('review packet binding')
    accepted = len(entries)
    automated_gate_total = accepted * len(GATE_NAMES)
    automated_gate_passes = automated_gate_total
    boundary_incidents = sum((item['predictive_boundary_incidents'] for item in entries))
    review_counts = {field: sum((1 for review in review_map.values() if review[field] == 'PASS')) for field in REVIEW_FIELDS}
    review_failures = {field: sum((1 for review in review_map.values() if review[field] == 'FAIL')) for field in REVIEW_FIELDS}
    thresholds = policy['completion_thresholds']
    if accepted < 30:
        status = 'IN_PROGRESS'
    elif len(review_map) < 30:
        status = 'COMPLETE_PENDING_HUMAN_REVIEW'
    else:
        pass_condition = automated_gate_passes / automated_gate_total >= thresholds['automated_gate_pass_rate'] and boundary_incidents <= thresholds['predictive_boundary_incidents_max'] and (review_counts['clarity'] >= thresholds['clarity_pass_min']) and (review_counts['evidence_comprehension'] >= thresholds['evidence_comprehension_pass_min']) and (review_counts['useful_without_prediction'] >= thresholds['useful_without_prediction_pass_min'])
        status = 'PASS' if pass_condition else 'FAIL'
    return {'schema_version': 'market_cosmographer_btc_daily_utility_pilot_summary_v0_1', 'pilot_id': policy['pilot_id'], 'status': status, 'planned_days': 30, 'accepted_entries': accepted, 'first_observation_date': entries[0]['observation_date'] if entries else None, 'last_observation_date': entries[-1]['observation_date'] if entries else None, 'automated_gate_passes': automated_gate_passes, 'automated_gate_total': automated_gate_total, 'automated_gate_pass_rate': 1.0 if automated_gate_total else None, 'predictive_boundary_incidents': boundary_incidents, 'manual_reviews_received': len(review_map), 'manual_review_passes': review_counts, 'manual_review_failures': review_failures, 'commercial_ai_feed': 'CLOSED', 'public_release_authorized': False}

def render_summary(summary: dict) -> str:
    return '\n'.join(['# Market Cosmographer · BTC · 30-Day Utility Pilot', '', f"- Status: `{summary['status']}`", f"- Accepted entries: {summary['accepted_entries']} / {summary['planned_days']}", f"- First observation: {summary['first_observation_date']}", f"- Last observation: {summary['last_observation_date']}", f"- Automated gate pass rate: {summary['automated_gate_pass_rate']}", f"- Predictive-boundary incidents: {summary['predictive_boundary_incidents']}", f"- Human reviews received: {summary['manual_reviews_received']}", '', 'Commercial AI feed remains closed. Public release is not authorized by this summary.', ''])

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, default=Path('.'))
    parser.add_argument('--entries-dir', type=Path, required=True)
    parser.add_argument('--reviews-dir', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    policy = load_policy(args.repo.resolve())
    entry_paths = discover_json(args.entries_dir, 'btc_daily_utility_entry.json')
    review_paths = discover_json(args.reviews_dir, 'btc_daily_utility_review.json') if args.reviews_dir else []
    entries = [load_json(path) for path in entry_paths]
    reviews = [load_json(path) for path in review_paths]
    summary = aggregate(policy, entries, reviews)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'btc_daily_utility_pilot_summary.json').write_text(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    (args.output_dir / 'btc_daily_utility_pilot_summary.md').write_text(render_summary(summary), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
