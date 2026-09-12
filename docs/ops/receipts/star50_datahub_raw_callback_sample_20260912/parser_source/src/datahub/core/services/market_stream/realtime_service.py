# -*- coding: utf-8 -*-
# ---
# module_primary: market-stream
# module_related: [adapters]
# governed_surface: realtime tick normalization logic
# ---
from __future__ import annotations

from datahub.core.models.stream import RealtimeEnvelope


class RealtimeService:
    def normalize_tick(self, raw: dict) -> RealtimeEnvelope:
        return RealtimeEnvelope(
            symbol=str(raw["symbol"]),
            market=str(raw.get("market", "cn_a")),
            timestamp=str(raw["timestamp"]),
            trading_day=str(raw["trading_day"]),
            last_price=float(raw["last_price"]),
            volume=float(raw["volume"]),
            amount=float(raw["amount"]),
            bid_price_1=float(raw["bid_price_1"]),
            ask_price_1=float(raw["ask_price_1"]),
            bid_volume_1=float(raw["bid_volume_1"]),
            ask_volume_1=float(raw["ask_volume_1"]),
            available_at=str(raw["available_at"]),
            source_kind=str(raw.get("source_kind", "tdx_hq_stub")),
            sequence_no=int(raw.get("sequence_no", 0)),
            stream_id=str(raw.get("stream_id", "stream_default")),
            meta={},
        )
