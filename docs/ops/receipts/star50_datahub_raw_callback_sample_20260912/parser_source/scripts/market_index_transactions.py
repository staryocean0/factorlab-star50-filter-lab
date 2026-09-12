#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from datahub.config.settings import Settings  # noqa: E402
from datahub.core.services.market_indices.catalog import MarketIndexCatalog  # noqa: E402
from datahub.core.services.market_indices.transactions_service import (  # noqa: E402
    MarketIndexTransactionArchiveReader,
    MarketIndexTransactionQuery,
    MarketIndexTransactionToMinuteBarsDeriver,
    MarketIndexTransactionWriter,
    TdxMarketIndexTransactionProvider,
)
from tdx_data_sdk.api.hq import AsyncTdxHq_API  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Manage market-index 3s observations and derived 1m canonical bars."
    )
    parser.add_argument("--catalog")
    sub = parser.add_subparsers(dest="command", required=True)

    inspect = sub.add_parser("inspect-baidu")
    inspect.add_argument("--zip", required=True)
    inspect.add_argument("--symbol", action="append", dest="symbols")

    import_baidu = sub.add_parser("import-baidu")
    import_baidu.add_argument("--zip", required=True)
    import_baidu.add_argument("--symbol", action="append", dest="symbols")
    import_baidu.add_argument("--trading-day")
    import_baidu.add_argument("--dataset-version", required=True)
    import_baidu.add_argument("--lake-dir")
    import_baidu.add_argument("--db-path")

    download_tdx = sub.add_parser("download-tdx-day")
    download_tdx.add_argument("--trading-day", required=True)
    download_tdx.add_argument("--symbol", action="append", dest="symbols")
    download_tdx.add_argument(
        "--endpoint", required=True, help="host:port known to use a DIRECT 7709 route"
    )
    download_tdx.add_argument("--dataset-version", required=True)
    download_tdx.add_argument("--lake-dir")
    download_tdx.add_argument("--db-path")

    derive = sub.add_parser("derive-1m")
    derive.add_argument("--source-dataset-version", required=True)
    derive.add_argument("--dataset-suffix", required=True)
    derive.add_argument("--previous-canonical-version")
    derive.add_argument("--no-publish-canonical", action="store_true")
    derive.add_argument("--lake-dir")
    derive.add_argument("--db-path")

    query = sub.add_parser("query")
    query.add_argument("--dataset-version", required=True)
    query.add_argument("--symbol", action="append", dest="symbols", required=True)
    query.add_argument("--start-time", required=True)
    query.add_argument("--end-time", required=True)
    query.add_argument("--limit", type=int, default=10000)
    query.add_argument("--db-path")

    args = parser.parse_args(argv)
    settings = Settings.load()
    catalog = MarketIndexCatalog(path=args.catalog)
    db_path = getattr(args, "db_path", None) or settings.metadata.sqlite_path
    lake_dir = getattr(args, "lake_dir", None) or settings.paths.lake_dir

    if args.command == "inspect-baidu":
        inspect_result = MarketIndexTransactionArchiveReader(
            catalog=catalog
        ).inspect_zip(zip_path=args.zip, symbols=args.symbols)
        print(json.dumps(asdict(inspect_result), ensure_ascii=False, indent=2))
        return 0
    if args.command == "import-baidu":
        records, receipt = MarketIndexTransactionArchiveReader(
            catalog=catalog
        ).read_zip(
            zip_path=args.zip,
            symbols=args.symbols,
            trading_day=args.trading_day,
        )
        write_result = MarketIndexTransactionWriter(
            lake_dir=lake_dir, db_path=db_path
        ).write_records(
            records=records,
            source_receipt=receipt,
            dataset_version=args.dataset_version,
        )
        print(json.dumps(asdict(write_result), ensure_ascii=False, indent=2))
        return 0
    if args.command == "download-tdx-day":
        records, receipt = asyncio.run(
            _download_tdx_day(
                endpoint=args.endpoint,
                trading_day=args.trading_day,
                symbols=args.symbols,
                catalog=catalog,
            )
        )
        tdx_write_result = MarketIndexTransactionWriter(
            lake_dir=lake_dir, db_path=db_path
        ).write_records(
            records=records,
            source_receipt=receipt,
            dataset_version=args.dataset_version,
        )
        print(json.dumps(asdict(tdx_write_result), ensure_ascii=False, indent=2))
        return 0
    if args.command == "derive-1m":
        derive_result = MarketIndexTransactionToMinuteBarsDeriver(
            lake_dir=lake_dir, db_path=db_path
        ).derive_and_publish(
            source_dataset_version=args.source_dataset_version,
            dataset_suffix=args.dataset_suffix,
            previous_canonical_version=args.previous_canonical_version,
            publish_canonical=not args.no_publish_canonical,
        )
        payload = asdict(derive_result)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.command == "query":
        query_result = MarketIndexTransactionQuery(db_path=db_path).query(
            dataset_version=args.dataset_version,
            symbols=args.symbols,
            start_time=args.start_time,
            end_time=args.end_time,
            limit=args.limit,
        )
        print(
            json.dumps(
                query_result.model_dump(mode="json"), ensure_ascii=False, indent=2
            )
        )
        return 0
    return 1


async def _download_tdx_day(
    *,
    endpoint: str,
    trading_day: str,
    symbols: list[str] | None,
    catalog: MarketIndexCatalog,
):
    host, port_text = endpoint.rsplit(":", 1)
    client = await AsyncTdxHq_API.factory(
        server=(host, int(port_text)),
        timeout=8,
        heartbeat=False,
        auto_retry=False,
        raise_exception=False,
    )
    if client is None:
        raise RuntimeError(f"TDX endpoint did not create a client: {endpoint}")
    try:
        return await TdxMarketIndexTransactionProvider(
            client, catalog=catalog
        ).fetch_day(trading_day=trading_day, symbols=symbols)
    finally:
        await client.close()


if __name__ == "__main__":
    raise SystemExit(main())
