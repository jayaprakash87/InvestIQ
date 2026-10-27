"""Conservative connected issuer analysis from SEC annual facts and entitled prices.

No synthetic source data, forward earnings estimates, implicit FX conversions,
saved research history or automatic investment ratings are generated here.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from ..evidence import ValueUnit
from ..fundamentals import AnnualMetricFact
from ..market import (
    IssuerListing,
    PriceAdjustment,
    QuoteFreshness,
    QuoteKind,
    resolve_issuer,
)
from ..ports import (
    AnnualMetricsRequest,
    DataCapability,
    FundamentalsProvider,
    ProviderFailure,
    ProviderFailureCode,
    QuoteRequest,
)
from ..valuation import ScenarioAnalysis, ValuationScenario, evaluate_scenarios
from .connected_data import ConnectedDataService, QuoteResult


@dataclass(frozen=True, slots=True)
class CompanyResearchRequest:
    listing: IssuerListing
    max_quote_age: timedelta
    analyst_confirmed_share_basis: bool = False
    share_basis_rationale: str | None = None
    scenario_years: int | None = None
    scenarios: tuple[ValuationScenario, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.listing, IssuerListing):
            raise TypeError("listing must be IssuerListing")
        if not isinstance(self.max_quote_age, timedelta) or self.max_quote_age <= timedelta(0):
            raise ValueError("max_quote_age must be a positive timedelta")
        if not isinstance(self.analyst_confirmed_share_basis, bool):
            raise TypeError("analyst_confirmed_share_basis must be a boolean")
        if self.analyst_confirmed_share_basis and (
            not isinstance(self.share_basis_rationale, str)
            or not self.share_basis_rationale.strip()
        ):
            raise ValueError("confirmed share basis requires an analyst rationale")
        if (self.scenario_years is None) != (not self.scenarios):
            raise ValueError("scenario_years and nonempty scenarios must be provided together")
        if self.scenario_years is not None and (
            type(self.scenario_years) is not int or self.scenario_years <= 0
        ):
            raise ValueError("scenario_years must be a positive integer")
        if not isinstance(self.scenarios, tuple) or any(
            not isinstance(s, ValuationScenario) for s in self.scenarios
        ):
            raise TypeError("scenarios must be a tuple of ValuationScenario")


@dataclass(frozen=True, slots=True)
class CompanyResearchResult:
    """Transient view. Holding a quote in memory is NOT permission to persist it."""

    issuer: str
    observed_at: datetime
    quote: QuoteResult
    annual_facts: tuple[AnnualMetricFact, ...]
    annual_pe_proxy: Decimal | None
    scenarios: ScenarioAnalysis | None
    warnings: tuple[str, ...]


class ConnectedResearchService:
    def __init__(
        self,
        *,
        data: ConnectedDataService,
        fundamentals: FundamentalsProvider,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._data = data
        self._fundamentals = fundamentals
        self._clock = clock or (lambda: datetime.now(UTC))

    async def analyze(
        self, request: CompanyResearchRequest, *, refresh: bool = False
    ) -> CompanyResearchResult:
        if not isinstance(request, CompanyResearchRequest):
            raise TypeError("request must be CompanyResearchRequest")
        now = self._clock()
        if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("clock must return a timezone-aware datetime")
        now_utc = now.astimezone(UTC)
        listing = request.listing
        issuer = resolve_issuer(
            [listing], instrument=listing.instrument, on=now_utc.date()
        )
        if not self._fundamentals.capabilities.has(DataCapability.FUNDAMENTALS):
            raise ProviderFailure(
                self._fundamentals.capabilities.provider,
                ProviderFailureCode.UNSUPPORTED_REQUEST,
                "Provider does not support annual fundamentals",
            )
        observations = await self._fundamentals.get_annual_metrics(
            AnnualMetricsRequest(issuer=issuer, as_of=now_utc)
        )
        if not isinstance(observations, tuple) or any(
            not isinstance(item, AnnualMetricFact)
            or item.issuer != issuer
            or item.filed_on >= now_utc.date()
            or item.retrieved_at.astimezone(UTC) > now_utc
            for item in observations
        ):
            raise ProviderFailure(
                self._fundamentals.capabilities.provider,
                ProviderFailureCode.INVALID_RESPONSE,
                "Annual fundamentals have invalid issuer or date context",
            )
        if len({fact.metric for fact in observations}) != len(observations):
            raise ProviderFailure(
                self._fundamentals.capabilities.provider,
                ProviderFailureCode.INVALID_RESPONSE,
                "Duplicate annual financial concepts were returned",
            )
        price = await self._data.quote(
            QuoteRequest(listing.instrument, kind=QuoteKind.CLOSE),
            max_age=request.max_quote_age,
            allow_cache=not refresh,
        )
        warnings: list[str] = [
            "SEC filing dates do not verify an exact public-release instant; not an intraday as-of backtest.",
            "Annual diluted EPS is not forward EPS or trailing-twelve-month earnings.",
        ]
        if price.quote.timeliness.value == "unknown":
            warnings.append("Quote delivery entitlement/delay is unverified; do not label it live.")
        if price.quote.adjustment == PriceAdjustment.UNKNOWN:
            warnings.append("Quote adjustment/split basis is unknown; compatibility needs analyst review.")
        if price.freshness != QuoteFreshness.WITHIN_POLICY:
            warnings.append("Quote fails the supplied age policy; current valuation suppressed.")
        annual_pe: Decimal | None = None
        analysis: ScenarioAnalysis | None = None
        eps = next((f for f in observations if f.metric == "diluted_eps"), None)
        if eps is None:
            warnings.append("Annual reported diluted EPS not available from supported SEC tags.")
        else:
            for item in observations:
                if item.metric != "diluted_eps" and (
                    item.period_start != eps.period_start or item.period_end != eps.period_end
                ):
                    warnings.append(
                        f"{item.metric} reports a different annual fiscal period; do not combine directly."
                    )
            if eps.value <= 0:
                warnings.append("Nonpositive diluted EPS: P/E and EPS-growth scenarios are not applicable.")
            elif eps.unit != ValueUnit.MONEY_PER_SHARE or eps.currency != price.quote.currency:
                warnings.append("EPS unit/currency incompatible with quote; explicit FX conversion required.")
            elif price.quote.event_at.astimezone(UTC).date() <= eps.filed_on:
                warnings.append("Price precedes or overlaps the filing date; no supported time alignment.")
            elif not request.analyst_confirmed_share_basis:
                warnings.append(
                    "Issuer-wide diluted EPS may not match this share class or split basis; "
                    "analyst confirmation required before calculating P/E."
                )
            elif price.freshness == QuoteFreshness.WITHIN_POLICY:
                annual_pe = price.quote.price / eps.value
                # This is only a conditional, user-specified scenario model.
                # Float calculations are approximate; inputs retain Decimal originals.
                if request.scenarios:
                    analysis = evaluate_scenarios(
                        start_eps=float(eps.value),
                        initial_price=float(price.quote.price),
                        years=request.scenario_years,
                        scenarios=request.scenarios,
                    )
                    warnings.append(
                        "Scenario growth, terminal multiples and weights are analyst assumptions, "
                        "not measured probabilities or forecast earnings."
                    )
        if request.scenarios and analysis is None:
            warnings.append("Requested scenario analysis withheld because valuation inputs are incompatible.")
        return CompanyResearchResult(
            issuer=f"{issuer.namespace}:{issuer.value}",
            observed_at=now_utc,
            quote=price,
            annual_facts=observations,
            annual_pe_proxy=annual_pe,
            scenarios=analysis,
            warnings=tuple(dict.fromkeys(warnings)),
        )
