# -*- coding: utf-8 -*-
# ---
# module_primary: market-stream
# module_related: [orchestration]
# governed_surface: recording coordination and lifecycle management
# ---
from __future__ import annotations

from datahub.core.services.recording_service import RecordingService


class RecordingCoordinator:
    def __init__(self, service: RecordingService) -> None:
        self._service = service

    def start(self, *, market: str, symbol_scope: list[str]) -> dict:
        return self._service.start(market=market, symbol_scope=symbol_scope)

    def stop(self) -> dict:
        return self._service.stop()

    async def on_tick(self, tick: dict) -> None:
        self._service.append_tick(tick)
        try:
            self._service.flush()
        except Exception:
            return

    def status(self) -> dict:
        return self._service.status()

    def datasets(self, *, trading_day: str | None, symbol: str | None) -> list[dict]:
        return self._service.list_datasets(trading_day=trading_day, symbol=symbol)
