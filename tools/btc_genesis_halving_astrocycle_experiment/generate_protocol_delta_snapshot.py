#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

CANON_REL = Path('docs/crypto-astro-service/btc-protocol-price-history/BTC_HALVING_EPOCH_ARCHIVE_v0_1.csv')
DESIGN_REL = Path('docs/crypto-astro-service/btc_genesis_next_halving_astrocycle_experiment_design_v0_1.json')
READINESS_REL = Path('docs/crypto-astro-service/btc_astromodule_merriman_gap_and_readiness_v0_1.json')


def parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith('Z'):
        raise ValueError('UTC Z timestamp required')
    return datetime.fromisoformat(value[:-1] + '+00:00')


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def load_archive(repo: Path) -> list[dict[str, str]]:
    with (repo / CANON_REL).open(newline='', encoding='utf-8') as handle:
        rows = list(csv.DictReader(handle))
    heights = [int(row['start_block']) for row in rows]
    if heights != [0, 210000, 420000, 630000, 840000]:
        raise ValueError('unexpected halving archive heights')
    if any(row['boundary_hash_recomputed'] != 'PASS' for row in rows):
        raise ValueError('halving boundary proof failure')
    return rows


def verify_header(header_hex: str, expected_hash: str) -> dict:
    header_hex = header_hex.strip().lower()
    if len(header_hex) != 160:
        raise ValueError('80-byte header required')
    try:
        header = bytes.fromhex(header_hex)
    except ValueError as exc:
        raise ValueError('header hex') from exc
    single = hashlib.sha256(header).hexdigest()
    recomputed = hashlib.sha256(hashlib.sha256(header).digest()).digest()[::-1].hex()
    if recomputed != expected_hash:
        raise ValueError('header block hash mismatch')
    return {
        'raw_header_hex': header_hex,
        'raw_header_bytes': 80,
        'raw_header_sha256': single,
        'block_hash_recomputed': recomputed,
        'proof_status': 'PASS',
    }


def build_snapshot(
    repo: Path,
    tip_height: int,
    tip_block: dict,
    tip_header_hex: str,
    generated_at: str,
    source_digests: dict[str, str],
) -> dict:
    design = read_json(repo / DESIGN_REL)
    readiness = read_json(repo / READINESS_REL)
    rows = load_archive(repo)
    if design['canonical_protocol_anchors']['next_halving_start_height'] != 1050000:
        raise ValueError('next halving height drift')
    if tip_height < 840000 or tip_height >= 1050000:
        raise ValueError('tip outside current epoch')
    if int(tip_block.get('height', -1)) != tip_height:
        raise ValueError('tip block height mismatch')
    block_hash = tip_block.get('id')
    if not isinstance(block_hash, str) or len(block_hash) != 64:
        raise ValueError('tip block hash')
    proof = verify_header(tip_header_hex, block_hash)
    required_digests = {
        'tip_height_response_sha256',
        'tip_hash_response_sha256',
        'tip_block_response_sha256',
        'tip_header_response_sha256',
    }
    if set(source_digests) != required_digests:
        raise ValueError('dynamic source digest set')
    if any(
        len(value) != 64 or any(char not in '0123456789abcdef' for char in value)
        for value in source_digests.values()
    ):
        raise ValueError('dynamic source digest')

    tip_time = datetime.fromtimestamp(int(tip_block['timestamp']), tz=timezone.utc)
    generation_time = parse_utc(generated_at)
    if generation_time < tip_time:
        raise ValueError('generation before tip')

    genesis_time = parse_utc(rows[0]['actual_boundary_timestamp_utc'])
    epoch_time = parse_utc(rows[4]['actual_boundary_timestamp_utc'])
    next_height = 1050000
    remaining = next_height - tip_height
    target_seconds = remaining * 600
    target_eta = tip_time + timedelta(seconds=target_seconds)
    static_target = parse_utc(rows[4]['next_protocol_target_boundary_estimate_utc'])

    snapshot = {
        'schema_version': 'btc_genesis_next_halving_protocol_delta_snapshot_v0_1',
        'status': 'PASS',
        'generated_at_utc': generated_at,
        'source': {
            'dynamic_provider': 'MEMPOOL_SPACE_ESPLORA',
            'dynamic_endpoints': {
                'tip_height': '/api/blocks/tip/height',
                'block_hash_by_height': '/api/block-height/{height}',
                'block': '/api/block/{hash}',
                'raw_header': '/api/block/{hash}/header',
            },
            'tip_height': tip_height,
            'tip_block_hash': block_hash,
            'tip_block_timestamp_utc': tip_time.isoformat().replace('+00:00', 'Z'),
            'dynamic_response_digests': source_digests,
            'header_proof': proof,
            'tip_confirmation_depth_at_capture': 0,
            'tip_chain_state': 'UNFINALIZED_TIP_SUBJECT_TO_REORG',
            'applicability': 'POINT_IN_TIME_ONLY',
            'static_halving_archive_blob': '2fd152d190bcc09846654a78915c0c17a8f16bf0',
        },
        'anchors': {
            'genesis': {'height': 0, 'timestamp_utc': rows[0]['actual_boundary_timestamp_utc'], 'hash': rows[0]['boundary_block_hash']},
            'current_epoch_start': {'height': 840000, 'timestamp_utc': rows[4]['actual_boundary_timestamp_utc'], 'hash': rows[4]['boundary_block_hash']},
            'current_tip': {'height': tip_height, 'timestamp_utc': tip_time.isoformat().replace('+00:00', 'Z'), 'hash': block_hash},
            'next_halving': {'height': next_height, 'timestamp_status': 'ESTIMATE_ONLY_NOT_CONSENSUS'},
        },
        'delta': {
            'blocks_since_genesis': tip_height,
            'blocks_since_current_epoch_start': tip_height - 840000,
            'current_epoch_progress_ratio': round((tip_height - 840000) / 210000, 12),
            'blocks_to_next_halving': remaining,
            'target_seconds_to_next_halving': target_seconds,
            'target_days_to_next_halving': round(target_seconds / 86400, 6),
            'protocol_target_eta_from_tip_timestamp_utc': target_eta.isoformat().replace('+00:00', 'Z'),
            'static_epoch_target_boundary_estimate_utc': static_target.isoformat().replace('+00:00', 'Z'),
            'days_since_genesis': round((tip_time - genesis_time).total_seconds() / 86400, 6),
            'days_since_current_epoch_start': round((tip_time - epoch_time).total_seconds() / 86400, 6),
        },
        'astromodule': {
            'readiness_status': readiness['status'],
            'deterministic_research_run': readiness['readiness_decision']['astromodule_deterministic_research_run'],
            'a_e_numeric_activation': readiness['readiness_decision']['a_e_numeric_activation'],
            'anchor_schedule': ['GENESIS_BLOCK', 'HISTORICAL_HALVING_BLOCKS', 'CURRENT_TIP_BLOCK'],
            'future_halving_anchor': 'BLOCK_HEIGHT_ONLY_UNTIL_OBSERVED',
            'planetary_values_in_this_snapshot': False,
        },
        'boundary': {
            'internal_research_only': True,
            'calendar_eta_is_exact': False,
            'tip_is_finalized': False,
            'halving_price_causality': False,
            'astro_price_causality': False,
            'prediction': False,
            'trading_signal': False,
            'public_surface_change': False,
            'daily_utility_pilot_change': False,
        },
    }
    snapshot['snapshot_id'] = 'btc:protocol-delta:' + hashlib.sha256(canonical_bytes(snapshot)).hexdigest()[:16]
    return snapshot


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, default=Path('.'))
    parser.add_argument('--tip-height-file', type=Path, required=True)
    parser.add_argument('--tip-hash-file', type=Path, required=True)
    parser.add_argument('--tip-block-file', type=Path, required=True)
    parser.add_argument('--tip-header-file', type=Path, required=True)
    parser.add_argument('--generated-at-utc', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()

    height_raw = args.tip_height_file.read_bytes()
    hash_raw = args.tip_hash_file.read_bytes()
    block_raw = args.tip_block_file.read_bytes()
    header_raw = args.tip_header_file.read_bytes()
    tip_height = int(height_raw.decode().strip())
    expected_hash = hash_raw.decode().strip()
    tip_block = json.loads(block_raw)
    if tip_block.get('id') != expected_hash:
        raise ValueError('tip hash response mismatch')
    source_digests = {
        'tip_height_response_sha256': sha256_bytes(height_raw),
        'tip_hash_response_sha256': sha256_bytes(hash_raw),
        'tip_block_response_sha256': sha256_bytes(block_raw),
        'tip_header_response_sha256': sha256_bytes(header_raw),
    }
    snapshot = build_snapshot(
        args.repo.resolve(),
        tip_height,
        tip_block,
        header_raw.decode(),
        args.generated_at_utc,
        source_digests,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(snapshot, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
