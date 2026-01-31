from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def _message_from_detail(detail):
    """Turn DRF exception .detail (str, list, or dict) into a single string."""
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        return detail[0] if detail else "Validation error"
    if isinstance(detail, dict):
        for key in ("non_field_errors", "error", "detail"):
            if key in detail and detail[key]:
                val = detail[key]
                return val[0] if isinstance(val, list) else val
        first_key = next(iter(detail))
        first_val = detail[first_key]
        return first_val[0] if isinstance(first_val, list) else str(first_val)
    return str(detail)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return None

    message = _message_from_detail(response.data)
    response.data = {"error": message}
    return response