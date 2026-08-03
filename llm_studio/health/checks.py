"""Read-only health checks for the local Windows desktop stack."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from llm_studio.capabilities import get_capabilities_for_config
from llm_studio.models.storage import layout_from_config
from llm_studio.version import get_version_info


@dataclass(frozen=True)
class HealthCheckResult:
    name: str
    status: str
    message: str
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "message": self.message,
            "details": self.details or {},
        }


class HealthChecker:
    """Build a lightweight or full health payload from initialized API state."""

    def __init__(self, state: Any):
        self.state = state
        self.config = getattr(state, "config", None)

    def run(self, *, full: bool = False) -> dict[str, Any]:
        checks = [
            self._server_alive(),
            self._configuration_loaded(),
            self._storage_writable(),
            self._database_accessible(),
            self._capabilities_consistent(),
        ]
        if full:
            checks.extend(
                [
                    self._job_queue_available(),
                    self._model_registry_available(),
                    self._adapter_registry_available(),
                    self._feature_flags_available(),
                ]
            )
        warnings = [check.message for check in checks if check.status == "warning"]
        return {
            "status": self._overall_status(checks),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": "full" if full else "quick",
            "version": get_version_info(),
            "checks": {check.name: check.to_dict() for check in checks},
            "warnings": warnings,
        }

    @staticmethod
    def _overall_status(checks: list[HealthCheckResult]) -> str:
        if any(check.status == "error" for check in checks):
            return "error"
        if any(check.status == "warning" for check in checks):
            return "warning"
        return "ok"

    def _server_alive(self) -> HealthCheckResult:
        return HealthCheckResult("server", "ok", "FastAPI application is running.")

    def _configuration_loaded(self) -> HealthCheckResult:
        if self.config is None:
            return HealthCheckResult("configuration", "error", "Configuration is not loaded.")
        return HealthCheckResult(
            "configuration",
            "ok",
            "Configuration is loaded.",
            {"config_file": Path(self.config.config_path).name},
        )

    def _storage_writable(self) -> HealthCheckResult:
        if self.config is None:
            return HealthCheckResult("storage", "error", "Configuration is required for storage checks.")
        try:
            layout = layout_from_config(self.config)
            layout.ensure()
            with NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=layout.diagnostics_dir,
                prefix="health-",
                suffix=".tmp",
                delete=False,
            ) as handle:
                handle.write("ok")
                temp_path = Path(handle.name)
            temp_path.unlink(missing_ok=True)
            return HealthCheckResult(
                "storage",
                "ok",
                "Managed data directories are writable.",
                {"diagnostics_dir": layout.diagnostics_dir.name},
            )
        except Exception as exc:
            return HealthCheckResult("storage", "error", f"Storage check failed: {exc}")

    def _database_accessible(self) -> HealthCheckResult:
        if self.config is None:
            return HealthCheckResult("database", "error", "Configuration is required for database checks.")
        db_path = self._novel_db_path()
        try:
            db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(db_path) as conn:
                conn.execute("SELECT 1")
                tables = {
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                }
            expected = {
                "novel_projects",
                "generation_records",
                "revision_records",
                "training_datasets",
                "finetune_runs",
                "evaluation_runs",
            }
            present = sorted(expected.intersection(tables))
            missing = sorted(expected.difference(tables))
            status = "ok" if not missing else "warning"
            return HealthCheckResult(
                "database",
                status,
                (
                    "Novel Studio database is accessible."
                    if not missing
                    else "Database is accessible; some stage tables are not initialized yet."
                ),
                {
                    "database_file": db_path.name,
                    "expected_tables_present": present,
                    "expected_tables_missing": missing,
                },
            )
        except Exception as exc:
            return HealthCheckResult("database", "error", f"Database check failed: {exc}")

    def _capabilities_consistent(self) -> HealthCheckResult:
        caps = {capability.name: capability for capability in get_capabilities_for_config(self.config)}
        required = {
            "novel_studio": "partial",
            "writing_workspace": "available",
            "revision_system": "available",
            "dataset_builder": "available",
            "finetune_center": "available",
            "novel_rag_memory": "available",
            "full_evaluation_center": "available",
            "novel_studio_product_ui": "available",
            "windows_desktop_release": "available",
            "health_checks": "available",
            "backup_restore": "available",
        }
        mismatches = {
            name: {
                "expected": expected,
                "actual": caps.get(name).status.value if caps.get(name) else None,
            }
            for name, expected in required.items()
            if caps.get(name) is None or caps[name].status.value != expected
        }
        if mismatches:
            return HealthCheckResult(
                "capabilities",
                "warning",
                "Capabilities are readable but do not all advertise the Stage 12 product surface.",
                {"mismatches": mismatches},
            )
        return HealthCheckResult(
            "capabilities",
            "ok",
            "Capabilities match the Stage 12 product surface.",
        )

    def _job_queue_available(self) -> HealthCheckResult:
        queue = getattr(self.state, "job_queue", None)
        repository = getattr(self.state, "job_repository", None)
        if queue is None or repository is None:
            return HealthCheckResult("job_queue", "warning", "Job queue has not been initialized.")
        return HealthCheckResult("job_queue", "ok", "Job queue is initialized.")

    def _model_registry_available(self) -> HealthCheckResult:
        repository = getattr(self.state, "model_repository", None)
        if repository is None:
            return HealthCheckResult("model_registry", "warning", "Model repository is not attached to API state.")
        return HealthCheckResult("model_registry", "ok", "Model repository is attached.")

    def _adapter_registry_available(self) -> HealthCheckResult:
        repository = getattr(self.state, "adapter_repository", None)
        if repository is None:
            return HealthCheckResult("adapter_registry", "warning", "Adapter repository is not attached to API state.")
        return HealthCheckResult("adapter_registry", "ok", "Adapter repository is attached.")

    def _feature_flags_available(self) -> HealthCheckResult:
        if self.config is None:
            return HealthCheckResult("feature_flags", "error", "Configuration is required for feature flags.")
        features = self.config.get("features", {})
        if not isinstance(features, dict):
            return HealthCheckResult("feature_flags", "error", "features must be a mapping.")
        enabled = sorted(
            name
            for name, value in features.items()
            if isinstance(value, dict) and value.get("enabled") is True
        )
        return HealthCheckResult(
            "feature_flags",
            "ok",
            "Feature flags are readable.",
            {"enabled": enabled},
        )

    def _novel_db_path(self) -> Path:
        assert self.config is not None
        novel_cfg = self.config.get("novels", {})
        db_value = novel_cfg.get("db_path", "./data/novels/novels.sqlite") if isinstance(novel_cfg, dict) else "./data/novels/novels.sqlite"
        db_path = Path(str(db_value))
        if not db_path.is_absolute():
            db_path = Path(self.config.config_path).parent / db_path
        return db_path.resolve()


def build_health_payload(state: Any, *, full: bool = False) -> dict[str, Any]:
    return HealthChecker(state).run(full=full)
