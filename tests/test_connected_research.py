"""Current company research: numeric, provenance and negative-case acceptance."""

import asyncio
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from investiq_core.application.connected_data import ConnectedDataService
from investiq_core.application.connected_research import (
    CompanyResearchRequest,
    ConnectedResearchService,
)
from investiq_core.evidence import InstrumentId, ValueUnit
from investiq_core.fundamentals import AnnualMetricFact
from investiq_core.market import (
    IssuerId,
    IssuerListing,
    MarketQuote,
    MarketSession,
    QuoteKind,
    QuoteTimeliness,
)
from investiq_core.ports import DataCapability, ProviderCapabilities, ProviderFailure
from investiq_core.valuation import ValuationScenario

NOW = datetime(2026, 10, 27, 14, tzinfo=UTC)
ISSUER = IssuerId("SEC_CIK", "0000320193")
INSTRUMENT = InstrumentId("DEMO", "XNAS", "USD")
LISTING = IssuerListing(
    issuer=ISSUER, instrument=INSTRUMENT, effective_from=date(2020, 1, 1),
    source_reference="synthetic:issuer-listing", verified_at=NOW,
)


def quote(price="125.50", *, seconds=20, timeliness=QuoteTimeliness.UNKNOWN):
    return MarketQuote(
        quote_id="synthetic:minute-close",
        instrument=INSTRUMENT,
        provider="Synthetic Quote",
        provider_symbol="DEMO",
        source_reference="synthetic:quote",
        kind=QuoteKind.CLOSE,
        price=Decimal(price),
        currency="USD",
        event_at=NOW - timedelta(seconds=seconds),
        received_at=NOW - timedelta(seconds=5),
        session=MarketSession.CLOSED,
        timeliness=timeliness,
        entitlement_scope="synthetic:no-storage",
    )


def fact(metric="diluted_eps", value="6.125", *, currency="USD",
         unit=ValueUnit.MONEY_PER_SHARE):
    return AnnualMetricFact(
        issuer=ISSUER, metric=metric, value=Decimal(value), unit=unit,
        currency=currency, period_start=date(2025, 1, 1),
        period_end=date(2025, 12, 31),
        accession="0000320193-26-000001", filed_on=date(2026, 2, 11),
        source_reference="https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json",
        taxonomy="us-gaap", tag="EarningsPerShareDiluted", retrieved_at=NOW,
    )


class FakeQuote:
    capabilities = ProviderCapabilities(
        "Synthetic Quote", frozenset({DataCapability.QUOTES})
    )

    def __init__(self, observed=None):
        self.observed = observed if observed is not None else quote()
        self.calls = 0

    async def get_quote(self, request):
        self.calls += 1
        return self.observed


class FakeFilings:
    capabilities = ProviderCapabilities(
        "Synthetic Filings", frozenset({DataCapability.FILINGS})
    )

    async def list_filings(self, request):
        return ()


class FakeFundamentals:
    capabilities = ProviderCapabilities(
        "Synthetic Annual", frozenset({DataCapability.FUNDAMENTALS})
    )

    def __init__(self, facts=None):
        self.facts = tuple(facts) if facts is not None else (fact(),)
        self.calls = 0

    async def get_annual_metrics(self, request):
        self.calls += 1
        return self.facts


def research(*, quote_provider=None, facts_provider=None):
    price = quote_provider if quote_provider is not None else FakeQuote()
    facts = facts_provider if facts_provider is not None else FakeFundamentals()
    connected = ConnectedDataService(
        quote_provider=price, filing_provider=FakeFilings(),
        principal_scope="one-researcher", clock=lambda: NOW,
    )
    return ConnectedResearchService(
        data=connected, fundamentals=facts, clock=lambda: NOW
    ), price, facts


def request(*, confirmed=False, rationale=None, years=None, scenarios=(),
            max_age=timedelta(minutes=5)):
    return CompanyResearchRequest(
        listing=LISTING, max_quote_age=max_age,
        analyst_confirmed_share_basis=confirmed,
        share_basis_rationale=rationale,
        scenario_years=years, scenarios=scenarios,
    )


def run(coro):
    return asyncio.run(coro)


def test_source_attribution_and_unverified_basis_suppress_plausible_wrong_pe():
    app, provider, fundamentals = research()
    outcome = run(app.analyze(request()))
    assert outcome.issuer == "SEC_CIK:0000320193"
    assert outcome.quote.quote.price == Decimal("125.50")
    assert outcome.quote.freshness.value == "within_policy"
    assert outcome.annual_facts[0].value == Decimal("6.125")
    assert outcome.annual_facts[0].source_reference.startswith("https://data.sec.gov/")
    assert outcome.annual_pe_proxy is None
    assert any("analyst confirmation" in w for w in outcome.warnings)
    assert any("not forward" in w for w in outcome.warnings)
    assert any("not label it live" in w for w in outcome.warnings)
    assert provider.calls == fundamentals.calls == 1


def test_confirmed_basis_enables_only_honestly_labeled_annual_pe():
    app, _, _ = research()
    outcome = run(app.analyze(request(
        confirmed=True, rationale="Checked share class and split basis against SEC filing"
    )))
    assert outcome.annual_pe_proxy == Decimal("125.50") / Decimal("6.125")
    assert outcome.scenarios is None
    assert outcome.quote.quote.rights.allows("snapshot") is False


@pytest.mark.parametrize("negative", ["0", "-1.25"])
def test_nonpositive_eps_is_not_a_meaningful_pe_or_growth_scenario(negative):
    app, _, _ = research(facts_provider=FakeFundamentals((fact(value=negative),)))
    outcome = run(app.analyze(request(confirmed=True, rationale="verified")))
    assert outcome.annual_pe_proxy is None
    assert any("Nonpositive" in s for s in outcome.warnings)


def test_currency_mismatch_and_stale_close_suppress_valuation():
    app, _, _ = research(facts_provider=FakeFundamentals((fact(currency="EUR"),)))
    mismatch = run(app.analyze(request(confirmed=True, rationale="verified")))
    assert mismatch.annual_pe_proxy is None
    assert any("FX conversion" in item for item in mismatch.warnings)
    app, _, _ = research(quote_provider=FakeQuote(quote(seconds=400)))
    stale = run(app.analyze(request(confirmed=True, rationale="verified")))
    assert stale.annual_pe_proxy is None
    assert any("current valuation suppressed" in item for item in stale.warnings)


def test_no_eps_and_different_fiscal_periods_show_explicit_gaps():
    net_income = fact("net_income", "1000000", unit=ValueUnit.MONEY)
    app, _, _ = research(facts_provider=FakeFundamentals((net_income,)))
    empty_eps = run(app.analyze(request(confirmed=True, rationale="verified")))
    assert empty_eps.annual_pe_proxy is None
    assert any("not available" in item for item in empty_eps.warnings)
    older_revenue = replace(
        net_income, metric="revenue", period_start=date(2024, 1, 1),
        period_end=date(2024, 12, 31),
    )
    app, _, _ = research(facts_provider=FakeFundamentals((fact(), older_revenue)))
    outcome = run(app.analyze(request(confirmed=True, rationale="verified")))
    assert any("different annual fiscal period" in item for item in outcome.warnings)


def test_optional_explicit_scenarios_use_existing_deterministic_engine():
    scenarios = (
        ValuationScenario("bear", -0.02, 13, 0.2),
        ValuationScenario("base", 0.08, 21, 0.6),
        ValuationScenario("bull", 0.18, 29, 0.2),
    )
    app, _, _ = research()
    out = run(app.analyze(request(
        confirmed=True, rationale="Verified quote/earnings share basis",
        years=3, scenarios=scenarios,
    )))
    assert out.scenarios is not None
    assert len(out.scenarios.outcomes) == 3
    assert out.scenarios.expected_terminal_price > 0
    assert any("analyst assumptions" in w for w in out.warnings)
    with pytest.raises(ValueError, match="together"):
        request(years=3)
    with pytest.raises(ValueError, match="rationale"):
        request(confirmed=True)


def test_refresh_changes_current_price_without_modifying_provider_facts():
    q = FakeQuote()
    fundamentals = FakeFundamentals()
    app, _, _ = research(quote_provider=q, facts_provider=fundamentals)
    request_ = request(confirmed=True, rationale="matched and verified")
    first = run(app.analyze(request_))
    q.observed = quote("150.00")
    second = run(app.analyze(request_, refresh=True))
    assert first.annual_pe_proxy != second.annual_pe_proxy
    assert first.annual_facts == second.annual_facts
    assert q.calls == fundamentals.calls == 2


def test_invalid_issuer_filing_cutoff_and_duplicate_metric_are_rejected():
    wrong = replace(fact(), issuer=IssuerId("SEC_CIK", "0000777777"))
    for facts in ((wrong,), (fact(), fact())):
        app, _, _ = research(facts_provider=FakeFundamentals(facts))
        with pytest.raises(ProviderFailure):
            run(app.analyze(request()))


def test_issuer_mapping_expired_rejected_before_vendor_calls():
    expiring = replace(LISTING, effective_until=date(2020, 12, 31))
    app, q, fundamentals = research()
    with pytest.raises(ValueError, match="no issuer mapping"):
        run(app.analyze(CompanyResearchRequest(
            listing=expiring, max_quote_age=timedelta(minutes=5)
        )))
    assert q.calls == 0 and fundamentals.calls == 0


def test_price_before_annual_filing_date_does_not_support_pe():
    old = quote(seconds=20)
    old = replace(
        old, event_at=datetime(2026, 2, 10, tzinfo=UTC),
        received_at=datetime(2026, 2, 10, 1, tzinfo=UTC),
    )
    app, _, _ = research(quote_provider=FakeQuote(old))
    result = run(app.analyze(request(confirmed=True, rationale="verified",
                                     max_age=timedelta(days=300))))
    assert result.annual_pe_proxy is None
    assert any("Price precedes" in w for w in result.warnings)


def test_annual_fact_is_reported_only_no_estimated_eps_guessed():
    app, _, _ = research(facts_provider=FakeFundamentals(()))
    result = run(app.analyze(request()))
    assert result.annual_facts == ()
    assert result.annual_pe_proxy is None
    assert result.scenarios is None
