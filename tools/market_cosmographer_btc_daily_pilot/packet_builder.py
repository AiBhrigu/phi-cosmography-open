"""Build the evidence-bound Market Cosmographer daily packet."""
from __future__ import annotations
from datetime import date, timedelta
from tools.market_cosmographer_btc_daily_pilot.common import *
from tools.market_cosmographer_btc_daily_pilot.compute import *
def build_packet(policy: dict, rows: list[dict], manifest: dict, correction_ledger: dict, proof: dict, observation_day: date, generated_at_utc: str, validator) -> tuple[dict, dict, dict]:
    previous_day = observation_day - timedelta(days=1)
    current_row = next((row for row in rows if row['observation_date'] == observation_day.isoformat()))
    previous_row = next((row for row in rows if row['observation_date'] == previous_day.isoformat()))
    current_metrics = recompute_tier2(rows, observation_day)
    previous_metrics = recompute_tier2(rows, previous_day)
    current_state = state_payload(current_row, current_metrics)
    previous_state = state_payload(previous_row, previous_metrics)
    current_state_sha = sha256_bytes(canonical_bytes(current_state))
    previous_state_sha = sha256_bytes(canonical_bytes(previous_state))
    freshness, age_hours = freshness_status(policy, current_row['close_time_utc'], generated_at_utc)
    if freshness != policy['freshness_policy']['pilot_accepts_only']:
        raise PilotError(f'pilot requires FRESH observation, found {freshness}')
    manifest_bytes = pretty_bytes(manifest)
    correction_bytes = pretty_bytes(correction_ledger)
    proof_bytes = pretty_bytes(proof)
    packet_id = f'btc:daily:{observation_day.isoformat()}:{current_state_sha[:16]}'
    previous_packet_id = f'btc:daily:{previous_day.isoformat()}:{previous_state_sha[:16]}'
    interval = f'between {previous_day.isoformat()} and {observation_day.isoformat()} completed UTC observations'
    source_refs = {}
    packet_sources = []
    for item in manifest['archives']:
        ref = 'binance_btcusdt_1d_' + item['observation_date'].replace('-', '_')
        source_refs[item['archive_id']] = ref
        packet_sources.append({'source_ref': ref, 'provider': 'BINANCE_PUBLIC_DATA', 'source_class': 'CHECKSUM_BOUND_DAILY_ARCHIVE', 'source_locator': item['zip_url'], 'expected_sha256': item['expected_sha256'], 'actual_sha256': item['actual_sha256'], 'fetched_at_utc': item['fetched_at_utc'], 'observed_at_utc': item['observed_at_utc'], 'correction_status': 'CLEAR', 'rights_status': 'INTERNAL_RESEARCH_ALLOWED'})
    current_ref = source_refs[current_row['archive_id']]
    facts = []
    for fact_id, key, unit in (('btc_open', 'open', 'USDT'), ('btc_high', 'high', 'USDT'), ('btc_low', 'low', 'USDT'), ('btc_close', 'close', 'USDT'), ('btc_base_volume', 'base_volume', 'BTC'), ('btc_quote_volume', 'quote_volume', 'USDT'), ('btc_trade_count', 'trade_count', 'count')):
        facts.append({'fact_id': fact_id, 'value': current_row[key], 'unit': unit, 'evidence_tier': T0, 'source_refs': [current_ref], 'eligibility': 'ALLOWED'})
    metrics = [{'metric_id': metric_id, 'value': current_metrics[metric_id], 'unit': 'ratio', 'observation_window': WINDOWS[metric_id], 'methodology_id': METHODOLOGY_ID, 'methodology_sha256': METHODOLOGY_SHA256, 'evidence_tier': T2, 'stability_status': 'PASS', 'eligibility': 'ALLOWED', 'source_fact_ids': FACT_BINDING[metric_id], 'correction_status': 'CLEAR'} for metric_id in TIER2_METRICS]
    changes = []
    for metric_id in TIER2_METRICS:
        current_value = current_metrics[metric_id]
        previous_value = previous_metrics[metric_id]
        delta = round12(current_value - previous_value)
        changes.append({'metric_id': metric_id, 'current_packet_id': packet_id, 'previous_packet_id': previous_packet_id, 'comparison_status': 'COMPARABLE', 'current_value': current_value, 'previous_value': previous_value, 'raw_delta': delta, 'delta_unit': 'ratio', 'historical_direction': 'UP' if delta > 0 else 'DOWN' if delta < 0 else 'UNCHANGED', 'methodology_match': True, 'correction_status': 'CLEAR', 'interval_label': interval})
    label = range_state(current_metrics['range_position_30d'])
    human = {'observation': f"At {current_row['close_time_utc']}, the latest accepted completed UTC BTC observation closed at {current_row['close']:.2f} USDT. Its trailing 30-day range position was {current_metrics['range_position_30d']:.6f}, classified as {label}.", 'change': f"The comparison interval was {interval}. return_1d changed from {pct(previous_metrics['return_1d'])} to {pct(current_metrics['return_1d'])}; return_7d from {pct(previous_metrics['return_7d'])} to {pct(current_metrics['return_7d'])}; range_position_30d from {ratio(previous_metrics['range_position_30d'])} to {ratio(current_metrics['range_position_30d'])}; quote_volume_ratio_to_prior_30d_median from {ratio(previous_metrics['quote_volume_ratio_to_prior_30d_median'])} to {ratio(current_metrics['quote_volume_ratio_to_prior_30d_median'])}.", 'evidence': 'The four Tier 2 metrics were recomputed from 32 checksum-bound Binance daily archives, with contiguous UTC rows, matching methodology bindings, correction control, and prefix-invariance proof.', 'uncertainty': 'Predictive power has not been demonstrated. The packet is descriptive and internal research only.', 'boundary': validator.CANONICAL_BOUNDARY}
    packet = {'schema_version': 'market_cosmographer_ai_descriptive_packet_v0_1', 'packet_id': packet_id, 'packet_generation_id': f'btc-daily-pilot-v0-1:{observation_day.isoformat()}:{generated_at_utc}', 'subject': {'asset_id': 'bitcoin', 'symbol': 'BTC', 'market': 'BTCUSDT_SPOT', 'interval': '1d_UTC', 'quote_asset': 'USDT'}, 'observation': {'observation_date': observation_day.isoformat(), 'as_of_utc': current_row['close_time_utc'], 'input_max_timestamp_utc': current_row['close_time_utc'], 'generated_at_utc': generated_at_utc, 'freshness_policy_id': policy['freshness_policy']['freshness_policy_id'], 'freshness_status': freshness}, 'sources': packet_sources, 'facts': facts, 'metrics': metrics, 'labels': [{'label_id': 'range_state', 'value': label, 'input_metric_id': 'range_position_30d', 'input_metric_tier': T2, 'threshold_contract_id': METHODOLOGY_ID, 'threshold_contract_sha256': METHODOLOGY_SHA256, 'calibration_status': 'PASS', 'effective_eligibility': 'ALLOWED'}], 'changes': changes, 'evidence': {'source_manifest_sha256': sha256_bytes(manifest_bytes), 'methodology_sha256': METHODOLOGY_SHA256, 'correction_ledger_sha256': sha256_bytes(correction_bytes), 'no_lookahead_proof_sha256': sha256_bytes(proof_bytes), 'stability_review_id': STABILITY_REVIEW_ID, 'stability_review_sha256': STABILITY_REVIEW_SHA256}, 'uncertainty': {'uncertainty_status': 'DISCLOSED', 'reasons': ['Predictive power has not been demonstrated.', 'The packet is an internal descriptive utility-pilot observation.'], 'unstable_metric_ids': ['drawdown_from_365d_high', 'realized_volatility_30d_annualized', 'return_30d', 'trend_persistence_30d'], 'blocked_label_ids': ['drawdown_state', 'return_state', 'trend_state', 'volatility_state', 'volume_state'], 'stale_source_refs': [], 'incomparable_change_ids': [], 'unresolved_correction_ids': []}, 'exclusions': [{'field_id': field_id, 'reason': reason} for field_id, reason in sorted(validator.expected_exclusions().items())], 'human_read': human, 'boundary': {'descriptive_only': True, 'predictive_power_proven': False, 'forecast_allowed': False, 'scenario_probability_allowed': False, 'trading_signal_allowed': False, 'price_target_allowed': False, 'investment_recommendation_allowed': False}, 'distribution': {'mode': 'INTERNAL_RESEARCH_ONLY', 'commercial_ai_feed': False, 'data_rights_status': 'PENDING', 'correction_sla_status': 'PENDING', 'ai_consumer_utility_status': 'PENDING'}}
    state = {'current': {**current_state, 'state_sha256': current_state_sha}, 'previous': {**previous_state, 'state_sha256': previous_state_sha}}
    diagnostics = {'freshness_status': freshness, 'age_hours': round(age_hours, 6)}
    return (packet, state, diagnostics)
