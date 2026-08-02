"""Health endpoint payloads independent of any web framework."""

from pydantic import BaseModel, ConfigDict

from app.monitoring.health import HealthCheck


class HealthResponse(BaseModel):
    """Serializable application health response."""

    model_config = ConfigDict(frozen=True)

    status: str
    checks: tuple[HealthCheck, ...]


def build_health_response(checks: tuple[HealthCheck, ...]) -> HealthResponse:
    """Build an API-neutral response from health check results."""
    status = "ok" if all(check.status == "ok" for check in checks) else "degraded"
    return HealthResponse(status=status, checks=checks)
