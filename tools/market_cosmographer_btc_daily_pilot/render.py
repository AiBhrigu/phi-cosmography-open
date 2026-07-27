"""Deterministic RU/EN renderers and build outputs."""
from __future__ import annotations
from pathlib import Path
from tools.market_cosmographer_btc_daily_pilot.common import *
from tools.market_cosmographer_btc_daily_pilot.compute import pct, ratio
def render_en(packet: dict) -> str:
    metrics = {item['metric_id']: item['value'] for item in packet['metrics']}
    label = packet['labels'][0]['value']
    return '\n'.join(['# Market Cosmographer · BTC · Daily Descriptive Read', '', f"**Accepted completed UTC observation:** {packet['observation']['as_of_utc']}", '', packet['human_read']['observation'], '', '## Allowed descriptive metrics', '', f"- 1-day return: {pct(metrics['return_1d'])}", f"- 7-day return: {pct(metrics['return_7d'])}", f"- 30-day range position: {ratio(metrics['range_position_30d'])} ({label})", f"- Quote-volume ratio to prior 30-day median: {ratio(metrics['quote_volume_ratio_to_prior_30d_median'])}", '', '## Historical change', '', packet['human_read']['change'], '', '## Evidence', '', packet['human_read']['evidence'], '', '## Uncertainty', '', packet['human_read']['uncertainty'], '', '## Boundary', '', packet['human_read']['boundary'], '', f"Packet ID: `{packet['packet_id']}`", 'Distribution: `INTERNAL_RESEARCH_ONLY`', ''])

def render_ru(packet: dict) -> str:
    metrics = {item['metric_id']: item['value'] for item in packet['metrics']}
    changes = {item['metric_id']: item for item in packet['changes']}
    label = packet['labels'][0]['value']
    label_ru = {'LOWER': 'нижняя часть', 'MIDDLE': 'средняя часть', 'UPPER': 'верхняя часть'}[label]
    close = next((item['value'] for item in packet['facts'] if item['fact_id'] == 'btc_close'))
    previous_date = packet['changes'][0]['previous_packet_id'].split(':')[2]
    current_date = packet['observation']['observation_date']
    return '\n'.join(['# Market Cosmographer · BTC · Ежедневное описательное чтение', '', f"**Принятое завершённое UTC-наблюдение:** {packet['observation']['as_of_utc']}", '', f"Цена закрытия BTC составляла {close:.2f} USDT. Положение в завершённом 30-дневном диапазоне — {metrics['range_position_30d']:.6f}; классификация: {label_ru} диапазона.", '', '## Разрешённые описательные метрики', '', f"- Доходность за 1 завершённый UTC-день: {pct(metrics['return_1d'])}", f"- Доходность за 7 завершённых UTC-дней: {pct(metrics['return_7d'])}", f"- Положение в 30-дневном диапазоне: {ratio(metrics['range_position_30d'])} ({label_ru})", f"- Отношение quote volume к медиане предыдущих 30 дней: {ratio(metrics['quote_volume_ratio_to_prior_30d_median'])}", '', '## Историческое изменение', '', f"Интервал: {previous_date} → {current_date}. return_1d: {pct(changes['return_1d']['previous_value'])} → {pct(changes['return_1d']['current_value'])}; return_7d: {pct(changes['return_7d']['previous_value'])} → {pct(changes['return_7d']['current_value'])}; range_position_30d: {ratio(changes['range_position_30d']['previous_value'])} → {ratio(changes['range_position_30d']['current_value'])}; quote-volume ratio: {ratio(changes['quote_volume_ratio_to_prior_30d_median']['previous_value'])} → {ratio(changes['quote_volume_ratio_to_prior_30d_median']['current_value'])}.", '', '## Доказательства', '', 'Четыре метрики Tier 2 пересчитаны из 32 ежедневных Binance-архивов с контрольными суммами. Проверены непрерывность UTC-ряда, frozen methodology, correction control и prefix invariance.', '', '## Неопределённость', '', 'Прогнозная сила не доказана. Пакет является внутренним описательным наблюдением utility pilot.', '', '## Граница', '', 'Чтение описывает только наблюдаемое состояние рынка и историческое изменение. Оно не прогнозирует цену, не предоставляет торговый сигнал, не оценивает будущие вероятности, не устанавливает ценовую цель и не является инвестиционной рекомендацией.', '', f"Packet ID: `{packet['packet_id']}`", 'Распространение: `INTERNAL_RESEARCH_ONLY`', ''])

def write_build_outputs(output_dir: Path, packet: dict, state: dict, manifest: dict, correction_ledger: dict, proof: dict, diagnostics: dict, policy: dict, validator, repo: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    validator.validate_packet(packet, validator.load_json(repo / CONTRACT_REL))
    payloads = {'btc_daily_descriptive_packet.json': pretty_bytes(packet), 'btc_daily_descriptive_read.en.md': render_en(packet).encode('utf-8'), 'btc_daily_descriptive_read.ru.md': render_ru(packet).encode('utf-8'), 'btc_daily_source_manifest.json': pretty_bytes(manifest), 'btc_daily_correction_ledger.json': pretty_bytes(correction_ledger), 'btc_daily_no_lookahead_proof.json': pretty_bytes(proof), 'btc_daily_state_pair.json': pretty_bytes(state)}
    output_hashes = {name: sha256_bytes(data) for name, data in payloads.items()}
    report = {'schema_version': 'market_cosmographer_btc_daily_build_report_v0_1', 'status': 'PASS', 'pilot_id': policy['pilot_id'], 'pilot_day_index': pilot_day_index(policy, parse_date(packet['observation']['observation_date'])), 'packet_id': packet['packet_id'], 'observation_date': packet['observation']['observation_date'], 'generated_at_utc': packet['observation']['generated_at_utc'], 'freshness_status': diagnostics['freshness_status'], 'age_hours': diagnostics['age_hours'], 'source_archive_count': manifest['archive_count'], 'source_integrity': 'PASS', 'utc_contiguity': 'PASS', 'correction_control': 'PASS', 'no_lookahead': 'PASS', 'methodology_binding': 'PASS', 'contract_validation': 'PASS', 'predictive_boundary': 'PASS', 'render_languages': ['en', 'ru'], 'distribution': 'INTERNAL_RESEARCH_ONLY', 'commercial_ai_feed': 'CLOSED', 'public_page_change': False, 'public_snapshot_change': False, 'output_sha256': output_hashes}
    payloads['btc_daily_build_report.json'] = pretty_bytes(report)
    for name, data in payloads.items():
        (output_dir / name).write_bytes(data)
    return report
