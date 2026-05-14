import logging
import sys
import uuid
from contextvars import ContextVar

# ContextVar to store request/correlation ID
correlation_id: ContextVar[str] = ContextVar("correlation_id", default="system")

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        from app.core.context import tenant_id, unit_id, sector_id
        
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "correlation_id": correlation_id.get(),
            "tenant_id": str(tenant_id.get()) if tenant_id.get() else None,
            "unit_id": str(unit_id.get()) if unit_id.get() else None,
            "sector_id": str(sector_id.get()) if sector_id.get() else None,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add any extra fields passed in the 'extra' dict
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
            
        import json
        return json.dumps(log_data)

def setup_logging():
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    
    if not logger.handlers:
        logger.addHandler(handler)
    
    return logger

logger = setup_logging()
