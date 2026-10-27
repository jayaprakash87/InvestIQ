"""Map transport failures to the stable, public ProviderFailure taxonomy."""

from __future__ import annotations

from ..ports import ProviderFailure, ProviderFailureCode
from ._http import (
    TransportInvalidResponseError,
    TransportStatusError,
    TransportTimeoutError,
    TransportUnavailableError,
)


def translate_error(provider: str, error: Exception) -> ProviderFailure:
    if isinstance(error, TransportStatusError):
        if error.status == 401:
            code = ProviderFailureCode.UNAUTHORIZED
        elif error.status == 403:
            code = ProviderFailureCode.ENTITLEMENT_DENIED
        elif error.status == 404:
            code = ProviderFailureCode.MISSING_DATA
        elif error.status == 429:
            code = ProviderFailureCode.RATE_LIMITED
        elif error.status >= 500:
            code = ProviderFailureCode.TEMPORARILY_UNAVAILABLE
        else:
            code = ProviderFailureCode.INVALID_RESPONSE
        return ProviderFailure(
            provider, code, "Provider HTTP request failed",
            retry_after_seconds=(
                error.retry_after_seconds if code == ProviderFailureCode.RATE_LIMITED else None
            ),
        )
    if isinstance(error, TransportTimeoutError):
        return ProviderFailure(provider, ProviderFailureCode.TIMEOUT, "Provider request timed out")
    if isinstance(error, TransportUnavailableError):
        return ProviderFailure(
            provider, ProviderFailureCode.TEMPORARILY_UNAVAILABLE, "Provider unavailable"
        )
    if isinstance(error, TransportInvalidResponseError):
        return ProviderFailure(
            provider, ProviderFailureCode.INVALID_RESPONSE, "Provider response was invalid"
        )
    return ProviderFailure(provider, ProviderFailureCode.INVALID_RESPONSE, "Invalid provider response")
