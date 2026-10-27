"""SEC Companyfacts annual US-GAAP normalization, no network or paid data."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from investiq_core.adapters.sec_companyfacts import SecCompanyFactsProvider
from investiq_core.market import IssuerId
from investiq_core.ports import AnnualMetricsRequest, ProviderFailure, ProviderFailureCode

NOW = datetime(2026, 10, 27, 14, tzinfo=UTC)
ISSUER = IssuerId("SEC_CIK", "320193")
ACC = "0000320193-26-000001"


def annual(value, *, filed="2026-02-11", accession=ACC, **changes):
    record = {
        "start": "2025-01-01", "end": "2025-12-31",
        "filed": filed, "accn": accession,
        "form": "10-K", "fp": "FY", "fy": 2025, "val": value,
    }
    record.update(changes)
    return record


def companyfacts(*, cik=320193):
    return {
        "cik": cik,
        "entityName": "Synthetic Issuer",
        "facts": {"us-gaap": {
            "EarningsPerShareDiluted": {
                "units": {"USD/shares": [
                    annual(Decimal("6.125")),
                    annual(Decimal("3.50"), start="2024-01-01", end="2024-12-31",
                           filed="2025-02-11", accession="0000320193-25-000001"),
                    annual(Decimal("9.99"), filed="2026-10-27",
                           accession="0000320193-26-000099"),
                    annual(Decimal(999), form="10-Q", fp="Q3"),
                ]}
            },
            "RevenueFromContractWithCustomerExcludingAssessedTax": {
                "units": {"USD": [annual(150_000_000)]}
            },
            "NetIncomeLoss": {"units": {"USD": [annual(90_000_000)]}},
            "NetCashProvidedByUsedInOperatingActivities": {
                "units": {"USD": [annual(15_000_000)]}
            },
        }},
    }


class FakeHTTP:
    def __init__(self, payload):
        self.payload = payload
        self.requests = []

    async def get_json(self, url, *, headers):
        self.requests.append((url, dict(headers)))
        return self.payload


def fetch(payload, *, at=NOW):
    fake = FakeHTTP(payload)
    provider = SecCompanyFactsProvider(
        user_agent="InvestIQ Tests developer@example.org",
        transport=fake, clock=lambda: NOW,
    )
    items = asyncio.run(provider.get_annual_metrics(AnnualMetricsRequest(ISSUER, at)))
    return items, fake


def test_sec_annual_facts_preserve_exact_money_period_accession_and_source():
    rows, transport = fetch(companyfacts())
    facts = {item.metric: item for item in rows}
    assert set(facts) == {"diluted_eps", "revenue", "net_income", "operating_cash_flow"}
    assert facts["diluted_eps"].value == Decimal("6.125")
    assert facts["diluted_eps"].currency == "USD"
    assert facts["diluted_eps"].period_start.isoformat() == "2025-01-01"
    assert facts["diluted_eps"].period_end.isoformat() == "2025-12-31"
    assert facts["diluted_eps"].filed_on.isoformat() == "2026-02-11"
    assert facts["diluted_eps"].accession == ACC
    assert facts["diluted_eps"].tag == "EarningsPerShareDiluted"
    assert facts["diluted_eps"].retrieved_at == NOW
    assert "companyfacts/CIK0000320193.json" in facts["diluted_eps"].source_reference
    assert facts["revenue"].value == Decimal(150_000_000)
    assert transport.requests[0][1]["User-Agent"].endswith("developer@example.org")


def test_sec_filters_same_day_filing_and_later_amended_annual_fact():
    payload = companyfacts()
    payload["facts"]["us-gaap"]["EarningsPerShareDiluted"]["units"]["USD/shares"].append(
        annual(Decimal("7.25"), filed="2026-07-01",
               accession="0000320193-26-000055", form="10-K/A")
    )
    rows, _ = fetch(payload)
    eps = next(f for f in rows if f.metric == "diluted_eps")
    assert eps.value == Decimal("7.25")
    assert eps.accession == "0000320193-26-000055"
    rows, _ = fetch(payload, at=datetime(2026, 7, 1, 23, tzinfo=UTC))
    eps = next(f for f in rows if f.metric == "diluted_eps")
    assert eps.value == Decimal("6.125")


def test_conflicting_latest_annual_tags_yield_gap_not_arbitrary_revenue():
    payload = companyfacts()
    payload["facts"]["us-gaap"]["Revenues"] = {
        "units": {"USD": [annual(Decimal(188000000))]}
    }
    rows, _ = fetch(payload)
    assert "revenue" not in {item.metric for item in rows}
    assert "diluted_eps" in {item.metric for item in rows}


@pytest.mark.parametrize("bad", ["cik", "floats", "period", "time", "quarter", "noeps"])
def test_sec_rejects_wrong_entity_and_ignores_unsupported_annual_fact_context(bad):
    payload = companyfacts()
    if bad == "cik":
        payload["cik"] = "7777777777"
        with pytest.raises(ProviderFailure) as error:
            fetch(payload)
        assert error.value.code == ProviderFailureCode.INVALID_RESPONSE
        return
    container = payload["facts"]["us-gaap"]["EarningsPerShareDiluted"]["units"]["USD/shares"]
    if bad == "floats":
        container[0]["val"] = 6.125  # Fake adapter cannot inject float as reported exact
    elif bad == "period":
        container[0]["start"] = "2025-10-01"
    elif bad == "time":
        container[0]["filed"] = "2035-02-01"
    elif bad == "quarter":
        container[0]["form"] = "10-Q"
    elif bad == "noeps":
        del payload["facts"]["us-gaap"]["EarningsPerShareDiluted"]
    rows, _ = fetch(payload)
    assert "diluted_eps" not in {item.metric for item in rows} or (
        next(f for f in rows if f.metric == "diluted_eps").value == Decimal("3.50")
    )


def test_sec_requires_exact_issuer_and_current_nonfuture_cutoff():
    payload = companyfacts()
    payload["cik"] = "0000320193"
    rows, _ = fetch(payload)
    assert rows
    fake = FakeHTTP(payload)
    provider = SecCompanyFactsProvider(
        user_agent="InvestIQ Tests developer@example.org",
        transport=fake, clock=lambda: NOW,
    )
    with pytest.raises(ProviderFailure) as error:
        asyncio.run(provider.get_annual_metrics(
            AnnualMetricsRequest(ISSUER, datetime(2026, 10, 28, tzinfo=UTC))
        ))
    assert error.value.code == ProviderFailureCode.UNSUPPORTED_REQUEST
    with pytest.raises(ProviderFailure) as error:
        asyncio.run(provider.get_annual_metrics(
            AnnualMetricsRequest(IssuerId("LEI", "0123456789"), NOW)
        ))
    assert error.value.code == ProviderFailureCode.UNSUPPORTED_INSTRUMENT
