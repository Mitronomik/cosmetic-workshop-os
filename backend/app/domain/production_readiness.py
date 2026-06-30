from enum import StrEnum


class ProductionReadinessStatus(StrEnum):
    READY = "ready"
    BLOCKED = "blocked"
    WARNING = "warning"


class ProductionReadinessSeverity(StrEnum):
    BLOCKING = "blocking"
    WARNING = "warning"
    INFO = "info"


__all__ = ["ProductionReadinessSeverity", "ProductionReadinessStatus"]
