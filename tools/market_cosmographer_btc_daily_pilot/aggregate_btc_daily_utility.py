#!/usr/bin/env python3
"""Aggregate immutable Market Cosmographer BTC daily utility entries and optional reviews."""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import date, datetime, timedelta
from pathlib import Path

POLICY_REL = Path('docs/crypto-astro-service/market_cosmographer_btc_daily_utility_pilot_policy_v0_1.json')
GATE_NAMES = {'source_checksums', 'utc_contiguity', 'freshness', 'no_lookahead', 'methodology_binding', 'descriptive_contract_validation', 'deterministic_dual_build', 'predictive_boundary'}
REVIEW_FIELDS = ('clarity', 'evidence_comprehension', 'useful_without_prediction')

class AggregateError(RuntimeError):
    """Fail-closed pilot aggregation error."""

def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))

def pretty_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')

def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def valid_sha(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in '0123456789abcdef' for char in value)

def parse_date(value: str) -> date:
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise AggregateError('invalid observation date') from exc
    if parsed.isoformat() != value:
        raise AggregateError('noncanonical observation date')
    return parsed

def parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith('Z'):
        raise AggregateError('UTC review timestamp required')
    try:
        return datetime.fromisoformat(value[:-1] + '+00:00')
    except ValueError as exc:
        raise AggregateError('invalid UTC review timestamp') from exc

def load_policy(repo: Path) -> dict:
    policy = load_json(repo / POLICY_REL)
    if policy.get('schema_version') != 'market_cosmographer_btc_daily_utility_pilot_policy_v0_1' or policy.get('planned_consecutive_days') != 30:
        raise AggregateError('policy identity')
    start = parse_date(policy['start_observation_date']); end = parse_date(policy['end_observation_date'])
    if (end - start).days + 1 != 30:
        raise AggregateError('policy window')
    return policy

def discover_json(root: Path, filename: str) -> list[Path]:
    return sorted(path for path in root.rglob(filename) if path.is_file()) if root.exists() else []

def validate_entry(entry: dict, policy: dict) -> None:
    required = {'schema_version','pilot_id','pilot_day_index','planned_days','observation_date','generated_at_utc','packet_id','packet_sha256','previous_packet_id','previous_utility_entry_sha256','source_manifest_sha256','build_report_sha256','read_en_sha256','read_ru_sha256','automated_gates','predictive_boundary_incidents','manual_utility_review','distribution','commercial_ai_feed'}
    if set(entry) != required:
        raise AggregateError('entry fields')
    if entry['schema_version'] != 'market_cosmographer_btc_daily_utility_entry_v0_1' or entry['pilot_id'] != policy['pilot_id'] or entry['planned_days'] != 30:
        raise AggregateError('entry identity')
    day_index = entry['pilot_day_index']
    if not isinstance(day_index, int) or not 1 <= day_index <= 30:
        raise AggregateError('entry day index')
    expected_date = parse_date(policy['start_observation_date']) + timedelta(days=day_index - 1)
    if parse_date(entry['observation_date']) != expected_date:
        raise AggregateError('entry date/index binding')
    parse_utc(entry['generated_at_utc'])
    if not isinstance(entry['packet_id'], str) or not entry['packet_id']:
        raise AggregateError('packet ID')
    for field in ('packet_sha256','source_manifest_sha256','build_report_sha256','read_en_sha256','read_ru_sha256'):
        if not valid_sha(entry[field]):
            raise AggregateError(f'entry hash: {field}')
    if set(entry['automated_gates']) != GATE_NAMES or any(value != 'PASS' for value in entry['automated_gates'].values()):
        raise AggregateError('automated gates')
    if entry['predictive_boundary_incidents'] != 0:
        raise AggregateError('predictive boundary incident')
    if entry['distribution'] != 'INTERNAL_RESEARCH_ONLY' or entry['commercial_ai_feed'] is not False:
        raise AggregateError('entry distribution')
    embedded = entry['manual_utility_review']
    if set(embedded) != {'status', *REVIEW_FIELDS} or embedded['status'] != 'PENDING' or any(embedded[field] != 'PENDING' for field in REVIEW_FIELDS):
        raise AggregateError('immutable entry review state')

def validate_review(review: dict, policy: dict) -> None:
    required = {'schema_version','pilot_id','observation_date','packet_id','reviewed_at_utc','clarity','evidence_comprehension','useful_without_prediction','notes'}
    if set(review) != required or review['schema_version'] != 'market_cosmographer_btc_daily_utility_review_v0_1' or review['pilot_id'] != policy['pilot_id']:
        raise AggregateError('review identity')
    parse_date(review['observation_date']); parse_utc(review['reviewed_at_utc'])
    if any(review[field] not in {'PASS','FAIL'} for field in REVIEW_FIELDS) or not isinstance(review['notes'], str):
        raise AggregateError('review value')

def aggregate(policy: dict, entries: list[dict], reviews: list[dict]) -> dict:
    for entry in entries:
        validate_entry(entry, policy)
    entries = sorted(entries, key=lambda item: item['pilot_day_index'])
    indices = [item['pilot_day_index'] for item in entries]
    if len(indices) != len(set(indices)) or (indices and indices != list(range(1, len(indices) + 1))):
        raise AggregateError('entries are not one consecutive prefix')
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
            expected_previous_sha = sha256(pretty_bytes(previous))
            if entry['previous_utility_entry_sha256'] != expected_previous_sha:
                raise AggregateError('utility entry hash chain')
    review_map = {}
    for review in reviews:
        validate_review(review, policy)
        key = review['observation_date']
        if key in review_map:
            raise AggregateError('duplicate review')
        review_map[key] = review
    entry_by_date = {entry['observation_date']: entry for entry in entries}
    if not set(review_map) <= set(entry_by_date):
        raise AggregateError('review without entry')
    for observation_date, review in review_map.items():
        if review['packet_id'] != entry_by_date[observation_date]['packet_id']:
            raise AggregateError('review packet binding')
    accepted = len(entries)
    gate_total = accepted * len(GATE_NAMES)
    gate_passes = gate_total
    boundary_incidents = sum(item['predictive_boundary_incidents'] for item in entries)
    pass_counts = {field: sum(1 for review in review_map.values() if review[field] == 'PASS') for field in REVIEW_FIELDS}
    fail_counts = {field: sum(1 for review in review_map.values() if review[field] == 'FAIL') for field in REVIEW_FIELDS}
    thresholds = policy['completion_thresholds']
    if accepted < 30:
        status = 'IN_PROGRESS'
    elif len(review_map) < 30:
        status = 'COMPLETE_PENDING_HUMAN_REVIEW'
    else:
        passes = gate_passes / gate_total >= thresholds['automated_gate_pass_rate'] and boundary_incidents <= thresholds['predictive_boundary_incidents_max'] and pass_counts['clarity'] >= thresholds['clarity_pass_min'] and pass_counts['evidence_comprehension'] >= thresholds['evidence_comprehension_pass_min'] and pass_counts['useful_without_prediction'] >= thresholds['useful_without_prediction_pass_min']
        status = 'PASS' if passes else 'FAIL'
    return {'schema_version':'market_cosmographer_btc_daily_utility_pilot_summary_v0_1','pilot_id':policy['pilot_id'],'status':status,'planned_days':30,'accepted_entries':accepted,'first_observation_date':entries[0]['observation_date'] if entries else None,'last_observation_date':entries[-1]['observation_date'] if entries else None,'automated_gate_passes':gate_passes,'automated_gate_total':gate_total,'automated_gate_pass_rate':1.0 if gate_total else None,'predictive_boundary_incidents':boundary_incidents,'manual_reviews_received':len(review_map),'manual_review_passes':pass_counts,'manual_review_failures':fail_counts,'commercial_ai_feed':'CLOSED','public_release_authorized':False}

def render_summary(summary: dict) -> str:
    return '\n'.join(['# Market Cosmographer · BTC · 30-Day Utility Pilot','',f"- Status: `{summary['status']}`",f"- Accepted entries: {summary['accepted_entries']} / {summary['planned_days']}",f"- First observation: {summary['first_observation_date']}",f"- Last observation: {summary['last_observation_date']}",f"- Automated gate pass rate: {summary['automated_gate_pass_rate']}",f"- Predictive-boundary incidents: {summary['predictive_boundary_incidents']}",f"- Human reviews received: {summary['manual_reviews_received']}",'','Commercial AI feed remains closed. Public release is not authorized by this summary.',''])

def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument('--repo',type=Path,default=Path('.')); parser.add_argument('--entries-dir',type=Path,required=True); parser.add_argument('--reviews-dir',type=Path); parser.add_argument('--output-dir',type=Path,required=True); args=parser.parse_args()
    policy=load_policy(args.repo.resolve()); entries=[load_json(path) for path in discover_json(args.entries_dir,'btc_daily_utility_entry.json')]; reviews=[load_json(path) for path in discover_json(args.reviews_dir,'btc_daily_utility_review.json')] if args.reviews_dir else []
    summary=aggregate(policy,entries,reviews); args.output_dir.mkdir(parents=True,exist_ok=True); (args.output_dir/'btc_daily_utility_pilot_summary.json').write_text(json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8'); (args.output_dir/'btc_daily_utility_pilot_summary.md').write_text(render_summary(summary),encoding='utf-8'); print(json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)); return 0
if __name__ == '__main__':
    raise SystemExit(main())
