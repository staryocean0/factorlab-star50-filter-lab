# -*- coding: utf-8 -*-
# ---
# module_primary: market-stream
# module_related: [orchestration]
# governed_surface: recording logic and state Transitions
# ---
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from datahub.core.models.dataset import DataQualityReport
from datahub.orchestration.recording_state_machine import RecordingStateMachine
from datahub.orchestration.states import RecordingStatus
from datahub.storage.repositories.dataset_versions import DatasetVersionRepository
from datahub.storage.repositories.quality_reports import QualityReportRepository
from datahub.storage.repositories.recording_datasets import RecordingDatasetRepository
from datahub.storage.repositories.recording_runtime import RecordingRuntimeRepository
from datahub.storage.writer import StorageWriter


class RecordingService:
    def __init__(self, *, base_dir: str | Path, db_path: str | Path) -> None:
        self._writer = StorageWriter(base_dir=base_dir)
        self._runtime_repo = RecordingRuntimeRepository(db_path=db_path)
        self._datasets_repo = RecordingDatasetRepository(db_path=db_path)
        self._dataset_versions_repo = DatasetVersionRepository(db_path=db_path)
        self._quality_reports_repo = QualityReportRepository(db_path=db_path)
        self._state_machine = RecordingStateMachine()
        self._buffer: list[dict] = []
        self._runtime_id = "default"
        self._market = "cn_a"
        self._trading_day: str | None = None
        self._symbol_scope: list[str] = []
        self._consecutive_flush_failures = 0
        self._flush_failure_threshold = 3

    def start(self, *, market: str, symbol_scope: list[str]) -> dict:
        now = datetime.now(timezone.utc)
        trading_day = now.date().isoformat()
        normalized_scope = sorted(set(symbol_scope))
        current = self._runtime_repo.get(self._runtime_id)
        current_state = current["state"] if current else RecordingStatus.IDLE.value

        if not self._state_machine.can_start(current_state):
            if (
                current_state in {RecordingStatus.RECORDING.value, RecordingStatus.FLUSHING.value}
                and current["market"] == market
                and current["symbol_scope"] == normalized_scope
            ):
                return self.status()

        self._buffer.clear()
        self._consecutive_flush_failures = 0
        self._market = market
        self._trading_day = trading_day
        self._symbol_scope = normalized_scope

        # Transition to STARTING first
        self._runtime_repo.upsert(
            runtime_id=self._runtime_id,
            state=RecordingStatus.STARTING.value,
            market=market,
            symbol_scope=self._symbol_scope,
            trading_day=trading_day,
            started_at=now.isoformat(),
        )

        # Then to RECORDING
        self._runtime_repo.upsert(
            runtime_id=self._runtime_id,
            state=RecordingStatus.RECORDING.value,
            market=market,
            symbol_scope=self._symbol_scope,
            trading_day=trading_day,
            started_at=now.isoformat(),
        )
        return self.status()

    def append_tick(self, tick: dict) -> None:
        runtime = self._runtime_repo.get(self._runtime_id)
        if runtime is None or runtime["state"] not in {"RECORDING", "FLUSHING"}:
            return
        self._buffer.append(
            {
                "symbol": tick["symbol"],
                "market": tick["market"],
                "timestamp": tick["timestamp"],
                "trading_day": tick["trading_day"],
                "last_price": tick["last_price"],
                "volume": tick["volume"],
                "amount": tick["amount"],
                "bid_price_1": tick["bid_price_1"],
                "ask_price_1": tick["ask_price_1"],
                "bid_volume_1": tick["bid_volume_1"],
                "ask_volume_1": tick["ask_volume_1"],
                "available_at": tick["available_at"],
                "source_kind": tick.get("source_kind", "stub"),
                "sequence_no": tick.get("sequence_no", 0),
                "stream_id": tick.get("stream_id", "stream_default"),
            }
        )

    def flush(self, *, fail_fast: bool = False) -> dict | None:
        runtime = self._runtime_repo.get(self._runtime_id)
        if runtime is None or not self._state_machine.can_flush(runtime["state"]):
            return None
        if not self._buffer:
            return None
        self._runtime_repo.upsert(
            runtime_id=self._runtime_id,
            state=RecordingStatus.FLUSHING.value,
            market=self._market,
            symbol_scope=self._symbol_scope,
            trading_day=self._trading_day,
            started_at=runtime["started_at"],
        )
        dataset_version = (
            f"recording_{self._market}_{self._trading_day}_{uuid4().hex[:8]}"
        )
        rows = list(self._buffer)
        quality_report = DataQualityReport(
            report_id=f"quality_{dataset_version}",
            target_dataset_version=dataset_version,
            duplicate_count=0,
            null_counts={},
            quality_score=100.0,
            generated_at=rows[-1]["timestamp"],
        )
        try:
            result = self._writer.commit_recording_dataset(
                dataset_version=dataset_version,
                rows=rows,
                market=self._market,
                trading_day=str(self._trading_day),
                symbol_scope=self._symbol_scope,
                quality_report=quality_report,
            )
        except Exception:
            self._consecutive_flush_failures += 1
            target_state = (
                RecordingStatus.FAILED.value
                if fail_fast
                or self._consecutive_flush_failures >= self._flush_failure_threshold
                else RecordingStatus.RECORDING.value
            )
            self._runtime_repo.upsert(
                runtime_id=self._runtime_id,
                state=target_state,
                market=self._market,
                symbol_scope=self._symbol_scope,
                trading_day=self._trading_day,
                started_at=runtime["started_at"],
            )
            raise
        self._quality_reports_repo.save(
            report_id=result["quality_report"].report_id,
            dataset_version=result["dataset_version"],
            report=result["quality_report"],
        )
        self._datasets_repo.save(
            dataset_version=result["dataset_version"],
            market=result["market"],
            trading_day=result["trading_day"],
            symbol_scope=result["symbol_scope"],
            storage_uri=result["storage_uri"],
            record_count=result["record_count"],
        )
        self._dataset_versions_repo.save(
            dataset_version=result["dataset_version"],
            dataset_id="recording_ticks",
            dataset_kind="recording",
            state="READY",
            market=result["market"],
            frequency="tick",
            time_range_start=rows[0]["timestamp"],
            time_range_end=rows[-1]["timestamp"],
            storage_uri=result["storage_uri"],
            manifest_id=result["manifest"].manifest_id,
            quality_report_id=result["quality_report"].report_id,
        )
        self._consecutive_flush_failures = 0
        self._buffer.clear()
        self._runtime_repo.upsert(
            runtime_id=self._runtime_id,
            state=RecordingStatus.RECORDING.value,
            market=self._market,
            symbol_scope=self._symbol_scope,
            trading_day=self._trading_day,
            started_at=runtime["started_at"],
        )
        return result

    def stop(self) -> dict:
        try:
            self.flush(fail_fast=True)
        except Exception:
            return self.status()
        runtime = self._runtime_repo.get(self._runtime_id)
        if runtime is None or not self._state_machine.can_stop(runtime["state"]):
            return self._idle_status()

        # Transition to STOPPING
        self._runtime_repo.upsert(
            runtime_id=self._runtime_id,
            state=RecordingStatus.STOPPING.value,
            market=runtime["market"],
            symbol_scope=runtime["symbol_scope"],
            trading_day=runtime["trading_day"],
            started_at=runtime["started_at"],
        )

        self._runtime_repo.upsert(
            runtime_id=self._runtime_id,
            state=RecordingStatus.STOPPED.value,
            market=runtime["market"],
            symbol_scope=runtime["symbol_scope"],
            trading_day=runtime["trading_day"],
            started_at=runtime["started_at"],
        )
        self._consecutive_flush_failures = 0
        return self.status()


    def status(self) -> dict:
        runtime = self._runtime_repo.get(self._runtime_id)
        if runtime is None:
            return self._idle_status()
        latest_dataset = self._datasets_repo.list()[:1]
        state_map = {
            "IDLE": "idle",
            "STARTING": "starting",
            "RECORDING": "recording",
            "FLUSHING": "recording",
            "STOPPING": "stopping",
            "STOPPED": "stopped",
            "FAILED": "failed",
        }
        return {
            "runtime_id": runtime["runtime_id"],
            "state": state_map.get(runtime["state"], "idle"),
            "market": runtime["market"],
            "trading_day": runtime["trading_day"],
            "symbol_scope": runtime["symbol_scope"],
            "started_at": runtime["started_at"],
            "active_streams": len(runtime["symbol_scope"]),
            "last_dataset_version": latest_dataset[0].dataset_version
            if latest_dataset
            else None,
        }

    def list_datasets(
        self, *, trading_day: str | None = None, symbol: str | None = None
    ) -> list[dict]:
        return self._datasets_repo.list(trading_day=trading_day, symbol=symbol)

    @staticmethod
    def _idle_status() -> dict:
        return {
            "runtime_id": "default",
            "state": "idle",
            "market": None,
            "trading_day": None,
            "symbol_scope": [],
            "started_at": None,
            "active_streams": 0,
            "last_dataset_version": None,
        }
