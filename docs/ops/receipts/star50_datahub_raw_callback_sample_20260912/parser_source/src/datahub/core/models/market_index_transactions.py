# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MarketIndexTransactionsDataset(BaseModel):
    dataset_version: str | None = None
    schema_version: str = "market_index_transactions.v1"
    items: list[dict[str, Any]] = Field(default_factory=list)
    quality_summary: dict[str, Any] = Field(default_factory=dict)
