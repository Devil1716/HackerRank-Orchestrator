"""Health checks are deterministic and read-only."""

from pathlib import Path

from app.monitoring.health import check_paths


def test_health_reports_existing_and_missing_paths(tmp_path: Path) -> None:
    """Report the state of configured paths without mutating them."""
    checks = check_paths(tmp_path, tmp_path / "missing")
    assert checks[0].status == "ok"
    assert checks[1].status == "degraded"
