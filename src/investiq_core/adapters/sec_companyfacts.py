"""SEC EDGAR Companyfacts adapter with conservative annual GAAP selection.

Only a small set of us-gaap concepts and 10-K / 10-K/A annual vintages.
Fiscal-year filings are not intraday-publication proof, and XBRL frame labels
are never assumed to establish issuer-specific fiscal comparability.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Callable
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from ..evidence import ValueUnit
from ..fundamentals import AnnualMetricFact
from ..ports import (
    AnnualMetricsRequest,
    DataCapability,
    ProviderCapabilities,
    ProviderFailure,
    ProviderFailureCode,
)
from ._errors import translate_error
from ._http import (
    JsonTransport,
    TransportInvalidResponseError,
    TransportStatusError,
    TransportTimeoutError,
    TransportUnavailableError,
    UrllibJsonTransport,
)
from .sec_edgar import SecEdgarFilingProvider

SEC_COMPANYFACTS_ORIGIN = "https://data.sec.gov/api/xbrl/companyfacts/"

# Conservative, explicitly mapped concepts only. No derived FCF or TTM.
_ANNUAL_TAGS: tuple[tuple[str, str, ValueUnit, str], ...] = (
    ("diluted_eps", "EarningsPerShareDiluted", ValueUnit.MONEY_PER_SHARE, "USD/shares"),
    ("revenue", "RevenueFromContractWithCustomerExcludingAssessedTax", ValueUnit.MONEY, "USD"),
    ("revenue", "Revenues", ValueUnit.MONEY, "USD"),
    ("net_income", "NetIncomeLoss", ValueUnit.MONEY, "USD"),
    ("operating_cash_flow", "NetCashProvidedByUsedInOperatingActivities", ValueUnit.MONEY, "USD"),
)


class SecCompanyFactsProvider(SecEdgarFilingProvider):
    """Read annual US-GAAP facts for a known CIK with the SEC pacing policy.

    Default 8-MB bound permits typical companyfacts responses; no provider
    data is saved, cached or copied into the public repository.
    """

    capabilities = ProviderCapabilities(
        "SEC EDGAR", frozenset({DataCapability.FUNDAMENTALS, DataCapability.FILINGS})
    )

    def __init__(
        self,
        *,
        user_agent: str,
        transport: JsonTransport | None = None,
        clock: Callable[[], datetime] | None = None,
        min_interval_seconds: float = 1.0,
    ) -> None:
        super().__init__(
            user_agent=user_agent,
            transport=transport if transport is not None else UrllibJsonTransport(max_bytes=8_000_000),
            clock=clock,
            min_interval_seconds=min_interval_seconds,
        )

    async def get_annual_metrics(
        self, request: AnnualMetricsRequest
    ) -> tuple[AnnualMetricFact, ...]:
        if not isinstance(request, AnnualMetricsRequest):
            raise TypeError("request must be AnnualMetricsRequest")
        issuer = request.issuer
        if issuer.namespace != "SEC_CIK" or re.fullmatch(r"[0-9]{1,10}", issuer.value) is None:
            raise ProviderFailure(
                "SEC EDGAR", ProviderFailureCode.UNSUPPORTED_INSTRUMENT,
                "Only explicit SEC CIK issuer IDs are supported",
            )
        cik = int(issuer.value)
        if not cik:
            raise ProviderFailure(
                "SEC EDGAR", ProviderFailureCode.UNSUPPORTED_INSTRUMENT, "SEC CIK must be nonzero"
            )
        url = f"{SEC_COMPANYFACTS_ORIGIN}CIK{cik:010d}.json"
        async with self._lock:
            loop = asyncio.get_running_loop()
            if self._last_request is not None:
                wait = self._interval - (loop.time() - self._last_request)
                if wait > 0:
                    await asyncio.sleep(wait)
            self._last_request = loop.time()
            try:
                payload = await self._transport.get_json(
                    url, headers={"User-Agent": self._user_agent}
                )
            except (
                TransportStatusError,
                TransportTimeoutError,
                TransportUnavailableError,
                TransportInvalidResponseError,
            ) as error:
                raise translate_error("SEC EDGAR", error) from None
        fetched = self._clock()
        if not isinstance(fetched, datetime) or fetched.tzinfo is None or fetched.utcoffset() is None:
            raise ValueError("SEC clock must return a timezone-aware datetime")
        if request.as_of.astimezone(UTC) > fetched.astimezone(UTC):
            raise ProviderFailure(
                "SEC EDGAR", ProviderFailureCode.UNSUPPORTED_REQUEST,
                "Cannot analyze a future filing cutoff",
            )
        try:
            return _annual_facts(payload, request, cik, fetched, url)
        except (KeyError, TypeError, ValueError, OverflowError):
            raise ProviderFailure(
                "SEC EDGAR", ProviderFailureCode.INVALID_RESPONSE,
                "SEC Companyfacts response failed structural validation",
            ) from None


def _annual_facts(
    payload: Any, request: AnnualMetricsRequest, cik: int, fetched: datetime, url: str
) -> tuple[AnnualMetricFact, ...]:
    if not isinstance(payload, dict):
        raise TypeError("SEC Companyfacts must be an object")
    raw_cik = payload.get("cik")
    if type(raw_cik) is int:
        actual_cik = raw_cik
    elif isinstance(raw_cik, str) and re.fullmatch(r"[0-9]{1,10}", raw_cik):
        actual_cik = int(raw_cik)
    else:
        raise ValueError("Invalid SEC CIK")
    if actual_cik != cik:
        raise ValueError("Companyfacts issuer mismatch")
    facts = payload["facts"]
    if not isinstance(facts, dict):
        raise TypeError("facts must be an object")
    gaap = facts.get("us-gaap", {})
    if not isinstance(gaap, dict):
        raise TypeError("us-gaap must be an object")

    # A filed calendar date is not a verified UTC dissemination instant:
    # exclude the entire as-of calendar day, conservatively.
    cutoff = request.as_of.astimezone(UTC).date()
    selected: dict[str, list[AnnualMetricFact]] = {}
    for metric, tag, unit, unit_key in _ANNUAL_TAGS:
        concept = gaap.get(tag)
        if concept is None:
            continue
        if not isinstance(concept, dict) or not isinstance(concept.get("units"), dict):
            raise TypeError("invalid SEC concept/units object")
        raw_rows = concept["units"].get(unit_key, [])
        if not isinstance(raw_rows, list):
            raise TypeError("XBRL units data must be an array")
        for row in raw_rows:
            if not isinstance(row, dict):
                raise TypeError("XBRL fact must be an object")
            if row.get("form") not in ("10-K", "10-K/A") or row.get("fp") != "FY":
                continue
            try:
                start = date.fromisoformat(row["start"])
                end = date.fromisoformat(row["end"])
                filed = date.fromisoformat(row["filed"])
                accn = row["accn"]
                value = row["val"]
            except (KeyError, TypeError, ValueError):
                # A selected FY fact with incomplete context is unusable,
                # not an invitation to guess its period or filing.
                continue
            if (
                not isinstance(accn, str)
                or not re.fullmatch(r"[0-9]{10}-[0-9]{2}-[0-9]{6}", accn)
                or filed >= cutoff
                or filed < end
                or end > cutoff
                or not 330 <= (end - start).days + 1 <= 395
            ):
                continue
            if type(value) is int:
                number = Decimal(value)
            elif isinstance(value, Decimal):
                number = value
            else:
                # JSON floats are parsed as Decimal by the default transport.
                # Do not interpret Python binary floats from custom transports.
                continue
            if not number.is_finite():
                continue
            try:
                selected.setdefault(metric, []).append(
                    AnnualMetricFact(
                        issuer=request.issuer,
                        metric=metric,
                        value=number,
                        unit=unit,
                        currency="USD",
                        period_start=start,
                        period_end=end,
                        accession=accn,
                        filed_on=filed,
                        source_reference=url,
                        taxonomy="us-gaap",
                        tag=tag,
                        retrieved_at=fetched,
                    )
                )
            except (TypeError, ValueError):
                continue

    results: list[AnnualMetricFact] = []
    for metric, rows in selected.items():
        if not rows:
            continue
        # Current (not historical snapshot) vintage of the latest annual
        # period; latest filed form can amend/restate an older annual period.
        latest_period = max((row.period_end, row.period_start) for row in rows)
        period_rows = [
            row for row in rows if (row.period_end, row.period_start) == latest_period
        ]
        latest_filing = max(row.filed_on for row in period_rows)
        latest = [row for row in period_rows if row.filed_on == latest_filing]
        # Conflicting tags/accessions for same filing day are ambiguous.
        if len({(r.value, r.currency, r.unit) for r in latest}) > 1:
            continue
        # Prefer deterministic representation of duplicated/reported facts.
        results.append(min(latest, key=lambda r: (r.accession, r.tag)))
    return tuple(sorted(results, key=lambda item: item.metric))
