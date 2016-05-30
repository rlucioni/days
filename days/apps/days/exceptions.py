"""Custom exceptions."""


class ForcedRollback(Exception):
    """Raised when intentionally rolling back a transaction."""
    pass
