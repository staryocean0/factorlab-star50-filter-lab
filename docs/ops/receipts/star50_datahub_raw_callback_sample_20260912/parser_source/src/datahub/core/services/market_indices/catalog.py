# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable
import json


DEFAULT_MARKET_INDEX_CATALOG = (
    Path(__file__).resolve().parents[5]
    / "config"
    / "market_indices"
    / "core_market_indices.v1.json"
)


@dataclass(frozen=True, slots=True)
class MarketIndexDefinition:
    symbol: str
    index_code: str
    name_zh: str
    name_en: str
    publisher: str
    publisher_code: str
    exchange: str
    category: str
    launch_date: str
    tdx_market_code: int
    tdx_transaction_code: str | None
    source_archive_code: str | None
    official_url: str
    derivative_underlyings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["derivative_underlyings"] = list(self.derivative_underlyings)
        return payload


class MarketIndexCatalog:
    def __init__(self, *, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else DEFAULT_MARKET_INDEX_CATALOG
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != "datahub.market_index_catalog.v1":
            raise ValueError("unsupported market index catalog schema")
        self.catalog_id = str(payload.get("catalog_id") or "")
        self.product_contract = str(payload.get("product_contract") or "")
        self.market = str(payload.get("market") or "")
        self.instrument_type = str(payload.get("instrument_type") or "")
        self.frequency_capabilities = dict(payload.get("frequency_capabilities") or {})
        self.lifecycle_policy = dict(payload.get("lifecycle_policy") or {})
        self.definitions = tuple(
            _definition(item) for item in payload.get("indices") or []
        )
        self._validate()

    def select(
        self, symbols: Iterable[str] | None = None
    ) -> list[MarketIndexDefinition]:
        requested = {
            str(item or "").strip().upper()
            for item in (symbols or [])
            if str(item or "").strip()
        }
        if not requested:
            return list(self.definitions)
        matched = [
            item
            for item in self.definitions
            if item.symbol.upper() in requested or item.index_code.upper() in requested
        ]
        found = {
            value
            for item in matched
            for value in (item.symbol.upper(), item.index_code.upper())
        }
        missing = sorted(requested - found)
        if missing:
            raise ValueError(f"unknown market index symbols: {','.join(missing)}")
        return matched

    def payload(self) -> dict[str, Any]:
        return {
            "schema_version": "datahub.market_index_catalog.v1",
            "catalog_id": self.catalog_id,
            "product_contract": self.product_contract,
            "market": self.market,
            "instrument_type": self.instrument_type,
            "frequency_capabilities": self.frequency_capabilities,
            "lifecycle_policy": self.lifecycle_policy,
            "index_count": len(self.definitions),
            "indices": [item.to_dict() for item in self.definitions],
        }

    def _validate(self) -> None:
        if self.market != "cn_index" or self.instrument_type != "market_index":
            raise ValueError("market index catalog has invalid product identity")
        if not self.product_contract:
            raise ValueError("market index catalog must bind a product contract")
        contract_path = Path(__file__).resolve().parents[5] / self.product_contract
        if not contract_path.is_file():
            raise ValueError(
                f"market index product contract does not exist: {contract_path}"
            )
        if not self.definitions:
            raise ValueError("market index catalog is empty")
        symbols = [item.symbol for item in self.definitions]
        codes = [item.index_code for item in self.definitions]
        if len(symbols) != len(set(symbols)) or len(codes) != len(set(codes)):
            raise ValueError(
                "market index catalog symbols and index codes must be unique"
            )
        for item in self.definitions:
            expected_suffix = ".SH" if item.tdx_market_code == 1 else ".SZ"
            if item.tdx_market_code not in {0, 1} or not item.symbol.endswith(
                expected_suffix
            ):
                raise ValueError(
                    f"market index catalog TDX route mismatch: {item.symbol}"
                )
            if not item.official_url.startswith("https://"):
                raise ValueError(
                    f"market index official URL must use HTTPS: {item.symbol}"
                )
        daily = self.frequency_capabilities.get("1d") or {}
        if daily.get("status") != "supported":
            raise ValueError("market index catalog must declare governed 1d support")


def _definition(payload: dict[str, Any]) -> MarketIndexDefinition:
    required = (
        "symbol",
        "index_code",
        "name_zh",
        "name_en",
        "publisher",
        "publisher_code",
        "exchange",
        "category",
        "launch_date",
        "tdx_market_code",
        "official_url",
    )
    missing = [key for key in required if payload.get(key) in (None, "")]
    if missing:
        raise ValueError(
            f"market index catalog entry missing fields: {','.join(missing)}"
        )
    return MarketIndexDefinition(
        symbol=str(payload["symbol"]).strip().upper(),
        index_code=str(payload["index_code"]).strip(),
        name_zh=str(payload["name_zh"]).strip(),
        name_en=str(payload["name_en"]).strip(),
        publisher=str(payload["publisher"]).strip(),
        publisher_code=str(payload["publisher_code"]).strip().upper(),
        exchange=str(payload["exchange"]).strip().upper(),
        category=str(payload["category"]).strip(),
        launch_date=str(payload["launch_date"]).strip(),
        tdx_market_code=int(payload["tdx_market_code"]),
        tdx_transaction_code=(
            str(payload["tdx_transaction_code"]).strip()
            if payload.get("tdx_transaction_code")
            else None
        ),
        source_archive_code=(
            str(payload["source_archive_code"]).strip()
            if payload.get("source_archive_code")
            else None
        ),
        official_url=str(payload["official_url"]).strip(),
        derivative_underlyings=tuple(
            str(item).strip() for item in payload.get("derivative_underlyings") or []
        ),
    )
