"""Checksum-bound Binance daily archive acquisition and parsing."""
from __future__ import annotations
import csv, io, math, time, urllib.error, urllib.request, zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from tools.market_cosmographer_btc_daily_pilot.common import PilotError, SOURCE_ROOT, parse_utc, sha256_bytes
def archive_name(day: date) -> str:
    return f'BTCUSDT-1d-{day.isoformat()}.zip'

def member_name(day: date) -> str:
    return f'BTCUSDT-1d-{day.isoformat()}.csv'

def archive_url(day: date) -> str:
    return f'{SOURCE_ROOT}/{archive_name(day)}'

def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={'User-Agent': 'BHRIGU-MARKET-COSMOGRAPHER-DAILY-PILOT/0.1', 'Cache-Control': 'no-cache'})
    error = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                if response.status != 200:
                    raise PilotError(f'HTTP {response.status}: {url}')
                return response.read()
        except (urllib.error.URLError, TimeoutError, PilotError) as exc:
            error = exc
            if attempt < 4:
                time.sleep(1.5 * (attempt + 1))
    raise PilotError(f'download failed: {url}: {error}')

def parse_checksum(payload: bytes, expected_name: str) -> str:
    try:
        parts = payload.decode('utf-8').strip().split()
    except UnicodeDecodeError as exc:
        raise PilotError('checksum is not UTF-8') from exc
    if len(parts) < 2:
        raise PilotError('checksum format')
    digest, found_name = (parts[0].lower(), parts[-1].lstrip('*'))
    if len(digest) != 64 or any((char not in '0123456789abcdef' for char in digest)):
        raise PilotError('checksum digest')
    if found_name != expected_name:
        raise PilotError('checksum filename binding')
    return digest

def fetch_source_window(folder: Path, start: date, end: date) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    current = start
    while current <= end:
        name = archive_name(current)
        zip_path = folder / name
        checksum_path = folder / f'{name}.CHECKSUM'
        checksum_payload = download(archive_url(current) + '.CHECKSUM')
        expected = parse_checksum(checksum_payload, name)
        archive_payload = download(archive_url(current))
        actual = sha256_bytes(archive_payload)
        if actual != expected:
            raise PilotError(f'provider checksum mismatch: {current}')
        checksum_path.write_bytes(checksum_payload)
        zip_path.write_bytes(archive_payload)
        current += timedelta(days=1)

def binance_time(raw: str) -> datetime:
    try:
        numeric = int(raw)
    except ValueError as exc:
        raise PilotError('archive timestamp') from exc
    divisor = 1000000 if numeric >= 10 ** 15 else 1000
    return datetime.fromtimestamp(numeric / divisor, tz=timezone.utc)

def number(raw: str, where: str, positive: bool=False) -> float:
    try:
        value = float(raw)
    except ValueError as exc:
        raise PilotError(f'archive {where}') from exc
    if not math.isfinite(value) or value < 0 or (positive and value <= 0):
        raise PilotError(f'archive {where}')
    return value

def parse_daily_archive(day: date, payload: bytes) -> dict:
    expected_member = member_name(day)
    try:
        archive = zipfile.ZipFile(io.BytesIO(payload))
    except zipfile.BadZipFile as exc:
        raise PilotError(f'bad ZIP: {day}') from exc
    if archive.namelist() != [expected_member]:
        raise PilotError(f'archive member mismatch: {day}')
    rows = []
    with archive.open(expected_member) as raw:
        for line_number, row in enumerate(csv.reader(io.TextIOWrapper(raw, encoding='utf-8', newline='')), 1):
            if len(row) != 12:
                raise PilotError(f'archive columns: {day}:{line_number}')
            open_time, close_time = (binance_time(row[0]), binance_time(row[6]))
            if open_time.date() != day or open_time.time() != datetime.min.time() or close_time.date() != day:
                raise PilotError(f'archive UTC day: {day}')
            open_value = number(row[1], 'open', True)
            high = number(row[2], 'high', True)
            low = number(row[3], 'low', True)
            close = number(row[4], 'close', True)
            base_volume = number(row[5], 'base volume')
            quote_volume = number(row[7], 'quote volume')
            try:
                trades = int(row[8])
            except ValueError as exc:
                raise PilotError('archive trades') from exc
            if trades < 0 or high < max(open_value, low, close) or low > min(open_value, high, close):
                raise PilotError(f'archive OHLC invariant: {day}')
            rows.append({'observation_date': day.isoformat(), 'close_time_utc': close_time.isoformat().replace('+00:00', 'Z'), 'open': open_value, 'high': high, 'low': low, 'close': close, 'base_volume': base_volume, 'quote_volume': quote_volume, 'trade_count': trades})
    if len(rows) != 1:
        raise PilotError(f'daily archive row count: {day}')
    return rows[0]

def read_source_window(folder: Path, start: date, end: date, fetched_at_utc: str) -> tuple[list[dict], dict]:
    parse_utc(fetched_at_utc, 'fetched_at_utc')
    rows = []
    archives = []
    current = start
    while current <= end:
        name = archive_name(current)
        zip_path = folder / name
        checksum_path = folder / f'{name}.CHECKSUM'
        if not zip_path.is_file() or not checksum_path.is_file():
            raise PilotError(f'source file missing: {name}')
        payload = zip_path.read_bytes()
        expected = parse_checksum(checksum_path.read_bytes(), name)
        actual = sha256_bytes(payload)
        if actual != expected:
            raise PilotError(f'local checksum mismatch: {current}')
        row = parse_daily_archive(current, payload)
        row['archive_id'] = f'daily:{current.isoformat()}'
        row['archive_sha256'] = actual
        rows.append(row)
        archives.append({'archive_id': row['archive_id'], 'frequency': 'daily', 'observation_date': current.isoformat(), 'zip_url': archive_url(current), 'checksum_url': archive_url(current) + '.CHECKSUM', 'expected_sha256': expected, 'actual_sha256': actual, 'bytes': len(payload), 'member': member_name(current), 'row_count': 1, 'observed_at_utc': row['close_time_utc'], 'fetched_at_utc': fetched_at_utc})
        current += timedelta(days=1)
    expected_dates = [(start + timedelta(days=index)).isoformat() for index in range((end - start).days + 1)]
    if [row['observation_date'] for row in rows] != expected_dates:
        raise PilotError('source window not contiguous')
    manifest = {'schema_version': 'market_cosmographer_btc_daily_source_manifest_v0_1', 'status': 'PASS', 'provider': 'BINANCE_PUBLIC_DATA', 'market': 'BTCUSDT_SPOT', 'interval': '1d_UTC', 'window_start_date': start.isoformat(), 'window_end_date': end.isoformat(), 'archive_count': len(archives), 'archives': archives, 'raw_archive_distribution': False}
    return (rows, manifest)
