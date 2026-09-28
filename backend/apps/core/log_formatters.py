import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    """
    One JSON object per line, so log platforms (CloudWatch, Datadog, Loki...) can
    filter by level, logger or status code without parsing free text.
    """

    def format(self, record):
        entry = {
            "time": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Django's request logger attaches these to 4xx/5xx records.
        if hasattr(record, "status_code"):
            entry["status_code"] = record.status_code
        request = getattr(record, "request", None)
        if request is not None and hasattr(request, "path"):
            entry["method"] = request.method
            entry["path"] = request.path
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)
