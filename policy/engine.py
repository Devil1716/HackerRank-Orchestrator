"""Deterministic policy checks before and after Router reasoning."""

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.models import ActionType, Decision, DecisionPacket


@dataclass(frozen=True)
class PolicyDirective:
    """Immutable policy result carried from pre-routing to enforcement."""

    policy_version: str = "policy-v1"
    forced_action: ActionType | None = None
    reasons: tuple[str, ...] = ()


class PolicyEngine:
    """Evaluate safety, urgency, relationship, and quiet-hour policies."""

    def before_router(self, packet: DecisionPacket) -> PolicyDirective:
        """Compute policy constraints from deterministic packet signals."""
        reasons: list[str] = []
        forced_action: ActionType | None = None
        if self.is_explicit_scam(packet) and (
            packet.signals.spam.value >= 0.85 or packet.signals.risk.value >= 0.85
        ):
            forced_action = ActionType.MUTE
            reasons.append("spam_or_critical_risk_override")
        elif packet.signals.urgency.value >= 0.85 and packet.signals.risk.value < 0.75:
            forced_action = ActionType.NOTIFY
            reasons.append("emergency_override")
        elif self._quiet_hours(packet) and packet.signals.urgency.value < 0.75:
            forced_action = ActionType.DIGEST
            reasons.append("quiet_hours")
        return PolicyDirective(forced_action=forced_action, reasons=tuple(reasons))

    def after_router(
        self, packet: DecisionPacket, decision: Decision, directive: PolicyDirective
    ) -> Decision:
        """Enforce the pre-routing directive so the Router cannot violate policy."""
        if directive.forced_action is None or decision.action in (
            directive.forced_action,
            ActionType.MUTE,
        ):
            return decision
        reason = "Policy override ({}): {}".format(
            directive.policy_version, "; ".join(directive.reasons)
        )
        return decision.model_copy(
            update={
                "action": directive.forced_action,
                "reason": f"{reason}. {decision.reason}",
                "confidence": min(decision.confidence, 0.99),
            }
        )

    @staticmethod
    def _quiet_hours(packet: DecisionPacket) -> bool:
        window = packet.context.recipient.do_not_disturb_window
        if not window:
            return False
        try:
            start_text, end_text = window.split("-", maxsplit=1)
            start_hour, start_minute = (int(value) for value in start_text.split(":", 1))
            end_hour, end_minute = (int(value) for value in end_text.split(":", 1))
            current = packet.context.message.created_at.astimezone(
                ZoneInfo(packet.context.recipient.timezone)
            )
            if not isinstance(current, datetime):
                return False
            current_minutes = current.hour * 60 + current.minute
            start = start_hour * 60 + start_minute
            end = end_hour * 60 + end_minute
            return (
                current_minutes >= start or current_minutes < end
                if start > end
                else start <= current_minutes < end
            )
        except (TypeError, ValueError, ZoneInfoNotFoundError):
            return False

    @staticmethod
    def is_explicit_scam(packet: DecisionPacket) -> bool:
        """Identify high-precision scam language before applying a hard mute."""
        text = packet.context.message.message_text.lower()
        return any(
            term in text
            for term in ("otp", "password", "prize", "lottery", "click here", "verify account")
        )
