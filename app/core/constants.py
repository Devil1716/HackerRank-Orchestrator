"""Stable domain constants shared by boundaries."""

from app.models.enums import ActionType, ConversationType, MessageType

Action = ActionType

__all__ = ["Action", "ConversationType", "MessageType"]
