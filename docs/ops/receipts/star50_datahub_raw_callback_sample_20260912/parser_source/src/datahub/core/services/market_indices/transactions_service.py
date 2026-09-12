# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import hashlib
import io
import json
import shutil
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol, Sequence

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from datahub.core.models.dataset import DataQualityReport, DatasetManifest
from datahub.core.models.market_index_transactions import MarketIndexTransactionsDataset
from datahub.core.services.history.partitioned_canonical_publisher import (
    PartitionedCanonicalPublishResult,
    PartitionedCanonicalPublisher,
)
from datahub.storage.repositories.dataset_manifests import DatasetManifestRepository
from datahub.storage.repositories.dataset_versions import DatasetVersionRepository
from datahub.storage.repositories.quality_reports import QualityReportRepository

from .catalog import MarketIndexCatalog, MarketIndexDefinition

DATASET_KIND = "market_index_transactions"
DATASET_ID = "market_index_transactions_cn_3s"
SCHEMA_VERSION = "market_index_transactions.v1"
FREQUENCY = "3s"
MARKET = "cn_index"
BAIDU_SOURCE_KIND = "baidu_netdisk_market_index_transaction_3s"
TDX_SOURCE_KIND = "tdx_market_index_history_transaction_reconstructed_3s"
MINUTE_SOURCE_DATASET_ID = "bars_cn_index_1m_market_index_transaction_derived"


@dataclass(frozen=True, slots=True)
class IndexTransactionInspectResult:
    archive_path: str
    archive_sha256: str
    member_count: int
    selected_members: list[str]
    header_sets: list[list[str]]
    sample_rows: list[dict[str, Any]]
    consistent: bool


@dataclass(frozen=True, slots=True)
class IndexTransactionWriteResult:
    dataset_version: str
    state: str
    storage_uri: str
    record_count: int
    symbol_scope: list[str]
    time_range: dict[str, str]
    coverage: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class IndexMinuteDerivationResult:
    source_dataset_version: str
    bars_source_dataset_version: str
    bars_source_storage_uri: str
    record_count: int
    canonical: PartitionedCanonicalPublishResult | None
    coverage: dict[str, Any]


class TdxIndexTransactionClient(Protocol):
    async def get_history_transaction_data(
        self, market: int, code: str, start: int, count: int, date: int
    ) -> object | None: ...


class MarketIndexTransactionArchiveReader:
    REQUIRED_COLUMNS = ("时间", "价位", "成交额")

    def __init__(self, *, catalog: MarketIndexCatalog | None = None) -> None:
        self.catalog = catalog or MarketIndexCatalog()

    def inspect_zip(
        self, *, zip_path: str | Path, symbols: Iterable[str] | None = None
    ) -> IndexTransactionInspectResult:
        definitions = self.catalog.select(symbols)
        selected = {
            f"{item.source_archive_code or item.index_code}.csv"
            for item in definitions
        }
        samples: list[dict[str, Any]] = []
        headers: list[list[str]] = []
        with zipfile.ZipFile(zip_path) as archive:
            members = sorted(
                name for name in archive.namelist() if name.endswith(".csv")
            )
            chosen = [name for name in members if Path(name).name in selected]
            for name in chosen:
                reader = csv.DictReader(
                    io.StringIO(archive.read(name).decode("utf-8-sig"))
                )
                headers.append(list(reader.fieldnames or []))
                first = next(reader, None)
                if first is not None:
                    samples.append({"member": name, **first})
        unique_headers = {tuple(item) for item in headers}
        return IndexTransactionInspectResult(
            archive_path=str(zip_path),
            archive_sha256=_sha256_file(Path(zip_path)),
            member_count=len(members),
            selected_members=chosen,
            header_sets=[list(item) for item in sorted(unique_headers)],
            sample_rows=samples,
            consistent=bool(chosen) and unique_headers == {self.REQUIRED_COLUMNS},
        )

    def read_zip(
        self,
        *,
        zip_path: str | Path,
        symbols: Iterable[str] | None = None,
        trading_day: str | None = None,
        invalid_row_policy: str = "raise",
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        if invalid_row_policy not in {"raise", "quarantine"}:
            raise ValueError("invalid_row_policy must be raise or quarantine")
        definitions = self.catalog.select(symbols)
        by_member = {
            f"{item.source_archive_code or item.index_code}.csv": item
            for item in definitions
        }
        archive_sha = _sha256_file(Path(zip_path))
        rows: list[dict[str, Any]] = []
        invalid_rows: list[dict[str, Any]] = []
        seen_members: set[str] = set()
        with zipfile.ZipFile(zip_path) as archive:
            for name in sorted(archive.namelist()):
                definition = by_member.get(Path(name).name)
                if definition is None:
                    continue
                seen_members.add(Path(name).name)
                reader = csv.DictReader(
                    io.StringIO(archive.read(name).decode("utf-8-sig"))
                )
                if tuple(reader.fieldnames or []) != self.REQUIRED_COLUMNS:
                    raise ValueError(
                        f"unsupported market-index transaction header in {name}: {reader.fieldnames}"
                    )
                for row_index, raw in enumerate(reader):
                    try:
                        normalized = _normalize_observation(
                            definition=definition,
                            observation_datetime=str(raw.get("时间") or ""),
                            price=raw.get("价位"),
                            amount=raw.get("成交额"),
                            source_kind=BAIDU_SOURCE_KIND,
                            timestamp_mode="source_exact_3s",
                            source_file=name,
                            source_archive_sha256=archive_sha,
                            row_index=row_index,
                        )
                    except (TypeError, ValueError) as exc:
                        if invalid_row_policy == "raise":
                            raise
                        invalid_rows.append(
                            {
                                "member": name,
                                "row_index": row_index,
                                "raw": dict(raw),
                                "error_type": type(exc).__name__,
                                "error": str(exc),
                            }
                        )
                        continue
                    rows.append(normalized)
        expected_members = set(by_member)
        missing = sorted(expected_members - seen_members)
        if trading_day:
            normalized_day = _normalize_day(trading_day)
            wrong = sorted(
                {
                    row["trading_day"]
                    for row in rows
                    if row["trading_day"] != normalized_day
                }
            )
            if wrong:
                raise ValueError(
                    f"archive trading_day mismatch: expected {normalized_day}, got {wrong}"
                )
        receipt = {
            "source_kind": BAIDU_SOURCE_KIND,
            "archive_path": str(zip_path),
            "archive_sha256": archive_sha,
            "requested_symbols": [item.symbol for item in definitions],
            "selected_member_count": len(seen_members),
            "missing_members": missing,
            "source_archive_codes": {
                item.symbol: item.source_archive_code or item.index_code
                for item in definitions
            },
            "invalid_row_policy": invalid_row_policy,
            "invalid_row_count": len(invalid_rows),
            "invalid_rows": invalid_rows,
        }
        return rows, receipt


class TdxMarketIndexTransactionProvider:
    def __init__(
        self,
        client: TdxIndexTransactionClient,
        *,
        catalog: MarketIndexCatalog | None = None,
    ) -> None:
        self.client = client
        self.catalog = catalog or MarketIndexCatalog()

    async def fetch_day(
        self,
        *,
        trading_day: str,
        symbols: Iterable[str] | None = None,
        page_size: int = 2000,
        max_pages: int = 8,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        day = _normalize_day(trading_day)
        date_int = int(day.replace("-", ""))
        output: list[dict[str, Any]] = []
        page_counts: dict[str, list[int]] = {}
        for definition in self.catalog.select(symbols):
            pages: list[tuple[int, list[dict[str, Any]]]] = []
            for page in range(max_pages):
                start = page * page_size
                payload = await self.client.get_history_transaction_data(
                    definition.tdx_market_code,
                    definition.tdx_transaction_code or definition.index_code,
                    start,
                    page_size,
                    date_int,
                )
                rows = (
                    [dict(item) for item in payload]
                    if isinstance(payload, list)
                    else []
                )
                pages.append((start, rows))
                if len(rows) < page_size:
                    break
            page_counts[definition.symbol] = [len(rows) for _, rows in pages]
            output.extend(
                _reconstruct_tdx_observations(definition, day=day, pages=pages)
            )
        return output, {
            "source_kind": TDX_SOURCE_KIND,
            "trading_day": day,
            "page_counts": page_counts,
            "timestamp_mode": "minute_protocol_plus_stable_sequence_rank_3s",
            "amount_mapping": "TDX vol * 100 CNY",
            "transaction_route_codes": {
                item.symbol: item.tdx_transaction_code or item.index_code
                for item in self.catalog.select(symbols)
            },
        }


class MarketIndexTransactionWriter:
    def __init__(self, *, lake_dir: str | Path, db_path: str | Path) -> None:
        self.lake_dir = Path(lake_dir)
        self.db_path = Path(db_path)

    def write_records(
        self,
        *,
        records: Sequence[Mapping[str, Any]],
        source_receipt: Mapping[str, Any],
        dataset_version: str,
    ) -> IndexTransactionWriteResult:
        rows = [dict(item) for item in records]
        rows.sort(
            key=lambda item: (
                item["symbol"],
                item["observation_datetime"],
                item["row_index"],
            )
        )
        if not rows:
            raise ValueError("market-index transaction records are empty")
        target = self.lake_dir / DATASET_KIND / f"dataset_version={dataset_version}"
        staging = target.parent / f".{target.name}.staging"
        if target.exists() or staging.exists():
            raise ValueError(f"dataset_version already exists: {dataset_version}")
        duplicate_count = len(rows) - len(
            {
                (row["symbol"], row["observation_datetime"], row["row_index"])
                for row in rows
            }
        )
        coverage = _observation_coverage(rows, duplicate_count=duplicate_count)
        state = "READY" if not coverage["blocking_reasons"] else "PARTIAL"
        start_time = min(str(row["observation_datetime"]) for row in rows)
        end_time = max(str(row["observation_datetime"]) for row in rows)
        symbols = sorted({str(row["symbol"]) for row in rows})
        staging.mkdir(parents=True, exist_ok=False)
        try:
            pq.write_table(pa.Table.from_pylist(rows), staging / "observations.parquet")
            receipt = dict(source_receipt)
            receipt["record_count"] = len(rows)
            receipt["receipt_sha256"] = _sha256_json(receipt)
            (staging / "source_receipt.json").write_text(
                json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            manifest = DatasetManifest(
                manifest_id=f"manifest_{dataset_version}",
                dataset_id=DATASET_ID,
                dataset_version=dataset_version,
                dataset_kind=DATASET_KIND,
                schema_version=SCHEMA_VERSION,
                market=MARKET,
                frequency=FREQUENCY,
                symbol_scope=symbols,
                time_range={"start_time": start_time, "end_time": end_time},
                storage_uri=str(target),
                record_count=len(rows),
                dataset_hash=_sha256_json(rows),
                format="parquet",
                generated_at=datetime.now(timezone.utc).isoformat(),
                layer="curated",
            )
            quality = DataQualityReport(
                report_id=f"quality_{dataset_version}",
                target_dataset_version=dataset_version,
                duplicate_count=duplicate_count,
                null_counts={
                    "price": sum(row.get("price") is None for row in rows),
                    "amount": sum(row.get("amount") is None for row in rows),
                },
                quality_score=100.0 if state == "READY" else 0.0,
                generated_at=datetime.now(timezone.utc).isoformat(),
            )
            (staging / "manifest.json").write_text(
                json.dumps(
                    manifest.model_dump(mode="json"), ensure_ascii=False, indent=2
                ),
                encoding="utf-8",
            )
            (staging / "quality_report.json").write_text(
                json.dumps(
                    quality.model_dump(mode="json"), ensure_ascii=False, indent=2
                ),
                encoding="utf-8",
            )
            (staging / "coverage_report.json").write_text(
                json.dumps(coverage, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            staging.rename(target)
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise
        DatasetManifestRepository(db_path=self.db_path).save(
            manifest_id=manifest.manifest_id,
            dataset_version=dataset_version,
            manifest=manifest,
        )
        QualityReportRepository(db_path=self.db_path).save(
            report_id=quality.report_id,
            dataset_version=dataset_version,
            report=quality,
        )
        DatasetVersionRepository(db_path=self.db_path).save(
            dataset_version=dataset_version,
            dataset_id=DATASET_ID,
            dataset_kind=DATASET_KIND,
            state=state,
            market=MARKET,
            frequency=FREQUENCY,
            time_range_start=start_time,
            time_range_end=end_time,
            storage_uri=str(target),
            manifest_id=manifest.manifest_id,
            quality_report_id=quality.report_id,
        )
        return IndexTransactionWriteResult(
            dataset_version=dataset_version,
            state=state,
            storage_uri=str(target),
            record_count=len(rows),
            symbol_scope=symbols,
            time_range={"start_time": start_time, "end_time": end_time},
            coverage=coverage,
        )


class MarketIndexTransactionQuery:
    def __init__(self, *, db_path: str | Path) -> None:
        self.repo = DatasetVersionRepository(db_path=db_path)

    def query(
        self,
        *,
        dataset_version: str,
        symbols: Iterable[str],
        start_time: str,
        end_time: str,
        limit: int = 10000,
    ) -> MarketIndexTransactionsDataset:
        dataset = self.repo.get(dataset_version)
        if dataset is None:
            return MarketIndexTransactionsDataset(dataset_version=None)
        if dataset["dataset_id"] != DATASET_ID or dataset["state"] != "READY":
            raise ValueError(
                "dataset_version is not a READY market-index transaction product"
            )
        selected = [str(item).upper() for item in symbols]
        placeholders = ",".join("?" for _ in selected)
        where = ["observation_datetime >= ?", "observation_datetime <= ?"]
        params: list[Any] = [
            str(Path(dataset["storage_uri"]) / "observations.parquet"),
            start_time,
            end_time,
        ]
        if selected:
            where.append(f"symbol IN ({placeholders})")
            params.extend(selected)
        params.append(max(1, min(int(limit), 200000)))
        with duckdb.connect(database=":memory:") as conn:
            cursor = conn.execute(
                "SELECT * FROM read_parquet(?) WHERE "
                + " AND ".join(where)
                + " ORDER BY observation_datetime, symbol, row_index LIMIT ?",
                params,
            )
            columns = [item[0] for item in (cursor.description or [])]
            items = [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]
        return MarketIndexTransactionsDataset(
            dataset_version=dataset_version,
            items=items,
            quality_summary={"timestamp_modes": _counts(items, "timestamp_mode")},
        )


class MarketIndexTransactionCoverageService:
    def __init__(self, *, db_path: str | Path) -> None:
        self.repo = DatasetVersionRepository(db_path=db_path)

    def audit(self, *, dataset_version: str) -> dict[str, Any]:
        dataset = self.repo.get(dataset_version)
        if dataset is None:
            return {"dataset_version": None, "coverage": {"data_ready": False}}
        if dataset["dataset_id"] != DATASET_ID:
            raise ValueError(
                "dataset_version is not a market-index transaction product"
            )
        coverage = json.loads(
            (Path(dataset["storage_uri"]) / "coverage_report.json").read_text(
                encoding="utf-8"
            )
        )
        return {
            "dataset_version": dataset_version,
            "dataset_state": dataset["state"],
            "coverage": coverage,
        }


class MarketIndexTransactionToMinuteBarsDeriver:
    def __init__(self, *, lake_dir: str | Path, db_path: str | Path) -> None:
        self.lake_dir = Path(lake_dir)
        self.db_path = Path(db_path)

    def derive_and_publish(
        self,
        *,
        source_dataset_version: str,
        dataset_suffix: str,
        previous_canonical_version: str | None = None,
        publish_canonical: bool = True,
    ) -> IndexMinuteDerivationResult:
        source = DatasetVersionRepository(db_path=self.db_path).get(
            source_dataset_version
        )
        if (
            source is None
            or source["dataset_id"] != DATASET_ID
            or source["state"] != "READY"
        ):
            raise ValueError("source must be a READY market-index transaction dataset")
        bars_version = f"{MINUTE_SOURCE_DATASET_ID}_{dataset_suffix}"
        bars_root = (
            self.lake_dir
            / "market_index_minute_bars_source"
            / f"dataset_version={bars_version}"
        )
        if bars_root.exists():
            raise ValueError(
                f"bars source dataset_version already exists: {bars_version}"
            )
        rows = _derive_minute_rows(
            parquet_path=Path(source["storage_uri"]) / "observations.parquet",
            dataset_version=bars_version,
        )
        coverage = _minute_coverage(rows)
        if coverage["blocking_reasons"]:
            raise ValueError(
                f"market-index 1m derivation failed: {coverage['blocking_reasons']}"
            )
        for (instrument_type, trading_month), partition_rows in _group_partitions(
            rows
        ).items():
            target = (
                bars_root
                / f"instrument_type={instrument_type}"
                / f"trading_month={trading_month}"
            )
            target.mkdir(parents=True, exist_ok=True)
            pq.write_table(
                pa.Table.from_pylist(partition_rows), target / "bars.parquet"
            )
        symbols = sorted({str(row["symbol"]) for row in rows})
        start_time = min(str(row["timestamp"]) for row in rows)
        end_time = max(str(row["timestamp"]) for row in rows)
        source_manifest = DatasetManifest(
            manifest_id=f"manifest_{bars_version}",
            dataset_id=MINUTE_SOURCE_DATASET_ID,
            dataset_version=bars_version,
            dataset_kind="bars",
            schema_version="bars.v1",
            market=MARKET,
            frequency="1m",
            symbol_scope=symbols,
            time_range={"start_time": start_time, "end_time": end_time},
            storage_uri=str(bars_root),
            record_count=len(rows),
            dataset_hash=_sha256_json(rows),
            format="parquet",
            generated_at=datetime.now(timezone.utc).isoformat(),
            layer="curated",
        )
        source_quality = DataQualityReport(
            report_id=f"quality_{bars_version}",
            target_dataset_version=bars_version,
            duplicate_count=int(coverage["duplicate_count"]),
            null_counts={"volume_not_available": len(rows)},
            quality_score=100.0,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
        (bars_root / "manifest.json").write_text(
            json.dumps(
                source_manifest.model_dump(mode="json"), ensure_ascii=False, indent=2
            ),
            encoding="utf-8",
        )
        (bars_root / "quality_report.json").write_text(
            json.dumps(
                source_quality.model_dump(mode="json"), ensure_ascii=False, indent=2
            ),
            encoding="utf-8",
        )
        (bars_root / "coverage_report.json").write_text(
            json.dumps(coverage, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        DatasetManifestRepository(db_path=self.db_path).save(
            manifest_id=source_manifest.manifest_id,
            dataset_version=bars_version,
            manifest=source_manifest,
        )
        QualityReportRepository(db_path=self.db_path).save(
            report_id=source_quality.report_id,
            dataset_version=bars_version,
            report=source_quality,
        )
        DatasetVersionRepository(db_path=self.db_path).save(
            dataset_version=bars_version,
            dataset_id=MINUTE_SOURCE_DATASET_ID,
            dataset_kind="bars",
            state="READY",
            market=MARKET,
            frequency="1m",
            time_range_start=start_time,
            time_range_end=end_time,
            storage_uri=str(bars_root),
            manifest_id=source_manifest.manifest_id,
            quality_report_id=source_quality.report_id,
        )
        canonical = None
        if publish_canonical:
            canonical = PartitionedCanonicalPublisher(
                lake_dir=self.lake_dir, db_path=self.db_path
            ).publish(
                source_dataset_version=bars_version,
                source_storage_uri=bars_root,
                market=MARKET,
                frequency="1m",
                dataset_suffix=dataset_suffix,
                previous_dataset_version=previous_canonical_version,
                source_label="market_index_transaction_derived_1m",
                replace_existing=False,
                allowed_source_instrument_types=["market_index"],
            )
        return IndexMinuteDerivationResult(
            source_dataset_version=source_dataset_version,
            bars_source_dataset_version=bars_version,
            bars_source_storage_uri=str(bars_root),
            record_count=len(rows),
            canonical=canonical,
            coverage=coverage,
        )


def _normalize_observation(
    *,
    definition: MarketIndexDefinition,
    observation_datetime: str,
    price: object,
    amount: object,
    source_kind: str,
    timestamp_mode: str,
    source_file: str,
    source_archive_sha256: str,
    row_index: int,
) -> dict[str, Any]:
    value = datetime.strptime(observation_datetime, "%Y-%m-%d %H:%M:%S")
    price_value = float(str(price))
    amount_value = float(str(amount))
    if price_value <= 0 or amount_value < 0:
        raise ValueError(f"invalid market-index observation: {observation_datetime}")
    return {
        "symbol": definition.symbol,
        "index_code": definition.index_code,
        "market": MARKET,
        "instrument_type": "market_index",
        "exchange": definition.exchange,
        "observation_datetime": value.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "trading_day": value.date().isoformat(),
        "observation_time": value.strftime("%H:%M:%S"),
        "price": price_value,
        "amount": amount_value,
        "volume": None,
        "session_phase": _session_phase(value.strftime("%H:%M:%S")),
        "timestamp_mode": timestamp_mode,
        "source_kind": source_kind,
        "source_file": source_file,
        "source_archive_sha256": source_archive_sha256,
        "row_index": int(row_index),
    }


def _reconstruct_tdx_observations(
    definition: MarketIndexDefinition,
    *,
    day: str,
    pages: list[tuple[int, list[dict[str, Any]]]],
) -> list[dict[str, Any]]:
    flat = [
        {"page_start": start, "page_row_index": index, **row}
        for start, rows in pages
        for index, row in enumerate(rows)
    ]
    flat.sort(
        key=lambda row: (
            str(row.get("time") or ""),
            int(row["page_start"]),
            int(row["page_row_index"]),
        )
    )
    ranks: dict[str, int] = defaultdict(int)
    output = []
    for row_index, row in enumerate(flat):
        minute = str(row.get("time") or "")[:5]
        rank = ranks[minute]
        ranks[minute] += 1
        if rank >= 20:
            raise ValueError(
                f"TDX index transaction minute has more than 20 rows: {minute}"
            )
        output.append(
            _normalize_observation(
                definition=definition,
                observation_datetime=f"{day} {minute}:{rank * 3:02d}",
                price=row.get("price"),
                amount=float(row.get("vol") or 0.0) * 100.0,
                source_kind=TDX_SOURCE_KIND,
                timestamp_mode="minute_protocol_plus_stable_sequence_rank_3s",
                source_file=f"tdx:{definition.tdx_market_code}:{definition.index_code}:{day}",
                source_archive_sha256="",
                row_index=row_index,
            )
        )
    return output


def _derive_minute_rows(
    *, parquet_path: Path, dataset_version: str
) -> list[dict[str, Any]]:
    with duckdb.connect(database=":memory:") as conn:
        source = (
            conn.execute(
                "SELECT * FROM read_parquet(?) ORDER BY symbol, observation_datetime, row_index",
                [str(parquet_path)],
            )
            .fetchdf()
            .to_dict("records")
        )
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in source:
        label = _minute_label(str(row["observation_time"]))
        if label is None:
            continue
        grouped[(str(row["symbol"]), str(row["trading_day"]), label)].append(row)
    output: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc).isoformat()
    for (symbol, day, label), rows in sorted(grouped.items()):
        rows.sort(
            key=lambda item: (str(item["observation_datetime"]), int(item["row_index"]))
        )
        prices = [float(item["price"]) for item in rows]
        output.append(
            {
                "symbol": symbol,
                "market": MARKET,
                "instrument_type": "market_index",
                "timestamp": f"{day}T{label}:00Z",
                "trading_day": day,
                "trading_month": day[:7],
                "open": prices[0],
                "high": max(prices),
                "low": min(prices),
                "close": prices[-1],
                "volume": None,
                "amount": sum(float(item["amount"]) for item in rows),
                "available_at": f"{day}T15:30:00+08:00",
                "ingested_at": now,
                "source_kind": "market_index_transaction_derived_1m",
                "dataset_version": dataset_version,
            }
        )
    return output


def _minute_label(value: str) -> str | None:
    hour, minute, second = (int(item) for item in value[:8].split(":"))
    total = hour * 60 + minute
    if 9 * 60 + 25 <= total < 9 * 60 + 30:
        return "09:31"
    if 9 * 60 + 30 <= total < 11 * 60 + 29:
        return _format_minute(total + 1)
    if 11 * 60 + 29 <= total <= 11 * 60 + 30:
        return "11:30"
    if 13 * 60 <= total < 14 * 60 + 58:
        return _format_minute(total + 1)
    if 14 * 60 + 58 <= total < 15 * 60:
        return _format_minute(min(total + 1, 15 * 60))
    if total == 15 * 60 and second <= 59:
        return "15:00"
    return None


def _format_minute(value: int) -> str:
    return f"{value // 60:02d}:{value % 60:02d}"


def _session_phase(value: str) -> str:
    if "09:15:00" <= value <= "09:24:59":
        return "pre_open_auction"
    if "09:25:00" <= value <= "09:29:59":
        return "open_call_auction"
    if ("09:30:00" <= value <= "11:30:59") or ("13:00:00" <= value <= "14:56:59"):
        return "continuous_auction"
    if "14:57:00" <= value <= "15:00:59":
        return "close_auction"
    return "outside_session"


def _observation_coverage(
    rows: list[dict[str, Any]], *, duplicate_count: int
) -> dict[str, Any]:
    invalid = sum(
        float(row.get("price") or 0) <= 0 or float(row.get("amount") or 0) < 0
        for row in rows
    )
    reconstructed = sum(row.get("timestamp_mode") != "source_exact_3s" for row in rows)
    blocking = []
    if duplicate_count:
        blocking.append("duplicate_observation_identity")
    if invalid:
        blocking.append("invalid_price_or_amount")
    return {
        "schema_version": "market_index_transactions_coverage.v1",
        "record_count": len(rows),
        "symbol_count": len({row["symbol"] for row in rows}),
        "trading_days": sorted({row["trading_day"] for row in rows}),
        "source_kind_counts": _counts(rows, "source_kind"),
        "timestamp_mode_counts": _counts(rows, "timestamp_mode"),
        "session_phase_counts": _counts(rows, "session_phase"),
        "reconstructed_timestamp_row_count": reconstructed,
        "volume_policy": "not_supplied_for_market_index_observations",
        "amount_policy": "CNY interval amount; TDX protocol vol is multiplied by 100",
        "duplicate_count": duplicate_count,
        "invalid_row_count": invalid,
        "blocking_reasons": blocking,
    }


def _minute_coverage(rows: list[dict[str, Any]]) -> dict[str, Any]:
    keys = [(row["symbol"], row["timestamp"]) for row in rows]
    duplicate_count = len(keys) - len(set(keys))
    labels = _counts(rows, "timestamp")
    blocking = ["duplicate_symbol_minute"] if duplicate_count else []
    return {
        "schema_version": "market_index_transaction_derived_1m_coverage.v1",
        "record_count": len(rows),
        "symbol_count": len({row["symbol"] for row in rows}),
        "duplicate_count": duplicate_count,
        "volume_policy": "null_not_available",
        "no_synthetic_carry_forward": True,
        "blocking_reasons": blocking,
        "label_count": len(labels),
    }


def _group_partitions(
    rows: list[dict[str, Any]],
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["instrument_type"]), str(row["trading_month"]))].append(row)
    return grouped


def _counts(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(field) or "")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _normalize_day(value: str) -> str:
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date().isoformat()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


__all__ = [
    "MarketIndexTransactionArchiveReader",
    "MarketIndexTransactionCoverageService",
    "MarketIndexTransactionQuery",
    "MarketIndexTransactionToMinuteBarsDeriver",
    "MarketIndexTransactionWriter",
    "TdxMarketIndexTransactionProvider",
]
