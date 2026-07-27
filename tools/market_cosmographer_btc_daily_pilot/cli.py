"""Command line routing for daily fetch, build, and entry finalization."""
from __future__ import annotations
import argparse, json
from datetime import timedelta
from pathlib import Path
from tools.market_cosmographer_btc_daily_pilot.common import *
from tools.market_cosmographer_btc_daily_pilot.source import *
from tools.market_cosmographer_btc_daily_pilot.compute import *
from tools.market_cosmographer_btc_daily_pilot.packet_builder import *
from tools.market_cosmographer_btc_daily_pilot.render import *
from tools.market_cosmographer_btc_daily_pilot.utility import *
def fetch_command(args) -> int:
    repo = args.repo.resolve()
    policy = validate_policy(load_json(repo / POLICY_REL))
    observation_day = parse_date(args.observation_date, 'observation date')
    pilot_day_index(policy, observation_day)
    source_start = observation_day - timedelta(days=31)
    fetch_source_window(args.archive_dir, source_start, observation_day)
    report = {'status': 'PASS', 'observation_date': observation_day.isoformat(), 'window_start_date': source_start.isoformat(), 'window_end_date': observation_day.isoformat(), 'archive_count': 32, 'provider_checksums': 'PASS'}
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 0

def build_command(args) -> int:
    repo = args.repo.resolve()
    policy = validate_policy(load_json(repo / POLICY_REL))
    observation_day = parse_date(args.observation_date, 'observation date')
    day_index = pilot_day_index(policy, observation_day)
    previous_day = observation_day - timedelta(days=1)
    source_start = observation_day - timedelta(days=31)
    rows, manifest = read_source_window(args.archive_dir, source_start, observation_day, args.generated_at_utc)
    if len(rows) != 32 or manifest['archive_count'] != 32:
        raise PilotError('daily source window must contain 32 archives')
    previous_manifest = args.previous_manifest
    if day_index > 1 and previous_manifest is None:
        raise PilotError('previous manifest required after pilot day 1')
    correction = build_correction_ledger(manifest, previous_manifest, observation_day)
    proof = build_no_lookahead_proof(rows, previous_day, observation_day)
    validator = load_validator(repo)
    packet, state, diagnostics = build_packet(policy, rows, manifest, correction, proof, observation_day, args.generated_at_utc, validator)
    report = write_build_outputs(args.output_dir, packet, state, manifest, correction, proof, diagnostics, policy, validator, repo)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 0

def finalize_command(args) -> int:
    policy = validate_policy(load_json(args.repo.resolve() / POLICY_REL))
    entry = finalize_utility_entry(policy, args.output_dir, args.previous_entry)
    print(json.dumps(entry, ensure_ascii=False, sort_keys=True, indent=2))
    return 0

def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', required=True)
    fetch = subparsers.add_parser('fetch')
    fetch.add_argument('--repo', type=Path, default=Path('.'))
    fetch.add_argument('--observation-date', required=True)
    fetch.add_argument('--archive-dir', type=Path, required=True)
    fetch.set_defaults(handler=fetch_command)
    build = subparsers.add_parser('build')
    build.add_argument('--repo', type=Path, default=Path('.'))
    build.add_argument('--observation-date', required=True)
    build.add_argument('--generated-at-utc', required=True)
    build.add_argument('--archive-dir', type=Path, required=True)
    build.add_argument('--output-dir', type=Path, required=True)
    build.add_argument('--previous-manifest', type=Path)
    build.set_defaults(handler=build_command)
    finalize = subparsers.add_parser('finalize-entry')
    finalize.add_argument('--repo', type=Path, default=Path('.'))
    finalize.add_argument('--output-dir', type=Path, required=True)
    finalize.add_argument('--previous-entry', type=Path)
    finalize.set_defaults(handler=finalize_command)
    args = parser.parse_args()
    return args.handler(args)
if __name__ == '__main__':
    raise SystemExit(main())
