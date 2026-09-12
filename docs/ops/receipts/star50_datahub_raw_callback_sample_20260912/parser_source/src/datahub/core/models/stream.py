# -*- coding: utf-8 -*-
from __future__ import annotations

from pydantic import BaseModel, Field


class RealtimeEnvelope(BaseModel):
    symbol: str
    market: str = "cn_a"
    timestamp: str
    trading_day: str
    last_price: float
    volume: float
    amount: float
    bid_price_1: float
    ask_price_1: float
    bid_volume_1: float
    ask_volume_1: float
    available_at: str
    source_kind: str = "stub"
    sequence_no: int = 0
    stream_id: str = "stream_default"
    meta: dict[str, str] = Field(default_factory=dict)
