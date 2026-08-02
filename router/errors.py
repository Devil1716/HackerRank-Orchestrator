"""Typed Router Agent failures."""


class RouterError(Exception):
    """Base Router Agent failure."""


class ProviderError(RouterError):
    """Provider invocation failed."""


class InvalidDecisionError(RouterError):
    """Provider output could not be validated."""


class PromptBudgetError(RouterError):
    """Prompt could not fit the configured budget."""
